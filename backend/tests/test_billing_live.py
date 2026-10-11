"""Billing authenticity, quota concurrency, entitlements, and live protocol tests."""

import asyncio
import base64
import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from answerai.internal.db import get_async_db
from answerai.models.auths import Auths
from answerai.models.billing import BillingAccount, BillingEvent, LiveLease, Subscription, UsageBucket
from answerai.models.config import Config
from answerai.routers import billing, live
from answerai.utils import payments, plans
from answerai.utils.auth import get_current_user, get_verified_user
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select

pytest_plugins = ['test_email_verification']


async def member():
    return await Auths.insert_new_auth('member@example.com', 'test-hash', 'Member', role='user')


async def enable(**overrides):
    values = plans.BillingSettings(enabled=True).model_dump()
    values.update(overrides)
    await Config.upsert({'billing.settings': values})
    return values


async def subscription(user, provider='stripe', status='pending', end=0):
    row = Subscription(
        id='local-sub',
        user_id=user.id,
        provider=provider,
        provider_id='sub_verified',
        status=status,
        period_end=end,
        created_at=int(time.time()),
        reconciled_at=0,
        cancel_at_period_end=False,
    )
    async with get_async_db() as db:
        db.add(row)
        await db.commit()
    return row


@pytest.mark.asyncio
async def test_limits_are_atomic_across_concurrent_workers(harness):
    await enable()
    user = await member()

    async def attempt():
        try:
            await plans.reserve(user.id, [('messages', 86400, 4, 1), ('requests', 60, 4, 1)], now=1700000000)
            return True
        except HTTPException as error:
            assert error.status_code == 429
            return False

    results = await asyncio.gather(*(attempt() for _ in range(20)))
    assert sum(results) == 4
    async with get_async_db() as db:
        rows = (await db.scalars(select(UsageBucket))).all()
        assert len(rows) == 2
        assert {row.used for row in rows} == {4}


@pytest.mark.asyncio
async def test_failed_multi_counter_reservation_rolls_back(harness):
    user = await member()
    with pytest.raises(HTTPException):
        await plans.reserve(user.id, [('messages', 86400, 100, 1), ('requests', 60, 0, 1)])
    async with get_async_db() as db:
        assert (await db.scalars(select(UsageBucket))).all() == []


@pytest.mark.asyncio
async def test_window_reset_and_zero_limit(harness):
    user = await member()
    await plans.reserve(user.id, [('requests', 60, 1, 1)], now=120)
    with pytest.raises(HTTPException) as limited:
        await plans.reserve(user.id, [('requests', 60, 1, 1)], now=121)
    assert limited.value.headers['Retry-After'] == '59'
    await plans.reserve(user.id, [('requests', 60, 1, 1)], now=180)
    with pytest.raises(HTTPException):
        await plans.reserve(user.id, [('live_minutes', 86400, 0, 1)])


@pytest.mark.asyncio
async def test_model_feature_restrictions_and_expiring_paid_access(harness):
    values = await enable()
    values['free']['models'] = ['free-model']
    await Config.upsert({'billing.settings': values})
    user = await member()
    await plans.require_model(user, 'free-model')
    with pytest.raises(HTTPException):
        await plans.require_model(user, 'premium-model')
    with pytest.raises(HTTPException):
        await plans.require_feature(user, 'live_calls')
    await subscription(user, status='active', end=int(time.time()) + 3600)
    assert (await plans.entitlement(user))[0] == 'plus'
    await plans.require_model(user, 'premium-model')
    await plans.require_feature(user, 'live_video')
    async with get_async_db() as db:
        row = await db.get(Subscription, 'local-sub')
        row.period_end = int(time.time()) - 1
        await db.commit()
    assert (await plans.entitlement(user))[0] == 'free'


@pytest.mark.asyncio
async def test_blocked_override_works_even_when_paywall_disabled(harness):
    user = await member()
    await Config.upsert({'billing.settings': {'enabled': False}})
    async with get_async_db() as db:
        db.add(BillingAccount(user_id=user.id, override='blocked', override_until=0))
        await db.commit()
    with pytest.raises(HTTPException):
        await plans.require_model(user, 'any')
    with pytest.raises(HTTPException):
        await plans.require_feature(user, 'uploads')
    assert (await plans.entitlement(harness[4]))[0] == 'admin'
    await plans.require_model(harness[4], 'any')


