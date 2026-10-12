"""Privileged account controls with durable, sanitized audit records."""

import time
from typing import Literal

from answerai.internal.db import get_async_db
from answerai.models.admin_actions import AdminAction
from answerai.models.auths import Auth, Auths
from answerai.models.billing import BillingAccount, BillingEvent, LiveLease, Subscription, UsageBucket
from answerai.models.config import Config
from answerai.models.oauth_sessions import OAuthSession
from answerai.models.users import Users
from answerai.routers.mfa import MfaRoute
from answerai.utils.admin_actions import record_action
from answerai.utils.auth import get_admin_user
from answerai.utils.payments import reconcile
from answerai.utils.plans import entitlement
from answerai.utils.security_policy import SecurityPolicy, security_policy
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, func, select

router = APIRouter(route_class=MfaRoute)


async def target_user(identifier):
    user = (
        await Users.get_user_by_email(identifier.strip())
        if '@' in identifier
        else await Users.get_user_by_id(identifier)
    )
    if not user:
        raise HTTPException(404, 'Account not found.')
    return user


class AccountAction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['reset_usage', 'stop_call', 'revoke_sessions', 'disable_login', 'enable_login']
    reason: str = Field(min_length=3, max_length=500)


@router.get('/policy')
async def get_policy(user=Depends(get_admin_user)):
    return (await security_policy()).model_dump()


@router.post('/policy')
async def update_policy(form: SecurityPolicy, user=Depends(get_admin_user)):
    async with get_async_db() as db:
        await Config.upsert({'security.policy': form.model_dump()}, db=db)
        record_action(db, user.id, 'security.policy.updated', details=form.model_dump())
        await db.commit()
    return form.model_dump()


@router.get('/accounts/{identifier}')
async def inspect_account(identifier: str, user=Depends(get_admin_user)):
    target = await target_user(identifier)
    name, plan, _ = await entitlement(target)
    now = int(time.time())
    async with get_async_db() as db:
        auth = await db.get(Auth, target.id)
        override = await db.get(BillingAccount, target.id)
        lease = await db.get(LiveLease, target.id)
        usage = (
            await db.scalars(
                select(UsageBucket).where(
                    UsageBucket.user_id == target.id, UsageBucket.starts_at >= now // 86400 * 86400
                )
            )
        ).all()
        subscriptions = (
            await db.scalars(
                select(Subscription)
                .where(Subscription.user_id == target.id)
                .order_by(Subscription.created_at.desc())
                .limit(50)
            )
        ).all()
    return {
        'id': target.id,
        'name': target.name,
        'email': target.email,
        'role': target.role,
        'login_enabled': bool(auth and auth.active),
        'email_verified': bool(auth and auth.email_verified),
        'plan': name,
        'entitlements': plan.model_dump(),
        'override': override.override if override else '',
        'override_until': override.override_until if override else 0,
        'active_call': bool(lease and lease.expires_at > now),
        'usage': [
            {'metric': row.metric, 'used': row.used, 'resets_at': row.starts_at + row.window}
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


@router.post('/accounts/{identifier}/actions')
async def account_action(identifier: str, form: AccountAction, user=Depends(get_admin_user)):
    target = await target_user(identifier)
    if target.role == 'admin' and form.action not in {'stop_call', 'reset_usage'}:
        raise HTTPException(400, 'Administrator login and sessions are protected from these account controls.')
    async with get_async_db() as db:
        if form.action == 'reset_usage':
            await db.execute(delete(UsageBucket).where(UsageBucket.user_id == target.id))
        elif form.action == 'stop_call':
            await db.execute(delete(LiveLease).where(LiveLease.user_id == target.id))
        else:
            auth = await db.get(Auth, target.id)
            if not auth:
                raise HTTPException(404, 'Authentication record not found.')
            if form.action != 'enable_login':
                await Auths.revoke_sessions_by_user_id(target.id, db=db)
                await db.execute(delete(OAuthSession).where(OAuthSession.user_id == target.id))
                await db.execute(delete(LiveLease).where(LiveLease.user_id == target.id))
            if form.action in {'disable_login', 'enable_login'}:
                auth.active = form.action == 'enable_login'
        record_action(db, user.id, 'account.' + form.action, target.id, {'reason': form.reason})
        await db.commit()
    if form.action in {'revoke_sessions', 'disable_login'}:
        from answerai.socket.main import disconnect_user_sessions

        await disconnect_user_sessions(target.id)
    return {'message': 'Account control applied.', 'account': await inspect_account(target.id, user)}


@router.post('/subscriptions/{subscription_id}/reconcile')
async def reconcile_subscription(subscription_id: str, user=Depends(get_admin_user)):
    async with get_async_db() as db:
        subscription = await db.get(Subscription, subscription_id)
    if not subscription or not subscription.provider_id:
        raise HTTPException(
            409,
            'No verified provider subscription ID is available. '
            'Reconcile an ambiguous checkout in the merchant dashboard first.',
        )
    await reconcile(subscription.provider, subscription.provider_id)
    async with get_async_db() as db:
        record_action(
            db,
            user.id,
            'subscription.reconciled',
            subscription.user_id,
            {'subscription_id': subscription.id, 'provider': subscription.provider},
        )
        await db.commit()
    return await inspect_account(subscription.user_id, user)


@router.get('/actions')
async def actions(limit: int = Query(default=50, ge=1, le=200), user=Depends(get_admin_user)):
    async with get_async_db() as db:
        rows = (
            await db.scalars(
                select(AdminAction).order_by(AdminAction.created_at.desc(), AdminAction.id.desc()).limit(limit)
            )
        ).all()
    return [
        {
            'id': row.id,
            'actor_id': row.actor_id,
            'target_id': row.target_id,
            'action': row.action,
            'details': row.details,
            'created_at': row.created_at,
        }
        for row in rows
    ]


@router.get('/overview')
async def overview(user=Depends(get_admin_user)):
    now = int(time.time())
    async with get_async_db() as db:
        active_calls = await db.scalar(select(func.count()).select_from(LiveLease).where(LiveLease.expires_at > now))
        active_subscriptions = await db.scalar(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.status == 'active', Subscription.period_end > now)
        )
        webhook_events = await db.scalar(select(func.count()).select_from(BillingEvent))
    return {
        'active_calls': active_calls,
        'active_subscriptions': active_subscriptions,
        'verified_webhook_events': webhook_events,
    }
