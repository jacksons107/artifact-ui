# artifact-ui

An MCP server that lets Claude render interactive system architecture diagrams in a browser tab. Claude describes a system semantically (nodes, edges, groups, sequences); the tool handles all layout, colors, and interactivity automatically.

## What it does

Claude calls `render_artifact` with a `system_spec` payload describing a codebase or system. The tool opens a browser tab with five linked views of the same spec:

| View | Description |
|---|---|
| **Architecture** | Box-and-arrow graph. Click any node for a detail panel. Filter by node kind. |
| **Layers** | Horizontal swim-lanes (shown when groups with `kind: "layer"` exist). |
| **Sequences** | Swim-lane sequence diagrams with a dropdown selector (shown when sequences exist). |
| **Matrix** | Adjacency matrix — who calls whom at a glance. |
| **Components** | Filterable table of all nodes with all metadata. |

Two render modes:

- **`immediate`** — renders and returns right away.
- **`interactive`** — blocks until the user submits via `window.artifact.submit(payload)` in the browser, then returns that payload to Claude. Use for decisions.

## Spec schema

Claude provides a JSON payload. The LLM describes *what exists*; the renderer decides *how to show it*.

```json
{
  "title": "My System",
  "description": "optional one-liner",
  "nodes": [
    {
      "id": "api",
      "label": "API Server",
      "kind": "service",
      "description": "optional — shown in the detail panel on click",
      "tech": "Go",
      "owner": "platform-team",
      "status": "stable",
      "tags": ["critical"]
    }
  ],
  "edges": [
    {
      "from": "ui",
      "to": "api",
      "kind": "calls",
      "label": "REST",
      "async": false,
      "protocol": "HTTP"
    }
  ],
  "groups": [
    {
      "id": "backend",
      "label": "Backend",
      "kind": "layer",
      "members": ["api", "db"]
    }
  ],
  "sequences": [
    {
      "id": "login",
      "label": "Login Flow",
      "steps": [
        {"from": "client", "to": "api", "label": "POST /login"},
        {"from": "api", "to": "db", "label": "lookup user"}
      ]
    }
  ]
}
```

**Node kinds:** `service` `module` `class` `db` `queue` `external` `package` `file` `function`  
**Edge kinds:** `calls` `imports` `depends` `emits` `subscribes` `reads` `writes` `deploys` `owns`  
**Group kinds:** `layer` `package` `team` `domain` `deployment`

`async: true` on an edge renders it dashed. Node and edge kinds drive all colors — the LLM never specifies colors directly.

## Architecture

```
CLAUDE.md ──at session start──▶ Claude (LLM)
                                      │
                              tool call: get_example / render_artifact
                                      │
Claude Code  ──stdio JSON-RPC──▶  server.py
                                      │
                             ├── template_loader.py   builds tool description Claude sees
                             ├── system_spec_examples.py   reference specs for get_example
                             ├── system_spec.py        renderer (layout + all five views)
                             │     └── design_system.py   CSS tokens, shared HTML utilities
                             └── /tmp/artifact_ui/{id}.html
                                      │
                             webbrowser.open()
                                      │
                    ┌─────────────────┴──────────────────┐
                    ▼                                     ▼
         FastAPI :8765                          asyncio.Event (interactive mode)
         GET /artifact/{id} → serves file       POST /artifact/event → event.set()
                                                unblocks MCP tool call response
```

The MCP stdio server and FastAPI HTTP server share one asyncio event loop via `asyncio.gather()`. Interactive mode works because the browser's POST directly sets an `asyncio.Event` in the same process — no IPC needed.

### File structure

```
server.py                  MCP + FastAPI server, tool handlers
system_spec.py             renderer — layout, all five views, CSS, JS
system_spec_examples.py    three reference specs (sys_microservices, sys_event_driven, sys_monolith)
template_loader.py         builds the tool description Claude sees at session start
design_system.py           CSS design tokens and shared HTML utilities
```

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Add to `~/.claude.json` under `mcpServers`:

```json
"artifact-ui": {
  "command": "/path/to/artifact-ui/.venv/bin/python",
  "args": ["/path/to/artifact-ui/server.py"]
}
```

> **Important:** Do not run `server.py` manually as a background process. Claude Code manages the lifecycle — running it separately splits the HTTP server and MCP server into different processes, which breaks interactive mode.

After reconnecting (`/mcp` in Claude Code), always start a **new conversation** so Claude picks up the latest `CLAUDE.md` and tool descriptions.
