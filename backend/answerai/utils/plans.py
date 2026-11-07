"""Server-enforced plans with database-atomic quota reservations across workers."""

import time
import asyncio
import json

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
    messages_per_five_hours: int | None = Field(default=None, ge=0, le=1000000)
    messages_per_week: int | None = Field(default=None, ge=0, le=10000000)
    tokens_per_five_hours: int | None = Field(default=None, ge=0, le=1000000000)
    tokens_per_day: int | None = Field(default=None, ge=0, le=1000000000)
    tokens_per_week: int | None = Field(default=None, ge=0, le=1000000000)
    max_output_tokens: int = Field(default=4096, ge=1, le=1000000)
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


# Long windows are anchored at first use; short burst/daily limits retain UTC boundaries.
LONG_WINDOWS = {18000, 604800}
RATE_METRICS = {'messages', 'requests', 'tokens', 'audio', 'live_minutes', '_anchor', *FEATURES}


def plan_limits(plan):
    return [
        ('messages', 86400, plan.messages_per_day),
        ('requests', 60, plan.requests_per_minute),
        ('messages', 18000, plan.messages_per_five_hours),
        ('messages', 604800, plan.messages_per_week),
        ('tokens', 18000, plan.tokens_per_five_hours),
        ('tokens', 86400, plan.tokens_per_day),
        ('tokens', 604800, plan.tokens_per_week),
    ]


async def usage_snapshot(user_id, plan, now=None):
    now = int(time.time()) if now is None else now
    async with get_async_db() as db:
        rows = (
            await db.scalars(
                select(UsageBucket).where(
                    UsageBucket.user_id == user_id,
                    UsageBucket.starts_at + UsageBucket.window > now,
                    UsageBucket.metric != '_anchor',
                )
            )
        ).all()
    limits = {(metric, window): maximum for metric, window, maximum in plan_limits(plan)}
    limits.update({(feature, 86400): maximum for feature, maximum in plan.feature_limits.items()})
    limits.update({('audio', 86400): plan.audio_requests_per_day, ('live_minutes', 86400): plan.live_minutes_per_day})
    return [
        {
            'metric': row.metric,
            'window': row.window,
            'used': row.used,
            'limit': limits.get((row.metric, row.window)),
            'remaining': max(0, limits[(row.metric, row.window)] - row.used)
            if limits.get((row.metric, row.window)) is not None
            else None,
            'resets_at': row.starts_at + row.window,
        }
        for row in rows
    ]


def token_reservation(payload, plan):
    """Conservative text-token credits, not a provider invoice/tokenizer claim.

    Charge UTF-8 bytes plus structural overhead and a bounded output allowance.
    Reservation is retained on cancellation and for providers without usage reporting.
    """
    options = payload.get('options') or {}
    if not isinstance(options, dict):
        raise HTTPException(400, 'Invalid generation options.')
    requested = [payload.get(key) for key in ('max_tokens', 'max_completion_tokens', 'max_output_tokens')]
    requested.append(options.get('num_predict'))
    supplied = [value for value in requested if value is not None]
    if any(type(value) is not int or value < 1 for value in supplied):
        raise HTTPException(400, 'Output token limits must be positive integers.')
    allowance = min([plan.max_output_tokens, *supplied])
    # Set every supplied alias so no larger alias overrides the cap downstream.
    for key in ('max_tokens', 'max_completion_tokens', 'max_output_tokens'):
        if key in payload:
            payload[key] = allowance
    if not any(key in payload for key in ('max_tokens', 'max_completion_tokens', 'max_output_tokens')):
        payload['max_tokens'] = allowance
    if 'input' in payload:
        payload['max_output_tokens'] = allowance
        payload.pop('max_tokens', None)
    if 'options' in payload or 'prompt' in payload:
        payload['options'] = {**options, 'num_predict': allowance}
    content = {key: payload[key] for key in ('messages', 'input', 'prompt', 'system', 'tools') if key in payload}
    return len(json.dumps(content, ensure_ascii=False).encode('utf-8')) + 1024 + allowance


