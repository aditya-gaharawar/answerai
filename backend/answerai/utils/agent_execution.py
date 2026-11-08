"""Bound tool execution and report repairable input errors without repeating side effects."""

import asyncio
import math
import os


def missing_tool_arguments(params, schema):
    required = schema.get('required') or []
    required = [name for name in required if isinstance(name, str)] if isinstance(required, list) else []
    missing = [name for name in required if name not in params]
    if missing:
        return 'Missing required arguments: ' + ', '.join(missing) + '. Use the tool schema and try again.'
    return None


def tool_timeout(name, kind):
    if kind == 'builtin' and name in {'ask_user', 'timer', 'delegate_task'}:
        return None
    default = 600.0 if kind == 'builtin' and name in {'generate_image', 'edit_image'} else 180.0
    try:
        value = float(os.getenv('AGENT_TOOL_TIMEOUT_SECONDS', str(default)))
        return max(1.0, min(value, 1800.0)) if math.isfinite(value) else default
    except ValueError:
        return default


async def run_agent_tool(awaitable, name, kind='', *, timeout=None):
    seconds = tool_timeout(name, kind) if timeout is None else timeout
    deadline = asyncio.timeout(seconds)
    try:
        async with deadline:
            return await awaitable
    except TimeoutError:
        if not deadline.expired():
            raise
        return {
            'error': f'Tool "{name}" did not finish within {seconds:g} seconds.',
            'error_type': 'timeout',
            'retryable': False,
            'message': 'Inspect the current state before retrying; remote work or side effects may still be running.',
        }


# Only known read-only built-ins are eligible; connector annotations are not an authorization boundary.
PARALLEL_READ_TOOLS = {
    'search_web',
    'research_web',
    'fetch_url',
    'search_tools',
    'get_current_timestamp',
    'calculate_timestamp',
    'list_chat_files',
    'grep_chat_files',
    'query_chat_files',
    'view_file',
    'list_knowledge_bases',
    'search_knowledge_bases',
    'search_knowledge_files',
    'grep_knowledge_files',
    'query_knowledge_files',
    'query_knowledge_bases',
    'view_knowledge_file',
    'search_notes',
    'view_note',
    'search_chats',
    'view_chat',
    'search_memories',
    'list_memories',
    'read_memory_path',
    'list_memory_paths',
    'view_skill',
    'read_skill_file',
    'grep_skill_files',
}


def requires_tool_approval(call, metadata):
    """Only server-known read tools bypass interactive approval in explicit agent mode."""
    if metadata.get('params', {}).get('agent_mode') != 'agent':
        return True
    name = call.get('name') or call.get('function', {}).get('name')
    tool = metadata.get('tools', {}).get(name, {})
    return not (name in PARALLEL_READ_TOOLS and tool.get('type') == 'builtin' and not tool.get('direct'))


async def execute_agent_batch(calls, tools, execute, *, parallelism=4):
    """Run contiguous read batches concurrently, preserving action barriers and provider result order."""
    results = {}
    pending = []
    parallelism = max(1, min(parallelism, 8))

    async def flush():
        if not pending:
            return
        import json
        import copy

        # Join identical read calls only inside this contiguous batch, never across actions or requests.
        shared = {}
        async with asyncio.TaskGroup() as group:
            tasks = []
            for call in pending:
                arguments = call.get('arguments', '{}')
                try:
                    arguments = json.loads(arguments) if isinstance(arguments, str) else arguments
                    key = json.dumps([call.get('name'), arguments], sort_keys=True)
                except (ValueError, TypeError):
                    key = call['call_id']
                if key not in shared:
                    shared[key] = group.create_task(execute(call))
                tasks.append(shared[key])
        for call, task in zip(pending, tasks):
            value = task.result()
            if isinstance(value, tuple) and len(value) == 5:
                value = (copy.deepcopy(value[0]), copy.deepcopy(value[1]), *value[2:])
            else:
                value = copy.deepcopy(value)
            results[call['call_id']] = value
        pending.clear()

    for call in calls:
        tool = tools.get(call.get('name'), {})
        safe_read = call.get('name') in PARALLEL_READ_TOOLS and tool.get('type') == 'builtin' and not tool.get('direct')
        if safe_read:
            pending.append(call)
            if len(pending) >= parallelism:
                await flush()
        else:
            await flush()
            results[call['call_id']] = await execute(call)
    await flush()
    return results


def failure_key(name, params):
    import hashlib
    import json

    encoded = json.dumps([name, params], sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def repeated_tool_failure(metadata, name, params):
    failures = metadata.get('_agent_failed_calls', {})
    count = failures.get(failure_key(name, params), 0) if isinstance(failures, dict) else 0
    if isinstance(count, int) and count >= 2:
        return {
            'error': 'This tool call has already failed. Change its arguments, use another tool or report the blocker.',
            'error_type': 'repeated_tool_failure',
            'retryable': False,
        }
    return None


def record_tool_result(metadata, name, params, result):
    import json

    failure = None
    if isinstance(result, dict):
        failure = result if result.get('error') else None
    elif isinstance(result, str):
        if result.lstrip().lower().startswith('error:'):
            failure = {'error': result}
        else:
            try:
                parsed = json.loads(result)
                failure = parsed if isinstance(parsed, dict) and parsed.get('error') else None
            except (ValueError, TypeError):
                pass
    failures = metadata.setdefault('_agent_failed_calls', {})
    if not isinstance(failures, dict):
        failures = metadata['_agent_failed_calls'] = {}
    key = failure_key(name, params)
    if failure:
        if key not in failures and len(failures) >= 64:
            failures.pop(next(iter(failures)))
        previous = failures.get(key, 0)
        previous = previous if isinstance(previous, int) else 0
        failures[key] = 2 if failure.get('retryable') is False else previous + 1
    else:
        failures.pop(key, None)
    return bool(failure)
