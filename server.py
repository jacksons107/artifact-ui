import asyncio
import atexit
import json
import os
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

from templates import render_chart, render_form, render_markdown, render_options, render_table
import compose as compose_module
import template_loader
from template_extractor import save_template, spawn_extractor_agent

BUILTIN_RENDERERS = {
    "options": render_options,
    "table": render_table,
    "markdown": render_markdown,
    "form": render_form,
    "chart": render_chart,
    "compose": lambda data: compose_module.render_compose(
        data, {**BUILTIN_RENDERERS, **template_loader.get_all_renderers()}.get
    ),
}

template_loader.load_learned_templates()

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
function __artifactSave() {{
  var blob = new Blob([document.documentElement.outerHTML], {{type: 'text/html'}});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = '{artifact_id}.html';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(a.href);
}}
</script>
<style>
#__artifact_save_btn {{
  position: fixed;
  bottom: 16px;
  right: 16px;
  z-index: 99999;
  background: #1e293b;
  color: #94a3b8;
  border: 1.5px solid #334155;
  border-radius: 8px;
  padding: 7px 14px;
  font-size: 0.75rem;
  font-family: system-ui, sans-serif;
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.15s, border-color 0.15s, color 0.15s;
}}
#__artifact_save_btn:hover {{
  opacity: 1;
  border-color: #3b82f6;
  color: #e2e8f0;
}}
</style>
<button id="__artifact_save_btn" onclick="__artifactSave()">⬇ Save</button>"""
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

LEARN_TEMPLATE_DESCRIPTION = """\
Save a reusable template extracted from raw HTML you just generated.

Call this immediately after any render_artifact call that used the raw 'html' field.
Analyze the HTML you generated, identify the repeating UI pattern, parameterize it, \
and provide a Python render function so future similar UIs can use template+data instead of raw HTML.

Rules for the 'code' field:
- Signature: def render_{name}(data: dict) -> str:
- Returns a complete HTML document (DOCTYPE through </html>)
- Tailwind CDN only: <script src="https://cdn.tailwindcss.com"></script>
- Dark slate theme (bg-slate-900, slate color palette)
- Must contain </body> tag
- Escape all literal JS/CSS braces as {{ and }}
- Use data.get() with sensible defaults
- Only stdlib imports (json, html) — no third-party Python packages
"""


@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    template_loader.load_learned_templates()
    return [
        types.Tool(
            name="learn_template",
            description=LEARN_TEMPLATE_DESCRIPTION,
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Short snake_case identifier, e.g. 'metric_cards', 'status_timeline'.",
                    },
                    "description": {
                        "type": "string",
                        "description": "One sentence: what this UI pattern is and when to use it.",
                    },
                    "schema_example": {
                        "type": "object",
                        "description": "Minimal JSON example showing the data structure the function expects.",
                    },
                    "code": {
                        "type": "string",
                        "description": "The complete Python render function as a string.",
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "1-2 sentences: why this pattern is worth a reusable template and what makes it general rather than one-off.",
                    },
                },
                "required": ["name", "description", "schema_example", "code", "reasoning"],
            },
        ),
        types.Tool(
            name="render_artifact",
            description=template_loader.build_tool_description(),
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
                    "mode": {
                        "type": "string",
                        "enum": ["immediate", "interactive"],
                        "description": "'immediate' returns at once. 'interactive' blocks until window.artifact.submit(payload) is called.",
                    },
                    "template": template_loader.build_template_schema_property(),
                    "data": {
                        "type": "object",
                        "description": "JSON data for the chosen template. See tool description for schemas.",
                    },
                    "html": {
                        "type": "string",
                        "description": "Full HTML to render. Only required when 'template' is not used.",
                    },
                },
                "required": ["artifact_id", "title", "mode"],
            },
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    if name == "learn_template":
        ok, reason = save_template(
            name=arguments["name"],
            description=arguments["description"],
            schema_example=arguments.get("schema_example", {}),
            code=arguments["code"],
            reasoning=arguments.get("reasoning", ""),
        )
        if ok:
            result = {"status": "saved", "name": arguments["name"]}
        else:
            result = {"status": "rejected", "reason": reason}
        return [types.TextContent(type="text", text=json.dumps(result))]

    if name != "render_artifact":
        raise ValueError(f"Unknown tool: {name}")

    artifact_id = arguments["artifact_id"]
    mode = arguments["mode"]
    template = arguments.get("template")

    if template:
        all_renderers = {**BUILTIN_RENDERERS, **template_loader.get_all_renderers()}
        renderer = all_renderers.get(template)
        if renderer is None:
            raise ValueError(f"Unknown template: {template!r}. Valid: {list(all_renderers)}")
        html = renderer(arguments.get("data") or {})
    else:
        html = arguments.get("html")
        if not html:
            raise ValueError("Either 'template'+'data' or 'html' must be provided.")
        asyncio.create_task(spawn_extractor_agent(html))

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
    pid_file = ARTIFACT_DIR / "server.pid"
    pid_file.write_text(str(os.getpid()))
    atexit.register(lambda: pid_file.unlink(missing_ok=True))

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
