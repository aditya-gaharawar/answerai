"""Consistent recovery hints for models without changing successful tool payloads."""

import json
from answerai.utils.agent_execution import PARALLEL_READ_TOOLS


def normalize_tool_error(result, name, kind):
    parsed = result
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
        except (ValueError, TypeError):
            if result.lstrip().lower().startswith(('error:', 'exception:', 'traceback', 'http error!')):
                parsed = {'error': result}
    if not isinstance(parsed, dict):
        return result
    if not parsed.get('error') and parsed.get('status') not in {'error', 'failed'} and not parsed.get('isError'):
        return result
    normalized = dict(parsed)
    normalized.setdefault('error', 'The tool did not complete successfully.')
    normalized.setdefault('error_type', 'tool_error')
    normalized['ok'] = False
    safe_read = kind == 'builtin' and name in PARALLEL_READ_TOOLS
    normalized.setdefault('retryable', safe_read)
    if normalized.get('error_type') == 'invalid_arguments':
        recovery = 'Correct the arguments using the schema before trying again.'
    elif normalized.get('retryable') is False or not safe_read:
        recovery = 'Inspect the current state before repeating this action. Report the blocker or use an authorized alternative.'
    else:
        recovery = (
            'Try a narrower query or another available source. Do not repeat an unchanged failing call indefinitely.'
        )
    normalized.setdefault('recovery', recovery)
    return normalized
