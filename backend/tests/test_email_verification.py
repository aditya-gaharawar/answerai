import asyncio
import re
import smtplib
import time
from unittest.mock import AsyncMock

import httpx
import pytest
import pytest_asyncio
from alembic.migration import MigrationContext
from alembic.operations import Operations
from answerai import events
from answerai.internal import db as database
from answerai.models.auths import Auth, Auths
from answerai.models.config import Config
from answerai.models.email_verifications import EmailVerification
from answerai.models.users import Users
from answerai.routers import auths
from answerai.routers import email_verification as routes
from answerai.utils import access_control
from answerai.utils import auth as authentication
from answerai.utils import email_verification as mail
from answerai.utils.auth import get_admin_user
from fastapi import FastAPI, HTTPException
from pydantic import SecretStr, ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def harness(tmp_path, monkeypatch):
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path}/application.db')
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(database, 'AsyncSessionLocal', sessions)
    async with engine.begin() as connection:
        await connection.run_sync(database.Base.metadata.create_all)
    old_defaults = Config.DEFAULTS.copy()
    old_persistent = Config.PERSISTENT_ENABLED
    Config.configure(
        defaults={
            'ui.enable_signup': True,
            'ui.enable_login_form': True,
            'ui.default_user_role': 'user',
            'ui.default_group_id': '',
            'auth.jwt_expiry': '1h',
            'auth.mfa.enable': False,
            'auth.mfa.allow_oauth_bypass': False,
            'auth.mfa.allow_trusted_header_bypass': False,
            'user.permissions': {},
            'auth.enable_api_keys': True,
        }
    )
    await Config.upsert(
        {
            mail.PREFIX + key: value
            for key, value in {
                'enabled': True,
                'smtp_host': 'smtp.example.com',
                'smtp_port': 587,
                'smtp_security': 'starttls',
                'smtp_username': '',
                'from_email': 'noreply@answerai.in',
                'from_name': 'ANSWERAI',
                'public_url': 'https://answerai.in',
                'token_ttl_seconds': 3600,
                'resend_cooldown_seconds': 60,
            }.items()
        }
    )
    admin = await Auths.insert_new_auth(
        'admin@example.com', await authentication.get_password_hash('Admin-Test-Password-123!'), 'Admin', role='admin'
    )
    monkeypatch.setattr(auths, 'publish_event', AsyncMock())
    monkeypatch.setattr(events, 'publish_event', AsyncMock())
    monkeypatch.setattr(access_control, 'get_permissions', AsyncMock(return_value={}))
    messages = []
    monkeypatch.setattr(mail, '_send', lambda settings, message: messages.append(message))
    for limiter in [
        auths.signup_rate_limiter,
        auths.signin_rate_limiter,
        routes.request_limiter,
        routes.email_limiter,
        routes.verify_limiter,
    ]:
        monkeypatch.setattr(limiter, '_memory_store', {})
    app = FastAPI()
    app.state.redis = None
    app.include_router(auths.router, prefix='/api/v1/auths')
    app.include_router(routes.router, prefix='/api/v1/auths/email')
    app.dependency_overrides[get_admin_user] = lambda: admin
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='https://answerai.in') as client:
        yield client, messages, sessions, app, admin
    Config.DEFAULTS = old_defaults
    Config.PERSISTENT_ENABLED = old_persistent
    await engine.dispose()


def extract_token(message):
    content = message.get_body(preferencelist=('plain',)).get_content()
    return re.search(r'#token=([A-Za-z0-9_-]+)', content).group(1)


async def signup(client, email='person@example.com'):
    return await client.post(
        '/api/v1/auths/signup', json={'email': email, 'name': 'Person', 'password': 'Test-Password-123!'}
    )


@pytest.mark.asyncio
async def test_signup_verification_and_login(harness):
    client, messages, sessions, _, _ = harness
    response = await signup(client)
    assert response.status_code == 200
    assert response.json()['next_step'] == 'verify_email'
    assert response.json()['email_sent'] is True
    assert 'token' not in response.json()
    assert 'token=' not in response.headers.get('set-cookie', '')
    token = extract_token(messages[0])
    async with sessions() as session:
        auth = (await session.execute(select(Auth).where(Auth.email == 'person@example.com'))).scalar_one()
        assert auth.email_verified is False
        record = await session.get(EmailVerification, auth.id)
        assert record.token_hash == mail.hash_token(token)
        assert record.token_hash != token
    pending = await client.post(
        '/api/v1/auths/signin', json={'email': 'person@example.com', 'password': 'Test-Password-123!'}
    )
    assert pending.json()['next_step'] == 'verify_email'
    assert 'token' not in pending.json()
    verified = await client.post('/api/v1/auths/email/verify', json={'token': token})
    assert verified.status_code == 200
    assert 'token' not in verified.json()
    replay = await client.post('/api/v1/auths/email/verify', json={'token': token})
    assert replay.status_code == 400
    login = await client.post(
        '/api/v1/auths/signin', json={'email': 'person@example.com', 'password': 'Test-Password-123!'}
    )
    assert login.status_code == 200
    assert login.json()['token']


