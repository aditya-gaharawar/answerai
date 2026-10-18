"""Connector presets and bounded, read-only account credential checks."""

import asyncio
import base64
import binascii
import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Literal

import aiohttp
from pydantic import BaseModel, Field, SecretStr, field_validator


class ConnectorCredentialForm(BaseModel):
    connector_id: Literal['github', 'gmail', 'slack', 'google-drive', 'google-calendar']
    key: SecretStr = Field(min_length=1, max_length=16384)

    @field_validator('key', mode='before')
    @classmethod
    def valid_key(cls, value):
        if not isinstance(value, str) or any(ord(c) < 33 or ord(c) > 126 for c in value.strip()):
            raise ValueError('Use an access token without spaces or line breaks.')
        return value.strip()


@lru_cache(maxsize=1)
def _catalog():
    path = Path(__file__).resolve().parent.parent / 'connectors/catalog.json'
    return json.loads(path.read_text())


def connector_catalog() -> list[dict]:
    return deepcopy(_catalog())


# No client-controlled URL, path, or headers. Never follow a token-bearing redirect.
PROBES = {
    'github': 'https://api.github.com/user',
    'gmail': 'https://gmail.googleapis.com/gmail/v1/users/me/profile',
    'slack': 'https://slack.com/api/auth.test',
    'google-drive': 'https://www.googleapis.com/drive/v3/about?fields=user(displayName)',
    'google-calendar': 'https://www.googleapis.com/calendar/v3/users/me/calendarList?maxResults=1',
}


def credential_status(status: int, body: object) -> dict:
    if status == 429 or (isinstance(body, dict) and body.get('error') == 'ratelimited'):
        return {'status': 'rate_limited', 'message': 'Provider rate limit reached. Retry later.'}
    if status == 401:
        return {'status': 'unauthorized', 'message': 'The access token is invalid or expired.'}
    if status == 403:
        return {
            'status': 'forbidden',
            'message': 'The provider denied access. Check scopes, account policy, and API enablement.',
        }
    if not 200 <= status < 300:
        return {'status': 'unavailable', 'message': 'The provider could not complete the credential check.'}
    if not isinstance(body, dict):
        return {'status': 'unavailable', 'message': 'The provider returned an unexpected response.'}
    if body.get('ok') is False:
        if body.get('error') in {'missing_scope', 'not_allowed_token_type', 'org_login_required'}:
            return {'status': 'forbidden', 'message': 'Check Slack token type, scopes, and workspace policy.'}
        return {'status': 'unauthorized', 'message': 'Slack rejected the access token or account access.'}
    if body.get('error'):
        return {'status': 'unavailable', 'message': 'The provider returned an error.'}
    return {
        'status': 'connected',
        'message': 'Credentials accepted. Individual tools still require their documented scopes and resource access.',
    }


async def check_connector_credentials(form: ConnectorCredentialForm, session, ssl=True) -> dict:
    headers = {'Authorization': f'Bearer {form.key.get_secret_value()}', 'Accept': 'application/json'}
    try:
        async with session.get(
            PROBES[form.connector_id],
            headers=headers,
            allow_redirects=False,
            timeout=aiohttp.ClientTimeout(total=15),
            ssl=ssl,
        ) as response:
            # Account checks are small; do not consume arbitrary error pages or bodies.
            try:
                raw = await response.content.readexactly(65537)
            except asyncio.IncompleteReadError as exc:
                raw = exc.partial
            if len(raw) > 65536:
                return {'status': 'unavailable', 'message': 'The provider response exceeded the check size limit.'}
            try:
                body = json.loads(raw)
            except (ValueError, UnicodeError):
                body = None
            result = credential_status(response.status, body)
            if result['status'] == 'connected':
                expected = {
                    'github': lambda data: isinstance(data.get('login'), str),
                    'gmail': lambda data: isinstance(data.get('emailAddress'), str),
                    'slack': lambda data: data.get('ok') is True,
                    'google-drive': lambda data: isinstance(data.get('user'), dict),
                    'google-calendar': lambda data: data.get('kind') == 'calendar#calendarList',
                }
                if not expected[form.connector_id](body):
                    return {'status': 'unavailable', 'message': 'The provider returned an unexpected account response.'}
            return result
    except (aiohttp.ClientError, TimeoutError):
        # Provider errors can contain URLs or tokens: never echo exception text.
        return {'status': 'unavailable', 'message': 'Could not reach the provider. Check connectivity and retry.'}


def normalize_connector_result(connection: dict, result):
    """Expose Gmail text bodies without asking a model to decode base64url."""
    if (connection.get('info') or {}).get('connector_id') != 'gmail' or not isinstance(result, dict):
        return result
    result = deepcopy(result)
    stack = [(result, 0)]
    remaining_chars = 100000
    visited = 0
    while stack and visited < 500:
        item, depth = stack.pop()
        visited += 1
        if depth > 20:
            continue
        if isinstance(item, dict):
            body = item.get('body')
            if item.get('mimeType') in {'text/plain', 'text/html'} and isinstance(body, dict):
                data = body.get('data')
                if isinstance(data, str) and len(data) <= 1500000 and remaining_chars > 0:
                    try:
                        raw = base64.b64decode(data + '=' * (-len(data) % 4), altchars=b'-_', validate=True)
                        text = raw.decode('utf-8', errors='replace')
                        body['text'] = text[:remaining_chars]
                        body['text_truncated'] = len(text) > remaining_chars
                        remaining_chars -= len(body['text'])
                        del body['data']
                    except (ValueError, binascii.Error):
                        pass
            stack.extend((value, depth + 1) for value in item.values() if isinstance(value, (dict, list)))
        elif isinstance(item, list):
            stack.extend((value, depth + 1) for value in item)
    return result
