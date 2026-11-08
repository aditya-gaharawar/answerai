"""Real database leases, restart safety, idempotency and owner isolation."""

import asyncio
import time
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import select

from answerai.internal.db import get_async_db
from answerai.models.agent_runs import AgentRun
from answerai.models.auths import Auths
from answerai.models.chats import Chats
from answerai.models.messages import Message  # noqa: F401
from answerai.routers import agent_runs
from answerai.utils.agent_runs import claim_run, checkpoint, execute_run
from answerai.utils.auth import get_current_user

pytest_plugins = ['test_email_verification']


async def owner(email='run@example.com'):
    return await Auths.insert_new_auth(email, 'test-only-hash', 'Research user', role='user')


async def enqueue(client, key=None):
    return await client.post(
        '/api/v1/agent-runs/',
        json={
            'objective': 'Find evidence about project milestones',
            'model_id': 'allowed',
            'request_key': key or str(uuid4()),
            'web_search': False,
        },
    )


@pytest.mark.asyncio
async def test_run_idempotency_and_owner_isolation(harness):
    client, _, _, app, _ = harness
    app.include_router(agent_runs.router, prefix='/api/v1/agent-runs')
    first = await owner()
    app.dependency_overrides[get_current_user] = lambda: first
    initial = await enqueue(client, 'same-key')
    assert initial.status_code == 200, initial.text
    repeated = await enqueue(client, 'same-key')
    assert repeated.json()['id'] == initial.json()['id']
    assert len((await client.get('/api/v1/agent-runs/')).json()) == 1
    other = await owner('other@example.com')
    app.dependency_overrides[get_current_user] = lambda: other
    assert (await client.get('/api/v1/agent-runs/')).json() == []
    denied = await client.post(f'/api/v1/agent-runs/{initial.json()["id"]}/cancel', json={})
    assert denied.status_code == 409


@pytest.mark.asyncio
async def test_single_claim_and_fenced_completion(harness):
    client, _, _, app, user = harness
    app.include_router(agent_runs.router, prefix='/api/v1/agent-runs')
    app.dependency_overrides[get_current_user] = lambda: user
    response = await enqueue(client)
    assert response.status_code == 200
    claims = await asyncio.gather(*(claim_run() for _ in range(8)))
    winners = [entry for entry in claims if entry]
    assert len(winners) == 1
    run_id, lease = winners[0]
    assert not await checkpoint(run_id, 'wrong-lease', 'completed', {})
    assert await checkpoint(run_id, lease, 'needs_review', {'phase': 'verify'})
    assert not await checkpoint(run_id, lease, 'completed', {})


@pytest.mark.asyncio
async def test_worker_crash_blocks_instead_of_replaying(harness):
    client, _, _, app, user = harness
    app.include_router(agent_runs.router, prefix='/api/v1/agent-runs')
    app.dependency_overrides[get_current_user] = lambda: user
    response = await enqueue(client)
    run_id, lease = await claim_run()
    async with get_async_db() as db:
        row = await db.get(AgentRun, run_id)
        row.lease_until = int(time.time()) - 1
        await db.commit()
    assert await claim_run() is None
    async with get_async_db() as db:
        row = await db.get(AgentRun, run_id)
        assert row.status == 'blocked'
    assert not await checkpoint(run_id, lease, 'completed', {})


@pytest.mark.asyncio
async def test_worker_invokes_real_chat_pipeline_contract_and_requires_verification(harness):
    client, _, _, app, user = harness
    app.include_router(agent_runs.router, prefix='/api/v1/agent-runs')
    app.dependency_overrides[get_current_user] = lambda: user
    await enqueue(client)
    run_id, lease = await claim_run()
    calls = []

    async def completion(request, payload, user):
        calls.append(payload)
        assert request.state.internal is True
        assert request.state.agent_read_only is True
        assert payload['params']['tool_approval_mode'] == 'full'
        await Chats.upsert_message_to_chat_by_id_and_message_id(
            payload['chat_id'],
            payload['id'],
            {'done': True, 'content': 'Evidence summary'},
        )

    app.state.CHAT_COMPLETION_HANDLER = completion
    await execute_run(app, run_id, lease)
    assert len(calls) == 1
    row = (await client.get('/api/v1/agent-runs/')).json()[0]
    assert row['status'] == 'needs_review'
    assert (await client.post(f'/api/v1/agent-runs/{run_id}/verify', json={})).status_code == 200
    assert (await client.get('/api/v1/agent-runs/')).json()[0]['status'] == 'completed'


