"""Local reproductions for security boundaries missed by the initial review."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from answerai.models.auths import Auths
from answerai.models.config import Config
from answerai.models.files import File  # noqa: F401 - register Socket.IO foreign-key tables
from answerai.models.messages import Message  # noqa: F401 - register Socket.IO foreign-key tables
from answerai.models.users import Users
from answerai.routers import auths
from answerai.socket import main as sockets
from answerai.utils.auth import create_token

pytest_plugins = ['test_email_verification']


@pytest.mark.asyncio
async def test_socket_session_uses_current_role_after_admin_demotion(harness, monkeypatch):
    target = await Auths.insert_new_auth('former-admin@example.com', 'test-hash', 'Former admin', role='admin')
    auth = await Auths.get_auth_by_id(target.id)
    token = create_token({'id': target.id, 'session_stamp': auth.session_stamp})
    stale = target.model_dump()
    sio = SimpleNamespace(get_session=AsyncMock(return_value={'user': stale, 'token': token}), disconnect=AsyncMock())
    monkeypatch.setattr(sockets, 'sio', sio)
    await Users.update_user_by_id(target.id, {'role': 'user'})
    resolved = await sockets.get_socket_session_user('local-test-session')
    assert resolved is not None
    assert resolved['id'] == target.id
    assert resolved['role'] == 'user'
    sio.disconnect.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize('proof', [True, False, None, 'true', 1])
async def test_unverified_provider_email_cannot_link_existing_account_via_token_exchange(harness, monkeypatch, proof):
    client, _, _, app, _ = harness
    victim = await Auths.insert_new_auth('victim@example.com', 'test-hash', 'Victim', role='user')
    provider = SimpleNamespace(
        userinfo=AsyncMock(
            return_value={
                'sub': 'attacker-provider-sub',
                'email': victim.email,
                'email_verified': proof,
            }
        )
    )
    app.state.oauth_manager = SimpleNamespace(
        get_client=Mock(return_value=provider),
        update_user_role_from_oauth=AsyncMock(side_effect=lambda **kwargs: kwargs['user']),
    )
    monkeypatch.setattr(auths, 'ENABLE_OAUTH_TOKEN_EXCHANGE', True)
    monkeypatch.setattr(auths, 'OAUTH_PROVIDERS', {'test-oidc': {'sub_claim': 'sub'}})
    monkeypatch.setattr(auths, 'OAUTH_TOKEN_EXCHANGE_TRUSTED_CLIENT_IDS', [])
    monkeypatch.setattr(auths, 'token_exchange_rate_limiter', None)
    await Config.upsert({'oauth.allowed_domains': ['*'], 'oauth.merge_accounts_by_email': True})
    result = await client.post(
        '/api/v1/auths/oauth/test-oidc/token/exchange', json={'token': 'provider-accepted-opaque-token'}
    )
    assert result.status_code == (200 if proof is True else 403)
    linked = await Users.get_user_by_oauth_sub('test-oidc', 'attacker-provider-sub')
    assert (linked is not None) == (proof is True)


@pytest.mark.asyncio
async def test_document_state_rechecks_read_access_for_existing_room(harness, monkeypatch):
    from answerai.models.notes import NoteForm, Notes

    target = await Auths.insert_new_auth('demoted-reader@example.com', 'test-hash', 'Reader', role='admin')
    owner = await Auths.insert_new_auth('note-owner@example.com', 'test-hash', 'Owner', role='user')
    note = await Notes.insert_new_note(owner.id, NoteForm(title='Private', data={'content': {'md': 'private proof'}}))
    auth = await Auths.get_auth_by_id(target.id)
    token = create_token({'id': target.id, 'session_stamp': auth.session_stamp})
    sio = SimpleNamespace(
        get_session=AsyncMock(return_value={'user': target.model_dump(), 'token': token}),
        emit=AsyncMock(),
        disconnect=AsyncMock(),
    )
    monkeypatch.setattr(sockets, 'sio', sio)
    monkeypatch.setattr(sockets, 'get_session_ids_from_room', lambda room: ['local-test-session'])
    monkeypatch.setattr(sockets, 'has_permission', AsyncMock(return_value=True))
    private_doc = sockets.Y.Doc({'text': sockets.Y.Text('private note proof')})
    document = SimpleNamespace(
        document_exists=AsyncMock(return_value=True),
        get_updates=AsyncMock(return_value=[list(private_doc.get_update())]),
    )
    monkeypatch.setattr(sockets, 'YDOC_MANAGER', document)
    await Users.update_user_by_id(target.id, {'role': 'user'})
    await sockets.yjs_document_state.__wrapped__('local-test-session', {'document_id': 'note:' + note.id})
    document.get_updates.assert_not_called()
    sio.emit.assert_not_called()
    await Users.update_user_by_id(target.id, {'role': 'admin'})
    await sockets.yjs_document_state.__wrapped__('local-test-session', {'document_id': 'note:' + note.id})
    recovered = sockets.Y.Doc()
    recovered.apply_update(bytes(sio.emit.await_args.args[1]['state']))
    assert str(recovered.get('text', type=sockets.Y.Text)) == 'private note proof'


def test_release_tag_cannot_become_shell_code(tmp_path):
    import os
    import subprocess
    from pathlib import Path

    import yaml

    workflow = yaml.safe_load((Path(__file__).parents[2] / '.github/workflows/docker.yaml').read_text())
    step = next(
        step
        for job in workflow['jobs'].values()
        for step in job.get('steps', [])
        if step.get('name') == 'Determine source and destination tags'
    )
    marker = tmp_path / 'shell-executed'
    tag = 'v$(touch${IFS}' + str(marker) + ')'
    assert subprocess.run(['git', 'check-ref-format', 'refs/tags/' + tag], capture_output=True).returncode == 0
    script = step['run'].replace('${{ github.ref }}', 'refs/tags/' + tag).replace('${{ github.ref_name }}', tag)
    script = script.replace('${{ matrix.suffix }}', '')
    result = subprocess.run(
        ['bash', '-eu', '-c', script],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            'GITHUB_REF': 'refs/tags/' + tag,
            'GITHUB_REF_NAME': tag,
            'GITHUB_OUTPUT': str(tmp_path / 'outputs'),
        },
    )
    assert not marker.exists(), 'Release tag executed as shell source'
    assert result.returncode != 0, 'Invalid Docker release tag should be rejected'


@pytest.mark.parametrize(
    'address', ['127.0.0.1', '10.0.0.1', '169.254.169.254', '::1', '::ffff:127.0.0.1', '64:ff9b::7f00:1']
)
def test_private_and_embedded_addresses_are_blocked(address, monkeypatch):
    from answerai.retrieval.web import utils as web

    monkeypatch.setattr(web, 'ENABLE_LOCAL_WEB_FETCH', False)
    monkeypatch.setattr(web, 'WEB_FETCH_FILTER_LIST', [])
    with pytest.raises(ValueError):
        web._assert_addresses_allowed([address])
    web._assert_addresses_allowed(['1.1.1.1', '2606:4700:4700::1111'])


def test_dns_rebinding_is_checked_before_opening_socket(monkeypatch):
    import socket

    from answerai.retrieval.web import utils as web

    monkeypatch.setattr(web, 'ENABLE_LOCAL_WEB_FETCH', False)
    monkeypatch.setattr(web, 'WEB_FETCH_FILTER_LIST', [])
    monkeypatch.setattr(
        web.socket,
        'getaddrinfo',
        lambda *args: [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 443))],
    )
    constructor = Mock()
    monkeypatch.setattr(web.socket, 'socket', constructor)
    with pytest.raises(ValueError):
        web._ssrf_safe_new_conn(SimpleNamespace(host='public.example', port=443))
    constructor.assert_not_called()


@pytest.mark.parametrize('path', ['../SKILL.md', '/SKILL.md', 'folder/../../SKILL.md', 'folder\\SKILL.md'])
def test_archive_import_rejects_traversal(path):
    import io
    import zipfile

    from answerai.utils.skill_files import parse_import

    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as archive:
        archive.writestr(path, '# Local security proof')
    with pytest.raises(ValueError):
        parse_import(output.getvalue(), 'proof.zip')


def test_archive_import_rejects_symlinks_and_bounded_zip_bomb():
    import io
    import stat
    import zipfile

    from answerai.utils.skill_files import MAX_FILE_BYTES, parse_import

    for mode, content in [(stat.S_IFLNK, b'/etc/passwd'), (stat.S_IFREG, b'x' * (MAX_FILE_BYTES + 1))]:
        output = io.BytesIO()
        info = zipfile.ZipInfo('SKILL.md')
        info.external_attr = (mode | 0o600) << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        with zipfile.ZipFile(output, 'w') as archive:
            archive.writestr(info, content)
        with pytest.raises(ValueError):
            parse_import(output.getvalue(), 'proof.zip')


@pytest.mark.parametrize('version', ['0.12.0', '0.12.1-rc.1'])
def test_valid_release_tags_remain_supported(version, tmp_path):
    import os
    import subprocess
    from pathlib import Path

    import yaml

    workflow = yaml.safe_load((Path(__file__).parents[2] / '.github/workflows/docker.yaml').read_text())
    step = next(
        step
        for job in workflow['jobs'].values()
        for step in job.get('steps', [])
        if step.get('name') == 'Determine source and destination tags'
    )
    output = tmp_path / 'outputs'
    script = step['run'].replace('${{ matrix.suffix }}', '-slim')
    result = subprocess.run(
        ['bash', '-eu', '-c', script],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            'GITHUB_REF': 'refs/tags/v' + version,
            'GITHUB_REF_NAME': 'v' + version,
            'GITHUB_OUTPUT': str(output),
        },
    )
    assert result.returncode == 0, result.stderr
    assert version + '-slim' in output.read_text()