@pytest.mark.asyncio
async def test_resend_rotates_token_and_applies_cooldown(harness):
    client, messages, sessions, _, _ = harness
    await signup(client)
    original = extract_token(messages[0])
    result = await client.post('/api/v1/auths/email/resend', json={'email': 'person@example.com'})
    assert result.status_code == 200
    assert len(messages) == 1
    async with sessions() as session:
        record = (await session.execute(select(EmailVerification))).scalar_one()
        record.sent_at -= 61
        await session.commit()
    await client.post('/api/v1/auths/email/resend', json={'email': 'person@example.com'})
    assert len(messages) == 2
    assert extract_token(messages[1]) != original
    assert (await client.post('/api/v1/auths/email/verify', json={'token': original})).status_code == 400
    assert (
        await client.post('/api/v1/auths/email/verify', json={'token': extract_token(messages[1])})
    ).status_code == 200


@pytest.mark.asyncio
async def test_expired_changed_email_and_disabled_account_rejected(harness):
    client, messages, sessions, _, _ = harness
    for email, change in [
        ('expired@example.com', 'expires'),
        ('changed@example.com', 'email'),
        ('disabled@example.com', 'active'),
    ]:
        await signup(client, email)
        token = extract_token(messages[-1])
        async with sessions() as session:
            auth = (await session.execute(select(Auth).where(Auth.email == email))).scalar_one()
            record = await session.get(EmailVerification, auth.id)
            if change == 'expires':
                record.expires_at = int(time.time()) - 1
            elif change == 'email':
                auth.email = 'new@example.com'
            else:
                auth.active = False
            await session.commit()
        assert (await client.post('/api/v1/auths/email/verify', json={'token': token})).status_code == 400
        async with sessions() as session:
            assert (await session.get(Auth, auth.id)).email_verified is False


@pytest.mark.asyncio
async def test_smtp_failure_keeps_account_unverified_and_recoverable(harness, monkeypatch):
    client, messages, sessions, _, _ = harness
    real_send = mail._send

    def fail(*args):
        raise smtplib.SMTPException('a-sensitive-provider-error')

    monkeypatch.setattr(mail, '_send', fail)
    response = await signup(client)
    assert response.status_code == 200
    assert response.json()['email_sent'] is False
    assert 'sensitive' not in response.text
    async with sessions() as session:
        record = (await session.execute(select(EmailVerification))).scalar_one()
        assert record.token_hash is None
        assert (await session.get(Auth, record.user_id)).email_verified is False
        record.sent_at -= 61
        await session.commit()
    monkeypatch.setattr(mail, '_send', real_send)
    assert (await client.post('/api/v1/auths/email/resend', json={'email': 'person@example.com'})).status_code == 200
    assert len(messages) == 1
    assert (
        await client.post('/api/v1/auths/email/verify', json={'token': extract_token(messages[0])})
    ).status_code == 200


@pytest.mark.asyncio
async def test_resend_does_not_disclose_accounts(harness):
    client, _, _, _, _ = harness
    await signup(client)
    known = await client.post('/api/v1/auths/email/resend', json={'email': 'person@example.com'})
    unknown = await client.post('/api/v1/auths/email/resend', json={'email': 'nobody@example.com'})
    verified = await client.post('/api/v1/auths/email/resend', json={'email': 'admin@example.com'})
    assert known.json() == unknown.json() == verified.json()
    assert all(response.status_code == 200 for response in (known, unknown, verified))


@pytest.mark.asyncio
async def test_disabled_verification_preserves_legacy_and_new_accounts(harness):
    client, messages, _, _, _ = harness
    await Config.upsert({mail.PREFIX + 'enabled': False})
    signup_response = await signup(client)
    assert signup_response.json()['token']
    assert messages == []
    existing = await client.post(
        '/api/v1/auths/signin', json={'email': 'admin@example.com', 'password': 'Admin-Test-Password-123!'}
    )
    assert existing.json()['token']


@pytest.mark.asyncio
async def test_policy_toggle_does_not_bypass_pending_verification(harness):
    client, messages, _, _, _ = harness
    await signup(client)
    await Config.upsert({mail.PREFIX + 'enabled': False})
    pending = await client.post(
        '/api/v1/auths/signin', json={'email': 'person@example.com', 'password': 'Test-Password-123!'}
    )
    assert pending.json()['next_step'] == 'verify_email'
    assert (
        await client.post('/api/v1/auths/email/verify', json={'token': extract_token(messages[0])})
    ).status_code == 200


