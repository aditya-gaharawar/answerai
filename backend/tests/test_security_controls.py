"""Local regression proofs for authorization, audit privacy, and admin operations."""

import ast
import hashlib
import hmac
import io
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from answerai.internal.db import get_async_db
from answerai.models.admin_actions import AdminAction
from answerai.models.auths import Auths
from answerai.models.billing import LiveLease, UsageBucket
from answerai.models.config import Config
from answerai.routers import admin_controls, utils
from answerai.utils import access_control, payments
from answerai.utils import security_policy as policy
from answerai.utils.auth import create_token, get_current_user, is_valid_token
from answerai.utils.secret_redaction import redact_body, redact_url
from fastapi import FastAPI, HTTPException, Request, UploadFile
from sqlalchemy import select

pytest_plugins = ['test_email_verification']


async def member():
    return await Auths.insert_new_auth('member@example.com', 'unused-test-hash', 'Member', role='user')


@pytest.mark.asyncio
async def test_code_execution_permission_before_jupyter_request(harness, monkeypatch):
    client, _, _, app, admin = harness
    target = await member()
    await Config.upsert({'code_execution.enable': True, 'code_execution.engine': 'jupyter'})
    app.include_router(utils.router, prefix='/api/v1/utils')
    app.dependency_overrides[get_current_user] = lambda: target
    permissions = AsyncMock(return_value=False)
    monkeypatch.setattr(access_control, 'has_permission', permissions)
    executor = AsyncMock(return_value={'stdout': 'authorized'})
    monkeypatch.setattr(utils, 'execute_code_jupyter', executor)
    result = await client.post('/api/v1/utils/code/execute', json={'code': 'print("local regression proof")'})
    assert result.status_code == 403
    executor.assert_not_called()
    permissions.return_value = True
    assert (
        await client.post('/api/v1/utils/code/execute', json={'code': 'print("allowed")'})
    ).status_code == 200
    executor.assert_awaited_once()
    app.dependency_overrides[get_current_user] = lambda: admin
    permissions.return_value = False
    assert (
        await client.post('/api/v1/utils/code/execute', json={'code': 'print("admin")'})
    ).status_code == 200


@pytest.mark.asyncio
async def test_upload_controller_blocks_before_storage(harness, monkeypatch):
    # Execute the real controller body without loading optional vector/OCR SDKs.
    source = Path(__file__).parents[1] / 'answerai/routers/files.py'
    node = next(
        node
        for node in ast.parse(source.read_text()).body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == 'upload_file_handler'
    )
    node.decorator_list = []
    node.returns = None
    for arg in node.args.args:
        arg.annotation = None
    node.args.defaults = [ast.Constant(None) for _ in node.args.args]
    storage = Mock()
    namespace = {'Config': Config, 'log': Mock(), 'Storage': storage}
    exec(
        compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(source), 'exec'),
        namespace,
    )
    target = await member()
    monkeypatch.setattr(access_control, 'has_permission', AsyncMock(return_value=False))
    upload = UploadFile(file=io.BytesIO(b'local proof'), filename='proof.txt')
    with pytest.raises(HTTPException) as error:
        await namespace['upload_file_handler'](file=upload, user=target)
    assert error.value.status_code == 403
    storage.upload_file.assert_not_called()
    monkeypatch.setattr(access_control, 'has_permission', AsyncMock(return_value=True))
    await Config.upsert({'rag.file.max_size': 1})
    upload.file = io.BytesIO(b'x' * (1024 * 1024 + 1))
    with pytest.raises(HTTPException) as error:
        await namespace['upload_file_handler'](file=upload, user=target)
    assert error.value.status_code == 413
    storage.upload_file.assert_not_called()


def test_size_check_does_not_read_bytes_or_change_stream_position():
    stream = io.BytesIO(b'x' * (1024 * 1024 + 1))
    stream.seek(11)
    with pytest.raises(HTTPException):
        policy.validate_upload_before_storage(stream, 1)
    assert stream.tell() == 11
    policy.validate_upload_before_storage(io.BytesIO(b'normal document'), 1)


