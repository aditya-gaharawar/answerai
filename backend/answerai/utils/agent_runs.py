"""Durable dispatch into the existing agent pipeline; uncertain actions are never replayed."""

import asyncio
import logging
import time
from contextlib import suppress
from datetime import timedelta
from uuid import uuid4

from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from answerai.internal.db import get_async_db
from answerai.models.agent_runs import AgentRun, AgentOwnerLease
from answerai.models.auths import Auths
from answerai.models.chats import ChatForm, Chats
from answerai.models.users import Users

log = logging.getLogger(__name__)
TERMINAL = {'completed', 'failed', 'cancelled', 'needs_review', 'blocked'}


def snapshot(row):
    return {
        key: getattr(row, key)
        for key in (
            'id',
            'prompt',
            'chat_id',
            'message_id',
            'model_id',
            'status',
            'checkpoint',
            'timeline',
            'token_budget',
            'tokens_used',
            'created_at',
            'updated_at',
            'deadline',
            'iterations',
            'resume_count',
        )
    }


async def _claim_run():
    now = int(time.time())
    async with get_async_db() as db:
        await db.execute(
            update(AgentRun)
            .where(AgentRun.status == 'queued', AgentRun.deadline <= now)
            .values(
                status='failed',
                checkpoint={'phase': 'expired', 'message': 'Queue deadline expired.'},
                updated_at=now,
            )
        )
        # An expired lease might have performed an external action. Block instead of replaying it.
        await db.execute(
            update(AgentRun)
            .where(
                AgentRun.status.in_(['running', 'pausing']),
                AgentRun.lease_until < now,
            )
            .values(
                status='blocked',
                lease=None,
                checkpoint={
                    'phase': 'interrupted',
                    'message': 'Worker lease expired. Inspect the conversation before starting new work.',
                },
                updated_at=now,
            )
        )
        run_id = await db.scalar(
            select(AgentRun.id)
            .where(
                AgentRun.status == 'queued',
                AgentRun.deadline > now,
                AgentRun.user_id.not_in(select(AgentOwnerLease.user_id).where(AgentOwnerLease.lease_until > now)),
            )
            .order_by(AgentRun.created_at)
            .limit(1)
        )
        if not run_id:
            await db.commit()
            return None
        row = await db.get(AgentRun, run_id)
        lease = str(uuid4())
        changed_owner = await db.execute(
            update(AgentOwnerLease)
            .where(
                AgentOwnerLease.user_id == row.user_id,
                AgentOwnerLease.lease_until <= now,
            )
            .values(run_id=run_id, lease=lease, lease_until=now + 60)
        )
        if not changed_owner.rowcount:
            db.add(AgentOwnerLease(user_id=row.user_id, run_id=run_id, lease=lease, lease_until=now + 60))
            await db.flush()
        result = await db.execute(
            update(AgentRun)
            .where(
                AgentRun.id == run_id,
                AgentRun.status == 'queued',
            )
            .values(status='running', lease=lease, lease_until=now + 60, updated_at=now)
        )
        if not result.rowcount:
            await db.rollback()
            return None
        await db.commit()
        return run_id, lease


async def claim_run():
    try:
        return await _claim_run()
    except IntegrityError:
        # Another instance acquired this owner concurrently; the transaction was rolled back.
        return None


async def checkpoint(run_id, lease, status, data):
    await record_run_event(run_id, lease, f'run.{status}', phase=data.get('phase'))
    async with get_async_db() as db:
        result = await db.execute(
            update(AgentRun)
            .where(
                AgentRun.id == run_id,
                AgentRun.lease == lease,
                AgentRun.status == 'running',
            )
            .values(status=status, checkpoint=data, updated_at=int(time.time()))
        )
        await db.commit()
        return bool(result.rowcount)


async def heartbeat(run_id, lease, task, expected_stamp):
    try:
        while not task.done():
            await asyncio.sleep(5)
            async with get_async_db() as db:
                row = await db.get(AgentRun, run_id)
                owner = row.user_id if row else None
                now = int(time.time())
                result = await db.execute(
                    update(AgentRun)
                    .where(
                        AgentRun.id == run_id,
                        AgentRun.lease == lease,
                        AgentRun.status == 'running',
                        AgentRun.deadline > now,
                    )
                    .values(lease_until=now + 60, updated_at=now)
                )
                await db.execute(
                    update(AgentOwnerLease)
                    .where(
                        AgentOwnerLease.run_id == run_id,
                        AgentOwnerLease.lease == lease,
                    )
                    .values(lease_until=now + 60)
                )
                await db.commit()
            auth = await Auths.get_auth_by_id(owner) if owner else None
            user = await Users.get_user_by_id(owner) if owner else None
            if (
                not result.rowcount
                or not auth
                or not auth.active
                or not auth.email_verified
                or auth.session_stamp != expected_stamp
                or not user
                or user.role not in {'user', 'admin'}
            ):
                task.cancel()
                return
    except asyncio.CancelledError:
        raise
    except Exception:
        log.exception('Agent lease heartbeat failed; stopping execution')
        task.cancel()


