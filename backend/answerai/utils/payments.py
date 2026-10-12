"""Hosted recurring checkout. Access derives from provider-verified billing state."""

import hashlib
import hmac
import json
import os
import time
from uuid import uuid4

import httpx
from answerai.internal.db import get_async_db
from answerai.models.billing import BillingAccount, BillingEvent, Subscription
from answerai.utils.plans import entitlement, settings
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError


async def api(provider, method, path, data=None, idempotency=None):
    if provider == 'stripe':
        key = os.getenv('STRIPE_SECRET_KEY', '')
        base = 'https://api.stripe.com/v1/'
        auth = (key, '')
    else:
        key = os.getenv('RAZORPAY_KEY_ID', '')
        secret = os.getenv('RAZORPAY_KEY_SECRET', '')
        base = 'https://api.razorpay.com/v1/'
        auth = (key, secret)
        if not secret:
            raise HTTPException(503, 'Payment credentials are not configured.')
    if not key:
        raise HTTPException(503, 'Payment credentials are not configured.')
    headers = {'Stripe-Version': '2024-06-20'} if provider == 'stripe' else {}
    if provider == 'stripe' and idempotency:
        headers['Idempotency-Key'] = idempotency
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.request(
                method,
                base + path,
                auth=auth,
                headers=headers,
                **({'data': data} if provider == 'stripe' else {'json': data}),
            )
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(
            503, 'Payment provider is unavailable or configuration is invalid. Please try again later.'
        ) from None


def configured(provider, config):
    return config.enabled and (
        config.stripe_enabled
        and bool(config.stripe_price_id)
        and bool(os.getenv('STRIPE_SECRET_KEY'))
        and bool(os.getenv('STRIPE_WEBHOOK_SECRET'))
        if provider == 'stripe'
        else config.razorpay_enabled
        and bool(config.razorpay_plan_id)
        and all(os.getenv(key) for key in ('RAZORPAY_KEY_ID', 'RAZORPAY_KEY_SECRET', 'RAZORPAY_WEBHOOK_SECRET'))
    )


async def catalogue(config):
    result = []
    for provider in ('stripe', 'razorpay'):
        if not configured(provider, config):
            continue
        try:
            if provider == 'stripe':
                price = await api(provider, 'GET', 'prices/' + config.stripe_price_id)
                if (
                    not price.get('active')
                    or price.get('type') != 'recurring'
                    or price.get('billing_scheme') != 'per_unit'
                    or price.get('unit_amount') is None
                ):
                    continue
                recurring = price['recurring']
                result.append(
                    {
                        'provider': provider,
                        'amount': price['unit_amount'],
                        'currency': price['currency'],
                        'interval': recurring['interval'],
                        'interval_count': recurring['interval_count'],
                    }
                )
            else:
                plan = await api(provider, 'GET', 'plans/' + config.razorpay_plan_id)
                result.append(
                    {
                        'provider': provider,
                        'amount': plan['item']['amount'],
                        'currency': plan['item']['currency'],
                        'interval': plan['period'],
                        'interval_count': plan['interval'],
                    }
                )
        except HTTPException:
            continue
    return result


async def checkout_lock(user_id):
    for attempt in range(3):
        try:
            async with get_async_db() as db:
                account = await db.get(BillingAccount, user_id)
                if account is None:
                    db.add(BillingAccount(user_id=user_id, override='', override_until=0, checkout_until=0))
                    await db.flush()
                now = int(time.time())
                changed = await db.execute(
                    update(BillingAccount)
                    .where(BillingAccount.user_id == user_id, BillingAccount.checkout_until <= now)
                    .values(checkout_until=now + 60)
                )
                if not changed.rowcount:
                    raise HTTPException(409, 'Checkout is already being prepared. Try again in a minute.')
                await db.commit()
            return
        except IntegrityError:
            if attempt == 2:
                raise HTTPException(409, 'Checkout is busy. Try again.') from None