@pytest.mark.asyncio
async def test_read_only_background_cannot_invoke_actions_even_with_full_approval():
    from test_agent_search_reliability import extract
    import json
    from unittest.mock import AsyncMock

    namespace = {'JSONCodec': SimpleNamespace(dumps=json.dumps)}
    execute = extract('utils/middleware.py', ['execute_tool_call'], namespace)['execute_tool_call']
    write = AsyncMock()
    metadata = {
        '_agent_read_only': True,
        'params': {'tool_approval_mode': 'full'},
        'tools': {'write_note': {'type': 'builtin', 'callable': write, 'spec': {}}},
    }
    result = await execute({}, metadata, None, {'name': 'write_note', 'arguments': {}})
    assert 'read-only' in result[1]['error']
    write.assert_not_awaited()


def test_strict_contracts_do_not_fetch_schemas_or_echo_sensitive_values():
    from answerai.utils.tool_contracts import validate_contract

    schema = {'type': 'object', 'required': ['count'], 'properties': {'count': {'type': 'integer', 'minimum': 1}}}
    assert validate_contract({'count': 1}, schema) is None
    assert 'type' in validate_contract({'count': 'secret-value'}, schema)
    assert 'secret-value' not in validate_contract({'count': 'secret-value'}, schema)
    assert validate_contract({}, {'$ref': 'http://127.0.0.1/secret'})


@pytest.mark.asyncio
async def test_pause_resume_is_bounded_and_queued_state_survives_refresh(harness):
    client, _, _, app, user = harness
    app.include_router(agent_runs.router, prefix='/api/v1/agent-runs')
    app.dependency_overrides[get_current_user] = lambda: user
    response = await enqueue(client)
    run_id = response.json()['id']
    for _ in range(3):
        assert (await client.post(f'/api/v1/agent-runs/{run_id}/pause', json={})).json()['status'] == 'paused'
        assert (await client.get('/api/v1/agent-runs/')).json()[0]['status'] == 'paused'
        assert (await client.post(f'/api/v1/agent-runs/{run_id}/resume', json={})).json()['status'] == 'queued'
    await client.post(f'/api/v1/agent-runs/{run_id}/pause', json={})
    assert (await client.post(f'/api/v1/agent-runs/{run_id}/resume', json={})).status_code == 409


@pytest.mark.asyncio
async def test_run_credit_budget_is_atomic_and_survives_worker_recovery(harness):
    from answerai.utils.agent_runs import reserve_run_credits
    from fastapi import HTTPException

    client, _, _, app, user = harness
    app.include_router(agent_runs.router, prefix='/api/v1/agent-runs')
    app.dependency_overrides[get_current_user] = lambda: user
    await enqueue(client)
    run_id, lease = await claim_run()
    async with get_async_db() as db:
        row = await db.get(AgentRun, run_id)
        row.token_budget = 6148
        await db.commit()

    async def attempt():
        request = SimpleNamespace(state=SimpleNamespace(agent_run_id=run_id, agent_run_lease=lease))
        try:
            await reserve_run_credits(request, {})
            return True
        except HTTPException as error:
            assert error.status_code == 429
            return False

    assert sum(await asyncio.gather(*(attempt() for _ in range(8)))) == 2
    async with get_async_db() as db:
        row = await db.get(AgentRun, run_id)
        assert row.tokens_used == 6148


