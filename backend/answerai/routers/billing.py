"""Plans, hosted payments, verified webhooks, and admin entitlements."""

import os
import time
from typing import Literal

from answerai.internal.db import get_async_db
from answerai.models.billing import BillingAccount, Subscription, UsageBucket
from answerai.models.config import Config
from answerai.models.users import Users
from answerai.routers.mfa import MfaRoute
from answerai.utils.admin_actions import record_action
from answerai.utils.auth import get_admin_user, get_verified_user
from answerai.utils.email_verification import EmailSettings
from answerai.utils.payments import catalogue, manage, process_webhook, start_checkout
from answerai.utils.plans import FEATURES, BillingSettings, entitlement, reserve, settings
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

router = APIRouter(route_class=MfaRoute)


class CheckoutForm(BaseModel):
    model_config = ConfigDict(extra='forbid')
    provider: Literal['stripe', 'razorpay']


class ManageForm(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['portal', 'cancel', 'resume', 'abandon']


class OverrideForm(BaseModel):
    model_config = ConfigDict(extra='forbid')
    plan: Literal['', 'free', 'plus', 'blocked']
    until: int = Field(default=0, ge=0)


@router.get('/me')
async def me(user=Depends(get_verified_user)):
    name, plan, config = await entitlement(user)
    now = int(time.time())
    async with get_async_db() as db:
        subscriptions = (
            await db.scalars(
                select(Subscription)
                .where(Subscription.user_id == user.id)
                .order_by(Subscription.created_at.desc())
                .limit(20)
            )
        ).all()
        usage = (
            await db.scalars(
                select(UsageBucket).where(UsageBucket.user_id == user.id, UsageBucket.starts_at >= now // 86400 * 86400)
            )
        ).all()
    return {
        'plan': name,
        'enabled': config.enabled,
        'entitlements': plan.model_dump(),
        'usage': [
            {'metric': row.metric, 'window': row.window, 'used': row.used, 'resets_at': row.starts_at + row.window}
            for row in usage
            if row.starts_at + row.window > now
        ],
        'subscriptions': [
            {
                'id': row.id,
                'provider': row.provider,
                'status': row.status,
                'period_end': row.period_end,
                'cancel_at_period_end': row.cancel_at_period_end,
            }
            for row in subscriptions
        ],
    }


@router.get('/plans')
async def plans(user=Depends(get_verified_user)):
    config = await settings()
    return {
        'enabled': config.enabled,
        'free': config.free.model_dump(),
        'plus': config.plus.model_dump(),
        'prices': await catalogue(config),
    }


@router.post('/checkout')
async def checkout(form: CheckoutForm, user=Depends(get_verified_user)):
    await reserve(user.id, [('checkout', 60, 3, 1)])
    return await start_checkout(user, form.provider)


@router.post('/subscriptions/{subscription_id}')
async def manage_subscription(subscription_id: str, form: ManageForm, user=Depends(get_verified_user)):
    await reserve(user.id, [('billing_management', 60, 10, 1)])
    return await manage(user, subscription_id, form.action)


async def webhook(request, provider):
    # Bound payload before buffering it. Providers retry non-2xx deliveries.
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 1048576:
            raise HTTPException(413, 'Webhook is too large.')
    signature = request.headers.get('stripe-signature' if provider == 'stripe' else 'x-razorpay-signature', '')
    await process_webhook(provider, bytes(body), signature, request.headers.get('x-razorpay-event-id', ''))
    return {'received': True}


@router.post('/webhooks/stripe')
async def stripe_webhook(request: Request):
    return await webhook(request, 'stripe')


@router.post('/webhooks/razorpay')
async def razorpay_webhook(request: Request):
    return await webhook(request, 'razorpay')


@router.get('/config')
async def get_config(user=Depends(get_admin_user)):
    return {
        **(await settings()).model_dump(),
        'feature_keys': FEATURES,
        'credentials': {
            key: bool(os.getenv(key))
            for key in (
                'STRIPE_SECRET_KEY',
                'STRIPE_WEBHOOK_SECRET',
                'RAZORPAY_KEY_ID',
                'RAZORPAY_KEY_SECRET',
                'RAZORPAY_WEBHOOK_SECRET',
            )
        },
    }


@router.post('/config')
async def save_config(form: BillingSettings, user=Depends(get_admin_user)):
    EmailSettings(public_url=form.public_url)
    for plan in (form.free, form.plus):
        if set(plan.features) - set(FEATURES):
            raise HTTPException(400, 'Unknown plan feature.')
    await Config.upsert({'billing.settings': form.model_dump()})
    return await get_config(user)


@router.get('/users/{user_id}')
async def get_user_plan(user_id: str, user=Depends(get_admin_user)):
    from answerai.routers.admin_controls import target_user

    target = await target_user(user_id)
    user_id = target.id
    if not target:
        raise HTTPException(404, 'User not found.')
    async with get_async_db() as db:
        account = await db.get(BillingAccount, user_id)
    return {
        'user_id': user_id,
        'plan': (await entitlement(target))[0],
        'override': account.override if account else '',
        'until': account.override_until if account else 0,
    }


@router.post('/users/{user_id}')
async def override_user(user_id: str, form: OverrideForm, user=Depends(get_admin_user)):
    from answerai.routers.admin_controls import target_user

    target = await target_user(user_id)
    user_id = target.id
    if not target:
        raise HTTPException(404, 'User not found.')
    if target.role == 'admin':
        raise HTTPException(400, 'Administrator accounts bypass plan limits.')
    if form.until and form.until <= int(time.time()):
        raise HTTPException(400, 'Override expiry must be in the future.')
    async with get_async_db() as db:
        account = await db.get(BillingAccount, user_id)
        if account is None:
            account = BillingAccount(user_id=user_id, checkout_until=0)
            db.add(account)
        account.override = form.plan
        account.override_until = form.until
        record_action(db, user.id, 'account.plan_override', user_id, {'plan': form.plan, 'until': form.until})
        await db.commit()
    return await get_user_plan(user_id, user)
