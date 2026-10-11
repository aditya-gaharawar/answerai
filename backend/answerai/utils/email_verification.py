"""Email verification settings, secure token lifecycle, and SMTP delivery."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import html
import logging
import os
import secrets
import smtplib
import ssl
import time
from email.errors import HeaderParseError
from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import formataddr
from typing import Literal
from urllib.parse import urlsplit

from answerai.env import WEBUI_SECRET_KEY
from answerai.internal.db import get_async_db
from answerai.models.auths import Auth
from answerai.models.config import Config
from answerai.models.email_verifications import EmailVerification
from answerai.utils.misc import validate_email_format
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

log = logging.getLogger(__name__)
PREFIX = 'auth.email_verification.'
PASSWORD_KEY = PREFIX + 'smtp_password_encrypted'
GENERIC_RESEND_MESSAGE = 'If this account needs verification, a verification email will be sent.'


def valid_delivery_email(value: str) -> bool:
    if any(char in value for char in ('\r', '\n', '\x00')):
        return False
    try:
        address = Address(addr_spec=value)
    except (ValueError, HeaderParseError):
        return False
    return address.addr_spec == value and validate_email_format(value)


class EmailSettings(BaseModel):
    model_config = ConfigDict(extra='forbid')
    enabled: bool = False
    smtp_host: str = Field(default='', max_length=255)
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_security: Literal['starttls', 'ssl'] = 'starttls'
    smtp_username: str = Field(default='', max_length=320)
    smtp_password: SecretStr | None = None
    from_email: str = Field(default='', max_length=320)
    from_name: str = Field(default='ANSWERAI', min_length=1, max_length=100)
    public_url: str = Field(default='https://answerai.in', max_length=2048)
    token_ttl_seconds: int = Field(default=3600, ge=300, le=86400)
    resend_cooldown_seconds: int = Field(default=60, ge=60, le=3600)

    @field_validator('smtp_host', 'smtp_username', 'from_email', 'from_name', 'public_url')
    @classmethod
    def safe_text(cls, value):
        if '\r' in value or '\n' in value or '\x00' in value:
            raise ValueError('Mail settings must not contain control characters.')
        return value.strip()

    @field_validator('from_email')
    @classmethod
    def valid_sender(cls, value):
        if value and not valid_delivery_email(value):
            raise ValueError('Enter a valid sender email address.')
        return value

    @field_validator('public_url')
    @classmethod
    def valid_public_url(cls, value):
        parts = urlsplit(value)
        local = parts.hostname in {'localhost', '127.0.0.1', '::1'}
        if (parts.scheme != 'https' and not (local and parts.scheme == 'http')) or not parts.hostname:
            raise ValueError('Public URL must use HTTPS, or HTTP on localhost for development.')
        if parts.username or parts.password or parts.query or parts.fragment:
            raise ValueError('Public URL must not contain credentials, a query, or a fragment.')
        return value.rstrip('/')


class UpdateEmailSettings(EmailSettings):
    clear_password: bool = False


def password_cipher():
    if not WEBUI_SECRET_KEY:
        raise HTTPException(503, 'A persistent application secret is required for SMTP configuration.')
    key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'answerai/email-smtp/v1').derive(
        WEBUI_SECRET_KEY.encode()
    )
    return Fernet(base64.urlsafe_b64encode(key))


async def get_email_settings(*, decrypt_password: bool = True) -> EmailSettings:
    defaults = {
        'enabled': os.getenv('ENABLE_EMAIL_VERIFICATION', 'false').lower() == 'true',
        'smtp_host': os.getenv('SMTP_HOST', ''),
        'smtp_port': os.getenv('SMTP_PORT', '587'),
        'smtp_security': os.getenv('SMTP_SECURITY', 'starttls'),
        'smtp_username': os.getenv('SMTP_USERNAME', ''),
        'from_email': os.getenv('SMTP_FROM_EMAIL', ''),
        'from_name': os.getenv('SMTP_FROM_NAME', 'ANSWERAI'),
        'public_url': os.getenv('WEBUI_URL', 'https://answerai.in'),
        'token_ttl_seconds': os.getenv('EMAIL_VERIFICATION_TOKEN_TTL_SECONDS', '3600'),
        'resend_cooldown_seconds': os.getenv('EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS', '60'),
    }
    values = await Config.get_many(*(PREFIX + key for key in defaults), PASSWORD_KEY)
    for field in defaults:
        if values.get(PREFIX + field) is not None:
            defaults[field] = values[PREFIX + field]
    encrypted = values.get(PASSWORD_KEY)
    if encrypted and not decrypt_password:
        password = 'configured'  # Presence marker only; never used for delivery.
    elif encrypted:
        try:
            password = password_cipher().decrypt(encrypted.encode()).decode()
        except (InvalidToken, ValueError):
            raise HTTPException(503, 'SMTP credentials are unavailable. Re-enter the SMTP password.') from None
    elif encrypted == '':
        password = ''  # Explicitly cleared; do not resurrect an environment credential.
    else:
        password = os.getenv('SMTP_PASSWORD', '')
    return EmailSettings(**defaults, smtp_password=SecretStr(password) if password else None)


def public_settings(settings: EmailSettings):
    return {**settings.model_dump(exclude={'smtp_password'}), 'password_configured': bool(settings.smtp_password)}


def require_mail_configuration(settings):
    if not settings.smtp_host or not settings.from_email:
        raise HTTPException(503, 'Email delivery is not configured. Ask an administrator to configure SMTP.')
    if settings.smtp_username and not settings.smtp_password:
        raise HTTPException(503, 'SMTP authentication requires a password.')


async def save_email_settings(form: UpdateEmailSettings):
    current = await get_email_settings(
        decrypt_password=form.enabled and not (form.clear_password or bool(form.smtp_password))
    )
    password = None if form.clear_password else form.smtp_password or current.smtp_password
    settings = EmailSettings(**form.model_dump(exclude={'clear_password', 'smtp_password'}), smtp_password=password)
    if settings.enabled:
        require_mail_configuration(settings)
    updates = {PREFIX + key: value for key, value in settings.model_dump(exclude={'smtp_password'}).items()}
    if form.clear_password:
        updates[PASSWORD_KEY] = ''
    elif form.smtp_password and form.smtp_password.get_secret_value():
        updates[PASSWORD_KEY] = password_cipher().encrypt(form.smtp_password.get_secret_value().encode()).decode()
    await Config.upsert(updates)
    return public_settings(settings)


def build_email(settings: EmailSettings, recipient: str, token: str | None = None) -> EmailMessage:
    message = EmailMessage()
    message['From'] = formataddr((settings.from_name, settings.from_email))
    message['To'] = recipient
    message['Subject'] = 'Verify your ANSWERAI email' if token else 'ANSWERAI email delivery test'
    if token:
        url = f'{settings.public_url}/auth/verify-email#token={token}'
        minutes = settings.token_ttl_seconds // 60
        text = (
            f'Welcome to ANSWERAI!\n\nConfirm your email address:\n{url}\n\n'
            f'This link expires in {minutes} minutes and can be used once.\n'
            'If you did not create an account, ignore this email. It will not activate the account.'
        )
        body = (
            f'<h1>Welcome to ANSWERAI</h1><p>Confirm your email address to finish signing up.</p>'
            f'<p><a href="{html.escape(url, quote=True)}">Verify email address</a></p>'
            f'<p>This link expires in {minutes} minutes and can be used once.</p>'
            '<p>If you did not create an account, ignore this email.</p>'
        )
    else:
        text = 'Your ANSWERAI SMTP configuration is working.'
        body = '<h1>ANSWERAI</h1><p>Your SMTP configuration is working.</p>'
    message.set_content(text)
    message.add_alternative(body, subtype='html')
    return message


def _send(settings, message):
    context = ssl.create_default_context()
    client_class = smtplib.SMTP_SSL if settings.smtp_security == 'ssl' else smtplib.SMTP
    kwargs = {'host': settings.smtp_host, 'port': settings.smtp_port, 'timeout': 20}
    if settings.smtp_security == 'ssl':
        kwargs['context'] = context
    with client_class(**kwargs) as client:
        if settings.smtp_security == 'starttls':
            client.ehlo()
            client.starttls(context=context)
            client.ehlo()
        if settings.smtp_username:
            client.login(settings.smtp_username, settings.smtp_password.get_secret_value())
        refused = client.send_message(message)
        if refused:
            raise smtplib.SMTPRecipientsRefused(refused)


async def send_email(settings, recipient, token=None):
    require_mail_configuration(settings)
    await asyncio.to_thread(_send, settings, build_email(settings, recipient, token))


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


async def issue_verification(user_id: str, settings: EmailSettings) -> bool:
    """Reserve a token atomically before delivery, including across multiple workers."""
    require_mail_configuration(settings)
    now = int(time.time())
    token = secrets.token_urlsafe(32)
    token_hash = hash_token(token)
    async with get_async_db() as db:
        auth = await db.get(Auth, user_id)
        if auth is None or not auth.active or auth.email_verified:
            return False
        email = auth.email
        values = dict(email=email, token_hash=token_hash, expires_at=now + settings.token_ttl_seconds, sent_at=now)
        record = await db.get(EmailVerification, user_id)
        if record:
            result = await db.execute(
                update(EmailVerification)
                .where(
                    EmailVerification.user_id == user_id,
                    EmailVerification.sent_at <= now - settings.resend_cooldown_seconds,
                )
                .values(**values)
            )
            if result.rowcount != 1:
                return False
        else:
            db.add(EmailVerification(user_id=user_id, **values))
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            return False
    try:
        await send_email(settings, email, token)
    except Exception:
        # Invalidate only our own token; retain the cooldown to bound failed delivery retries.
        async with get_async_db() as db:
            await db.execute(
                update(EmailVerification)
                .where(
                    EmailVerification.user_id == user_id,
                    EmailVerification.token_hash == token_hash,
                )
                .values(token_hash=None, expires_at=0)
            )
            await db.commit()
        log.warning('Verification email delivery failed; SMTP details and tokens withheld.')
        raise HTTPException(503, 'Email could not be delivered. Please try resending in a minute.') from None
    return True


async def consume_verification(token: str) -> None:
    """Verify the current credential email and consume the token in one transaction."""
    now = int(time.time())
    async with get_async_db() as db:
        record = (
            await db.execute(
                select(EmailVerification).where(
                    EmailVerification.token_hash == hash_token(token),
                    EmailVerification.expires_at > now,
                )
            )
        ).scalar_one_or_none()
        if record is None:
            raise HTTPException(400, 'This verification link is invalid or has expired. Request a new email.')
        # Deleting with the exact hash is a compare-and-swap: concurrent clicks cannot both succeed.
        removed = await db.execute(
            delete(EmailVerification).where(
                EmailVerification.user_id == record.user_id,
                EmailVerification.token_hash == hash_token(token),
                EmailVerification.expires_at > now,
            )
        )
        if removed.rowcount != 1:
            await db.rollback()
            raise HTTPException(400, 'This verification link has already been used. Please sign in.')
        verified = await db.execute(
            update(Auth)
            .where(
                Auth.id == record.user_id,
                Auth.email == record.email,
                Auth.active.is_(True),
                Auth.email_verified.is_(False),
            )
            .values(email_verified=True)
        )
        if verified.rowcount != 1:
            await db.rollback()
            raise HTTPException(400, 'This verification link is no longer valid. Request a new email.')
        await db.commit()
