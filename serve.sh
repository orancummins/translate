#!/usr/bin/env bash
# The always-on server (what the LaunchDaemon on the dev server runs; see dev-server-page/README.md "The run.sh contract").
# Foreground, binds $HOST:$PORT (127.0.0.1 behind nginx), reclaims its port, honours SKIP_PIP_INSTALL=1.
# KEY_MODE defaults to "visitor": every visitor pastes their own Claude and ElevenLabs keys, which stay in their browser;
# this server never stores a key and never uses one from .env. Run ./run.sh on your own machine instead.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-5056}"
export KEY_MODE="${KEY_MODE:-visitor}" SERVE=1 FLASK_DEBUG=0

if [ ! -d .venv ]; then python3 -m venv .venv; fi
if [ "${SKIP_PIP_INSTALL:-0}" != "1" ]; then .venv/bin/pip install --quiet --upgrade pip && .venv/bin/pip install --quiet -r requirements.txt; fi
mkdir -p data

# reclaim the port from a previous instance of this app (never kill an unrelated program)
PID_ON_PORT="$(lsof -ti tcp:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
if [ -n "$PID_ON_PORT" ]; then
  if ps -p "$PID_ON_PORT" -o command= | grep -q "app.py"; then kill "$PID_ON_PORT" 2>/dev/null || true; sleep 1; else
    echo "port $PORT is used by another program (pid $PID_ON_PORT)" >&2; exit 1; fi
fi

export HOST PORT
exec .venv/bin/python app.py