async def start_checkout(user, provider):
    config = await settings()
    if not configured(provider, config):
        raise HTTPException(503, 'This payment method is not configured.')
    name, _, _ = await entitlement(user, config)
    if name in {'blocked', 'admin', 'plus'}:
        raise HTTPException(409, 'Your account cannot start another paid subscription.')
    await checkout_lock(user.id)
    now = int(time.time())
    async with get_async_db() as db:
        # Do not create a second mandate while an existing one can still collect payment.
        existing = await db.scalar(
            select(Subscription)
            .where(
                Subscription.user_id == user.id,
                Subscription.status.not_in(['canceled', 'cancelled', 'expired', 'completed']),
            )
            .limit(1)
        )
        if existing:
            raise HTTPException(
                409, 'You already have a subscription or pending checkout. Use the billing page to manage it.'
            )
        local_id = str(uuid4())
        db.add(
            Subscription(
                id=local_id,
                user_id=user.id,
                provider=provider,
                status='pending',
                period_end=0,
                cancel_at_period_end=False,
                created_at=now,
                reconciled_at=0,
            )
        )
        await db.commit()
    try:
        if provider == 'stripe':
            session = await api(
                provider,
                'POST',
                'checkout/sessions',
                {
                    'mode': 'subscription',
                    'customer_email': user.email,
                    'line_items[0][price]': config.stripe_price_id,
                    'line_items[0][quantity]': '1',
                    'success_url': config.public_url + '/billing?checkout=returned',
                    'cancel_url': config.public_url + '/billing?checkout=cancelled',
                    'client_reference_id': local_id,
                    'metadata[billing_id]': local_id,
                    'subscription_data[metadata][billing_id]': local_id,
                    'expires_at': str(now + 86400),
                },
                idempotency=local_id,
            )
            values = {'checkout_id': session['id']}
            result = {'provider': provider, 'url': session['url']}
        else:
            subscription = await api(
                provider,
                'POST',
                'subscriptions',
                {
                    'plan_id': config.razorpay_plan_id,
                    'total_count': 120,
                    'quantity': 1,
                    'customer_notify': 1,
                    'expire_by': now + 86400,
                    'notes': {'billing_id': local_id},
                },
            )
            values = {'provider_id': subscription['id']}
            result = {
                'provider': provider,
                'subscription_id': subscription['id'],
                'key_id': os.environ['RAZORPAY_KEY_ID'],
                'email': user.email,
                'name': user.name,
            }
        async with get_async_db() as db:
            await db.execute(update(Subscription).where(Subscription.id == local_id).values(**values))
            await db.commit()
        return result
    except Exception:
        # Ambiguous network failures retain pending state to prevent a second charge.
        raise


def verify_signature(provider, body, signature, now=None):
    if provider == 'stripe':
        secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
        parts = {}
        for value in signature.split(','):
            key, _, item = value.partition('=')
            parts.setdefault(key, []).append(item)
        try:
            stamp = int(parts['t'][0])
        except (KeyError, ValueError):
            raise HTTPException(400, 'Invalid payment signature.') from None
        if abs((int(time.time()) if now is None else now) - stamp) > 300:
            raise HTTPException(400, 'Payment signature expired.')
        expected = hmac.new(secret.encode(), str(stamp).encode() + b'.' + body, hashlib.sha256).hexdigest()
        valid = any(hmac.compare_digest(expected, item) for item in parts.get('v1', []))
    else:
        secret = os.getenv('RAZORPAY_WEBHOOK_SECRET', '')
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        valid = hmac.compare_digest(expected, signature)
    if not secret or not valid:
        raise HTTPException(400, 'Invalid payment signature.')


