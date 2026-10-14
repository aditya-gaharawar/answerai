"""Server-enforced plans with database-atomic quota reservations across workers."""

import time

from answerai.internal.db import get_async_db
from answerai.models.billing import BillingAccount, LiveLease, Subscription, UsageBucket
from answerai.models.config import Config
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

FEATURES = (
    'uploads',
    'images',
    'web_search',
    'code_interpreter',
    'tools',
    'memory',
    'automations',
    'live_calls',
    'live_video',
    'direct_connections',
)
PERMISSIONS = {
    'chat.file_upload': 'uploads',
    'chat.image_generation': 'images',
    'features.image_generation': 'images',
    'features.web_search': 'web_search',
    'features.code_interpreter': 'code_interpreter',
    'chat.web_search': 'web_search',
    'chat.code_interpreter': 'code_interpreter',
    'chat.call': 'live_calls',
    'features.memories': 'memory',
    'features.direct_tool_servers': 'tools',
    'features.direct_connections': 'direct_connections',
    'features.automations': 'automations',
    'workspace.tools': 'tools',
    'workspace.tools_import': 'tools',
}


class Plan(BaseModel):
    model_config = ConfigDict(extra='forbid')
    models: list[str] = Field(default_factory=lambda: ['*'], max_length=500)
    feature_limits: dict[str, int] = Field(
        default_factory=lambda: {key: 10 if key == 'uploads' else 0 for key in FEATURES if not key.startswith('live_')}
    )
    messages_per_day: int = Field(default=20, ge=0, le=1000000)
    requests_per_minute: int = Field(default=5, ge=0, le=10000)
    audio_requests_per_day: int = Field(default=20, ge=0, le=1000000)
    live_minutes_per_day: int = Field(default=0, ge=0, le=1440)
    max_call_minutes: int = Field(default=15, ge=1, le=120)
    features: dict[str, bool] = Field(default_factory=lambda: {key: key == 'uploads' for key in FEATURES})

    @field_validator('feature_limits')
    @classmethod
    def valid_limits(cls, value):
        if any(
            key not in FEATURES or key.startswith('live_') or amount < 0 or amount > 1000000
            for key, amount in value.items()
        ):
            raise ValueError('Feature limits must be known features with values from 0 to 1000000.')
        return value


class BillingSettings(BaseModel):
    model_config = ConfigDict(extra='forbid')
    enabled: bool = False
    free: Plan = Field(default_factory=Plan)
    plus: Plan = Field(
        default_factory=lambda: Plan(
            feature_limits={
                key: 100 if key != 'direct_connections' else 0 for key in FEATURES if not key.startswith('live_')
            },
            messages_per_day=1000,
            requests_per_minute=60,
            audio_requests_per_day=200,
            live_minutes_per_day=60,
            max_call_minutes=30,
            features={key: key != 'direct_connections' for key in FEATURES},
        )
    )
    stripe_enabled: bool = False
    stripe_price_id: str = Field(default='', max_length=200)
    razorpay_enabled: bool = False
    razorpay_plan_id: str = Field(default='', max_length=200)
    public_url: str = 'https://answerai.in'

    @field_validator('public_url')
    @classmethod
    def valid_public_url(cls, value):
        from answerai.utils.email_verification import EmailSettings

        return EmailSettings(public_url=value).public_url


async def settings():
    return BillingSettings.model_validate(await Config.get('billing.settings') or {})


async def entitlement(user, config=None):
    config = config or await settings()
    now = int(time.time())
    if user.role == 'admin':
        return 'admin', config.plus, config
    async with get_async_db() as db:
        account = await db.get(BillingAccount, user.id)
        if account and account.override and (not account.override_until or account.override_until > now):
            name = account.override
        else:
            active = await db.scalar(
                select(Subscription.id)
                .where(Subscription.user_id == user.id, Subscription.status == 'active', Subscription.period_end > now)
                .limit(1)
            )
            name = 'plus' if active else 'free'
    if name == 'blocked':
        return (
            name,
            config.free.model_copy(
                update={
                    'features': {key: False for key in FEATURES},
                    'models': [],
                    'messages_per_day': 0,
                    'requests_per_minute': 0,
                    'audio_requests_per_day': 0,
                }
            ),
            config,
        )
    return name, config.plus if name == 'plus' or not config.enabled else config.free, config


