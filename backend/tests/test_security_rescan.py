"""Regression tests for provider and audio boundaries found by the rescan.

Provider calls are mocked. Controllers are AST-loaded to avoid optional ML SDKs;
the real FastAPI verified-user dependency and database plan policy are exercised.
"""

import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Depends, HTTPException, Request, status
from answerai.models.auths import Auths
from answerai.models.config import Config
from answerai.utils import plans
from answerai.utils.auth import get_current_user, get_verified_user
from answerai.utils.json_codec import JSONCodec

pytest_plugins = ['test_email_verification']


def controller(name, namespace):
    source = Path(__file__).parents[1] / 'answerai/routers/openai.py'
    node = next(n for n in ast.parse(source.read_text()).body if isinstance(n, ast.AsyncFunctionDef) and n.name == name)
    node.decorator_list = []
    namespace.update(
        Request=Request,
        Depends=Depends,
        get_verified_user=get_verified_user,
        HTTPException=HTTPException,
        status=status,
        JSONCodec=JSONCodec,
    )
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(source), 'exec'), namespace)
    return namespace[name]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'method,path',
    [
        ('GET', 'files/local-proof/content'),
        ('DELETE', 'files/local-proof'),
        ('POST', 'unused/../chat/completions'),
        ('POST', 'unused/../responses'),
    ],
)
@pytest.mark.parametrize('billing_enabled', [True, False])
async def test_restricted_member_cannot_use_provider_passthrough(harness, method, path, billing_enabled):
    client, _, _, app, _ = harness
    user = await Auths.insert_new_auth('scan@example.com', 'test-hash', 'Scan', role='user')
    app.dependency_overrides[get_current_user] = lambda: user
    values = plans.BillingSettings(enabled=billing_enabled).model_dump()
    values['free'].update(models=['allowed'], messages_per_day=0, requests_per_minute=0)
    await Config.upsert({'billing.settings': values})
    upstream = SimpleNamespace(headers={}, status=200, json=AsyncMock(return_value={'proof': 'mock-provider-data'}))
    session = SimpleNamespace(request=AsyncMock(return_value=upstream))
    target = controller(
        'proxy',
        {
            'ENABLE_OPENAI_API_PASSTHROUGH': True,
            'get_openai_connection': AsyncMock(return_value=('https://provider.invalid/v1', 'fake-key', {})),
            'get_headers_and_cookies': AsyncMock(return_value=({'Authorization': 'Bearer fake-key'}, {})),
            'get_session': AsyncMock(return_value=session),
            'AIOHTTP_CLIENT_SESSION_SSL': True,
            'get_client_timeout': Mock(return_value=None),
            'cleanup_response': AsyncMock(),
            'log': Mock(),
        },
    )
    app.state.OPENAI_MODELS = {'restricted': {'urlIdx': 0}}
    app.add_api_route('/openai/{path:path}', target, methods=['GET', 'POST', 'PUT', 'DELETE'])
    # Encode dot segments so the HTTP client does not normalize before ASGI routing.
    encoded = path.replace('..', '%2E%2E')
    result = await client.request(method, '/openai/' + encoded, json={'model': 'restricted'})
    if result.status_code == 200:
        session.request.assert_awaited_once()
        assert result.json() == {'proof': 'mock-provider-data'}
        assert session.request.await_args.kwargs['headers']['Authorization'] == 'Bearer fake-key'
        from yarl import URL

        assert str(URL(session.request.await_args.kwargs['url'])) == 'https://provider.invalid/v1/' + path.replace(
            'unused/../', ''
        )
    assert result.status_code == 403


@pytest.mark.asyncio
async def test_speech_respects_zero_request_limit(harness, tmp_path):
    import hashlib
    import aiofiles
    from fastapi.responses import FileResponse

    client, _, _, app, _ = harness
    user = await Auths.insert_new_auth('speech-scan@example.com', 'test-hash', 'Scan', role='user')
    app.dependency_overrides[get_current_user] = lambda: user
    values = plans.BillingSettings(enabled=True).model_dump()
    values['free'].update(models=['allowed'], messages_per_day=0, requests_per_minute=0)
    await Config.upsert({'billing.settings': values})

    async def chunks(_):
        yield b'mock audio'

    upstream = SimpleNamespace(raise_for_status=Mock(), content=SimpleNamespace(iter_chunked=chunks))
    session = SimpleNamespace(post=AsyncMock(return_value=upstream))
    target = controller(
        'speech',
        {
            'has_permission': AsyncMock(return_value=True),
            'Config': Config,
            'get_openai_runtime_config': AsyncMock(return_value=(True, ['https://api.openai.com/v1'], [], {})),
            'get_openai_connection': AsyncMock(return_value=('https://provider.invalid/v1', 'fake-key', {})),
            'get_headers_and_cookies': AsyncMock(return_value=({}, {})),
            'get_session': AsyncMock(return_value=session),
            'AIOHTTP_CLIENT_SESSION_SSL': True,
            'CACHE_DIR': tmp_path,
            'hashlib': hashlib,
            'aiofiles': aiofiles,
            'FileResponse': FileResponse,
            'log': Mock(),
        },
    )
    app.add_api_route('/openai/audio/speech', target, methods=['POST'])
    result = await client.post('/openai/audio/speech', json={'model': 'restricted-tts', 'input': 'local proof'})
    if result.status_code == 200:
        session.post.assert_awaited_once()
        assert result.content == b'mock audio'
    assert result.status_code in {403, 429}


@pytest.mark.asyncio
@pytest.mark.parametrize('path,code', [('/openai/chat/completions', 403), ('/openai/files', 403)])
async def test_canonical_routes_reject_restricted_member(harness, path, code):
    client, _, _, app, _ = harness
    user = await Auths.insert_new_auth('control@example.com', 'test-hash', 'Control', role='user')
    app.dependency_overrides[get_current_user] = lambda: user
    values = plans.BillingSettings(enabled=True).model_dump()
    values['free'].update(models=['allowed'], messages_per_day=0, requests_per_minute=0)
    await Config.upsert({'billing.settings': values})

    async def protected(current=Depends(get_verified_user)):
        return {'unexpected': True}

    app.add_api_route(path, protected, methods=['POST'])
    result = await client.post(path, json={'model': 'restricted'})
    assert result.status_code == code