async def reserve(user_id, limits, now=None):
    """All counters increment together, or none do. Zero is a hard limit."""
    now = int(time.time()) if now is None else now
    for attempt in range(5):
        try:
            async with get_async_db() as db:
                starts = {}
                created = False
                for metric, window, maximum, amount in limits:
                    if type(amount) is not int or amount < 0 or window <= 0 or maximum < 0:
                        raise ValueError('Invalid quota reservation.')
                    if window in LONG_WINDOWS and window not in starts:
                        anchor_id = f'{user_id}:anchor:{window}'
                        await db.execute(
                            update(UsageBucket)
                            .where(
                                UsageBucket.id == anchor_id,
                                UsageBucket.starts_at + window <= now,
                            )
                            .values(starts_at=now)
                        )
                        anchor = await db.scalar(
                            select(UsageBucket).where(UsageBucket.id == anchor_id).with_for_update()
                        )
                        if anchor is None:
                            anchor = UsageBucket(
                                id=anchor_id, user_id=user_id, metric='_anchor', window=window, starts_at=now, used=0
                            )
                            db.add(anchor)
                            await db.flush()
                        starts[window] = anchor.starts_at
                    start = starts.get(window, now // window * window)
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
                            headers={
                                'Retry-After': str(max(1, start + window - now)),
                                'X-RateLimit-Limit': str(maximum),
                                'X-RateLimit-Remaining': str(max(0, maximum - (existing.used if existing else 0))),
                                'X-RateLimit-Reset': str(start + window),
                            },
                        )
                    db.add(
                        UsageBucket(id=key, user_id=user_id, metric=metric, window=window, starts_at=start, used=amount)
                    )
                    await db.flush()
                    created = True
                # Indexed, user-scoped cleanup only when creating counters, never a global write per request.
                if created:
                    await db.execute(
                        delete(UsageBucket).where(
                            UsageBucket.user_id == user_id,
                            UsageBucket.metric != '_anchor',
                            UsageBucket.starts_at + UsageBucket.window <= now,
                        )
                    )
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
    name, plan, config = await entitlement(user)
    if name != 'admin' and (
        name == 'blocked' or (config.enabled and '*' not in plan.models and payload.get('model', '') not in plan.models)
    ):
        raise denied('this model')
    if name == 'admin' or not config.enabled:
        return

    def allowed(feature):
        if not plan.features.get(feature, False):
            raise denied(feature)

    if payload.get('model_item', {}).get('direct'):
        allowed('direct_connections')
    requested_features = set()
    for key, value in (payload.get('features') or {}).items():
        feature = {'image_generation': 'images'}.get(key, key)
        if value and feature in FEATURES:
            allowed(feature)
            requested_features.add(feature)
    if payload.get('tool_ids') or payload.get('tool_servers') or payload.get('tools'):
        allowed('tools')
        requested_features.add('tools')
    if payload.get('files'):
        allowed('uploads')
    token_limits = [
        (metric, window, maximum)
        for metric, window, maximum in plan_limits(plan)
        if metric == 'tokens' and maximum is not None
    ]
    amount = token_reservation(payload, plan) if token_limits else 0
    if token_limits:
        request.state.billing_output_cap = min(
            plan.max_output_tokens,
            *(
                value
                for value in [
                    payload.get('max_tokens'),
                    payload.get('max_completion_tokens'),
                    payload.get('max_output_tokens'),
                    (payload.get('options') or {}).get('num_predict'),
                ]
                if value is not None
            ),
        )
    if not getattr(request.state, 'billing_reserved', False):
        await reserve(
            user.id,
            [
                (metric, window, maximum, amount if metric == 'tokens' else 1)
                for metric, window, maximum in plan_limits(plan)
                if maximum is not None
            ]
            + [
                (feature, 86400, plan.feature_limits.get(feature, 0), 1)
                for feature in requested_features
                if not feature.startswith('live_')
            ],
        )
        request.state.billing_reserved = True
        if token_limits:
            request.state.billing_quota_user = user.id
            request.state.billing_token_limits = token_limits
            request.state.billing_initial_credit = amount
            request.state.billing_credit_available = True


def apply_output_cap(request, payload, *, ollama=False):
    """Reapply after server model defaults so aliases cannot override the reserved allowance."""
    cap = getattr(request.state, 'billing_output_cap', None)
    if cap is None:
        return
    if ollama and 'input' not in payload:
        options = payload.get('options') or {}
        value = options.get('num_predict')
        payload['options'] = {**options, 'num_predict': min(cap, value) if type(value) is int and value > 0 else cap}
        payload.pop('max_tokens', None)
        return
    keys = [key for key in ('max_tokens', 'max_completion_tokens', 'max_output_tokens') if key in payload]
    if not keys:
        keys = ['max_output_tokens' if 'input' in payload else 'max_tokens']
    for key in keys:
        value = payload.get(key)
        payload[key] = min(cap, value) if type(value) is int and value > 0 else cap


async def reserve_provider_tokens(request, payload, *, ollama=False):
    apply_output_cap(request, payload, ollama=ollama)
    limits = getattr(request.state, 'billing_token_limits', None)
    if not limits:
        return
    # A request may make several agent/tool provider calls. Only the first can use
    # its admission reservation; subsequent calls must reserve their own credits.
    if not hasattr(request.state, 'billing_credit_lock'):
        request.state.billing_credit_lock = asyncio.Lock()
    async with request.state.billing_credit_lock:
        content = {key: payload[key] for key in ('messages', 'input', 'prompt', 'system', 'tools') if key in payload}
        required = (
            len(json.dumps(content, ensure_ascii=False).encode('utf-8')) + 1024 + request.state.billing_output_cap
        )
        credit = request.state.billing_initial_credit if request.state.billing_credit_available else 0
        amount = max(0, required - credit)
        if amount:
            await reserve(
                request.state.billing_quota_user,
                [(metric, window, maximum, amount) for metric, window, maximum in limits],
            )
        request.state.billing_credit_available = False


async def reserve_audio(request, user, *, charge_request=True):
    """Share the audio budget with internal upload processing without double charging HTTP routes."""
    name, plan, config = await entitlement(user)
    if name == 'blocked':
        raise denied('audio')
    if not config.enabled or name == 'admin' or getattr(request.state, 'billing_audio_reserved', False):
        return
    charges = [('audio', 86400, plan.audio_requests_per_day, 1)]
    if charge_request:
        charges.insert(0, ('requests', 60, plan.requests_per_minute, 1))
    await reserve(user.id, charges)
    request.state.billing_audio_reserved = True


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
            await reserve_audio(request, user)

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
