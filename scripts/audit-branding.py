"""Audit all tracked and new source files for upstream branding outside legal notices."""

from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BRAND = re.compile(r'open[-_\s]?web[-_\s]?ui|\bowui\b|\b(?-i:WebUI)\b', re.I)
LEGAL_FILES = {'LICENSE', 'LICENSE_HISTORY', 'LICENSE_NOTICE', 'CONTRIBUTOR_LICENSE_AGREEMENT', 'BRANDING.md'}


def without_notices(text):
    text = re.sub(r'<!--\s*LICENSE covers.*?-->', '', text, flags=re.S)
    text = re.sub(r'(?m)^[ \t]*(?:#|//) LICENSE covers[^\n]*(?:\n[ \t]*(?:#|//)[^\n]*)*', '', text)
    text = re.sub(r'(?mi)^.*(?:copyright|Timothy Jaeryang Baek|tim@openwebui\.com).*$', '', text)
    return text


files = (
    subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT)
    .decode()
    .split('\0')
)
failures = []
checked = 0
for name in sorted(set(files)):
    # Archived historical checkouts are evidence, not current application source.
    if not name or name.startswith('internal-workspace/') or name == 'scripts/audit-branding.py':
        continue
    path = ROOT / name
    if not path.is_file() or path.name in LEGAL_FILES:
        continue
    if BRAND.search(name):
        failures.append(f'{name}: upstream identifier in path')
    try:
        text = path.read_text()
    except UnicodeError:
        continue
    checked += 1
    if name == 'README.md':
        text = text.split('## License and attribution')[0]
    if name == 'src/lib/components/chat/Settings/About.svelte':
        # Copyright owner remains upstream; this is required attribution.
        text = text.replace('Open WebUI Inc.', '')
    if name == 'crypto/encryption/src/lib.rs':
        # The verified upstream crypto artifact uses this exact protocol domain
        # separator. It is not displayed branding; changing it changes identity keys.
        text = text.replace('Open WebUI temporary chat identity v1', '[encryption identity domain]')
    text = without_notices(text)
    for line, value in enumerate(text.splitlines(), 1):
        if BRAND.search(value):
            failures.append(f'{name}:{line}: {value.strip()[:160]}')
if failures:
    print('\n'.join(failures))
    sys.exit(1)
print(f'Branding audit passed: {checked} text files; only retained legal notices contain upstream branding.')
