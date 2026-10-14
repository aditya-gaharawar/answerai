"""Explicit security policy and reusable permission/size checks."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from answerai.models.config import Config
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SecurityPolicy(BaseModel):
    model_config = ConfigDict(extra='forbid')
    max_request_mib: int = Field(default=64, ge=1, le=1024)
    allow_user_python_tools: bool = False
    allowed_cookie_origins: list[str] = Field(default_factory=list, max_length=100)
    trusted_oauth_email_providers: list[str] = Field(default_factory=list, max_length=100)

    @field_validator('allowed_cookie_origins')
    @classmethod
    def exact_origins(cls, values):
        normalized = []
        for value in values:
            parts = urlsplit(value)
            if (
                parts.scheme not in {'http', 'https'}
                or not parts.hostname
                or parts.username
                or parts.password
                or parts.query
                or parts.fragment
                or parts.path not in {'', '/'}
                or '*' in parts.netloc
            ):
                raise ValueError('Cookie origins must be exact HTTP(S) origins without credentials or paths.')
            parts.port  # Reject malformed ports.
            normalized.append(f'{parts.scheme}://{parts.netloc}'.lower())
        return list(dict.fromkeys(normalized))


async def security_policy() -> SecurityPolicy:
    return SecurityPolicy.model_validate(await Config.get('security.policy') or {})


async def require_user_permission(user, permission: str):
    from answerai.utils.access_control import has_permission

    if user.role != 'admin' and not await has_permission(
        user.id, permission, await Config.get('user.permissions') or {}
    ):
        raise HTTPException(403, 'Your administrator has disabled this feature for your account.')


async def allow_python_authoring(user) -> bool:
    return user.role == 'admin' or (await security_policy()).allow_user_python_tools


async def oauth_email_trusted(provider: str, claims: dict) -> bool:
    """An explicit negative claim never becomes proof through a trust override."""
    assertion = claims.get('email_verified')
    if assertion is True:
        return True
    if assertion is not None:
        return False
    return provider in (await security_policy()).trusted_oauth_email_providers


def validate_upload_before_storage(file, maximum_mib: int | None):
    """Inspect the spooled upload without allocating or persisting its contents."""
    if not maximum_mib:
        return
    position = file.tell()
    try:
        file.seek(0, 2)
        size = file.tell()
    finally:
        file.seek(position)
    if size > int(maximum_mib) * 1024 * 1024:
        raise HTTPException(413, 'File exceeds the configured upload size limit.')


class RequestBodyLimitMiddleware:
    """Cap bytes while ASGI streams them, before multipart parsing or authentication."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):  # noqa: C901 - ASGI protocol and origin validation
        from starlette.responses import JSONResponse

        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = dict(scope.get('headers', []))
        origin = headers.get(b'origin', b'').decode('latin-1')
        cookie = headers.get(b'cookie', b'').decode('latin-1')
        cookie_auth_origin = origin and re.search(r'(?:^|;\s*)token=', cookie) and b'authorization' not in headers
        if scope['method'] not in {'POST', 'PUT', 'PATCH'} and not cookie_auth_origin:
            return await self.app(scope, receive, send)
        policy = await security_policy()
        limit = policy.max_request_mib * 1024 * 1024
        if origin and re.search(r'(?:^|;\s*)token=', cookie) and b'authorization' not in headers:
            from answerai.config import CORS_ALLOW_ORIGIN
            from starlette.requests import Request

            request = Request(scope)
            own_origin = str(request.base_url).rstrip('/')
            trusted = {
                own_origin,
                *policy.allowed_cookie_origins,
                *(item for item in CORS_ALLOW_ORIGIN if item != '*'),
            }
            if origin == 'null' or origin not in trusted:
                return await JSONResponse(
                    {'detail': 'Untrusted origin for cookie-authenticated request.'}, status_code=403
                )(scope, receive, send)
        if scope['method'] not in {'POST', 'PUT', 'PATCH'}:
            return await self.app(scope, receive, send)
        length = headers.get(b'content-length')
        if length is not None:
            try:
                declared = int(length)
                if declared < 0:
                    raise ValueError
            except ValueError:
                return await JSONResponse({'detail': 'Invalid Content-Length.'}, status_code=400)(scope, receive, send)
            if declared > limit:
                return await JSONResponse(
                    {'detail': 'Request body exceeds the configured size limit.'}, status_code=413
                )(scope, receive, send)
        consumed = 0
        started = False

        async def limited_receive():
            nonlocal consumed
            message = await receive()
            if message['type'] == 'http.request':
                consumed += len(message.get('body', b''))
                if consumed > limit:
                    raise HTTPException(413, 'Request body exceeds the configured size limit.')
            return message

        async def tracked_send(message):
            nonlocal started
            if message['type'] == 'http.response.start':
                started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except HTTPException as exc:
            if exc.status_code != 413 or started:
                raise
            await JSONResponse({'detail': exc.detail}, status_code=413)(scope, receive, send)


def validate_speech_input(body: bytes) -> dict:
    """Bound TTS work before provider dispatch, independently of the plan toggle."""
    from answerai.utils.json_codec import JSONCodec

    if len(body) > 65536:
        raise HTTPException(413, 'Speech request is too large.')
    try:
        payload = JSONCodec.loads(body)
    except (ValueError, TypeError):
        raise HTTPException(400, 'Invalid speech JSON.') from None
    if not isinstance(payload, dict) or not isinstance(payload.get('input'), str) or not payload['input'].strip():
        raise HTTPException(400, 'Speech input must be nonempty text.')
    if len(payload['input']) > 4096:
        raise HTTPException(413, 'Speech input must not exceed 4096 characters.')
    return payload
