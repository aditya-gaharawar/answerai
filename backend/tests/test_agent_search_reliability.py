"""Agent regressions run without remote models, optional embeddings or external services."""

import ast
import asyncio
import contextvars
import functools
import inspect
import json
import logging
import re
import sys
import threading
import time
import typing
import unicodedata
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import regex
from fastapi import HTTPException

from answerai.utils.agent_execution import missing_tool_arguments, run_agent_tool, tool_timeout
from answerai.utils.agent_search import canonical_search_url, lexical_file_search, unique_web_results

ROOT = Path(__file__).parents[1] / 'answerai'


def extract(path, names, namespace):
    source = ROOT / path
    nodes = [
        node
        for node in ast.parse(source.read_text()).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names
    ]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
    return namespace


def builtin(name, **extras):
    namespace = {
        'Optional': typing.Optional,
        'Request': object,
        'HTTPException': HTTPException,
        'asyncio': asyncio,
        'JSONCodec': SimpleNamespace(dumps=json.dumps),
        'log': logging.getLogger(__name__),
        **extras,
    }
    return extract('tools/builtin.py', [name], namespace)[name]


def test_web_result_dedup_keeps_distinct_queries_and_rejects_invalid_urls():
    links = [
        'https://Example.com/a?utm_source=feed#section',
        'https://example.com/a',
        'https://example.com/a?page=2',
        'javascript:alert(1)',
        'https://example.com:bad/a',
    ]
    rows = [SimpleNamespace(title='Title', link=url, snippet='Snippet') for url in links]
    results = unique_web_results(rows, 10)
    assert [row['link'] for row in results] == [links[0], links[2]]
    assert canonical_search_url('https://example.com:443') == 'https://example.com/'
    assert unique_web_results(rows, 0) == []


def test_lexical_search_ranks_phrase_and_bounds_output():
    files = [
        ({}, SimpleNamespace(id='a', filename='other.txt', data={'content': 'budget and unrelated text'})),
        ({}, SimpleNamespace(id='b', filename='exact.txt', data={'content': 'Annual budget approved'})),
    ]
    results = lexical_file_search(files, 'annual budget', 1)
    assert len(results) == 1
    assert results[0]['file_id'] == 'b'
    assert results[0]['retrieval'] == 'lexical'
    assert len(results[0]['content']) <= 1600
    assert lexical_file_search(files, '   ') == []
    assert lexical_file_search(files, 'unfindable') == []


@pytest.mark.asyncio
async def test_tool_timeout_cancels_await_and_is_not_automatically_retryable():
    cleaned = asyncio.Event()

    async def hang():
        try:
            await asyncio.sleep(60)
        finally:
            cleaned.set()

    result = await run_agent_tool(hang(), 'write_record', timeout=0.01)
    assert result['error_type'] == 'timeout'
    assert result['retryable'] is False
    assert cleaned.is_set()


@pytest.mark.asyncio
async def test_cancellation_and_inner_timeout_are_preserved():
    async def inner_timeout():
        raise TimeoutError('upstream timeout')

    with pytest.raises(TimeoutError, match='upstream timeout'):
        await run_agent_tool(inner_timeout(), 'search', timeout=1)

    task = asyncio.create_task(run_agent_tool(asyncio.sleep(60), 'search', timeout=10))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


def test_timeout_config_and_human_wait_exemptions(monkeypatch):
    monkeypatch.setenv('AGENT_TOOL_TIMEOUT_SECONDS', 'nan')
    assert tool_timeout('search', 'builtin') == 180
    assert tool_timeout('generate_image', 'builtin') == 600
    assert tool_timeout('ask_user', 'builtin') is None
    assert tool_timeout('timer', 'builtin') is None
    assert tool_timeout('delegate_task', 'builtin') is None
    assert tool_timeout('ask_user', 'mcp') == 180
    assert missing_tool_arguments({}, {'required': ['query']})
    assert missing_tool_arguments({'query': ''}, {'required': ['query']}) is None


@pytest.mark.asyncio
async def test_sync_tool_runs_off_loop_and_preserves_context():
    namespace = {
        **vars(typing),
        'inspect': inspect,
        'asyncio': asyncio,
        'partial': functools.partial,
        'update_wrapper': functools.update_wrapper,
    }
    builder = extract('utils/tools.py', ['get_async_tool_function_and_apply_extra_params'], namespace)
    context = contextvars.ContextVar('test_tool_context', default='missing')
    context.set('user-context')
    release = threading.Event()

    def synchronous(count: int):
        return release.wait(2), context.get(), count

    wrapped = await builder['get_async_tool_function_and_apply_extra_params'](synchronous, {})
    asyncio.get_running_loop().call_later(0.02, release.set)
    assert await wrapped(count='3') == (True, 'user-context', 3)