@pytest.mark.asyncio
async def test_verification_precedes_mfa_and_application_tokens(harness):
    client, messages, _, _, _ = harness
    await Config.upsert({'auth.mfa.enable': True})
    pending = await signup(client)
    assert pending.json()['next_step'] == 'verify_email'
    user = await Users.get_user_by_email('person@example.com')
    auth = await Auths.get_auth_by_id(user.id)
    assert not await authentication.is_valid_token({'id': user.id, 'session_stamp': auth.session_stamp})
    with pytest.raises(HTTPException) as error:
        await authentication.create_session_response(None, user, auth=auth, mfa_verified=True)
    assert error.value.status_code == 403
    assert await authentication.get_verified_user_by_id(user.id) is None
    await client.post('/api/v1/auths/email/verify', json={'token': extract_token(messages[0])})
    login = await client.post(
        '/api/v1/auths/signin', json={'email': 'person@example.com', 'password': 'Test-Password-123!'}
    )
    assert login.json()['next_step'] == 'enroll'
    assert 'token' not in login.json()


@pytest.mark.asyncio
async def test_admin_settings_encrypt_and_preserve_password(harness):
    client, _, sessions, _, _ = harness
    values = (await client.get('/api/v1/auths/email/config')).json()
    values.pop('password_configured')
    values['smtp_password'] = 'test-SMTP-secret'
    saved = await client.post('/api/v1/auths/email/config', json=values)
    assert saved.status_code == 200
    assert saved.json()['password_configured'] is True
    assert 'test-SMTP-secret' not in saved.text
    async with sessions() as session:
        encrypted = (await session.get(Config, mail.PASSWORD_KEY)).value
        assert encrypted != 'test-SMTP-secret'
    values['smtp_password'] = None
    assert (await client.post('/api/v1/auths/email/config', json=values)).status_code == 200
    assert (await mail.get_email_settings()).smtp_password.get_secret_value() == 'test-SMTP-secret'
    values['clear_password'] = True
    assert (await client.post('/api/v1/auths/email/config', json=values)).status_code == 200
    assert (await mail.get_email_settings()).smtp_password is None


@pytest.mark.asyncio
async def test_admin_endpoints_require_authentication(harness):
    client, _, _, app, _ = harness
    app.dependency_overrides.clear()
    for method, path, body in [('GET', 'config', None), ('POST', 'config', {}), ('POST', 'test', {})]:
        response = await client.request(method, '/api/v1/auths/email/' + path, json=body)
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_tokens_do_not_echo_secret(harness):
    client, _, _, _, _ = harness
    response = await client.post('/api/v1/auths/email/verify', json={'token': 'secret-do-not-echo'})
    assert response.status_code == 422
    assert 'secret-do-not-echo' not in response.text
    assert response.headers['cache-control'] == 'no-store'


@pytest.mark.asyncio
async def test_verify_ip_limit(harness):
    client, _, _, _, _ = harness
    for _ in range(30):
        assert (await client.post('/api/v1/auths/email/verify', json={'token': 'x' * 43})).status_code == 400
    limited = await client.post('/api/v1/auths/email/verify', json={'token': 'x' * 43})
    assert limited.status_code == 429
    assert limited.headers['retry-after'] == '900'


@pytest.mark.asyncio
async def test_only_one_concurrent_token_consumption(harness):
    client, messages, _, _, _ = harness
    await signup(client)
    token = extract_token(messages[0])
    responses = await asyncio.gather(
        *(client.post('/api/v1/auths/email/verify', json={'token': token}) for _ in range(2))
    )
    assert sorted(response.status_code for response in responses) == [200, 400]


@pytest.mark.parametrize('security,port', [('starttls', 587), ('ssl', 465)])
def test_smtp_transport_validates_tls_and_authenticates(monkeypatch, security, port):
    calls = []

    class SMTP:
        def __init__(self, **kwargs):
            calls.append(('connect', kwargs))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def ehlo(self):
            calls.append(('ehlo',))

        def starttls(self, **kwargs):
            calls.append(('tls', kwargs))

        def login(self, username, password):
            calls.append(('login', username, password))

        def send_message(self, message):
            calls.append(('message', message))
            return {}

    monkeypatch.setattr(mail.smtplib, 'SMTP', SMTP)
    monkeypatch.setattr(mail.smtplib, 'SMTP_SSL', SMTP)
    settings = mail.EmailSettings(
        smtp_host='smtp.example.com',
        smtp_port=port,
        smtp_security=security,
        smtp_username='smtp-user',
        smtp_password=SecretStr('test-password'),
        from_email='noreply@answerai.in',
    )
    mail._send(settings, mail.build_email(settings, 'person@example.com', 'x' * 43))
    tls_context = (
        calls[0][1]['context'] if security == 'ssl' else next(call[1]['context'] for call in calls if call[0] == 'tls')
    )
    assert tls_context.check_hostname is True
    assert ('login', 'smtp-user', 'test-password') in calls
    message = next(call[1] for call in calls if call[0] == 'message')
    assert message.get_body(preferencelist=('html',)) is not None
    assert '/auth/verify-email#token=' in message.get_body(preferencelist=('plain',)).get_content()


