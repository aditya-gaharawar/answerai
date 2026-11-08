"""Local-only JSON Schema contracts for the V2 execution path."""

import json
from functools import lru_cache

from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.exceptions import NoSuchResource


def _deny_remote_schema(uri):
    raise NoSuchResource(ref=uri)


@lru_cache(maxsize=128)
def _validator(encoded):
    schema = json.loads(encoded)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, registry=Registry(retrieve=_deny_remote_schema))


def validate_contract(value, schema):
    """Return a value-free repair message, never fetch a remote schema or echo secret inputs."""
    try:
        validator = _validator(json.dumps(schema, sort_keys=True))
        error = next(validator.iter_errors(value), None)
        if error:
            path = '.'.join(str(part) for part in error.absolute_path) or 'arguments'
            return f'{path}: does not satisfy the tool {error.validator} constraint.'
        json.dumps(value, allow_nan=False)
    except Exception:
        return 'Tool contract is invalid or contains an unavailable schema reference.'
    return None