@pytest.mark.asyncio
async def test_execution_events_have_monotonic_order_and_reject_stale_worker(harness):
    from answerai.utils.agent_runs import record_run_event

    client, _, _, app, user = harness
    app.include_router(agent_runs.router, prefix='/api/v1/agent-runs')
    app.dependency_overrides[get_current_user] = lambda: user
    await enqueue(client)
    run_id, lease = await claim_run()
    assert not await record_run_event(run_id, 'stale', 'tool.started')
    assert await record_run_event(run_id, lease, 'tool.started', tool='search_web')
    assert await record_run_event(run_id, lease, 'tool.completed', tool='search_web')
    events = (await client.get('/api/v1/agent-runs/')).json()[0]['timeline']
    assert [item['sequence'] for item in events] == [1, 2, 3]
    assert events[-1]['type'] == 'tool.completed'


@pytest.mark.asyncio
async def test_research_cache_singleflight_is_scoped_and_bounded():
    from answerai.utils.research_cache import SearchCache

    cache = SearchCache(capacity=2, ttl=60)
    calls = []

    async def load():
        calls.append(1)
        await asyncio.sleep(0)
        return ['source']

    assert await asyncio.gather(*(cache.get(('user-a', 'query'), load) for _ in range(8))) == [['source']] * 8
    assert len(calls) == 1
    await cache.get(('user-b', 'query'), load)
    assert len(calls) == 2
    await cache.get(('user-c', 'query'), load)
    assert len(cache.values) == 2
    assert ('user-a', 'query') not in cache.values


@pytest.mark.asyncio
async def test_per_owner_leases_allow_other_users_to_progress(harness):
    client, _, _, app, user = harness
    app.include_router(agent_runs.router, prefix='/api/v1/agent-runs')
    app.dependency_overrides[get_current_user] = lambda: user
    first = (await enqueue(client)).json()
    await enqueue(client)
    second_user = await owner()
    app.dependency_overrides[get_current_user] = lambda: second_user
    other = (await enqueue(client)).json()
    a = await claim_run()
    b = await claim_run()
    assert {a[0], b[0]} == {first['id'], other['id']}
    assert await claim_run() is None


def test_agent_reads_bypass_approval_but_actions_and_connectors_do_not():
    from answerai.utils.agent_execution import requires_tool_approval

    metadata = {
        'params': {'agent_mode': 'agent'},
        'tools': {
            'search_web': {'type': 'builtin'},
            'send_email': {'type': 'mcp'},
            'fetch_url': {'type': 'mcp'},
        },
    }
    assert not requires_tool_approval({'function': {'name': 'search_web'}}, metadata)
    assert requires_tool_approval({'name': 'send_email'}, metadata)
    assert requires_tool_approval({'name': 'fetch_url'}, metadata)
    assert requires_tool_approval({'name': 'unknown'}, metadata)
    metadata['tools']['search_web']['direct'] = True
    assert requires_tool_approval({'name': 'search_web'}, metadata)
    metadata['tools']['search_web'].pop('direct')
    metadata['params']['agent_mode'] = 'auto'
    assert requires_tool_approval({'name': 'search_web'}, metadata)