@pytest.mark.asyncio
async def test_http_enforcement_covers_direct_provider_and_feature_routes(harness):
    client, _, _, app, _ = harness
    user = await member()
    app.dependency_overrides[get_current_user] = lambda: user
    values = await enable()
    values['free']['messages_per_day'] = 1
    values['free']['models'] = ['allowed']
    await Config.upsert({'billing.settings': values})

    @app.post('/openai/chat/completions')
    async def generation(request: Request, body: dict, current=Depends(get_verified_user)):
        await plans.reserve_generation(request, current, body)
        return {'ok': True}

    @app.post('/api/v1/images/generations')
    async def image(current=Depends(get_verified_user)):
        return {'ok': True}

    assert (await client.post('/openai/chat/completions', json={'model': 'denied'})).status_code == 403
    assert (await client.post('/api/v1/images/generations', json={})).status_code == 403
    assert (await client.post('/openai/chat/completions', json={'model': 'allowed'})).status_code == 200
    result = await client.post('/openai/chat/completions', json={'model': 'allowed'})
    assert result.status_code == 429
    assert int(result.headers['Retry-After']) > 0
    async with get_async_db() as db:
        assert (await db.scalar(select(UsageBucket).where(UsageBucket.metric == 'messages'))).used == 1


@pytest.mark.asyncio
async def test_generation_feature_limits_and_disallowed_direct_connections(harness):
    user = await member()
    values = await enable()
    values['free']['features']['web_search'] = True
    values['free']['feature_limits']['web_search'] = 1
    await Config.upsert({'billing.settings': values})

    def req():
        return SimpleNamespace(state=SimpleNamespace())

    await plans.reserve_generation(req(), user, {'model': 'any', 'features': {'web_search': True}})
    with pytest.raises(HTTPException) as limited:
        await plans.reserve_generation(req(), user, {'model': 'any', 'features': {'web_search': True}})
    assert limited.value.status_code == 429
    with pytest.raises(HTTPException) as denied:
        await plans.reserve_generation(req(), user, {'model': 'any', 'model_item': {'direct': True}})
    assert denied.value.status_code == 403


def test_gateway_signatures_tampering_and_expiry(monkeypatch):
    monkeypatch.setenv('STRIPE_WEBHOOK_SECRET', 'test-secret')
    monkeypatch.setenv('RAZORPAY_WEBHOOK_SECRET', 'test-secret')
    body = b'{"id":"evt_test"}'
    stamp = int(time.time())
    signature = hmac.new(b'test-secret', str(stamp).encode() + b'.' + body, hashlib.sha256).hexdigest()
    payments.verify_signature('stripe', body, f't={stamp},v1=wrong,v1={signature}')
    with pytest.raises(HTTPException):
        payments.verify_signature('stripe', body + b' ', f't={stamp},v1={signature}')
    with pytest.raises(HTTPException):
        payments.verify_signature('stripe', body, f't={stamp},v1={signature}', now=stamp + 301)
    razor = hmac.new(b'test-secret', body, hashlib.sha256).hexdigest()
    payments.verify_signature('razorpay', body, razor)
    with pytest.raises(HTTPException):
        payments.verify_signature('razorpay', body, 'wrong')


@pytest.mark.asyncio
async def test_stripe_grants_only_paid_matching_subscription_and_revokes_cancel(harness, monkeypatch):
    user = await member()
    await enable(stripe_price_id='price_plus')
    await subscription(user)
    remote = {
        'id': 'sub_verified',
        'status': 'active',
        'items': {
            'data': [{'price': {'id': 'price_plus'}, 'quantity': 1, 'current_period_end': int(time.time()) + 3600}]
        },
        'latest_invoice': 'in_verified',
    }
    invoice = {'status': 'open', 'paid': False}

    async def provider_api(provider, method, path, **kwargs):
        return remote if path.startswith('subscriptions/') else invoice

    monkeypatch.setattr(payments, 'api', provider_api)
    await payments.reconcile('stripe', 'sub_verified')
    assert (await plans.entitlement(user))[0] == 'free'
    invoice.update(status='paid', paid=True)
    await payments.reconcile('stripe', 'sub_verified')
    assert (await plans.entitlement(user))[0] == 'plus'
    remote['status'] = 'canceled'
    await payments.reconcile('stripe', 'sub_verified')
    assert (await plans.entitlement(user))[0] == 'free'
    remote['items']['data'][0]['price']['id'] = 'price_unrelated'
    with pytest.raises(HTTPException):
        await payments.reconcile('stripe', 'sub_verified')