async def execute_run(app, run_id, lease):
    from answerai.utils.plans import require_model
    from answerai.utils.tool_approval import pending_tool_calls

    async with get_async_db() as db:
        row = await db.get(AgentRun, run_id)
        if not row or row.lease != lease or row.status != 'running':
            return
        data = snapshot(row)
        owner = row.user_id
        options = dict(row.options or {})
    user = await Users.get_user_by_id(owner)
    auth = await Auths.get_auth_by_id(owner)
    if not user or user.role not in {'user', 'admin'} or not auth or not auth.active or not auth.email_verified:
        await checkpoint(run_id, lease, 'blocked', {'phase': 'authorization', 'message': 'Owner is no longer active.'})
        return
    await require_model(user, data['model_id'])
    from answerai.models.config import Config

    if options.get('web_search') and not await Config.get('web.search.enable'):
        await checkpoint(
            run_id,
            lease,
            'blocked',
            {
                'phase': 'configuration',
                'message': 'Web search is not configured. Enable a supported search provider or disable web research.',
            },
        )
        return
    # Reuses scoped, expiring internal authentication, never a persisted API credential.
    from answerai.utils.auth import create_token

    request = Request(
        {
            'type': 'http',
            'method': 'POST',
            'path': '/api/v1/agent-runs/internal',
            'query_string': b'',
            'headers': [],
            'app': app,
            'scheme': 'http',
            'server': ('127.0.0.1', 80),
            'client': ('127.0.0.1', 0),
        }
    )
    token = create_token(
        {'id': owner, 'typ': 'subagent', 'session_stamp': auth.session_stamp}, expires_delta=timedelta(hours=1)
    )
    request.state.token = HTTPAuthorizationCredentials(scheme='Bearer', credentials=token)
    request.state.internal = True
    request.state.enable_api_keys = False
    request.state.max_tool_call_iterations = data['iterations']
    request.state.agent_read_only = True
    request.state.agent_coordinator = True
    request.state.agent_run_id = run_id
    request.state.agent_run_lease = lease
    chat = await Chats.get_chat_by_id_and_user_id(data['chat_id'], owner)
    if not chat:
        prompt = data['checkpoint']['prompt']
        user_id = str(uuid4())
        chat = await Chats.insert_new_chat(
            data['chat_id'],
            owner,
            ChatForm(
                chat={
                    'title': prompt[:80],
                    'models': [data['model_id']],
                    'params': {'agent_mode': 'agent', 'tool_approval_mode': 'ask'},
                    'history': {
                        'currentId': data['message_id'],
                        'messages': {
                            user_id: {
                                'id': user_id,
                                'parentId': None,
                                'childrenIds': [data['message_id']],
                                'role': 'user',
                                'content': prompt,
                                'timestamp': int(time.time()),
                            },
                            data['message_id']: {
                                'id': data['message_id'],
                                'parentId': user_id,
                                'childrenIds': [],
                                'role': 'assistant',
                                'content': '',
                                'done': False,
                                'model': data['model_id'],
                            },
                        },
                    },
                    'messages': [{'role': 'user', 'content': prompt}],
                    'files': options.get('files') or [],
                }
            ),
        )
    if not chat:
        raise RuntimeError('Could not create execution conversation')
    from answerai.utils.tool_approval import build_tool_approval_resume_payload

    payload = await build_tool_approval_resume_payload(data['chat_id'], data['message_id'], chat=chat)
    payload['params'] = {**payload.get('params', {}), 'agent_mode': 'agent', 'tool_approval_mode': 'full'}
    payload['messages'].insert(
        0,
        {
            'role': 'system',
            'content': (
                'This is a read-only research execution. Plan, gather evidence, compare sources and verify findings. '
                'Use planner, researcher or verifier delegates for independent work when useful. '
                'Do not modify resources, send messages, publish, execute code or delegate actions. '
                'If the objective requires those capabilities, report the blocker. Cite the sources actually read.'
            ),
        },
    )
    payload.setdefault('features', {})['web_search'] = bool(options.get('web_search'))
    payload['files'] = options.get('files') or []
    payload['max_tokens'] = 2048
    payload['session_id'] = f'agent-run:{run_id}'
    await checkpoint(
        run_id, lease, 'running', {'phase': 'executing', 'message': 'Executing through the agent pipeline.'}
    )
    async with asyncio.timeout(max(1, data['deadline'] - time.time())):
        await app.state.CHAT_COMPLETION_HANDLER(request, payload, user=user)
    message = await Chats.get_message_by_id_and_message_id(data['chat_id'], data['message_id'])
    if not message:
        raise RuntimeError('Execution message is missing')
    if pending_tool_calls(message.get('output') or []):
        status, phase = 'approval_required', 'approval_required'
    elif message.get('error'):
        status, phase = 'failed', 'failed'
    elif not message.get('done'):
        status, phase = 'blocked', 'incomplete'
    else:
        status, phase = 'needs_review', 'verification_required'
    await checkpoint(
        run_id,
        lease,
        status,
        {
            'phase': phase,
            'message': 'Inspect the saved conversation and verify the result.',
        },
    )


