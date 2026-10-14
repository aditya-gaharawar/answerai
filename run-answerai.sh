#!/usr/bin/env bash
# Install, build, and serve ANSWERAI from any working directory.
set -Eeuo pipefail
trap 'echo "ANSWERAI setup failed at line ${LINENO}. Fix the error above and rerun this script." >&2' ERR

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$ROOT_DIR"

case "${1:-}" in
  -h|--help)
    cat <<'HELP'
Usage: ./run-answerai.sh [--skip-setup]

Default: create .venv, install all dependencies, build the frontend, start the server.
--skip-setup: start an already installed and built checkout.

Requires Python 3.11 or 3.12 and Node.js 22.17 or later in the 22.x series with npm for setup.
Optional: copy .env.example to .env and edit SMTP/provider settings.
Environment variables override .env. HOST defaults to 0.0.0.0; PORT to 8080.
Ctrl+C stops the server. Data and the generated signing key persist in backend/.
HELP
    exit 0 ;;
  ''|--skip-setup) ;;
  *) echo "Unknown option: $1. Use --help." >&2; exit 2 ;;
esac
[[ $# -le 1 ]] || { echo "Use --help for supported options." >&2; exit 2; }

if [[ "${1:-}" != --skip-setup ]]; then
  PYTHON_BIN="${ANSWERAI_PYTHON:-}"
  if [[ -z "$PYTHON_BIN" ]]; then
    for candidate in python3.11 python3.12 python3 python; do
      if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; assert (3,11) <= sys.version_info[:2] < (3,13)' 2>/dev/null; then
        PYTHON_BIN="$candidate"
        break
      fi
    done
  fi
  [[ -n "$PYTHON_BIN" ]] || { echo "Install Python 3.11 or 3.12 first." >&2; exit 1; }
  "$PYTHON_BIN" -c 'import sys; assert (3,11) <= sys.version_info[:2] < (3,13), "Python 3.11 or 3.12 is required"'
  command -v node >/dev/null 2>&1 || { echo "Install Node.js 22 first." >&2; exit 1; }
  command -v npm >/dev/null 2>&1 || { echo "Install npm first." >&2; exit 1; }
  node -e 'const [major, minor] = process.versions.node.split(".").map(Number); if (major !== 22 || minor < 17) { console.error("Node.js 22.17 or later in the 22.x series is required."); process.exit(1); }'

  if [[ ! -x .venv/bin/python ]]; then
    echo "Creating Python virtual environment..."
    "$PYTHON_BIN" -m venv .venv
  fi
  .venv/bin/python -c 'import sys; assert (3,11) <= sys.version_info[:2] < (3,13), "Recreate .venv using Python 3.11 or 3.12"'
  echo "Installing backend dependencies..."
  .venv/bin/python -m pip install -r backend/requirements.txt
  echo "Installing frontend dependencies..."
  CYPRESS_INSTALL_BINARY=0 npm ci --include=dev
  echo "Building frontend (allow several GB of available memory)..."
  NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=8192}" npm run build
fi

[[ -x .venv/bin/python && -f build/index.html ]] || {
  echo "Setup is incomplete. Run ./run-answerai.sh without --skip-setup." >&2
  exit 1
}
# Use dotenv's parser, not shell sourcing, so SMTP passwords and quoted values
# follow the same rules as the application. Existing exports take precedence.
export PATH="$ROOT_DIR/.venv/bin:$PATH"
exec .venv/bin/python - "$ROOT_DIR" <<'PY'
import os
import sys
from dotenv import load_dotenv

root = sys.argv[1]
load_dotenv(os.path.join(root, '.env'), override=False)
port = os.environ.get('PORT', '8080')
print(f'Starting ANSWERAI at http://localhost:{port} (Ctrl+C to stop).', flush=True)
os.execv('/bin/bash', ['bash', os.path.join(root, 'backend', 'start.sh')])
PY
