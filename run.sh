#!/usr/bin/env bash
# Install dependencies and (re)start the sales call trainer app.
# Restarts a currently-running instance instead of erroring out.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

VENV_DIR=".venv"
PID_FILE="data/app.pid"
PORT="${PORT:-5050}"

mkdir -p data

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtualenv in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Stop a previously-started instance, if any.
if [ -f "$PID_FILE" ]; then
    OLD_PID="$(cat "$PID_FILE")"
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Stopping existing instance (pid $OLD_PID)..."
        kill "$OLD_PID"
        for _ in $(seq 1 20); do
            kill -0 "$OLD_PID" 2>/dev/null || break
            sleep 0.2
        done
        kill -0 "$OLD_PID" 2>/dev/null && kill -9 "$OLD_PID" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
fi

# If something is still on the port, only stop it if it's clearly a previous
# instance of this app (matched by command line) -- never kill unrelated
# processes (e.g. macOS ControlCenter/AirPlay Receiver also uses port 5000).
EXISTING_PID="$(lsof -ti tcp:"$PORT" 2>/dev/null || true)"
if [ -n "$EXISTING_PID" ]; then
    if ps -p "$EXISTING_PID" -o command= | grep -q "app.py"; then
        echo "Stopping existing app instance on port $PORT (pid $EXISTING_PID)..."
        kill "$EXISTING_PID" 2>/dev/null || true
        sleep 1
        kill -0 "$EXISTING_PID" 2>/dev/null && kill -9 "$EXISTING_PID" 2>/dev/null || true
    else
        echo "Error: port $PORT is in use by another program (pid $EXISTING_PID: $(ps -p "$EXISTING_PID" -o comm=))." >&2
        echo "Set PORT to a different value, e.g.: PORT=5050 ./run.sh" >&2
        exit 1
    fi
fi

echo "Starting app on port $PORT..."
nohup python app.py > data/app.log 2>&1 &
echo $! > "$PID_FILE"

echo "App started (pid $(cat "$PID_FILE")). Logs: data/app.log"
echo "Open http://localhost:$PORT"