@pytest.mark.asyncio
async def test_streaming_body_and_cookie_origin_guard(harness):
    await Config.upsert({'security.policy': {'max_request_mib': 1}})
    app = FastAPI()
    app.add_middleware(policy.RequestBodyLimitMiddleware)
    reached = []

    @app.post('/upload')
    async def upload(request: Request):
        body = await request.body()
        reached.append(len(body))
        return {'bytes': len(body)}

    @app.get('/private')
    async def private():
        return {'private': True}

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url='https://answerai.in'
    ) as client:
        result = await client.post('/upload', content=b'x', headers={'Content-Length': '1048577'})
        assert result.status_code == 413 and not reached

        async def chunks():
            yield b'x' * 600000
            yield b'x' * 600000

        result = await client.post('/upload', content=chunks())
        assert result.status_code == 413 and not reached
        for method, path in [('POST', '/upload'), ('GET', '/private')]:
            for origin in ['https://attacker.invalid', 'null']:
                result = await client.request(
                    method, path, headers={'Cookie': 'token=test-session', 'Origin': origin}
                )
                assert result.status_code == 403
        assert (
            await client.post(
                '/upload',
                content=b'ok',
                headers={'Cookie': 'token=own-session', 'Origin': 'https://answerai.in'},
            )
        ).status_code == 200
        assert (
            await client.get(
                '/private',
                headers={'Authorization': 'Bearer explicit-client-key', 'Origin': 'https://client.invalid'},
            )
        ).status_code == 200
        await Config.upsert(
            {'security.policy': {'allowed_cookie_origins': ['https://owned-frontend.example']}}
        )
        assert (
            await client.get(
                '/private',
                headers={'Cookie': 'token=own-session', 'Origin': 'https://owned-frontend.example'},
            )
        ).status_code == 200


def test_nested_and_truncated_audit_credentials_are_redacted():
    body = json.dumps(
        {
            'smtp_password': 'password-secret',
            'OPENAI_API_KEYS': ['secret-one', 'secret-two'],
            'nested': [{'Authorization': 'Bearer test-token', 'refresh_token': 'refresh-secret'}],
            'url': 'https://user:pass@service.example/api?api_key=query-secret&mode=normal',
            'ordinary': 'keep me',
        }
    )
    redacted = redact_body(body)
    for value in [
        'password-secret',
        'secret-one',
        'secret-two',
        'test-token',
        'refresh-secret',
        'query-secret',
        'user:pass',
    ]:
        assert value not in redacted
    assert 'keep me' in redacted and 'mode=normal' in redacted
    assert 'cut-secret' not in redact_body('{"api_key": "cut-secret')
    assert 'array-secret' not in redact_body('{"api_keys": ["array-secret"')
    url = redact_url('https://u:p@answerai.in/api?token=url-secret&file=123#secret-fragment')
    assert 'url-secret' not in url and 'u:p' not in url and 'fragment' not in url and 'file=123' in url


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'claim,expected', [(True, True), (False, False), (None, False), ('true', False), (1, False)]
)
async def test_oauth_email_proof_is_strict(harness, claim, expected):
    assert await policy.oauth_email_trusted('oidc', {'email_verified': claim}) is expected
    await Config.upsert({'security.policy': {'trusted_oauth_email_providers': ['enterprise']}})
    assert await policy.oauth_email_trusted('enterprise', {}) is True
    assert await policy.oauth_email_trusted('enterprise', {'email_verified': False}) is False
    assert await policy.oauth_email_trusted('other', {}) is False


@pytest.mark.asyncio
async def test_server_python_authoring_requires_explicit_trust(harness):
    user = await member()
    assert not await policy.allow_python_authoring(user)
    assert await policy.allow_python_authoring(harness[4])
    await Config.upsert({'security.policy': {'allow_user_python_tools': True}})
    assert await policy.allow_python_authoring(user)


