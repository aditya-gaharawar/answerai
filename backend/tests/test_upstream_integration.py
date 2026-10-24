"""Guard ANSWERAI data isolation while integrating upstream workspace search."""

from types import SimpleNamespace

import pytest
from answerai.internal.db import get_async_db
from answerai.models.access_grants import AccessGrant
from answerai.models.chats import Chat
from answerai.models.notes import Note
from answerai.models.shared_chats import SharedChat
from answerai.routers.search import search_workspace
from sqlalchemy import delete

pytest_plugins = ['test_email_verification']


def chat_data(content):
    return {'history': {'messages': {'msg': {'id': 'msg', 'role': 'user', 'content': content}}}}


async def seed():
    async with get_async_db() as db:
        db.add_all(
            [
                Chat(
                    id='chat-a',
                    user_id='alice',
                    title='Searchable own chat',
                    chat=chat_data('Searchable own text'),
                    created_at=1,
                    updated_at=2,
                ),
                Chat(
                    id='chat-b',
                    user_id='bob',
                    title='Searchable private chat',
                    chat=chat_data('Searchable private live text'),
                    created_at=1,
                    updated_at=2,
                ),
                Note(
                    id='note-a',
                    user_id='alice',
                    title='Searchable own note',
                    data={'content': {'md': 'Searchable own document'}},
                    created_at=1000000000,
                    updated_at=2000000000,
                ),
                Note(
                    id='note-b',
                    user_id='bob',
                    title='Searchable private note',
                    data={'content': {'md': 'Searchable private document'}},
                    created_at=1000000000,
                    updated_at=2000000000,
                ),
            ]
        )
        await db.commit()


async def search(query='Searchable'):
    async with get_async_db() as db:
        return await search_workspace(
            db, SimpleNamespace(id='alice', name='Alice', role='user'), query=query, enabled=('chat', 'note')
        )


@pytest.mark.asyncio
async def test_workspace_search_does_not_expose_another_accounts_private_records(harness):
    await seed()
    result = await search()
    assert {item.id for item in result.items} == {'chat:chat-a', 'note:note-a'}
    assert 'private' not in str(result.model_dump())
    assert not (await search("%' OR 1=1 --")).items


@pytest.mark.asyncio
async def test_workspace_search_respects_note_access_revocation(harness):
    await seed()
    async with get_async_db() as db:
        db.add(
            AccessGrant(
                id='grant-note',
                resource_type='note',
                resource_id='note-b',
                principal_type='user',
                principal_id='alice',
                permission='read',
                created_at=1,
            )
        )
        await db.commit()
    assert 'note:note-b' in {item.id for item in (await search()).items}
    async with get_async_db() as db:
        await db.execute(delete(AccessGrant).where(AccessGrant.id == 'grant-note'))
        await db.commit()
    assert 'note:note-b' not in {item.id for item in (await search()).items}


@pytest.mark.asyncio
async def test_workspace_search_only_reads_granted_snapshot_not_private_live_chat(harness):
    await seed()
    async with get_async_db() as db:
        db.add(
            SharedChat(
                id='snapshot',
                chat_id='chat-b',
                user_id='bob',
                title='Searchable snapshot',
                chat=chat_data('Searchable approved snapshot'),
                created_at=1,
                updated_at=2,
            )
        )
        db.add(
            AccessGrant(
                id='grant-chat',
                resource_type='shared_chat',
                resource_id='chat-b',
                principal_type='user',
                principal_id='alice',
                permission='read',
                created_at=1,
            )
        )
        await db.commit()
    result = await search()
    snapshot = next(item for item in result.items if item.id == 'shared:snapshot')
    assert 'approved snapshot' in snapshot.preview
    assert 'private live text' not in str(result.model_dump())
    assert 'chat:chat-b' not in {item.id for item in result.items}