async def reconcile(provider, provider_id, payment=None):  # noqa: C901 - provider-specific payment checks
    """Fetch current provider state; never grant from browser callbacks or event metadata."""
    observed = time.time_ns() // 1000
    config = await settings()
    remote = await api(provider, 'GET', 'subscriptions/' + provider_id)
    async with get_async_db() as db:
        local = await db.scalar(
            select(Subscription).where(Subscription.provider == provider, Subscription.provider_id == provider_id)
        )
        if local is None:
            local_id = ((remote.get('metadata') if provider == 'stripe' else remote.get('notes')) or {}).get(
                'billing_id'
            )
            local = await db.get(Subscription, local_id) if local_id else None
        if not local or local.provider != provider or (local.provider_id and local.provider_id != provider_id):
            return
        local_id = local.id
        old_end = local.period_end
    paid = False
    period_end = old_end
    if provider == 'stripe':
        items = remote.get('items', {}).get('data', [])
        if (
            len(items) != 1
            or items[0].get('price', {}).get('id') != config.stripe_price_id
            or items[0].get('quantity') != 1
        ):
            raise HTTPException(400, 'Subscription does not match the configured plan.')
        invoice_id = remote.get('latest_invoice')
        if invoice_id:
            invoice = await api(
                provider, 'GET', 'invoices/' + (invoice_id if isinstance(invoice_id, str) else invoice_id['id'])
            )
            paid = invoice.get('status') == 'paid' and invoice.get('paid', True)
            if paid and invoice.get('charge'):
                charge = await api(provider, 'GET', 'charges/' + invoice['charge'])
                paid = not charge.get('refunded', False) and charge.get('paid', False)
            if paid:
                period_end = int(
                    items[0].get('current_period_end')
                    or remote.get('current_period_end')
                    or max(
                        (line.get('period', {}).get('end', 0) for line in invoice.get('lines', {}).get('data', [])),
                        default=0,
                    )
                )
        status = (
            'active'
            if remote.get('status') == 'active' and paid
            else (
                'pending'
                if remote.get('status') in {'incomplete', 'trialing'}
                else ('inactive' if remote.get('status') == 'active' else remote.get('status', 'inactive'))
            )
        )
        cancel = bool(remote.get('cancel_at_period_end'))
    else:
        if remote.get('plan_id') != config.razorpay_plan_id or remote.get('quantity', 1) != 1:
            raise HTTPException(400, 'Subscription does not match the configured plan.')
        # Reconcile the latest paid period rather than trusting a possibly old charge event.
        invoices = await api(provider, 'GET', 'invoices?subscription_id=' + provider_id + '&count=100')
        candidates = [
            invoice
            for invoice in invoices.get('items', [])
            if invoice.get('subscription_id') == provider_id
            and invoice.get('status') == 'paid'
            and invoice.get('payment_id')
            and invoice.get('billing_end')
        ]
        invoice = max(candidates, key=lambda item: int(item['billing_end']), default=None)
        if invoice:
            verified = await api(provider, 'GET', 'payments/' + invoice['payment_id'])
            paid = (
                verified.get('status') == 'captured'
                and verified.get('refund_status') != 'full'
                and verified.get('invoice_id') == invoice['id']
                and verified.get('amount') == invoice.get('amount')
                and verified.get('currency') == invoice.get('currency')
            )
            if paid:
                period_end = min(int(invoice['billing_end']), int(remote.get('current_end') or 0))
        if not paid:
            period_end = 0
        status = (
            'active'
            if remote.get('status') == 'active' and period_end > int(time.time())
            else (
                'pending'
                if remote.get('status') in {'created', 'authenticated'}
                else ('inactive' if remote.get('status') == 'active' else remote.get('status', 'inactive'))
            )
        )
        cancel = bool(remote.get('has_scheduled_changes') and remote.get('change_scheduled_at'))
    async with get_async_db() as db:
        await db.execute(
            update(Subscription)
            .where(Subscription.id == local_id, Subscription.reconciled_at <= observed)
            .values(
                provider_id=provider_id,
                status=status,
                period_end=period_end,
                cancel_at_period_end=cancel,
                reconciled_at=observed,
            )
        )
        await db.commit()