@pytest.mark.asyncio
async def test_razorpay_requires_captured_payment_bound_to_subscription(harness, monkeypatch):
    user = await member()
    await enable(razorpay_plan_id='plan_plus')
    await subscription(user, provider='razorpay')
    end = int(time.time()) + 3600
    invoice = {
        'id': 'inv_paid',
        'subscription_id': 'sub_verified',
        'status': 'paid',
        'payment_id': 'pay_verified',
        'billing_end': end,
        'amount': 10000,
        'currency': 'INR',
    }
    data = {
        'subscriptions/sub_verified': {'status': 'active', 'plan_id': 'plan_plus', 'current_end': end},
        'payments/pay_verified': {'status': 'captured', 'invoice_id': 'inv_paid', 'amount': 10000, 'currency': 'INR'},
        'invoices?subscription_id=sub_verified&count=100': {'items': []},
    }
    monkeypatch.setattr(payments, 'api', AsyncMock(side_effect=lambda provider, method, path: data[path]))
    await payments.reconcile('razorpay', 'sub_verified')
    assert (await plans.entitlement(user))[0] == 'free'
    data['invoices?subscription_id=sub_verified&count=100']['items'] = [invoice]
    await payments.reconcile('razorpay', 'sub_verified', 'pay_verified')
    assert (await plans.entitlement(user))[0] == 'plus'
    data['payments/pay_verified']['amount'] = 1
    await payments.reconcile('razorpay', 'sub_verified', 'pay_verified')
    assert (await plans.entitlement(user))[0] == 'free'
    data['payments/pay_verified']['amount'] = 10000
    data['payments/pay_verified']['refund_status'] = 'full'
    await payments.reconcile('razorpay', 'sub_verified')
    assert (await plans.entitlement(user))[0] == 'free'
    invoice['subscription_id'] = 'sub_someone_else'
    await payments.reconcile('razorpay', 'sub_verified')
    assert (await plans.entitlement(user))[0] == 'free'


@pytest.mark.asyncio
async def test_webhook_idempotency_and_browser_does_not_grant(harness, monkeypatch):
    await enable()
    user = await member()
    await subscription(user)
    monkeypatch.setenv('STRIPE_WEBHOOK_SECRET', 'test-secret')
    mocked = AsyncMock()
    monkeypatch.setattr(payments, 'reconcile', mocked)
    body = json.dumps(
        {'id': 'evt_once', 'type': 'checkout.session.completed', 'data': {'object': {'subscription': 'sub_verified'}}}
    ).encode()
    stamp = int(time.time())
    sig = hmac.new(b'test-secret', str(stamp).encode() + b'.' + body, hashlib.sha256).hexdigest()
    for _ in range(2):
        await payments.process_webhook('stripe', body, f't={stamp},v1={sig}')
    assert mocked.await_count == 1
    assert (await plans.entitlement(user))[0] == 'free'
    async with get_async_db() as db:
        assert await db.get(BillingEvent, 'stripe:evt_once')


@pytest.mark.asyncio
async def test_checkout_uses_server_price_and_prevents_duplicate_payment(harness, monkeypatch):
    user = await member()
    await enable(
        stripe_enabled=True, stripe_price_id='price_server', razorpay_enabled=True, razorpay_plan_id='plan_server'
    )
    for key in [
        'STRIPE_SECRET_KEY',
        'STRIPE_WEBHOOK_SECRET',
        'RAZORPAY_KEY_ID',
        'RAZORPAY_KEY_SECRET',
        'RAZORPAY_WEBHOOK_SECRET',
    ]:
        monkeypatch.setenv(key, 'test-secret')
    calls = []

    async def provider_api(provider, method, path, data=None, **kwargs):
        calls.append((provider, path, data))
        return {'id': 'cs_test', 'url': 'https://checkout.stripe.com/test'}

    monkeypatch.setattr(payments, 'api', provider_api)
    result = await payments.start_checkout(user, 'stripe')
    assert result['url'].startswith('https://checkout.stripe.com/')
    assert calls[0][2]['line_items[0][price]'] == 'price_server'
    with pytest.raises(HTTPException):
        await payments.start_checkout(user, 'razorpay')
    assert len(calls) == 1
    assert (await plans.entitlement(user))[0] == 'free'