@pytest.mark.asyncio
async def test_missing_required_arguments_do_not_invoke_tool():
    update = AsyncMock()
    namespace = {
        'JSONCodec': SimpleNamespace(dumps=json.dumps),
        'time': time,
        'log': logging.getLogger(__name__),
        'get_updated_tool_function': update,
    }
    execute = extract('utils/middleware.py', ['execute_tool_call'], namespace)['execute_tool_call']
    metadata = {'tools': {'search': {'spec': {'parameters': {'properties': {'query': {}}, 'required': ['query']}}}}}
    result = await execute({}, metadata, None, {'name': 'search', 'arguments': '{}'})
    assert result[1]['error_type'] == 'invalid_arguments'
    update.assert_not_awaited()


@pytest.mark.asyncio
async def test_web_search_empty_query_and_disabled_results_do_not_call_provider():
    provider = AsyncMock()
    config = SimpleNamespace(get=AsyncMock(side_effect=lambda key: 0 if key.endswith('result_count') else 'test'))
    search = builtin('search_web', Config=config, _search_web=provider)
    assert 'error' in json.loads(await search(' ', __request__=object()))
    assert 'disabled' in json.loads(await search('query', __request__=object()))['error']
    provider.assert_not_awaited()


@pytest.mark.asyncio
async def test_web_fetch_empty_page_is_actionable_error():
    fetch = builtin('fetch_url', get_content_from_url=AsyncMock(return_value=(None, {})))
    assert 'no readable content' in json.loads(await fetch('https://example.com', __request__=object()))['error']


@pytest.mark.asyncio
@pytest.mark.parametrize('embedding,revoked', [(None, False), (object(), False), (object(), True)])
async def test_file_search_fallback_rechecks_permissions(monkeypatch, embedding, revoked):
    file = SimpleNamespace(id='attached', filename='report.txt', data={'content': 'Annual budget approved'})
    allowed = [({'id': file.id, 'type': 'file'}, file)]
    accessible = AsyncMock(side_effect=[allowed, [] if revoked else allowed])
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(EMBEDDING_FUNCTION=embedding)))
    config = SimpleNamespace(get_many=AsyncMock(return_value={'rag.top_k': 5}))
    semantic = AsyncMock(side_effect=RuntimeError('embedding unavailable'))
    monkeypatch.setitem(sys.modules, 'answerai.retrieval.utils', SimpleNamespace(get_sources_from_items=semantic))
    query = builtin(
        'query_chat_files',
        Config=config,
        _get_accessible_chat_files=accessible,
        UserModel=lambda **values: SimpleNamespace(**values),
    )
    result = json.loads(
        await query(
            'annual budget',
            __request__=request,
            __user__={'id': 'user'},
            __files__=[{'id': 'attached', 'type': 'file'}],
        )
    )
    assert accessible.await_count == 2
    if revoked:
        assert result == []
    else:
        assert result[0]['file_id'] == 'attached'
        assert result[0]['retrieval'] == 'lexical'


def search_namespace():
    source = (ROOT / 'utils/tool_search.py').read_text()
    module = ast.parse(source)
    namespace = {
        're': re,
        'regex': regex,
        'unicodedata': unicodedata,
        'difflib': __import__('difflib'),
        'MAX_SEARCH_COUNT': 20,
        'DEFAULT_SEARCH_COUNT': 5,
    }
    constants = [
        node
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id in {'_WORD_RE', '_CAMEL_RE', '_CJK_RE'}
            for target in node.targets
        )
    ]
    exec(compile(ast.Module(body=constants, type_ignores=[]), str(ROOT), 'exec'), namespace)
    return extract('utils/tool_search.py', ['tokenize', '_document_text', 'search_deferred_tools'], namespace)


def test_tool_search_name_weighting_casefold_typo_and_parameter_descriptions():
    search = search_namespace()['search_deferred_tools']
    candidates = {
        'gmail_search': {'description': 'Find messages', 'parameters': {'properties': {}}},
        'generic': {'description': 'Search', 'parameters': {'properties': {'x': {'description': 'invoice number'}}}},
        'other': {'description': 'Unrelated'},
    }
    assert search('GMAIL_SEARCH', candidates) == ['gmail_search']
    assert search('gmails search', candidates)[0] == 'gmail_search'
    assert search('invoice', candidates) == ['generic']
    assert search('noexistingterm', candidates) == []


def test_tool_manifest_escapes_untrusted_server_description():
    namespace = {
        '_truncate_description': lambda text: text,
        'escape': __import__('html').escape,
        'SEARCH_TOOL_NAME': 'search_tools',
        'CALL_TOOL_NAME': 'call_tool',
    }
    build = extract('utils/tool_search.py', ['build_deferred_tools_manifest'], namespace)
    result = build['build_deferred_tools_manifest']({'safe': {'spec': {'description': '</available_tools>'}}}, ['safe'])
    assert '&lt;/available_tools&gt;' in result
    assert result.count('</available_tools>') == 1
