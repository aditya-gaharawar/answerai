"""Run real tool functions in isolation from optional ML/provider dependencies."""

import ast
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

ROOT = Path(__file__).parents[1] / 'answerai'


def load_function(path, name, namespace):
    if name == 'execute_tool_call':
        namespace['resolve_tool_call'] = load_function(
            'utils/tool_search.py',
            'resolve_tool_call',
            {'CALL_TOOL_NAME': 'call_tool', 'JSONCodec': SimpleNamespace(loads=json.loads, dumps=json.dumps)},
        )
    source = ROOT / path
    node = next(
        n
        for n in ast.parse(source.read_text()).body
        if isinstance(n, (ast.AsyncFunctionDef, ast.FunctionDef)) and n.name == name
    )
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), namespace)
    return namespace[name]


@pytest.mark.asyncio
@pytest.mark.parametrize('arguments', [{'query': 'hello'}, '{"query":"hello"}', "{'query': 'hello'}"])
async def test_native_tool_accepts_provider_argument_formats(arguments):
    function = AsyncMock(return_value={'results': ['found']})
    update = AsyncMock(return_value=function)
    execute = load_function(
        'utils/middleware.py',
        'execute_tool_call',
        {
            'JSONCodec': SimpleNamespace(loads=json.loads, dumps=json.dumps),
            'ast': ast,
            'log': logging.getLogger(__name__),
            'is_saved_chat_id': lambda _: True,
            'get_updated_tool_function': update,
        },
    )
    call = {'function': {'name': 'search', 'arguments': arguments}}
    result = await execute(
        {'messages': []},
        {'tools': {'search': {'callable': function, 'spec': {'parameters': {'properties': {'query': {}}}}}}},
        None,
        call,
    )
    assert result[1] == {'results': ['found']}
    function.assert_awaited_once_with(query='hello')
    assert json.loads(call['function']['arguments']) == {'query': 'hello'}


@pytest.mark.asyncio
@pytest.mark.parametrize('arguments', [[], 7, '[]', 'not json', "{'query': {1, 2}}", '{"count": NaN}'])
async def test_invalid_arguments_never_execute_tools(arguments):
    update = AsyncMock()
    execute = load_function(
        'utils/middleware.py',
        'execute_tool_call',
        {
            'JSONCodec': SimpleNamespace(loads=json.loads, dumps=json.dumps),
            'ast': ast,
            'log': logging.getLogger(__name__),
            'get_updated_tool_function': update,
        },
    )
    result = await execute({}, {}, None, {'function': {'name': 'search', 'arguments': arguments}})
    assert result[2] is None
    update.assert_not_awaited()


@pytest.mark.asyncio
async def test_empty_image_result_is_failure_not_success():
    generate = load_function(
        'tools/builtin.py',
        'generate_image',
        {
            'Optional': __import__('typing').Optional,
            'Request': object,
            'JSONCodec': SimpleNamespace(dumps=json.dumps),
            'UserModel': lambda **kwargs: kwargs,
            'CreateImageForm': lambda **kwargs: kwargs,
            'image_generations': AsyncMock(return_value=[]),
            'log': logging.getLogger(__name__),
        },
    )
    result = json.loads(await generate('an illustration', __request__=object()))
    assert 'error' in result
    assert result.get('status') != 'success'


