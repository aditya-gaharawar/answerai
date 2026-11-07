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
