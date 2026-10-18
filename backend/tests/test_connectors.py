import ast
import asyncio
import base64
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import aiohttp
import pytest
from answerai.utils.connectors import (
    PROBES,
    ConnectorCredentialForm,
    check_connector_credentials,
    connector_catalog,
    credential_status,
    normalize_connector_result,
)
from fastapi import Depends, FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError


@pytest.mark.parametrize('connector_id', list(PROBES))
def test_native_templates_only_include_read_operations(connector_id):
    template = next(p for p in connector_catalog() if p['id'] == connector_id)
    assert template['read_only'] is True
    assert template['url'].startswith('https://')
    assert template['auth_type'] == 'bearer'
    operation_ids = []
    for path, methods in template['spec']['paths'].items():
        assert set(methods) == {'get'}
        operation_ids.append(methods['get']['operationId'])
        for param in methods['get']['parameters']:
            if param['in'] == 'path':
                assert '{' + param['name'] + '}' in path
                assert param['required'] is True
    assert len(operation_ids) == len(set(operation_ids))
    assert 'key' not in template


def test_catalog_returns_copies():
    values = connector_catalog()
    values[0]['name'] = 'changed'
    assert connector_catalog()[0]['name'] != 'changed'


@pytest.mark.parametrize('connector_id', ['https://attacker.invalid', 'file:///etc/passwd', 'notion', 'unknown'])
def test_probe_destination_cannot_be_supplied_by_client(connector_id):
    with pytest.raises(ValidationError):
        ConnectorCredentialForm(connector_id=connector_id, key='test-token')


@pytest.mark.parametrize('key', ['', ' ', 'abc\r\nInjected: value', 'a' * 16385])
def test_invalid_tokens_are_rejected(key):
    with pytest.raises(ValidationError):
        ConnectorCredentialForm(connector_id='gmail', key=key)


@pytest.mark.parametrize(
    'status,body,expected',
    [
        (401, {}, 'unauthorized'),
        (403, {}, 'forbidden'),
        (429, {}, 'rate_limited'),
        (302, {}, 'unavailable'),
        (503, {}, 'unavailable'),
        (200, None, 'unavailable'),
        (200, {'ok': False, 'error': 'invalid_auth'}, 'unauthorized'),
        (200, {'ok': False, 'error': 'missing_scope'}, 'forbidden'),
        (200, {'ok': False, 'error': 'ratelimited'}, 'rate_limited'),
        (200, {'error': {'message': 'sensitive-provider-text'}}, 'unavailable'),
    ],
)
def test_provider_failures_are_classified_without_echoing_response(status, body, expected):
    result = credential_status(status, body)
    assert result['status'] == expected
    assert 'sensitive-provider-text' not in json.dumps(result)


class Body:
    def __init__(self, data):
        self.data = data

    async def readexactly(self, count):
        if len(self.data) < count:
            raise asyncio.IncompleteReadError(self.data, count)
        return self.data[:count]


class Response:
    def __init__(self, status=200, body=None, raw=None):
        self.status = status
        self.content = Body(raw if raw is not None else json.dumps(body).encode())

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'connector_id,body',
    [
        ('github', {'login': 'fixture-user'}),
        ('gmail', {'emailAddress': 'fixture@example.com'}),
        ('slack', {'ok': True}),
        ('google-drive', {'user': {}}),
        ('google-calendar', {'kind': 'calendar#calendarList'}),
    ],
)
async def test_probe_is_bounded_and_never_returns_account_data(connector_id, body):
    calls = []

    class Session:
        def get(self, url, **kwargs):
            calls.append((url, kwargs))
            return Response(body=body)

    form = ConnectorCredentialForm(connector_id=connector_id, key='fixture-access-token')
    result = await check_connector_credentials(form, Session())
    assert result['status'] == 'connected'
    assert calls[0][0] == PROBES[connector_id]
    assert calls[0][1]['allow_redirects'] is False
    assert calls[0][1]['timeout'].total == 15
    assert calls[0][1]['headers']['Authorization'] == 'Bearer fixture-access-token'
    assert 'fixture' not in json.dumps(result)
    assert 'fixture-access-token' not in repr(form)


@pytest.mark.asyncio
@pytest.mark.parametrize('response', [Response(raw=b'not json'), Response(raw=b'x' * 65537), Response(body={})])
async def test_unexpected_account_responses_do_not_claim_connection(response):
    session = SimpleNamespace(get=lambda *a, **kw: response)
    result = await check_connector_credentials(ConnectorCredentialForm(connector_id='gmail', key='fixture'), session)
    assert result['status'] == 'unavailable'


@pytest.mark.asyncio
async def test_probe_exception_cannot_leak_credentials():
    class Session:
        def get(self, *args, **kwargs):
            raise aiohttp.ClientError('SECRET-ACCESS-TOKEN')

    result = await check_connector_credentials(
        ConnectorCredentialForm(connector_id='gmail', key='SECRET-ACCESS-TOKEN'), Session()
    )
    assert result['status'] == 'unavailable'
    assert 'SECRET' not in json.dumps(result)


