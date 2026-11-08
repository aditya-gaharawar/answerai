"""Owner-scoped execution history and explicit cancellation/verification controls."""

import time
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from answerai.internal.db import get_async_db
from answerai.models.agent_runs import AgentRun
from answerai.utils.auth import get_verified_user
from answerai.utils.plans import require_feature, require_model, reserve
from answerai.utils.agent_runs import snapshot

router = APIRouter()


class CreateRun(BaseModel):
    model_config = ConfigDict(extra='forbid')
    objective: str = Field(min_length=1, max_length=16000)
    model_id: str = Field(min_length=1, max_length=200)
    request_key: str = Field(min_length=1, max_length=100)
    max_seconds: int = Field(default=300, ge=30, le=3600)
    max_iterations: int = Field(default=12, ge=1, le=40)
    token_budget: int = Field(default=256000, ge=4096, le=500000)
    web_search: bool = True
    file_ids: list[str] = Field(default_factory=list, max_length=20)


def same_submission(row, form, files):
    return (
        row.prompt == form.objective
        and row.model_id == form.model_id
        and row.max_seconds == form.max_seconds
        and row.iterations == form.max_iterations
        and row.token_budget == form.token_budget
        and row.options == {'web_search': form.web_search, 'files': files}
    )


@router.get('/')
async def list_runs(since: int = 0, user=Depends(get_verified_user)):
    async with get_async_db() as db:
        rows = (
            await db.scalars(
                select(AgentRun)
                .where(AgentRun.user_id == user.id, AgentRun.updated_at >= max(0, since))
                .order_by(AgentRun.created_at.desc())
                .limit(100)
            )
        ).all()
    return [snapshot(row) for row in rows]


@router.post('/')
async def create_run(form: CreateRun, user=Depends(get_verified_user)):
    if not form.objective.strip():
        raise HTTPException(400, 'An objective is required.')
    await require_feature(user, 'tools')
    await require_model(user, form.model_id)
    if form.web_search:
        await require_feature(user, 'web_search')
    files = []
    if form.file_ids:
        from answerai.models.files import Files

        await require_feature(user, 'uploads')
        for file_id in dict.fromkeys(form.file_ids):
            file = await Files.get_file_by_id(file_id)
            if not file or file.user_id != user.id:
                raise HTTPException(404, 'An attached file is unavailable.')
            files.append({'id': file.id, 'name': file.filename, 'type': 'file'})
    async with get_async_db() as db:
        previous = await db.scalar(
            select(AgentRun).where(
                AgentRun.user_id == user.id,
                AgentRun.request_key == form.request_key,
            )
        )
        if previous:
            if not same_submission(previous, form, files):
                raise HTTPException(409, 'This request key is already assigned to another objective.')
            return snapshot(previous)
    await reserve(user.id, [('agent_submissions', 60, 5, 1)])
    now = int(time.time())
    row = AgentRun(
        id=str(uuid4()),
        user_id=user.id,
        request_key=form.request_key,
        chat_id=str(uuid4()),
        message_id=str(uuid4()),
        prompt=form.objective,
        model_id=form.model_id,
        status='queued',
        lease_until=0,
        checkpoint={'phase': 'queued', 'prompt': form.objective},
        created_at=now,
        updated_at=now,
        deadline=now + form.max_seconds,
        iterations=form.max_iterations,
        max_seconds=form.max_seconds,
        resume_count=0,
        token_budget=form.token_budget,
        tokens_used=0,
        options={'web_search': form.web_search, 'files': files},
        timeline=[{'sequence': 1, 'at': now, 'type': 'run.queued'}],
        event_sequence=1,
    )
    try:
        async with get_async_db() as db:
            db.add(row)
            await db.commit()
    except IntegrityError:
        async with get_async_db() as db:
            row = await db.scalar(
                select(AgentRun).where(
                    AgentRun.user_id == user.id,
                    AgentRun.request_key == form.request_key,
                )
            )
            if row is None:
                raise
            if not same_submission(row, form, files):
                raise HTTPException(409, 'This request key is already assigned to another objective.')
    return snapshot(row)


@router.post('/{run_id}/cancel')
async def cancel_run(run_id: str, user=Depends(get_verified_user)):
    async with get_async_db() as db:
        result = await db.execute(
            update(AgentRun)
            .where(
                AgentRun.id == run_id,
                AgentRun.user_id == user.id,
                AgentRun.status.in_(['queued', 'running', 'pausing', 'paused', 'blocked', 'approval_required']),
            )
            .values(status='cancelled', lease=None, checkpoint={'phase': 'cancelled'}, updated_at=int(time.time()))
        )
        await db.commit()
    if not result.rowcount:
        raise HTTPException(409, 'Run unavailable or no longer cancellable.')
    return {'status': 'cancelled'}


