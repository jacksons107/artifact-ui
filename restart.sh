#!/usr/bin/env bash
# Kill any running artifact-ui server instances (orphans from previous Claude sessions).
# Claude Code manages server startup automatically via the MCP config — do NOT start
# a background process here, as that splits the HTTP server and MCP server into separate
# processes that cannot share in-memory session state (breaking interactive mode).
set -euo pipefail

PORT=8765
KILLED=0

# Kill any process holding the port
PIDS=$(lsof -ti ":$PORT" 2>/dev/null || true)
if [ -n "$PIDS" ]; then
  echo $PIDS | xargs kill 2>/dev/null && echo "Killed process(es) on port $PORT: $PIDS." || true
  KILLED=1
fi

# Also kill any stray server.py processes from this project
STRAY=$(pgrep -f "artifact-ui/server.py" 2>/dev/null || true)
if [ -n "$STRAY" ]; then
  echo $STRAY | xargs kill 2>/dev/null && echo "Killed stray server.py (PID $STRAY)." || true
  KILLED=1
fi

[ $KILLED -eq 0 ] && echo "No running artifact-ui servers found." || true
echo "Done. Reconnect via /mcp to start a fresh server."