def test_gmail_text_is_decoded_without_changing_other_connectors_or_source_data():
    encoded = base64.urlsafe_b64encode('Hello from Gmail ✓'.encode()).decode().rstrip('=')
    original = {
        'payload': {
            'mimeType': 'multipart/alternative',
            'parts': [{'mimeType': 'text/plain', 'body': {'data': encoded}}],
        }
    }
    result = normalize_connector_result({'info': {'connector_id': 'gmail'}}, original)
    assert result['payload']['parts'][0]['body']['text'] == 'Hello from Gmail ✓'
    assert 'data' not in result['payload']['parts'][0]['body']
    assert original['payload']['parts'][0]['body']['data'] == encoded
    assert normalize_connector_result({'info': {'connector_id': 'slack'}}, original) is original


def test_gmail_invalid_data_and_attachments_are_preserved():
    original = {'payload': {'mimeType': 'text/plain', 'body': {'data': '%%%'}}}
    assert normalize_connector_result({'info': {'connector_id': 'gmail'}}, original) == original
    attachment = {'mimeType': 'application/pdf', 'body': {'data': 'aGVsbG8'}}
    assert normalize_connector_result({'info': {'connector_id': 'gmail'}}, attachment) == attachment


@pytest.mark.asyncio
async def test_catalog_and_probe_require_admin_and_honor_plugin_switch():
    source = Path(__file__).parents[1] / 'answerai/routers/configs.py'
    nodes = [
        n
        for n in ast.parse(source.read_text()).body
        if isinstance(n, ast.AsyncFunctionDef) and n.name in {'get_connector_catalog', 'test_connector_credentials'}
    ]
    authorized = False

    async def admin():
        if not authorized:
            raise HTTPException(403, 'Admin required')
        return SimpleNamespace(id='admin')

    from fastapi import APIRouter

    router = APIRouter()
    namespace = {
        'router': router,
        'Depends': Depends,
        'get_admin_user': admin,
        'HTTPException': HTTPException,
        'ENABLE_TOOL_SERVERS': True,
        'connector_catalog': connector_catalog,
        'ConnectorCredentialForm': ConnectorCredentialForm,
        'check_connector_credentials': AsyncMock(),
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
    app = FastAPI()
    app.include_router(router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        assert (await client.get('/connectors/catalog')).status_code == 403
        assert (
            await client.post('/connectors/test', json={'connector_id': 'gmail', 'key': 'fixture'})
        ).status_code == 403
        authorized = True
        assert (await client.get('/connectors/catalog')).status_code == 200
        namespace['ENABLE_TOOL_SERVERS'] = False
        assert (await client.get('/connectors/catalog')).status_code == 403
        assert (
            await client.post('/connectors/test', json={'connector_id': 'gmail', 'key': 'fixture'})
        ).status_code == 403
    namespace['check_connector_credentials'].assert_not_awaited()


def tool_functions(namespace):
    source = Path(__file__).parents[1] / 'answerai/utils/tools.py'
    names = {'resolve_schema', 'convert_openapi_to_tool_payload', 'execute_tool_server'}
    nodes = [
        node
        for node in ast.parse(source.read_text()).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names
    ]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
    return namespace


def test_all_preset_operations_convert_to_native_agent_tools():
    import copy
    from typing import Any

    namespace = tool_functions({'copy': copy, 'Any': Any})
    namespace['OPENAPI_HTTP_METHODS'] = {'get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'trace'}
    names = []
    for preset in connector_catalog():
        if preset['type'] != 'openapi':
            continue
        tools = namespace['convert_openapi_to_tool_payload'](preset['spec'])
        assert len(tools) == len(preset['spec']['paths'])
        names.extend(tool['name'] for tool in tools)
        for tool in tools:
            assert set(tool['parameters']['required']) <= tool['parameters']['properties'].keys()
    assert len(names) == len(set(names))


@pytest.mark.asyncio
async def test_real_openapi_executor_encodes_calendar_queries_and_uses_get():
    import copy
    import logging
    from typing import Any
    from urllib.parse import parse_qs, quote, urlencode, urlparse

    calls = []

    class ProviderResponse:
        status = 200
        headers = {'Content-Type': 'application/json'}

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def json(self):
            return {'items': []}

    class Session:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def get(self, url, **kwargs):
            calls.append((url, kwargs))
            return ProviderResponse()

    namespace = tool_functions(
        {
            'copy': copy,
            'Any': Any,
            'quote': quote,
            'urlencode': urlencode,
            'OPENAPI_HTTP_METHODS': {'get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'trace'},
            'ENABLE_TOOL_SERVERS': True,
            'AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER': 15,
            'AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL': True,
            'AIOHTTP_CLIENT_ALLOW_REDIRECTS': False,
            'aiohttp': SimpleNamespace(ClientSession=lambda **kw: Session(), ClientTimeout=aiohttp.ClientTimeout),
            'log': logging.getLogger(__name__),
        }
    )
    preset = next(p for p in connector_catalog() if p['id'] == 'google-calendar')
    result, _ = await namespace['execute_tool_server'](
        preset['url'],
        {'Authorization': 'Bearer fixture'},
        {},
        'calendar_list_events',
        {'calendar_id': 'primary', 'singleEvents': True, 'q': 'meeting & notes'},
        {'openapi': preset['spec']},
    )
    assert result == {'items': []}
    parsed = urlparse(calls[0][0])
    assert parsed.path.endswith('/calendars/primary/events')
    assert parse_qs(parsed.query) == {'singleEvents': ['true'], 'q': ['meeting & notes']}