@router.post('/{run_id}/verify')
async def verify_run(run_id: str, user=Depends(get_verified_user)):
    # Explicit user verification is honest; model output alone cannot establish task success.
    async with get_async_db() as db:
        result = await db.execute(
            update(AgentRun)
            .where(
                AgentRun.id == run_id,
                AgentRun.user_id == user.id,
                AgentRun.status == 'needs_review',
            )
            .values(status='completed', checkpoint={'phase': 'verified_by_user'}, updated_at=int(time.time()))
        )
        await db.commit()
    if not result.rowcount:
        raise HTTPException(409, 'Run is not awaiting verification.')
    return {'status': 'completed'}


@router.post('/{run_id}/pause')
async def pause_run(run_id: str, user=Depends(get_verified_user)):
    async with get_async_db() as db:
        row = await db.scalar(
            select(AgentRun)
            .where(
                AgentRun.id == run_id,
                AgentRun.user_id == user.id,
            )
            .with_for_update()
        )
        if not row or row.status not in {'queued', 'running'}:
            raise HTTPException(409, 'Run is not running or queued.')
        row.status = 'paused' if row.status == 'queued' else 'pausing'
        row.updated_at = int(time.time())
        await db.commit()
        return snapshot(row)


@router.post('/{run_id}/resume')
async def resume_run(run_id: str, user=Depends(get_verified_user)):
    from answerai.models.chats import Chats
    from answerai.utils.agent_execution import PARALLEL_READ_TOOLS
    from answerai.utils.tool_approval import pending_tool_calls, complete_tool_call

    async with get_async_db() as db:
        row = await db.scalar(
            select(AgentRun)
            .where(
                AgentRun.id == run_id,
                AgentRun.user_id == user.id,
            )
            .with_for_update()
        )
        if not row or row.status not in {'paused', 'blocked'} or row.resume_count >= 3:
            raise HTTPException(409, 'Run cannot resume; inspect its conversation or start a new task.')
        await require_model(user, row.model_id)
        await require_feature(user, 'tools')
        message = await Chats.get_message_by_id_and_message_id(row.chat_id, row.message_id)
        for call in pending_tool_calls((message or {}).get('output') or []):
            if call.get('name') not in PARALLEL_READ_TOOLS:
                raise HTTPException(409, 'Resolve outstanding interactive actions in the conversation first.')
            if call.get('status') == 'in_progress':
                from answerai.utils.json_codec import JSONCodec

                call_id = call.get('call_id') or call['id']
                await complete_tool_call(
                    row.chat_id,
                    row.message_id,
                    {**call, 'call_id': call_id, 'status': 'failed'},
                    {
                        'type': 'function_call_output',
                        'id': f'fco_{call_id}',
                        'call_id': call_id,
                        'status': 'completed',
                        'output': [
                            {
                                'type': 'input_text',
                                'text': JSONCodec.dumps({'error': 'Read interrupted by pause/recovery.'}),
                            }
                        ],
                    },
                )
        row.status = 'queued'
        row.lease = None
        row.resume_count += 1
        row.deadline = int(time.time()) + row.max_seconds
        row.updated_at = int(time.time())
        row.checkpoint = {'phase': 'resuming', 'prompt': row.prompt}
        await db.commit()
        return snapshot(row)


@router.get('/{run_id}/events')
async def stream_events(run_id: str, request: Request, after: int = 0, user=Depends(get_verified_user)):
    import asyncio
    import json
    from fastapi.responses import StreamingResponse

    async with get_async_db() as db:
        row = await db.scalar(select(AgentRun).where(AgentRun.id == run_id, AgentRun.user_id == user.id))
        if row is None:
            raise HTTPException(404, 'Execution not found.')

    async def stream():
        cursor = max(0, after)
        started = time.monotonic()
        while time.monotonic() - started < 60 and not await request.is_disconnected():
            async with get_async_db() as db:
                row = await db.scalar(select(AgentRun).where(AgentRun.id == run_id, AgentRun.user_id == user.id))
                if row is None:
                    return
                events = list(row.timeline or [])
                status = row.status
            for event in events:
                if event['sequence'] > cursor:
                    cursor = event['sequence']
                    yield f'id: {cursor}\nevent: activity\ndata: {json.dumps(event)}\n\n'
            if status in {'completed', 'failed', 'cancelled', 'needs_review', 'blocked', 'paused'}:
                yield f'event: state\ndata: {json.dumps({"status": status})}\n\n'
                return
            yield ': heartbeat\n\n'
            await asyncio.sleep(1)

    return StreamingResponse(
        stream(), media_type='text/event-stream', headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'}
    )
