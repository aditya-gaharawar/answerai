import ast
import json
import logging
import os
import sys
import types
from pathlib import Path

import pytest
from answerai.utils.model_safety import validate_model_snapshot


def write_index(root, shard):
    root.mkdir(parents=True, exist_ok=True)
    (root / 'model.safetensors.index.json').write_text(json.dumps({'weight_map': {'layer': shard}}))


@pytest.mark.parametrize('shard', ['../secret', '/etc/passwd', 'C:/secret', 'C:secret', '..\\secret', '', None, []])
def test_model_shards_cannot_escape_snapshot(tmp_path, shard):
    write_index(tmp_path, shard)
    with pytest.raises(ValueError):
        validate_model_snapshot(str(tmp_path))


def test_regular_shard_and_huggingface_blob_symlink_are_supported(tmp_path):
    repo = tmp_path / 'models--example--safe'
    snapshot = repo / 'snapshots' / 'revision'
    blobs = repo / 'blobs'
    blobs.mkdir(parents=True)
    (blobs / 'hash').write_bytes(b'weights')
    write_index(snapshot, 'model-1.safetensors')
    (snapshot / 'model-1.safetensors').symlink_to(blobs / 'hash')
    validate_model_snapshot(str(snapshot))


def test_model_shard_symlink_cannot_read_unrelated_files(tmp_path):
    root = tmp_path / 'model'
    write_index(root, 'weights')
    secret = tmp_path / 'secret'
    secret.write_text('outside-model')
    (root / 'weights').symlink_to(secret)
    with pytest.raises(ValueError, match='escapes'):
        validate_model_snapshot(str(root))


@pytest.mark.skipif(not hasattr(os, 'mkfifo'), reason='FIFO test requires POSIX')
@pytest.mark.parametrize('pipe_is_index', [False, True])
def test_model_loader_rejects_named_pipes_without_reading(tmp_path, pipe_is_index):
    if pipe_is_index:
        os.mkfifo(tmp_path / 'model.safetensors.index.json')
    else:
        write_index(tmp_path, 'weights')
        os.mkfifo(tmp_path / 'weights')
    with pytest.raises(ValueError, match='regular files'):
        validate_model_snapshot(str(tmp_path))


def test_cached_model_path_still_passes_validation(tmp_path, monkeypatch):
    # Run the actual path-resolution function without importing optional ML runtimes.
    source = Path(__file__).parents[1] / 'answerai/retrieval/utils.py'
    function = next(
        node
        for node in ast.parse(source.read_text()).body
        if isinstance(node, ast.FunctionDef) and node.name == 'get_model_path'
    )
    namespace = {'os': os, 'OFFLINE_MODE': False, 'log': logging.getLogger(__name__)}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
    hub = types.ModuleType('huggingface_hub')
    hub.snapshot_download = lambda **kwargs: str(tmp_path)
    monkeypatch.setitem(sys.modules, 'huggingface_hub', hub)
    write_index(tmp_path, '../outside')
    with pytest.raises(ValueError):
        namespace['get_model_path']('example/model', True)
    with pytest.raises(ValueError):
        namespace['get_model_path'](str(tmp_path))

    def unavailable(**kwargs):
        raise OSError('snapshot unavailable')

    hub.snapshot_download = unavailable
    with pytest.raises(RuntimeError, match='local model snapshot'):
        namespace['get_model_path']('example/model', True)
