"""System-level policy regressions for the ANSWERAI feature integration."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy import select

from answerai.internal.db import get_async_db
from answerai.models.auths import Auths
from answerai.models.billing import BillingAccount, UsageBucket
from answerai.models.config import Config
from answerai.routers.admin_controls import target_user
from answerai.utils import payments, plans
from answerai.utils.auth import get_current_user, get_verified_user
from answerai.utils.email_verification import EmailSettings
from answerai.utils.security_policy import validate_speech_input
from test_security_rescan import controller

pytest_plugins = ['test_email_verification']
AUDIO_PATHS = ['/openai/audio/speech', '/api/v1/audio/speech', '/api/v1/audio/transcriptions']


async def configure_member(app, **free):
    user = await Auths.insert_new_auth('review@example.com', 'test-hash', 'Review', role='user')
    app.dependency_overrides[get_current_user] = lambda: user
    values = plans.BillingSettings(enabled=True).model_dump()
    values['free'].update(free)
    await Config.upsert({'billing.settings': values})
    return user


@pytest.mark.asyncio
async def test_audio_entry_points_share_atomic_budget(harness):
    client, _, _, app, _ = harness
    user = await configure_member(app, requests_per_minute=10, audio_requests_per_day=1)

    async def accepted(current=Depends(get_verified_user)):
        return {'ok': True}

    for path in AUDIO_PATHS:
        app.add_api_route(path, accepted, methods=['POST'])
    assert (await client.post(AUDIO_PATHS[0], json={'input': 'hello'})).status_code == 200
    for path in AUDIO_PATHS[1:]:
        result = await client.post(path, json={'input': 'hello'})
        assert result.status_code == 429
        assert 'Retry-After' in result.headers
    async with get_async_db() as db:
        rows = (await db.scalars(select(UsageBucket).where(UsageBucket.user_id == user.id))).all()
        assert {row.metric: row.used for row in rows} == {'audio': 1, 'requests': 1}


@pytest.mark.asyncio
async def test_blocked_account_cannot_use_audio_when_billing_disabled(harness):
    client, _, _, app, _ = harness
    user = await configure_member(app)
    await Config.upsert({'billing.settings': {'enabled': False}})
    async with get_async_db() as db:
        db.add(BillingAccount(user_id=user.id, override='blocked', override_until=0))
        await db.commit()

    async def accepted(current=Depends(get_verified_user)):
        return {'ok': True}

    for path in AUDIO_PATHS:
        app.add_api_route(path, accepted, methods=['POST'])
        assert (await client.post(path, json={'input': 'hello'})).status_code == 403


@pytest.mark.asyncio
async def test_invalid_generation_json_returns_client_error(harness):
    client, _, _, app, _ = harness
    await configure_member(app)

    async def accepted(current=Depends(get_verified_user)):
        return {'ok': True}

    app.add_api_route('/openai/chat/completions', accepted, methods=['POST'])
    result = await client.post(
        '/openai/chat/completions', content=b'{broken', headers={'Content-Type': 'application/json'}
    )
    assert result.status_code == 400


@pytest.mark.asyncio
@pytest.mark.parametrize('enabled', [False, True])
async def test_provider_proxy_preserves_explicit_admin_opt_in(harness, enabled):
    client, _, _, app, admin = harness
    app.dependency_overrides[get_current_user] = lambda: admin
    upstream = SimpleNamespace(headers={}, status=200, json=AsyncMock(return_value={'proof': 'admin'}))
    session = SimpleNamespace(request=AsyncMock(return_value=upstream))
    target = controller(
        'proxy',
        {
            'ENABLE_OPENAI_API_PASSTHROUGH': enabled,
            'get_openai_connection': AsyncMock(return_value=('https://provider.invalid/v1', 'fake-key', {})),
            'get_headers_and_cookies': AsyncMock(return_value=({}, {})),
            'get_session': AsyncMock(return_value=session),
            'AIOHTTP_CLIENT_SESSION_SSL': True,
            'get_client_timeout': Mock(return_value=None),
            'cleanup_response': AsyncMock(),
            'log': Mock(),
        },
    )
    app.add_api_route('/openai/{path:path}', target, methods=['GET'])
    result = await client.get('/openai/files')
    assert result.status_code == (200 if enabled else 403)
    assert session.request.await_count == int(enabled)


@pytest.mark.parametrize(
    'payload,code',
    [
        (b'not-json', 400),
        (b'[]', 400),
        (b'{"input": 123}', 400),
        (b'{"input": " "}', 400),
        (json.dumps({'input': 'x' * 4097}).encode(), 413),
        (json.dumps({'input': 'ok', 'extra': 'x' * 65536}).encode(), 413),
    ],
)
def test_speech_payload_rejects_unbounded_or_invalid_input(payload, code):
    with pytest.raises(HTTPException) as exc:
        validate_speech_input(payload)
    assert exc.value.status_code == code


def test_speech_payload_accepts_supported_boundary():
    assert validate_speech_input(json.dumps({'input': 'x' * 4096}).encode())['input'] == 'x' * 4096


@pytest.mark.parametrize(
    'url',
    ['https://answerai.in:wrong', 'https://answerai.in:99999', 'https://answer ai.in', 'https://answerai.in/\tbad'],
)
def test_email_settings_reject_broken_public_links(url):
    with pytest.raises(ValidationError):
        EmailSettings(public_url=url)


@pytest.mark.asyncio
async def test_admin_account_lookup_normalizes_email(harness):
    user = await configure_member(harness[3])
    assert (await target_user('  REVIEW@EXAMPLE.COM  ')).id == user.id
    assert (await target_user('  ' + user.id + '  ')).id == user.id


@pytest.mark.parametrize('provider', ['stripe', 'razorpay'])
@pytest.mark.parametrize('signature', ['é', 'x' * 4097])
def test_webhook_invalid_signature_is_client_error(provider, signature):
    with pytest.raises(HTTPException) as exc:
        payments.verify_signature(provider, b'{}', signature)
    assert exc.value.status_code == 400