@pytest.mark.asyncio
async def test_admin_only_settings_and_subscription_ownership(harness):
    client, _, _, app, admin = harness
    user = await member()
    app.include_router(billing.router, prefix='/api/v1/billing')
    app.include_router(live.router, prefix='/api/v1/live')
    app.dependency_overrides[get_current_user] = lambda: user
    from answerai.utils.auth import get_admin_user

    app.dependency_overrides.pop(get_admin_user)
    assert (await client.get('/api/v1/billing/config')).status_code == 401
    assert (await client.get('/api/v1/live/config')).status_code == 401
    await subscription(admin)
    assert (await client.post('/api/v1/billing/subscriptions/local-sub', json={'action': 'cancel'})).status_code == 404
    app.dependency_overrides[get_current_user] = lambda: admin
    result = await client.post('/api/v1/billing/users/' + user.id, json={'plan': 'plus'})
    assert result.json()['plan'] == 'plus'
    result = await client.get('/api/v1/billing/config')
    assert result.status_code == 200
    assert 'STRIPE_SECRET_KEY' in result.json()['credentials']
    assert result.json()['credentials']['STRIPE_SECRET_KEY'] in (True, False)


@pytest.mark.asyncio
async def test_call_lease_exclusivity_and_stale_cleanup(harness):
    user = await member()
    await plans.acquire_lease(user.id, 'first')
    with pytest.raises(HTTPException) as error:
        await plans.acquire_lease(user.id, 'second')
    assert error.value.status_code == 409
    await plans.release_lease(user.id, 'wrong')
    async with get_async_db() as db:
        row = await db.get(LiveLease, user.id)
        row.expires_at = 0
        await db.commit()
    await plans.acquire_lease(user.id, 'second')
    await plans.release_lease(user.id, 'first')
    async with get_async_db() as db:
        assert (await db.get(LiveLease, user.id)).session_id == 'second'
    await plans.release_lease(user.id, 'second')


def test_live_media_validation_and_provider_translation():
    pcm = base64.b64encode(b'\0\0' * 960).decode()
    jpeg = base64.b64encode(b'\xff\xd8\xff' + b'frame').decode()
    assert live.input_events('openai', {'type': 'audio', 'data': pcm})[0]['type'] == 'input_audio_buffer.append'
    assert (
        live.input_events('gemini', {'type': 'audio', 'data': pcm})[0]['realtimeInput']['audio']['mimeType']
        == 'audio/pcm;rate=16000'
    )
    assert (
        live.input_events('openai', {'type': 'video', 'data': jpeg})[0]['item']['content'][0]['type'] == 'input_image'
    )
    assert 'video' in live.input_events('gemini', {'type': 'video', 'data': jpeg})[0]['realtimeInput']
    for event in [
        {'type': 'audio', 'data': 'invalid!!'},
        {'type': 'video', 'data': pcm},
        {'type': 'session.update'},
        {'type': 'audio', 'data': base64.b64encode(b'x').decode()},
        {'type': 'audio', 'data': 'A' * 20000},
    ]:
        with pytest.raises(ValueError):
            live.input_events('openai', event)


def test_live_setup_has_no_tools_and_normalized_audio_transcripts():
    config = live.LiveSettings()
    openai = live.provider_setup(config, 'openai')
    gemini = live.provider_setup(config, 'gemini')
    assert openai['session']['audio']['input']['turn_detection']['create_response'] is True
    assert 'tools' not in openai['session']
    assert gemini['setup']['generationConfig']['responseModalities'] == ['AUDIO']
    assert 'tools' not in gemini['setup']
    assert live.output_events('openai', {'type': 'session.updated'}) == [{'type': 'ready', 'input_rate': 24000}]
    assert live.output_events('gemini', {'setupComplete': {}}) == [{'type': 'ready', 'input_rate': 16000}]
    events = live.output_events(
        'gemini',
        {
            'serverContent': {
                'modelTurn': {'parts': [{'inlineData': {'mimeType': 'audio/pcm;rate=24000', 'data': 'AAA='}}]},
                'inputTranscription': {'text': 'Hello'},
                'outputTranscription': {'text': 'Hi'},
                'turnComplete': True,
            }
        },
    )
    assert [event['type'] for event in events] == ['audio', 'transcript', 'transcript', 'turn_done']
    assert (
        live.output_events('openai', {'type': 'error', 'error': {'message': 'sk-do-not-expose-secret'}})[0][
            'message'
        ].find('sk-do-not-expose-secret')
        == -1
    )


@pytest.mark.asyncio
async def test_live_provider_access_and_config_secrets(harness, monkeypatch):
    user = await member()
    await enable()
    await Config.upsert({'live.settings': {'enabled': True}})
    monkeypatch.setenv('OPENAI_REALTIME_API_KEY', 'test-openai-secret')
    monkeypatch.setenv('GEMINI_LIVE_API_KEY', 'test-gemini-secret')
    options = await live.providers(user)
    assert len(options['providers']) == 2
    assert not options['allowed']
    assert all(not item['allowed'] for item in options['providers'])
    await subscription(user, status='active', end=int(time.time()) + 3600)
    assert (await live.providers(user))['allowed'] is True
    assert (await live.providers(user))['camera_allowed'] is True
    config = await live.get_config(harness[4])
    assert 'test-openai-secret' not in json.dumps(config)
    assert config['openai_key_configured'] is True


