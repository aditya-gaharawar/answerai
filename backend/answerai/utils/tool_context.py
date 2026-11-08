"""Promote relevant authorized tools without hiding the discovery fallback."""

import re

INTENTS = (
    (r'\b(search|research|latest|news|sources|web)\b', ('research_web', 'search_web', 'fetch_url')),
    (r'https?://', ('fetch_url',)),
    (r'\b(file|pdf|document|spreadsheet|attached|upload)\b', ('list_chat_files', 'query_chat_files', 'view_file')),
    (r'\b(image|picture|illustration|draw|logo)\b', ('generate_image', 'edit_image')),
    (r'\b(code|python|javascript|calculate|chart|analyze|analyse)\b', ('execute_code',)),
    (r'\b(remember|memory|recall)\b', ('search_memories',)),
)


def contextual_tools(form_data, tools, limit=8):
    # User text selects relevance only. Authorization and discovery remain authoritative.
    messages = form_data.get('messages') or []
    latest = next((message for message in reversed(messages) if message.get('role') == 'user'), {})
    content = latest.get('content', '')
    if isinstance(content, list):
        content = ' '.join(str(part.get('text', '')) for part in content if isinstance(part, dict))
    text = str(content)[:8000].casefold()
    names = []
    if form_data.get('files'):
        names.extend(('list_chat_files', 'query_chat_files', 'view_file'))
    for pattern, candidates in INTENTS:
        if re.search(pattern, text):
            names.extend(candidates)
    return list(dict.fromkeys(name for name in names if name in tools))[:limit]