def denied(feature):
    return HTTPException(403, f'Your plan does not include {feature.replace("_", " ")}. View plans at /billing.')


async def feature_allowed(user_id, feature, role=None):
    from types import SimpleNamespace

    if role is None:
        from answerai.models.users import Users

        user = await Users.get_user_by_id(user_id)
        if not user:
            return False
    else:
        user = SimpleNamespace(id=user_id, role=role)
    name, plan, config = await entitlement(user)
    return name == 'admin' or (name != 'blocked' and (not config.enabled or plan.features.get(feature, False)))


async def require_feature(user, feature):
    if not await feature_allowed(user.id, feature, user.role):
        raise denied(feature)


async def require_model(user, model_id):
    name, plan, config = await entitlement(user)
    if name != 'admin' and (
        name == 'blocked' or (config.enabled and '*' not in plan.models and model_id not in plan.models)
    ):
        raise denied('this model')


async def reserve(user_id, limits, now=None):
    """All counters increment together, or none do. Zero is a hard limit."""
    now = int(time.time()) if now is None else now
    for attempt in range(5):
        try:
            async with get_async_db() as db:
                for metric, window, maximum, amount in limits:
                    start = now // window * window
                    key = f'{user_id}:{metric}:{window}:{start}'
                    changed = await db.execute(
                        update(UsageBucket)
                        .where(UsageBucket.id == key, UsageBucket.used + amount <= maximum)
                        .values(used=UsageBucket.used + amount)
                    )
                    if changed.rowcount:
                        continue
                    existing = await db.get(UsageBucket, key)
                    if existing or amount > maximum:
                        raise HTTPException(
                            429,
                            f'{metric.replace("_", " ").capitalize()} limit reached. View plans at /billing.',
                            headers={'Retry-After': str(start + window - now)},
                        )
                    db.add(
                        UsageBucket(id=key, user_id=user_id, metric=metric, window=window, starts_at=start, used=amount)
                    )
                    await db.flush()
                # Daily buckets need only a week of history for the current usage UI.
                await db.execute(delete(UsageBucket).where(UsageBucket.starts_at < now - 7 * 86400))
                await db.commit()
            return
        except IntegrityError:
            if attempt == 4:
                raise HTTPException(503, 'Usage counters are busy. Try again.') from None


async def reserve_generation(request, user, payload):
    if (
        not isinstance(payload.get('model'), str)
        or not isinstance(payload.get('model_item', {}), dict)
        or not isinstance(payload.get('features') or {}, dict)
    ):
        raise HTTPException(400, 'Invalid model or feature options.')
    await require_model(user, payload.get('model', ''))
    name, plan, config = await entitlement(user)
    if name == 'admin' or not config.enabled:
        return
    if payload.get('model_item', {}).get('direct'):
        await require_feature(user, 'direct_connections')
    requested_features = set()
    for key, value in (payload.get('features') or {}).items():
        feature = {'image_generation': 'images'}.get(key, key)
        if value and feature in FEATURES:
            await require_feature(user, feature)
            requested_features.add(feature)
    if payload.get('tool_ids') or payload.get('tool_servers') or payload.get('tools'):
        await require_feature(user, 'tools')
        requested_features.add('tools')
    if payload.get('files'):
        await require_feature(user, 'uploads')
    if not getattr(request.state, 'billing_reserved', False):
        await reserve(
            user.id,
            [('messages', 86400, plan.messages_per_day, 1), ('requests', 60, plan.requests_per_minute, 1)]
            + [
                (feature, 86400, plan.feature_limits.get(feature, 0), 1)
                for feature in requested_features
                if not feature.startswith('live_')
            ],
        )
        request.state.billing_reserved = True