@pytest.mark.asyncio
async def test_live_websocket_authentication_and_provider_lifecycle(harness, monkeypatch):  # noqa: C901
    from aiohttp import WSMsgType
    from fastapi.testclient import TestClient

    _, _, _, app, admin = harness
    app.include_router(live.router, prefix='/api/v1/live')
    await Config.upsert({'live.settings': {'enabled': True}})
    monkeypatch.setenv('GEMINI_LIVE_API_KEY', 'test-server-key')
    monkeypatch.setattr(live, 'get_verified_user_by_token', AsyncMock(return_value=None))

    def invalid_call():
        with TestClient(app) as client:
            with client.websocket_connect('/api/v1/live/call') as socket:
                socket.send_json({'type': 'auth', 'token': 'invalid', 'provider': 'gemini'})
                result = socket.receive_json()
                assert result['type'] == 'error'
                assert 'Sign in' in result['message']

    await asyncio.to_thread(invalid_call)

    sent = []

    class Upstream:
        def __init__(self):
            self.pending = None

        async def __aenter__(self):
            self.pending = asyncio.Queue()
            return self

        async def __aexit__(self, *args):
            pass

        async def send_json(self, message):
            sent.append(message)
            if message.get('realtimeInput', {}).get('audio'):
                await self.pending.put(
                    SimpleNamespace(
                        type=WSMsgType.TEXT,
                        data=json.dumps(
                            {
                                'serverContent': {
                                    'inputTranscription': {'text': 'Backend heard audio'},
                                    'turnComplete': True,
                                }
                            }
                        ),
                    )
                )

        async def receive(self):
            return SimpleNamespace(type=WSMsgType.BINARY, data=b'{"setupComplete": {}}')

        def __aiter__(self):
            return self

        async def __anext__(self):
            return await self.pending.get()

    class ProviderSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def ws_connect(self, url, **kwargs):
            assert url == live.GEMINI_URL
            assert kwargs['headers'] == {'x-goog-api-key': 'test-server-key'}
            return Upstream()

    monkeypatch.setattr(live.aiohttp, 'ClientSession', lambda **kwargs: ProviderSession())
    monkeypatch.setattr(live, 'get_verified_user_by_token', AsyncMock(return_value=admin))

    def valid_call():
        with TestClient(app) as client:
            with client.websocket_connect('/api/v1/live/call') as socket:
                socket.send_json({'type': 'auth', 'token': 'test', 'provider': 'gemini'})
                ready = socket.receive_json()
                assert ready['type'] == 'ready' and ready['input_rate'] == 16000
                socket.send_json({'type': 'audio', 'data': base64.b64encode(b'\0\0' * 640).decode()})
                transcript = socket.receive_json()
                assert transcript['type'] == 'transcript' and transcript['text'] == 'Backend heard audio'
                assert socket.receive_json()['type'] == 'turn_done'
                socket.send_json({'type': 'end'})

    await asyncio.to_thread(valid_call)
    assert sent[0]['setup']['model'].startswith('models/')
    assert sent[1]['realtimeInput']['audio']['mimeType'] == 'audio/pcm;rate=16000'
    async with get_async_db() as db:
        assert await db.get(LiveLease, admin.id) is None


@pytest.mark.asyncio
async def test_current_stripe_invoice_refund_revokes_access(harness, monkeypatch):
    user = await member()
    await enable(stripe_price_id='price_plus')
    await subscription(user, status='active', end=int(time.time()) + 3600)
    data = {
        'subscriptions/sub_verified': {
            'id': 'sub_verified',
            'status': 'active',
            'items': {
                'data': [{'price': {'id': 'price_plus'}, 'quantity': 1, 'current_period_end': int(time.time()) + 3600}]
            },
            'latest_invoice': 'invoice_paid',
        },
        'invoices/invoice_paid': {'status': 'paid', 'paid': True, 'charge': 'ch_refunded'},
        'charges/ch_refunded': {'paid': True, 'refunded': True},
    }
    monkeypatch.setattr(payments, 'api', AsyncMock(side_effect=lambda provider, method, path: data[path]))
    await payments.reconcile('stripe', 'sub_verified')
    assert (await plans.entitlement(user))[0] == 'free'
