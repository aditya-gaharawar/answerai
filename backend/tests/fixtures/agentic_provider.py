"""Deterministic OpenAI protocol fixture for local verification only; never a production provider."""

import json
import time
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()


@app.get('/v1/models')
async def models():
    return {'object': 'list', 'data': [{'id': 'agent-validation', 'object': 'model', 'owned_by': 'local-test'}]}


@app.post('/v1/chat/completions')
async def completion(request: Request):
    data = await request.json()
    has_tool = any(m.get('role') == 'tool' for m in data.get('messages', []))
    available = {t.get('function', {}).get('name') for t in data.get('tools', [])}
    use_tool = not has_tool and 'get_current_timestamp' in available
    delta = (
        {
            'tool_calls': [
                {
                    'index': 0,
                    'id': 'call_validation_clock',
                    'type': 'function',
                    'function': {'name': 'get_current_timestamp', 'arguments': '{}'},
                }
            ]
        }
        if use_tool
        else {
            'content': 'Validation complete: the timestamp tool ran successfully. This response is from a local test provider.'
        }
    )
    reason = 'tool_calls' if use_tool else 'stop'
    common = {
        'id': 'chatcmpl-validation',
        'object': 'chat.completion.chunk',
        'created': int(time.time()),
        'model': 'agent-validation',
    }
    if data.get('stream'):

        async def events():
            yield (
                'data: '
                + json.dumps(
                    {**common, 'choices': [{'index': 0, 'delta': {'role': 'assistant'}, 'finish_reason': None}]}
                )
                + '\n\n'
            )
            yield (
                'data: '
                + json.dumps({**common, 'choices': [{'index': 0, 'delta': delta, 'finish_reason': None}]})
                + '\n\n'
            )
            yield (
                'data: '
                + json.dumps(
                    {
                        **common,
                        'choices': [{'index': 0, 'delta': {}, 'finish_reason': reason}],
                        'usage': {'prompt_tokens': 100, 'completion_tokens': 30, 'total_tokens': 130},
                    }
                )
                + '\n\n'
            )
            yield 'data: [DONE]\n\n'

        return StreamingResponse(events(), media_type='text/event-stream')
    return {
        **common,
        'object': 'chat.completion',
        'choices': [{'index': 0, 'message': {'role': 'assistant', **delta}, 'finish_reason': reason}],
        'usage': {'prompt_tokens': 100, 'completion_tokens': 30, 'total_tokens': 130},
    }
