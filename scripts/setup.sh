#!/usr/bin/env bash

set -euo pipefail
cd "$(dirname "$0")/.."

case "$(uname -s)" in
  Darwin) REQUIREMENTS="requirements-macos.txt" ;;
  Linux) REQUIREMENTS="requirements-linux.txt" ;;
  *)
    echo "Unsupported OS: $(uname -s) -- this script supports macOS and Linux only." >&2
    echo "On Windows, run scripts\\setup.bat instead." >&2
    exit 1
    ;;
esac

echo "==> Installing JS dependencies"
npm install

command -v python3 >/dev/null 2>&1 || {
  echo "python3 not found on PATH. Install Python 3.11+ and re-run this script." >&2
  exit 1
}

PY_VERSION="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
PY_MAJOR="${PY_VERSION%.*}"
PY_MINOR="${PY_VERSION#*.}"
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
  echo "Warning: found Python $PY_VERSION, but this project needs 3.11+. Continuing anyway." >&2
fi

if [ -d .venv ]; then
  echo "==> Reusing existing .venv"
else
  echo "==> Creating Python virtual environment (.venv)"
  python3 -m venv .venv
fi

echo "==> Installing Python dependencies from $REQUIREMENTS"
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r "$REQUIREMENTS"

mkdir -p data

if [ -f data/global.db ]; then
  echo "==> data/global.db already exists -- skipping global_init.py"
  echo "    (it deletes and recreates global.db, wiping devices/scouts/schedule/settings;"
  echo "    delete data/global.db yourself first if you actually want that reset)"
else
  echo "==> Bootstrapping data/global.db"
  ./.venv/bin/python3 server/global_init.py
fi

echo "==> Building per-game-year databases from games/*/*.json"

./.venv/bin/python3 server/data_init.py

echo
echo "Setup complete."
echo "Run 'npm run dev:web' to start the Vite dev server + FastAPI backend together."

if [ "$(uname -s)" = "Linux" ]; then
  echo
  echo "Note: the BLE bridge (server/bluetooth_server.py) needs raw Bluetooth access"
  echo "on Linux. Grant it once with:"
  echo "    sudo setcap cap_net_raw,cap_net_admin+eip \$(readlink -f .venv/bin/python3)"
fi