@pytest.mark.asyncio
async def test_admin_account_lookup_controls_and_action_ledger(harness, monkeypatch):
    client, _, _, app, admin = harness
    user = await member()
    app.include_router(admin_controls.router, prefix='/api/v1/admin/controls')
    auth = await Auths.get_auth_by_id(user.id)
    token = create_token({'id': user.id, 'session_stamp': auth.session_stamp})
    from answerai.utils.auth import decode_token

    assert await is_valid_token(decode_token(token))
    async with get_async_db() as db:
        db.add(LiveLease(user_id=user.id, session_id='active-call', expires_at=9999999999))
        db.add(
            UsageBucket(
                id='test-usage', user_id=user.id, metric='messages', window=86400, starts_at=0, used=20
            )
        )
        await db.commit()
    import sys
    from types import ModuleType

    sockets = ModuleType('answerai.socket.main')
    disconnect = AsyncMock()
    sockets.disconnect_user_sessions = disconnect
    monkeypatch.setitem(sys.modules, 'answerai.socket.main', sockets)
    result = await client.get('/api/v1/admin/controls/accounts/MEMBER%40example.com')
    assert result.json()['id'] == user.id and result.json()['active_call']
    for action in ['reset_usage', 'stop_call', 'revoke_sessions', 'disable_login', 'enable_login']:
        result = await client.post(
            '/api/v1/admin/controls/accounts/' + user.id + '/actions',
            json={'action': action, 'reason': 'Regression proof'},
        )
        assert result.status_code == 200, result.text
    assert not await is_valid_token(decode_token(token))
    disconnect.assert_awaited()
    assert (await client.get('/api/v1/admin/controls/accounts/' + user.id)).json()['login_enabled'] is True
    async with get_async_db() as db:
        rows = (await db.scalars(select(AdminAction))).all()
        assert len(rows) == 5 and {row.actor_id for row in rows} == {admin.id}
        assert (await db.scalars(select(UsageBucket))).all() == []
        assert await db.get(LiveLease, user.id) is None
    assert (
        await client.post(
            '/api/v1/admin/controls/accounts/' + admin.id + '/actions',
            json={'action': 'disable_login', 'reason': 'Must reject'},
        )
    ).status_code == 400


@pytest.mark.asyncio
async def test_admin_controls_never_accessible_to_members(harness):
    client, _, _, app, _ = harness
    user = await member()
    app.include_router(admin_controls.router, prefix='/api/v1/admin/controls')
    from answerai.utils.auth import get_admin_user

    app.dependency_overrides.pop(get_admin_user)
    app.dependency_overrides[get_current_user] = lambda: user
    for path in ['policy', 'overview', 'actions', 'accounts/' + user.id]:
        assert (await client.get('/api/v1/admin/controls/' + path)).status_code == 401
    assert (
        await client.post('/api/v1/admin/controls/policy', json={'max_request_mib': 1024})
    ).status_code == 401


@pytest.mark.asyncio
async def test_razorpay_replay_cannot_bypass_dedup_with_an_unsigned_header(harness, monkeypatch):
    monkeypatch.setenv('RAZORPAY_WEBHOOK_SECRET', 'local-test-signing-secret')
    body = json.dumps(
        {'event': 'subscription.activated', 'payload': {'subscription': {'entity': {'id': 'sub_local'}}}}
    ).encode()
    signature = hmac.new(b'local-test-signing-secret', body, hashlib.sha256).hexdigest()
    reconciliation = AsyncMock()
    monkeypatch.setattr(payments, 'reconcile', reconciliation)
    for event_id in ['first-untrusted-header', 'second-untrusted-header']:
        await payments.process_webhook('razorpay', body, signature, event_id)
    reconciliation.assert_awaited_once()


def test_cookie_policy_accepts_only_exact_origins():
    from answerai.utils.security_policy import SecurityPolicy
    from pydantic import ValidationError

    assert SecurityPolicy(allowed_cookie_origins=['https://answerai.in/']).allowed_cookie_origins == [
        'https://answerai.in'
    ]
    for origin in [
        '*',
        'null',
        'https://user:password@example.com',
        'https://example.com/path',
        'https://*.example.com',
    ]:
        with pytest.raises(ValidationError):
            SecurityPolicy(allowed_cookie_origins=[origin])
