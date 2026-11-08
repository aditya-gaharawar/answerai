"""Tool relevance, safe batch coalescing and model-facing recovery contracts."""

import asyncio
import pytest
from answerai.utils.tool_context import contextual_tools
from answerai.utils.tool_outcomes import normalize_tool_error
from answerai.utils.agent_execution import execute_agent_batch


def test_context_uses_latest_user_and_only_authorized_tools():
    form = {
        'messages': [
            {'role': 'user', 'content': 'Generate an image'},
            {'role': 'assistant', 'content': 'research web'},
            {'role': 'user', 'content': 'Read the attached PDF'},
        ]
    }
    assert contextual_tools(form, {'query_chat_files': {}, 'generate_image': {}}) == ['query_chat_files']
    assert contextual_tools({'files': [{'id': 'a'}]}, {'list_chat_files': {}}) == ['list_chat_files']


def test_recovery_preserves_success_and_does_not_blindly_retry_actions():
    image = '{"url":"https://example.com/image.png"}'
    assert normalize_tool_error(image, 'generate_image', 'builtin') is image
    failure = normalize_tool_error('{"error":"unavailable"}', 'search_web', 'builtin')
    assert failure['ok'] is False and failure['retryable'] is True and failure['recovery']
    failure = normalize_tool_error('Error: uncertain', 'send_email', 'mcp')
    assert failure['retryable'] is False and 'Inspect' in failure['recovery']
    failure = normalize_tool_error({'error': 'deadline', 'retryable': False}, 'search_web', 'builtin')
    assert failure['retryable'] is False
    assert normalize_tool_error({'isError': True}, 'remote', 'mcp')['ok'] is False


@pytest.mark.asyncio
async def test_duplicate_reads_join_but_actions_and_read_after_action_execute():
    calls = [
        {'name': 'search_web', 'call_id': 'a', 'arguments': '{"q":"x"}'},
        {'name': 'search_web', 'call_id': 'b', 'arguments': '{ "q": "x" }'},
        {'name': 'write_note', 'call_id': 'c', 'arguments': '{}'},
        {'name': 'write_note', 'call_id': 'd', 'arguments': '{}'},
        {'name': 'search_web', 'call_id': 'e', 'arguments': '{"q":"x"}'},
    ]
    invoked = []

    async def execute(call):
        invoked.append(call['call_id'])
        await asyncio.sleep(0)
        return {'value': call['name']}

    results = await execute_agent_batch(
        calls, {name: {'type': 'builtin'} for name in ['search_web', 'write_note']}, execute
    )
    assert invoked == ['a', 'c', 'd', 'e']
    assert list(results) == ['a', 'b', 'c', 'd', 'e']
    assert results['a'] == results['b']
    results['a']['value'] = 'changed'
    assert results['b']['value'] == 'search_web'


@pytest.mark.asyncio
async def test_connector_named_like_builtin_is_never_coalesced():
    invoked = []

    async def execute(call):
        invoked.append(call['call_id'])
        return call['call_id']

    calls = [{'name': 'search_web', 'call_id': str(index), 'arguments': '{}'} for index in range(2)]
    await execute_agent_batch(calls, {'search_web': {'type': 'mcp'}}, execute)
    assert invoked == ['0', '1']
