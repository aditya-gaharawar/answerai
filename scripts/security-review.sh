#!/usr/bin/env bash
# Local source/history/dependency review; never attacks a deployed service.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 2
out="${1:-.security-review}"
mkdir -p "$out" || exit 2
out="$(cd "$out" && pwd)"
for executable in npm pip-audit bandit semgrep gitleaks uv git; do
  command -v "$executable" >/dev/null || {
    echo "Missing $executable. Install scanner tools in an isolated environment and use Node 22." >&2
    exit 2
  }
done
status=0
run_scan() {
  "$@" || status=1
}
{
  date -u +'%Y-%m-%dT%H:%M:%SZ'
  git rev-parse HEAD
  git rev-parse --is-shallow-repository
  npm --version
  pip-audit --version
  bandit --version
  SEMGREP_SEND_METRICS=off semgrep --version
  gitleaks version
  uv --version
} > "$out/provenance.txt" 2>&1
run_scan bash scripts/security-audit.sh "$out"
SEMGREP_SEND_METRICS=off run_scan semgrep scan \
  --config p/security-audit --config p/owasp-top-ten --config p/secrets \
  --metrics off --disable-version-check --timeout 20 --error --json \
  --output "$out/semgrep.json" . > "$out/semgrep.log" 2>&1
run_scan gitleaks git --redact=100 --no-banner --log-opts='--all' \
  --report-format json --report-path "$out/git-secrets.json" . > "$out/git-secrets.log" 2>&1
if uv export --locked --no-dev --no-emit-project --no-hashes --format requirements-txt \
  --output-file "$out/locked-requirements.txt" > "$out/export.log" 2>&1; then
  run_scan pip-audit -r "$out/locked-requirements.txt" --no-deps --disable-pip \
    -f json -o "$out/locked-python.json" > "$out/locked-python.log" 2>&1
else
  status=1
fi
if uv pip compile backend/requirements.txt --python-version 3.11 --quiet \
  --output-file "$out/resolved-requirements.txt" > "$out/resolve.log" 2>&1; then
  run_scan pip-audit -r "$out/resolved-requirements.txt" --no-deps --disable-pip \
    -f json -o "$out/resolved-python.json" > "$out/resolved-python.log" 2>&1
else
  status=1
fi
printf 'Review reports: %s\nExit 1 means findings or scan errors; inspect JSON and logs.\n' "$out"
exit "$status"
