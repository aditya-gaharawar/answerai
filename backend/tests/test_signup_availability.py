"""Legacy config compatibility without making invalid authentication state permissive."""

import logging

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from answerai.models.config import Config
from answerai.utils.mfa import get_mfa_config, MfaConfigForm, log_auth_backend_failure

pytest_plugins = ['test_email_verification']


@pytest.mark.asyncio
@pytest.mark.parametrize('stored,expected', [('false', False), (' TRUE ', True), (0, False), (1, True)])
async def test_legacy_stored_mfa_flags(stored, expected, monkeypatch):
    async def get_many(*keys):
        return {key: stored for key in keys}

    monkeypatch.setattr(Config, 'get_many', get_many)
    config = await get_mfa_config()
    assert config.ENABLE_MFA is expected
    assert config.MFA_ALLOW_OAUTH_BYPASS is expected


@pytest.mark.asyncio
async def test_malformed_flags_fail_closed_and_admin_writes_remain_strict(monkeypatch):
    async def get_many(*keys):
        return {'auth.mfa.enable': 'invalid-secret-config'}

    monkeypatch.setattr(Config, 'get_many', get_many)
    with pytest.raises(ValidationError):
        await get_mfa_config()
    with pytest.raises(ValidationError):
        MfaConfigForm(ENABLE_MFA='false')


def test_database_diagnostics_do_not_log_credentials(caplog):
    error = OperationalError('INSERT secret-password', {'token': 'secret-token'}, Exception('no such column: mfa'))
    with caplog.at_level(logging.ERROR):
        log_auth_backend_failure('signup', error)
    assert 'database_schema' in caplog.text
    assert 'secret-password' not in caplog.text and 'secret-token' not in caplog.text


@pytest.mark.asyncio
async def test_signup_accepts_legacy_disabled_mfa_config(harness):
    from test_email_verification import signup

    client, messages, _, _, _ = harness
    await Config.upsert({'auth.mfa.enable': 'false', 'auth.mfa.allow_oauth_bypass': 'false'})
    response = await signup(client, 'legacy-flags@example.com')
    assert response.status_code == 200, response.text
    assert response.json()['next_step'] == 'verify_email'
    assert len(messages) == 1


@pytest.mark.asyncio
async def test_signup_rejects_unknown_mfa_config_without_creating_account(harness, caplog):
    from test_email_verification import signup
    from answerai.models.users import Users

    client, _, _, _, _ = harness
    await Config.upsert({'auth.mfa.enable': 'invalid-secret-config'})
    with caplog.at_level(logging.ERROR):
        response = await signup(client, 'blocked-config@example.com')
    assert response.status_code == 503
    assert await Users.get_user_by_email('blocked-config@example.com') is None
    assert 'stored_data_validation' in caplog.text
    assert 'invalid-secret-config' not in caplog.text