@pytest.mark.parametrize(
    'updates',
    [
        {'public_url': 'http://untrusted.example.com'},
        {'public_url': 'https://user:password@example.com'},
        {'from_name': 'Bad\r\nBcc: victim@example.com'},
        {'smtp_security': 'none'},
        {'token_ttl_seconds': 1},
    ],
)
def test_unsafe_mail_configuration_rejected(updates):
    with pytest.raises(ValidationError):
        mail.EmailSettings(**updates)


def test_migration_preserves_existing_accounts_and_downgrades(tmp_path):
    import importlib.util
    from pathlib import Path

    path = Path(__file__).parents[1] / 'answerai/migrations/versions/e8a14c7b9206_add_email_verification.py'
    spec = importlib.util.spec_from_file_location('email_migration', path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine(f'sqlite:///{tmp_path}/migration.db')
    with engine.begin() as connection:
        connection.exec_driver_sql('CREATE TABLE auth (id VARCHAR PRIMARY KEY, email VARCHAR)')
        connection.exec_driver_sql("INSERT INTO auth (id, email) VALUES ('existing', 'existing@example.com')")
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            assert connection.exec_driver_sql('SELECT email_verified FROM auth').scalar_one() == 1
            migration.downgrade()
        assert connection.exec_driver_sql('SELECT email FROM auth').scalar_one() == 'existing@example.com'
    engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_resends_send_only_one_new_email(harness):
    client, messages, sessions, _, _ = harness
    await signup(client)
    async with sessions() as session:
        record = (await session.execute(select(EmailVerification))).scalar_one()
        record.sent_at -= 61
        await session.commit()
    replies = await asyncio.gather(
        *(client.post('/api/v1/auths/email/resend', json={'email': 'person@example.com'}) for _ in range(2))
    )
    assert all(reply.status_code == 200 for reply in replies)
    assert len(messages) == 2


@pytest.mark.asyncio
async def test_malformed_email_cannot_inject_mail_headers(harness):
    client, messages, _, _, _ = harness
    address = 'person@example.com\r\nBcc: victim@example.com'
    assert (await signup(client, address)).status_code == 400
    assert (await client.post('/api/v1/auths/email/resend', json={'email': address})).status_code == 422
    assert messages == []


@pytest.mark.asyncio
async def test_missing_smtp_rejects_signup_before_account_creation(harness):
    client, _, _, _, _ = harness
    await Config.upsert({mail.PREFIX + 'smtp_host': ''})
    response = await signup(client)
    assert response.status_code == 503
    assert await Users.get_user_by_email('person@example.com') is None


@pytest.mark.asyncio
async def test_rotated_application_key_can_recover_mail_settings(harness):
    client, _, _, _, _ = harness
    await Config.upsert({mail.PASSWORD_KEY: 'unreadable-old-ciphertext'})
    response = await client.get('/api/v1/auths/email/config')
    assert response.status_code == 200
    values = response.json()
    assert values.pop('password_configured') is True
    values['smtp_password'] = 'replacement-test-password'
    assert (await client.post('/api/v1/auths/email/config', json=values)).status_code == 200
    assert (await mail.get_email_settings()).smtp_password.get_secret_value() == 'replacement-test-password'
    await Config.upsert({mail.PASSWORD_KEY: 'unreadable-old-ciphertext'})
    values['smtp_password'] = None
    values['enabled'] = False
    assert (await client.post('/api/v1/auths/email/config', json=values)).status_code == 200
    assert (await signup(client)).json()['token']


def test_full_fresh_database_migration_chain(tmp_path, monkeypatch):
    from pathlib import Path

    from alembic import command
    from alembic.config import Config as AlembicConfig
    from answerai import env
    from sqlalchemy import inspect

    url = f'sqlite:///{tmp_path}/full-migration.db'
    monkeypatch.setattr(env, 'DATABASE_URL', url)
    base = Path(__file__).parents[1] / 'answerai'
    config = AlembicConfig(str(base / 'alembic.ini'))
    config.set_main_option('script_location', str(base / 'migrations'))
    command.upgrade(config, 'head')
    engine = create_engine(url)
    with engine.connect() as connection:
        assert connection.exec_driver_sql('SELECT version_num FROM alembic_version').scalar_one() == 'a729d60cf132'
        assert 'email_verification' in inspect(connection).get_table_names()
        assert 'email_verified' in {column['name'] for column in inspect(connection).get_columns('auth')}
    engine.dispose()