@pytest.mark.asyncio
async def test_idempotency_rejects_changed_budget_or_capabilities(harness):
    client, _, _, app, user = harness
    app.include_router(agent_runs.router, prefix='/api/v1/agent-runs')
    app.dependency_overrides[get_current_user] = lambda: user
    assert (await enqueue(client, 'budget-key')).status_code == 200
    response = await client.post(
        '/api/v1/agent-runs/',
        json={
            'objective': 'Find evidence about project milestones',
            'model_id': 'allowed',
            'request_key': 'budget-key',
            'web_search': False,
            'token_budget': 32000,
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_failed_worker_cleanup_does_not_poison_dispatch(monkeypatch):
    import answerai.utils.agent_runs as runtime

    processed = asyncio.Event()
    attempts = 0
    dispatched = 0

    async def claim():
        nonlocal attempts
        attempts += 1
        return ('1', 'lease') if attempts == 1 else ('2', 'lease') if attempts == 3 else None

    async def execute(app, run_id, lease):
        nonlocal dispatched
        dispatched += 1
        if run_id == '1':
            raise RuntimeError('Simulated database failure during cleanup')
        processed.set()

    monkeypatch.setattr(runtime, 'claim_run', claim)
    monkeypatch.setattr(runtime, 'run_claimed', execute)
    worker = asyncio.create_task(runtime.worker_loop(None))
    try:
        await asyncio.wait_for(processed.wait(), timeout=3)
        assert dispatched == 2
        assert not worker.done()
    finally:
        worker.cancel()
        await asyncio.gather(worker, return_exceptions=True)


@pytest.mark.asyncio
async def test_parallel_tool_events_are_not_lost_on_sqlite(harness):
    from answerai.utils.agent_runs import record_run_event

    client, _, _, app, user = harness
    app.include_router(agent_runs.router, prefix='/api/v1/agent-runs')
    app.dependency_overrides[get_current_user] = lambda: user
    await enqueue(client)
    run_id, lease = await claim_run()
    results = await asyncio.gather(
        *(record_run_event(run_id, lease, 'tool.started', call_id=str(index)) for index in range(12))
    )
    assert all(results)
    events = (await client.get('/api/v1/agent-runs/')).json()[0]['timeline']
    assert [event['sequence'] for event in events] == list(range(1, 14))
    assert {event['call_id'] for event in events[1:]} == {str(index) for index in range(12)}


def test_durable_delegation_requires_read_role_and_joined_execution():
    from answerai.utils.agent_roles import read_only_delegation

    assert read_only_delegation('delegate_task', {'role': 'verifier'})
    assert not read_only_delegation('delegate_task', {'role': 'coder'})
    assert not read_only_delegation('delegate_task', {'role': 'researcher', 'background': True})
    assert not read_only_delegation('delegate_task', {})
    assert not read_only_delegation('send_email', {'role': 'researcher'})


def test_specialist_actions_keep_approvals_and_incomplete_work_is_not_success():
    from answerai.utils.agent_roles import specialist_params, specialist_completion_state

    assert specialist_params({'temperature': 0}, 'coder', {}) == {
        'temperature': 0,
        'agent_mode': 'agent',
        'tool_approval_mode': 'ask',
    }
    assert specialist_params({}, 'general', {'agent_mode': 'agent'})['tool_approval_mode'] == 'ask'
    assert specialist_params({}, 'researcher', {})['tool_approval_mode'] == 'full'
    pending = {
        'done': True,
        'output': [
            {'type': 'function_call', 'id': 'mail', 'name': 'send_email', 'status': 'pending'},
        ],
    }
    assert specialist_completion_state(pending)[0] == 'approval_required'
    assert specialist_completion_state({'done': False})[0] == 'blocked'
    assert specialist_completion_state({'done': True}) == ('completed', None)


@pytest.mark.asyncio
async def test_sse_replays_ordered_events_and_denies_other_owner(harness):
    client, _, _, app, user = harness
    app.include_router(agent_runs.router, prefix='/api/v1/agent-runs')
    app.dependency_overrides[get_current_user] = lambda: user
    await enqueue(client)
    run_id, lease = await claim_run()
    await checkpoint(run_id, lease, 'needs_review', {'phase': 'verification_required'})
    response = await client.get(f'/api/v1/agent-runs/{run_id}/events?after=1')
    assert response.status_code == 200
    assert 'event: activity' in response.text and 'id: 2' in response.text
    assert 'id: 1\n' not in response.text
    assert 'event: state' in response.text and 'needs_review' in response.text
    other = await owner('sse-other@example.com')
    app.dependency_overrides[get_current_user] = lambda: other
    assert (await client.get(f'/api/v1/agent-runs/{run_id}/events')).status_code == 404
