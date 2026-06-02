#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="/tmp/artifact_ui/server.pid"

if [ -f "$PID_FILE" ]; then
  kill "$(cat "$PID_FILE")" 2>/dev/null && echo "Stopped server." || echo "Process already gone."
  rm -f "$PID_FILE"
else
  echo "No PID file found — server may not be running."
fi

"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/server.py" &
echo "Started server (PID $!)."
