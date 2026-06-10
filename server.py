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

import system_spec as system_spec_module
import template_loader
import system_spec_examples

BUILTIN_RENDERERS = {
    "system_spec": system_spec_module.render_system_spec,
}

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
  background: #FAF9F5;
  color: #87867F;
  border: 1.5px solid #D1CFC5;
  border-radius: 8px;
  padding: 7px 14px;
  font-size: 0.75rem;
  font-family: ui-monospace, 'SF Mono', Menlo, monospace;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.15s, border-color 0.15s, color 0.15s;
}}
#__artifact_save_btn:hover {{
  opacity: 1;
  border-color: #D97757;
  color: #141413;
}}
</style>
<button id="__artifact_save_btn" onclick="__artifactSave()">⬇ Save</button>"""
    if "</body>" in html:
        return html.replace("</body>", snippet + "\n</body>", 1)
    return html + "\n" + snippet


# ── FastAPI routes ─────────────────────────────────────────────────────────────

@app.get("/artifact/{artifact_id}")
async def serve_artifact(artifact_id: str):
    path = ARTIFACT_DIR / artifact_id / f"{artifact_id}.html"
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


# ── Artifact persistence helpers ───────────────────────────────────────────────

def spec_path_for(html_path: Path) -> Path:
    """Sibling spec path for an artifact html path: foo/index.html -> foo/index.spec.json"""
    return html_path.with_suffix("").with_suffix(".spec.json")


# ── MCP tools ─────────────────────────────────────────────────────────────────

@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    example_names = list(system_spec_examples.EXAMPLES.keys())
    return [
        types.Tool(
            name="get_example",
            description=(
                "Return the full JSON payload for a named system_spec example. "
                "ALWAYS call this before constructing a spec — inspect the example to understand "
                "the correct shape, then adapt it for your system. "
                "Available: " + ", ".join(example_names) + "."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Example name: " + ", ".join(example_names) + ".",
                        "enum": example_names,
                    }
                },
                "required": ["name"],
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
                        "description": "The system_spec JSON payload. See tool description for schema.",
                    },
                    "path": {
                        "type": "string",
                        "description": (
                            "Optional absolute path to an .html file. If set, the rendered HTML "
                            "(and the spec as a sibling '<name>.spec.json') is also written there, "
                            "in addition to the usual /tmp preview. Use this to create or update a "
                            "persistent artifact that lives in the project (e.g. as living "
                            "documentation), and pass the same path again on later renders to "
                            "update it in place."
                        ),
                    },
                },
                "required": ["artifact_id", "title", "mode", "template", "data"],
            },
        ),
        types.Tool(
            name="save_artifact",
            description=(
                "Promote an already-rendered ephemeral artifact to a persistent location. "
                "Copies the artifact's HTML and spec JSON to 'path' (and a sibling "
                "'<name>.spec.json'), creating directories as needed. Use this after "
                "render_artifact when the user wants to keep a previously-generated artifact "
                "as a file in the project."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "artifact_id": {
                        "type": "string",
                        "description": "The artifact_id used in a previous render_artifact call.",
                    },
                    "path": {
                        "type": "string",
                        "description": "Absolute destination path for the .html file.",
                    },
                },
                "required": ["artifact_id", "path"],
            },
        ),
        types.Tool(
            name="get_artifact_spec",
            description=(
                "Read back the spec JSON for a persisted artifact, given the path to its .html "
                "file (looks for the sibling '<name>.spec.json'). Use this to load an existing "
                "persistent artifact's spec before editing it and re-rendering with "
                "render_artifact(path=...) to update it in place."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the artifact's .html file.",
                    },
                },
                "required": ["path"],
            },
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    if name == "get_example":
        example_name = arguments.get("name", "")
        example = system_spec_examples.EXAMPLES.get(example_name)
        if example is None:
            result = {"error": f"Unknown example: {example_name!r}", "available": list(system_spec_examples.EXAMPLES.keys())}
        else:
            result = example
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    if name == "save_artifact":
        artifact_id = arguments["artifact_id"]
        dest = Path(arguments["path"])
        src_dir = ARTIFACT_DIR / artifact_id
        src_html = src_dir / f"{artifact_id}.html"
        src_spec = src_dir / f"{artifact_id}.spec.json"
        if not src_html.exists():
            return [types.TextContent(type="text", text=json.dumps(
                {"error": f"No ephemeral artifact found for artifact_id={artifact_id!r}. Render it first."}
            ))]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest_spec = spec_path_for(dest)
        dest.write_text(src_html.read_text(encoding="utf-8"), encoding="utf-8")
        if src_spec.exists():
            dest_spec.write_text(src_spec.read_text(encoding="utf-8"), encoding="utf-8")
        return [types.TextContent(type="text", text=json.dumps(
            {"status": "saved", "path": str(dest), "spec_path": str(dest_spec)}
        ))]

    if name == "get_artifact_spec":
        html_path = Path(arguments["path"])
        spec_path = spec_path_for(html_path)
        if not spec_path.exists():
            return [types.TextContent(type="text", text=json.dumps(
                {"error": f"No spec found at {spec_path}."}
            ))]
        return [types.TextContent(type="text", text=spec_path.read_text(encoding="utf-8"))]

    if name != "render_artifact":
        raise ValueError(f"Unknown tool: {name}")

    artifact_id = arguments["artifact_id"]
    mode = arguments["mode"]
    template = arguments.get("template", "system_spec")
    data = arguments.get("data") or {}

    renderer = BUILTIN_RENDERERS.get(template)
    if renderer is None:
        raise ValueError(f"Unknown template: {template!r}. Valid: {list(BUILTIN_RENDERERS)}")
    rendered_html = renderer(data)

    html = inject_runtime(rendered_html, artifact_id)
    artifact_dir = ARTIFACT_DIR / artifact_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / f"{artifact_id}.html").write_text(html, encoding="utf-8")
    (artifact_dir / f"{artifact_id}.spec.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    persist_path = arguments.get("path")
    if persist_path:
        dest = Path(persist_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(rendered_html, encoding="utf-8")
        spec_path_for(dest).write_text(json.dumps(data, indent=2), encoding="utf-8")

    session: dict[str, Any] = {"event": asyncio.Event(), "result": None}
    artifact_sessions[artifact_id] = session

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