async def enforce_http(request, user):  # noqa: C901 - provider/route dispatch
    """Cover direct generation routes and feature APIs, including API-key callers."""
    path = request.url.path.rstrip('/')
    if request.method in {'POST', 'PUT', 'PATCH'}:
        requested_features = set()
        prefixes = {
            '/api/v1/files': 'uploads',
            '/api/v1/images': 'images',
            '/api/v1/memories': 'memory',
            '/api/v1/automations': 'automations',
            '/api/v1/tools': 'tools',
            '/api/v1/terminals': 'tools',
            '/api/v1/retrieval': 'uploads',
            '/api/v1/utils/code': 'code_interpreter',
        }
        for prefix, feature in prefixes.items():
            if (path == prefix or path.startswith(prefix + '/')) and not (
                prefix == '/api/v1/retrieval' and path.startswith('/api/v1/retrieval/process/web/search')
            ):
                await require_feature(user, feature)
                requested_features.add(feature)
        if path.startswith('/api/v1/retrieval/process/web/search') or '/search/web' in path:
            await require_feature(user, 'web_search')
            requested_features.discard('uploads')
            requested_features.add('web_search')
        if requested_features:
            name, plan, config = await entitlement(user)
            if config.enabled and name != 'admin':
                await reserve(
                    user.id,
                    [('requests', 60, plan.requests_per_minute, 1)]
                    + [(feature, 86400, plan.feature_limits.get(feature, 0), 1) for feature in requested_features],
                )
        if path.startswith('/openai/'):
            allowed = {'/openai/chat/completions', '/openai/responses', '/openai/audio/speech'}
            if path not in allowed:
                config = await settings()
                if config.enabled and user.role != 'admin':
                    raise denied('provider passthrough')
        if path in {'/openai/audio/speech', '/api/v1/audio/speech', '/api/v1/audio/transcriptions'}:
            name, plan, config = await entitlement(user)
            if name == 'blocked':
                raise denied('audio')
            if config.enabled and name != 'admin':
                await reserve(
                    user.id,
                    [('requests', 60, plan.requests_per_minute, 1), ('audio', 86400, plan.audio_requests_per_day, 1)],
                )
        generation = path in {
            '/api/chat/completions',
            '/api/v1/chat/completions',
            '/api/v1/responses',
            '/openai/chat/completions',
            '/openai/responses',
        } or (
            path.startswith('/ollama/')
            and any(
                part in path
                for part in (
                    '/api/chat',
                    '/api/generate',
                    '/v1/completions',
                    '/v1/chat/completions',
                    '/v1/messages',
                    '/v1/responses',
                )
            )
        )
        if generation:
            try:
                body = await request.json()
            except ValueError:
                raise HTTPException(400, 'Invalid JSON body.') from None
            if not isinstance(body, dict):
                raise HTTPException(400, 'Expected a JSON object.')
            await reserve_generation(request, user, body)


async def acquire_lease(user_id, session_id):
    now = int(time.time())
    try:
        async with get_async_db() as db:
            updated = await db.execute(
                update(LiveLease)
                .where(LiveLease.user_id == user_id, LiveLease.expires_at <= now)
                .values(session_id=session_id, expires_at=now + 90)
            )
            if not updated.rowcount:
                if await db.get(LiveLease, user_id):
                    raise HTTPException(409, 'You already have an active call.')
                db.add(LiveLease(user_id=user_id, session_id=session_id, expires_at=now + 90))
            await db.commit()
    except IntegrityError:
        raise HTTPException(409, 'You already have an active call.') from None


async def release_lease(user_id, session_id):
    async with get_async_db() as db:
        await db.execute(delete(LiveLease).where(LiveLease.user_id == user_id, LiveLease.session_id == session_id))
        await db.commit()
