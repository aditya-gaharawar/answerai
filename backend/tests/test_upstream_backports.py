"""Exercise provider payload and response regressions from upstream 0.13.0."""

import pytest
from answerai.utils.payload import apply_model_params_to_body_ollama, apply_model_params_to_body_openai
from answerai.utils.response import handle_responses_streaming_event


@pytest.mark.parametrize('provider', [apply_model_params_to_body_openai, apply_model_params_to_body_ollama])
def test_stop_sequences_preserve_unicode_and_decode_literal_newlines(provider):
    stops = ['終', 'café', '🛑', r'line\nbreak']
    result = provider({'stop': stops}, {})
    options = result.get('options', result)
    assert options['stop'] == ['終', 'café', '🛑', 'line\nbreak']
    assert stops[-1] == r'line\nbreak'


def test_truncated_response_preserves_output_and_provider_usage():
    output = [{'id': 'msg-1', 'type': 'message', 'content': [{'type': 'output_text', 'text': 'Partial answer'}]}]
    usage = {'input_tokens': 8, 'output_tokens': 12, 'total_tokens': 20}
    result, metadata = handle_responses_streaming_event(
        {'type': 'response.incomplete', 'response': {'id': 'response-1', 'output': [], 'usage': usage}}, output
    )
    assert result == output
    assert metadata == {'usage': usage, 'done': True, 'response_id': 'response-1'}


@pytest.mark.asyncio
async def test_pending_knowledge_stream_stops_when_read_access_is_revoked():
    # Load the real endpoint without the document-provider optional dependencies.
    import ast
    import json
    from pathlib import Path
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from starlette.responses import StreamingResponse

    source = Path(__file__).parents[1] / 'answerai/routers/knowledge.py'
    tree = ast.parse(source.read_text())
    endpoint = next(
        n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'get_pending_knowledge_files'
    )
    endpoint.decorator_list = []
    endpoint.args.defaults = [ast.Constant(None) for _ in endpoint.args.defaults]
    module = ast.Module(
        body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), endpoint],
        type_ignores=[],
    )
    user = SimpleNamespace(id='reader', role='user')
    pending = AsyncMock(return_value=[SimpleNamespace(model_dump=lambda: {'id': 'processing-file'})])
    grants = AsyncMock(side_effect=[True, False])
    scope = {
        'Knowledges': SimpleNamespace(
            get_knowledge_by_id=AsyncMock(return_value=SimpleNamespace(id='kb', user_id='owner'))
        ),
        'Files': SimpleNamespace(get_pending_files_for_knowledge=pending),
        'AccessGrants': SimpleNamespace(has_access=grants),
        'get_verified_user_by_id': AsyncMock(return_value=user),
        'asyncio': SimpleNamespace(sleep=AsyncMock()),
        'JSONCodec': SimpleNamespace(dumps=json.dumps),
        'StreamingResponse': StreamingResponse,
    }
    exec(compile(ast.fix_missing_locations(module), str(source), 'exec'), scope)
    response = await scope['get_pending_knowledge_files']('kb', True, user)
    iterator = response.body_iterator
    assert 'processing-file' in await anext(iterator)
    with pytest.raises(StopAsyncIteration):
        await anext(iterator)
    assert pending.await_count == 1
    assert grants.await_count == 2


@pytest.mark.parametrize('filename', ['renamed.xls', 'unknown.bin', 'download'])
def test_archive_size_guard_detects_zip_content_with_any_filename(tmp_path, filename):
    import ast
    import os
    import zipfile
    from pathlib import Path
    from types import SimpleNamespace

    source = Path(__file__).parents[1] / 'answerai/retrieval/loaders/main.py'
    tree = ast.parse(source.read_text())
    loader = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Loader')
    method = next(n for n in loader.body if isinstance(n, ast.FunctionDef) and n.name == '_get_loader')
    scope = {'zipfile': zipfile, 'os': os}
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), 'exec'), scope)
    path = tmp_path / filename
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('document.xml', b'x' * (2 * 1024 * 1024))
    with pytest.raises(ValueError, match='too large after decompression'):
        scope['_get_loader'](
            SimpleNamespace(config={'rag.file.max_size': 1}), filename, 'application/octet-stream', str(path)
        )
