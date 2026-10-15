"""Validate sharded model indexes before optional ML runtimes load their files."""

import json
import ntpath
import os
import stat
from pathlib import Path, PurePosixPath

MAX_INDEX_BYTES = 16 * 1024 * 1024


def validate_model_snapshot(model_path: str) -> None:
    root = Path(model_path).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('A model snapshot must be a directory')
    allowed_roots = [root]
    # HF snapshots use symlinks to content-addressed blobs in the same repo cache.
    if root.parent.name == 'snapshots' and root.parent.parent.name.startswith('models--'):
        blobs = root.parent.parent / 'blobs'
        if blobs.is_dir() and not blobs.is_symlink():
            allowed_roots.append(blobs.resolve())

    def checked_file(path: Path) -> Path:
        resolved = path.resolve(strict=True)
        if not any(resolved.is_relative_to(allowed) for allowed in allowed_roots):
            raise ValueError('Model index or shard escapes the model snapshot')
        if not stat.S_ISREG(resolved.stat().st_mode):
            raise ValueError('Model indexes and shards must be regular files')
        return resolved

    for index in root.rglob('*.index.json'):
        checked_file(index)
        weight_map = _read_weight_map(index)
        for shard in set(weight_map.values()):
            _validate_shard_name(shard)
            checked_file(index.parent / shard)


def _read_weight_map(index: Path) -> dict:
    # Nonblocking open + fstat also reject a FIFO swapped in after the path check.
    descriptor = os.open(index, os.O_RDONLY | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(descriptor, 'rb') as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError('Model indexes must be regular files')
        raw = handle.read(MAX_INDEX_BYTES + 1)
    if len(raw) > MAX_INDEX_BYTES:
        raise ValueError('Model shard index is too large')
    metadata = json.loads(raw)
    if not isinstance(metadata, dict):
        raise ValueError('Model shard index must be an object')
    weight_map = metadata.get('weight_map')
    if weight_map is None:
        return {}
    if not isinstance(weight_map, dict):
        raise ValueError('Model weight_map must be an object')
    if not all(isinstance(value, str) for value in weight_map.values()):
        raise ValueError('Model shard filenames must be strings')
    return weight_map


def _validate_shard_name(shard: str) -> None:
    if not isinstance(shard, str) or not shard or '\\' in shard or '\x00' in shard:
        raise ValueError('Invalid model shard filename')
    relative = PurePosixPath(shard)
    if relative.is_absolute() or ntpath.splitdrive(shard)[0] or '..' in relative.parts:
        raise ValueError('Model shard paths must stay inside the snapshot')
