"""Public verification endpoints and admin-only SMTP management."""

import hashlib
import logging

from answerai.models.auths import Auths
from answerai.models.users import Users
from answerai.routers.mfa import MfaRoute
from answerai.utils.auth import get_admin_user
from answerai.utils.email_verification import (
    GENERIC_RESEND_MESSAGE,
    UpdateEmailSettings,
    consume_verification,
    get_email_settings,
    issue_verification,
    public_settings,
    save_email_settings,
    send_email,
    valid_delivery_email,
)
from answerai.utils.rate_limit import RateLimiter
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

log = logging.getLogger(__name__)
router = APIRouter(route_class=MfaRoute)
request_limiter = RateLimiter(limit=10, window=900)
email_limiter = RateLimiter(limit=5, window=3600)
verify_limiter = RateLimiter(limit=30, window=900)


class EmailForm(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: str = Field(min_length=3, max_length=320)

    @field_validator('email')
    @classmethod
    def validate_email(cls, value):
        value = value.strip().lower()
        if not valid_delivery_email(value):
            raise ValueError('Enter a valid email address.')
        return value


class VerificationForm(BaseModel):
    model_config = ConfigDict(extra='forbid')
    token: SecretStr = Field(min_length=40, max_length=128)


async def limit_ip(request, limiter, purpose):
    ip = request.client.host if request.client else 'unknown'
    key = f'email-verification:{purpose}:' + hashlib.sha256(ip.encode()).hexdigest()
    if await limiter.is_limited(getattr(request.app.state, 'redis', None), key):
        raise HTTPException(429, 'Too many requests. Please try again later.', headers={'Retry-After': '900'})


@router.post('/verify')
async def verify(request: Request, form: VerificationForm):
    await limit_ip(request, verify_limiter, 'verify')
    await consume_verification(form.token.get_secret_value())
    return {'message': 'Your email is verified. You can now sign in.'}


@router.post('/resend')
async def resend(request: Request, form: EmailForm, response: Response, background_tasks: BackgroundTasks):
    await limit_ip(request, request_limiter, 'resend')
    email_key = 'email-verification:address:' + hashlib.sha256(form.email.encode()).hexdigest()
    if await email_limiter.is_limited(getattr(request.app.state, 'redis', None), email_key):
        # Same response for known and unknown addresses, including throttled addresses.
        return {'message': GENERIC_RESEND_MESSAGE, 'resend_after': 60}
    settings = await get_email_settings()
    account = await Users.get_user_by_email(form.email)
    if account:
        auth = await Auths.get_auth_by_id(account.id)
        if auth and auth.active and not auth.email_verified:
            background_tasks.add_task(deliver_verification, account.id, settings)
    response.headers['Cache-Control'] = 'no-store'
    return {'message': GENERIC_RESEND_MESSAGE, 'resend_after': settings.resend_cooldown_seconds}


async def deliver_verification(user_id, settings):
    try:
        await issue_verification(user_id, settings)
    except Exception:
        # Public response remains identical for unknown addresses and failed delivery.
        log.warning('Verification delivery could not complete; sensitive details withheld.')


@router.get('/config')
async def get_config(user=Depends(get_admin_user)):
    return public_settings(await get_email_settings(decrypt_password=False))


@router.post('/config')
async def update_config(form: UpdateEmailSettings, user=Depends(get_admin_user)):
    return await save_email_settings(form)


@router.post('/test')
async def test_email(request: Request, user=Depends(get_admin_user)):
    await limit_ip(request, request_limiter, 'test')
    try:
        await send_email(await get_email_settings(), user.email)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, 'Test email could not be sent. Check SMTP settings and server connectivity.') from None
    return {'message': 'Test email sent to your account email address.'}
