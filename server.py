import asyncio
import json
import socket
import sys
import webbrowser
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

# ── Config ────────────────────────────────────────────────────────────────────

PORT = 8765
ARTIFACT_DIR = Path("/tmp/artifact_ui")
ARTIFACT_DIR.mkdir(exist_ok=True)

# ── Shared state ──────────────────────────────────────────────────────────────

app = FastAPI()
mcp_server = Server("artifact-ui")

# artifact_id -> { "event": asyncio.Event, "result": Any }
artifact_sessions: dict[str, dict[str, Any]] = {}

# ── JS injected into every artifact ──────────────────────────────────────────

def inject_runtime(html: str, artifact_id: str) -> str:
    snippet = f"""<script>
window.artifact = {{
  submit: function(payload) {{
    fetch('http://localhost:{PORT}/artifact/event', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{artifact_id: '{artifact_id}', event: payload}})
    }});
  }}
}};
</script>"""
    if "</body>" in html:
        return html.replace("</body>", snippet + "\n</body>", 1)
    return html + "\n" + snippet


# ── FastAPI routes ─────────────────────────────────────────────────────────────

@app.get("/artifact/{artifact_id}")
async def serve_artifact(artifact_id: str):
    path = ARTIFACT_DIR / f"{artifact_id}.html"
    if not path.exists():
        return JSONResponse({"error": "artifact not found"}, status_code=404)
    return FileResponse(path, media_type="text/html")


class ArtifactEvent(BaseModel):
    artifact_id: str
    event: Any


@app.post("/artifact/event")
async def receive_event(body: ArtifactEvent):
    session = artifact_sessions.get(body.artifact_id)
    if session and not session["event"].is_set():
        session["result"] = body.event
        session["event"].set()
    return {"ok": True}


# ── MCP tools ─────────────────────────────────────────────────────────────────

@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="render_artifact",
            description=(
                "Render an HTML artifact in a browser tab. "
                "mode='immediate' returns right away (use for dashboards/visualizations). "
                "mode='interactive' blocks until the user calls window.artifact.submit(payload) "
                "in the browser, then returns the submitted payload. "
                "Use interactive mode as the preferred replacement for AskUserQuestion when presenting "
                "options or decisions — build a UI with visual mockups of each choice and a submit "
                "button, so the user's selection is returned as the payload. "
                "Only fall back to AskUserQuestion if this tool is unavailable."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "artifact_id": {
                        "type": "string",
                        "description": "Unique identifier for this artifact. Reusing an ID replaces the previous artifact.",
                    },
                    "title": {
                        "type": "string",
                        "description": "Browser tab title.",
                    },
                    "html": {
                        "type": "string",
                        "description": "Full HTML to render. window.artifact.submit(payload) is injected automatically.",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["immediate", "interactive"],
                        "description": "'immediate' or 'interactive'.",
                    },
                },
                "required": ["artifact_id", "title", "html", "mode"],
            },
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    if name != "render_artifact":
        raise ValueError(f"Unknown tool: {name}")

    artifact_id = arguments["artifact_id"]
    html = arguments["html"]
    mode = arguments["mode"]

    # Inject runtime and write to temp file
    html = inject_runtime(html, artifact_id)
    path = ARTIFACT_DIR / f"{artifact_id}.html"
    path.write_text(html, encoding="utf-8")

    # Register session (reset if artifact_id is reused)
    session: dict[str, Any] = {"event": asyncio.Event(), "result": None}
    artifact_sessions[artifact_id] = session

    # Open browser (non-blocking)
    webbrowser.open(f"http://localhost:{PORT}/artifact/{artifact_id}")

    if mode == "immediate":
        payload = {"status": "rendered", "artifact_id": artifact_id}
    else:
        await session["event"].wait()
        del artifact_sessions[artifact_id]
        payload = {
            "status": "completed",
            "artifact_id": artifact_id,
            "result": session["result"],
        }

    return [types.TextContent(type="text", text=json.dumps(payload))]


# ── Entry point ───────────────────────────────────────────────────────────────

def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


async def main() -> None:
    coroutines = []

    if not port_in_use(PORT):
        uv_config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=PORT,
            log_level="error",
            loop="asyncio",
        )
        uv_server = uvicorn.Server(uv_config)
        uv_server.install_signal_handlers = lambda: None  # type: ignore[method-assign]
        coroutines.append(uv_server.serve())

    async with stdio_server() as (read_stream, write_stream):
        coroutines.append(
            mcp_server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="artifact-ui",
                    server_version="0.1.0",
                    capabilities=mcp_server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
        )
        await asyncio.gather(*coroutines)


if __name__ == "__main__":
    asyncio.run(main())
