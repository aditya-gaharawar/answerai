"""Normalize native provider arguments before any tool can execute."""

import ast
import json


def parse_tool_arguments(arguments: object) -> dict:
    if arguments is None or (isinstance(arguments, str) and not arguments.strip()):
        return {}
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except ValueError:
            # Preserve compatibility with providers emitting Python-style objects.
            arguments = ast.literal_eval(arguments)
    if not isinstance(arguments, dict) or any(not isinstance(key, str) for key in arguments):
        raise ValueError('Tool arguments must be a JSON object with string keys.')
    # literal_eval can produce sets, bytes, or non-finite floats that cannot be
    # recorded in a provider-compatible JSON tool call.
    json.dumps(arguments, allow_nan=False)
    return dict(arguments)