async def run_claimed(app, run_id, lease):
    async with get_async_db() as db:
        row = await db.get(AgentRun, run_id)
        owner = row.user_id if row else None
    auth = await Auths.get_auth_by_id(owner) if owner else None
    task = asyncio.create_task(execute_run(app, run_id, lease))
    pulse = asyncio.create_task(heartbeat(run_id, lease, task, auth.session_stamp if auth else None))
    try:
        await task
    except asyncio.CancelledError:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        async with get_async_db() as db:
            await db.execute(
                update(AgentRun)
                .where(
                    AgentRun.id == run_id,
                    AgentRun.lease == lease,
                    AgentRun.status == 'pausing',
                )
                .values(status='paused', lease=None, checkpoint={'phase': 'paused'}, updated_at=int(time.time()))
            )
            await db.commit()
        await checkpoint(run_id, lease, 'blocked', {'phase': 'interrupted', 'message': 'Execution was interrupted.'})
        if asyncio.current_task().cancelling():
            raise
    except Exception:
        log.exception('Agent execution failed: %s', run_id)
        await checkpoint(
            run_id, lease, 'failed', {'phase': 'failed', 'message': 'Execution failed; inspect the conversation.'}
        )
    finally:
        pulse.cancel()
        with suppress(asyncio.CancelledError):
            await pulse
        async with get_async_db() as db:
            await db.execute(
                delete(AgentOwnerLease).where(
                    AgentOwnerLease.run_id == run_id,
                    AgentOwnerLease.lease == lease,
                )
            )
            await db.commit()


async def worker_loop(app):
    # One owner per lease; four active tasks per process. More instances share the same leases.
    active = set()
    try:
        while True:
            try:
                finished = {task for task in active if task.done()}
                active.difference_update(finished)
                for task in finished:
                    try:
                        task.result()
                    except asyncio.CancelledError:
                        pass
                    except Exception:
                        log.exception('Agent worker task failed during cleanup')
                if len(active) < 4:
                    claimed = await claim_run()
                    if claimed:
                        active.add(asyncio.create_task(run_claimed(app, *claimed)))
                        continue
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception('Agent worker could not poll execution state')
                await asyncio.sleep(2)
    finally:
        for task in active:
            task.cancel()
        await asyncio.gather(*active, return_exceptions=True)


async def record_run_event(run_id, lease, event_type, **details):
    # CAS protects SQLite too, where SELECT FOR UPDATE cannot serialize parallel tools.
    for _ in range(16):
        async with get_async_db() as db:
            row = await db.scalar(
                select(AgentRun)
                .where(AgentRun.id == run_id, AgentRun.lease == lease, AgentRun.status == 'running')
                .with_for_update()
            )
            if row is None:
                return False
            version = row.event_sequence
            events = list(row.timeline or [])
            sequence = max(version, events[-1]['sequence'] if events else 0) + 1
            events.append({'sequence': sequence, 'at': time.time(), 'type': event_type, **details})
            result = await db.execute(
                update(AgentRun)
                .where(
                    AgentRun.id == run_id,
                    AgentRun.lease == lease,
                    AgentRun.status == 'running',
                    AgentRun.event_sequence == version,
                )
                .values(timeline=events[-256:], event_sequence=sequence, updated_at=int(time.time()))
            )
            await db.commit()
            if result.rowcount:
                return True
        await asyncio.sleep(0)
    return False


async def reserve_run_credits(request, payload):
    from fastapi import HTTPException
    import json

    run_id = getattr(request.state, 'agent_run_id', None)
    if not run_id:
        return
    request.state.billing_output_cap = min(getattr(request.state, 'billing_output_cap', 2048), 2048)
    amount = (
        len(
            json.dumps(
                {key: payload[key] for key in ('messages', 'input', 'prompt', 'tools') if key in payload},
                ensure_ascii=False,
            ).encode()
        )
        + 1024
        + 2048
    )
    async with get_async_db() as db:
        result = await db.execute(
            update(AgentRun)
            .where(
                AgentRun.id == run_id,
                AgentRun.lease == request.state.agent_run_lease,
                AgentRun.status == 'running',
                AgentRun.tokens_used + amount <= AgentRun.token_budget,
            )
            .values(tokens_used=AgentRun.tokens_used + amount, updated_at=int(time.time()))
        )
        await db.commit()
    if not result.rowcount:
        raise HTTPException(429, 'Agent execution credit budget exhausted or execution stopped.')
