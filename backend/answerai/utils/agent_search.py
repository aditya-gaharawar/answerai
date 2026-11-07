"""Bounded lexical retrieval and URL normalization for agent search tools."""

import math
import heapq
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

MAX_CHUNK_CHARS = 1600
MAX_FILE_CHARS = 2_000_000
MAX_FILES = 100
MAX_CANDIDATES = 20000
TRACKING_KEYS = {'fbclid', 'gclid', 'msclkid'}
TOKEN_RE = re.compile(r'[^\W_]+', re.UNICODE)


def canonical_search_url(url):
    try:
        parts = urlsplit(str(url or '').strip())
        if parts.scheme.lower() not in {'http', 'https'} or not parts.hostname or parts.username:
            return None
        hostname = parts.hostname.encode('idna').decode().lower()
        if ':' in hostname:
            hostname = f'[{hostname}]'
        port = parts.port
        if port and port != (443 if parts.scheme.lower() == 'https' else 80):
            hostname += f':{port}'
        query = [
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if not key.lower().startswith('utm_') and key.lower() not in TRACKING_KEYS
        ]
        return urlunsplit((parts.scheme.lower(), hostname, parts.path or '/', urlencode(sorted(query)), ''))
    except (ValueError, UnicodeError):
        return None


def unique_web_results(results, count):
    """Deduplicate source URLs without removing meaningful query parameters or changing provider order."""
    if count <= 0:
        return []
    output = []
    seen = set()
    for result in results or []:
        key = canonical_search_url(result.link)
        if not key or key in seen:
            continue
        seen.add(key)
        output.append({'title': result.title, 'link': result.link, 'snippet': result.snippet})
        if len(output) >= count:
            break
    return output


def lexical_file_search(accessible, query, count=5):
    """Search only caller-authorized file models; cap work, result size and repeated passages."""
    terms = list(dict.fromkeys(TOKEN_RE.findall(query.casefold())))[:24]
    if not terms:
        return []
    candidates = []
    capacity = max(1, min(count, 20)) * 3
    scanned = 0
    phrase = query.strip().casefold()
    for file_index, (_, file) in enumerate(accessible[:MAX_FILES]):
        content = (file.data or {}).get('content')
        if not isinstance(content, str) or not content:
            continue
        content = content[:MAX_FILE_CHARS]
        for offset in range(0, len(content), MAX_CHUNK_CHARS - 200):
            if scanned >= MAX_CANDIDATES:
                break
            scanned += 1
            chunk = content[offset : offset + MAX_CHUNK_CHARS]
            folded = chunk.casefold()
            hits = [term for term in terms if term in folded]
            if not hits:
                continue
            score = len(hits) / len(terms)
            score += sum(math.log1p(folded.count(term)) for term in hits) / 100
            if phrase and phrase in folded:
                score += 1
            entry = (score, -file_index, -offset, str(file.id), chunk, file.filename)
            if len(candidates) < capacity:
                heapq.heappush(candidates, entry)
            else:
                heapq.heappushpop(candidates, entry)
        if scanned >= MAX_CANDIDATES:
            break
    candidates.sort(key=lambda row: (-row[0], row[3], -row[2]))
    output = []
    seen = set()
    for score, _, negative_offset, file_id, chunk, filename in candidates:
        fingerprint = ' '.join(chunk.split())
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        output.append(
            {
                'content': chunk,
                'source': filename,
                'file_id': file_id,
                'offset': -negative_offset,
                'retrieval': 'lexical',
                'score': round(score, 4),
            }
        )
        if len(output) >= max(1, min(count, 20)):
            break
    return output
