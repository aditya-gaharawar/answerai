"""Redact credentials from JSON audit bodies, truncated bodies, and request URLs."""

import json
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

MASK = '********'
SENSITIVE = re.compile(
    r'password|secret|token|api[_-]?keys?|authorization|cookie|credential|private[_-]?key|^key$', re.I
)
# A capped audit body can be incomplete JSON. Never retain an unterminated secret string.
FRAGMENT = re.compile(
    r'"([^"\\]*(?:password|secret|token|api[_-]?keys?|authorization|cookie|credential|private[_-]?key)[^"\\]*|key)"\s*:\s*("(?:[^"\\]|\\.)*(?:"|$)|\[[^\]]*(?:\]|$)|[^,}\s]+)',
    re.I,
)


def redact_value(value):
    if isinstance(value, dict):
        return {key: MASK if SENSITIVE.search(key) else redact_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, str) and value.startswith(('https://', 'http://')):
        return redact_url(value)
    return value


def redact_body(body: str) -> str:
    try:
        return json.dumps(redact_value(json.loads(body)), ensure_ascii=False)
    except (ValueError, TypeError):
        return FRAGMENT.sub(lambda match: json.dumps(match.group(1)) + ': ' + json.dumps(MASK), body)


def redact_url(url: str) -> str:
    parts = urlsplit(url)
    host = parts.netloc.rsplit('@', 1)[-1]  # Credentials in URLs are never diagnostic data.
    query = urlencode(
        [
            (key, MASK if SENSITIVE.search(key) else value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
        ]
    )
    return urlunsplit((parts.scheme, host, parts.path, query, ''))