async def process_webhook(provider, body, signature, event_id=''):  # noqa: C901 - provider/route dispatch
    verify_signature(provider, body, signature)
    try:
        event = json.loads(body)
    except ValueError:
        raise HTTPException(400, 'Invalid webhook body.') from None
    if not isinstance(event, dict):
        raise HTTPException(400, 'Invalid webhook body.')
    # Razorpay signs only the body, not its event-ID header. Bind deduplication to signed bytes.
    identifier = event.get('id') if provider == 'stripe' else hashlib.sha256(body).hexdigest()
    if not identifier or not isinstance(identifier, str) or len(identifier) > 200:
        raise HTTPException(400, 'Missing webhook event identifier.')
    dedup = f'{provider}:{identifier}'
    async with get_async_db() as db:
        if await db.get(BillingEvent, dedup):
            return
    if provider == 'stripe':
        kind = event.get('type', '')
        obj = event.get('data', {}).get('object', {})
        sub_id = None
        if kind.startswith('customer.subscription.'):
            sub_id = obj.get('id')
        elif kind.startswith('invoice.'):
            sub_id = obj.get('subscription') or obj.get('parent', {}).get('subscription_details', {}).get(
                'subscription'
            )
        elif kind == 'checkout.session.completed':
            sub_id = obj.get('subscription')
        elif kind == 'checkout.session.expired' and obj.get('id'):
            current = await api(provider, 'GET', 'checkout/sessions/' + obj['id'])
            if current.get('status') == 'expired':
                async with get_async_db() as db:
                    await db.execute(
                        update(Subscription)
                        .where(
                            Subscription.provider == provider,
                            Subscription.checkout_id == obj['id'],
                            Subscription.status == 'pending',
                        )
                        .values(status='expired')
                    )
                    await db.commit()
        elif kind == 'charge.refunded' and obj.get('invoice'):
            invoice = await api(provider, 'GET', 'invoices/' + obj['invoice'])
            sub_id = invoice.get('subscription')
        if sub_id:
            await reconcile(provider, sub_id)
    else:
        payload = event.get('payload', {})
        subscription = payload.get('subscription', {}).get('entity', {})
        kind = event.get('event', '')
        if kind.startswith('subscription.') and subscription.get('id'):
            payment = payload.get('payment', {}).get('entity', {}).get('id') if kind == 'subscription.charged' else None
            await reconcile(provider, subscription['id'], payment)
        elif kind == 'refund.processed':
            payment_id = payload.get('refund', {}).get('entity', {}).get('payment_id')
            if payment_id:
                payment_state = await api(provider, 'GET', 'payments/' + payment_id)
                invoice_id = payment_state.get('invoice_id')
                if invoice_id:
                    invoice = await api(provider, 'GET', 'invoices/' + invoice_id)
                    if invoice.get('subscription_id'):
                        await reconcile(provider, invoice['subscription_id'])
    try:
        async with get_async_db() as db:
            db.add(BillingEvent(id=dedup, created_at=int(time.time())))
            await db.commit()
    except IntegrityError:
        pass


async def manage(user, subscription_id, action):  # noqa: C901 - provider/route dispatch
    async with get_async_db() as db:
        subscription = await db.get(Subscription, subscription_id)
        if not subscription or subscription.user_id != user.id:
            raise HTTPException(404, 'Subscription not found.')
        provider, remote_id, checkout_id = subscription.provider, subscription.provider_id, subscription.checkout_id
    config = await settings()
    if action == 'resume' and subscription.status == 'pending':
        if provider == 'stripe' and checkout_id:
            session = await api(provider, 'GET', 'checkout/sessions/' + checkout_id)
            if session.get('status') == 'open':
                return {'provider': provider, 'url': session['url']}
        if provider == 'razorpay' and remote_id:
            return {
                'provider': provider,
                'subscription_id': remote_id,
                'key_id': os.environ.get('RAZORPAY_KEY_ID', ''),
                'email': user.email,
                'name': user.name,
            }
        raise HTTPException(409, 'Checkout is no longer available. Wait for its expiry or contact support.')
    if action == 'abandon' and subscription.status == 'pending':
        if provider == 'stripe' and checkout_id:
            await api(provider, 'POST', 'checkout/sessions/' + checkout_id + '/expire')
        elif provider == 'razorpay' and remote_id:
            await api(provider, 'POST', 'subscriptions/' + remote_id + '/cancel', {'cancel_at_cycle_end': 0})
        else:
            raise HTTPException(409, 'Checkout state is uncertain. Contact support before starting another payment.')
        async with get_async_db() as db:
            await db.execute(
                update(Subscription)
                .where(Subscription.id == subscription_id, Subscription.status == 'pending')
                .values(status='canceled')
            )
            await db.commit()
        return {'message': 'Pending checkout cancelled.'}
    if not remote_id:
        raise HTTPException(409, 'Subscription has not been activated yet.')
    if provider == 'stripe' and action == 'portal':
        remote = await api(provider, 'GET', 'subscriptions/' + remote_id)
        portal = await api(
            provider,
            'POST',
            'billing_portal/sessions',
            {'customer': remote['customer'], 'return_url': config.public_url + '/billing'},
        )
        return {'url': portal['url']}
    if action == 'cancel':
        if provider == 'stripe':
            await api(provider, 'POST', 'subscriptions/' + remote_id, {'cancel_at_period_end': 'true'})
        else:
            await api(provider, 'POST', 'subscriptions/' + remote_id + '/cancel', {'cancel_at_cycle_end': 1})
        async with get_async_db() as db:
            await db.execute(
                update(Subscription).where(Subscription.id == subscription_id).values(cancel_at_period_end=True)
            )
            await db.commit()
        return {'message': 'Renewal cancelled. Access continues until the paid period ends.'}
    raise HTTPException(400, 'Unsupported subscription action.')
