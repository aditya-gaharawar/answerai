#!/usr/bin/env bash
# Read-only scans. Reports include advisory metadata; never upload them automatically.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 2
out="${1:-.security-audit}"
mkdir -p "$out" || exit 2
for executable in npm pip-audit bandit; do
  command -v "$executable" >/dev/null || {
    echo "Missing $executable. Install npm and isolated pip-audit/bandit tooling first." >&2
    exit 2
  }
done
status=0
npm audit --json > "$out/npm.json" 2> "$out/npm.log" || status=1
pip-audit -r backend/requirements.txt --no-deps --disable-pip -f json -o "$out/python.json" > "$out/python.log" 2>&1 || status=1
bandit -r backend/answerai -f json -o "$out/bandit.json" > "$out/bandit.log" 2>&1 || status=1
printf 'Reports written to %s. Exit 1 indicates findings or scan errors; review logs and exposure before acting.\n' "$out"
exit "$status"