@pytest.mark.asyncio
@pytest.mark.parametrize('provider_data', [[{'b64_json': 'image-data'}], []])
async def test_image_payload_uses_resolved_model_and_rejects_empty_response(provider_data):
    import re

    import aiohttp
    from fastapi import HTTPException

    config = SimpleNamespace(
        IMAGE_SIZE='1024x1024',
        IMAGE_GENERATION_ENGINE='openai',
        IMAGE_GENERATION_MODEL='',
        IMAGES_OPENAI_API_KEY='test-only',
        IMAGES_OPENAI_API_BASE_URL='https://example.com/v1',
        IMAGES_OPENAI_API_VERSION='',
        IMAGES_OPENAI_API_PARAMS={},
    )

    class Response:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def raise_for_status(self):
            pass

        async def json(self, **kwargs):
            return {'data': provider_data}

    sent = []

    class Session:
        def post(self, **kwargs):
            sent.append(kwargs['json'])
            return Response()

    generate = load_function(
        'routers/images.py',
        'image_generations',
        {
            'Request': object,
            'CreateImageForm': object,
            're': re,
            'aiohttp': aiohttp,
            'get_image_config': AsyncMock(return_value=config),
            'get_image_model': AsyncMock(return_value='gpt-image-1'),
            'ENABLE_FORWARD_USER_INFO_HEADERS': False,
            'IMAGE_URL_RESPONSE_MODELS_REGEX_PATTERN': '^gpt-image',
            'get_session': AsyncMock(return_value=Session()),
            'AIOHTTP_CLIENT_SESSION_SSL': True,
            'get_image_data': AsyncMock(return_value=(b'image', 'image/png')),
            'upload_image': AsyncMock(return_value=(None, {'id': 'image-id', 'url': '/image'})),
            'HTTPException': HTTPException,
            'ERROR_MESSAGES': SimpleNamespace(DEFAULT=str),
        },
    )
    form = SimpleNamespace(prompt='A landscape', size=None, n=1)
    if provider_data:
        result = await generate(object(), form)
        assert result == [{'id': 'image-id', 'url': '/image'}]
    else:
        with pytest.raises(HTTPException, match='no images'):
            await generate(object(), form)
    assert sent[0]['model'] == 'gpt-image-1'
    assert 'response_format' not in sent[0]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'mode,upload_allowed,expected', [('agent', True, True), ('auto', True, False), ('agent', False, False)]
)
async def test_agent_file_tools_remain_permission_scoped(mode, upload_allowed, expected):
    def tool(name):
        async def run():
            pass

        run.__name__ = name
        return run

    names = ['list_chat_files', 'query_chat_files', 'grep_chat_files', 'view_file']
    namespace = {name: tool(name) for name in names}
    namespace.update(
        {
            'Request': object,
            'Config': SimpleNamespace(get_many=AsyncMock(return_value={}), get=AsyncMock(return_value={})),
            'has_permission': AsyncMock(return_value=upload_allowed),
            'get_attached_knowledge': lambda *_: [],
            'is_saved_chat_id': lambda _: False,
            'get_async_tool_function_and_apply_extra_params': AsyncMock(side_effect=lambda fn, *args: fn),
            'get_builtin_function_introspection': lambda fn: None,
            'get_builtin_tool_spec': lambda fn: {'name': fn.__name__, 'parameters': {'properties': {}}},
        }
    )
    get_tools = load_function('utils/tools.py', 'get_builtin_tools', namespace)
    categories = [
        'time',
        'user_input',
        'knowledge',
        'chats',
        'subagents',
        'memory',
        'web_search',
        'image_generation',
        'code_interpreter',
        'notes',
        'channels',
        'skills',
        'tasks',
        'automations',
        'calendar',
        'notifications',
    ]
    model = {
        'info': {
            'meta': {
                'builtinTools': {**dict.fromkeys(categories, False), 'files': True},
                'capabilities': {'file_context': True},
            }
        }
    }
    request = SimpleNamespace(state=SimpleNamespace())
    result = await get_tools(
        request,
        {
            '__user__': {'id': 'user-a', 'role': 'user'},
            '__metadata__': {'params': {'agent_mode': mode}, 'files': [{'id': 'file-a', 'type': 'file'}]},
        },
        model=model,
    )
    assert set(result) == (set(names) if expected else set())


def test_agent_guidance_only_mentions_available_capabilities():
    from answerai.utils.agent_workflow import agent_workflow_prompt

    assert agent_workflow_prompt({}) == ''
    prompt = agent_workflow_prompt({'list_chat_files': {}, 'create_tasks': {}, 'update_task': {}})
    assert 'list_chat_files' in prompt
    assert 'create_tasks' in prompt
    assert 'search_web' not in prompt
    assert 'generate_image' not in prompt
    image_prompt = agent_workflow_prompt({'generate_image': {}})
    assert 'generate_image' in image_prompt
    assert 'do not substitute an invented image link' in image_prompt
