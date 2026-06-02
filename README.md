# artifact-ui

An MCP server that lets Claude render HTML artifacts in a browser tab and optionally collect user input back into the conversation.

## What it does

Claude calls the `render_artifact` tool to open a live browser tab displaying anything from a simple options picker to a full dashboard. Two modes:

- **`immediate`** — renders and returns right away. Use for displays: charts, tables, diagrams, markdown documents.
- **`interactive`** — blocks until the user submits a result from the browser via `window.artifact.submit(payload)`, then returns that payload to Claude. Use for decisions and forms where Claude needs the user's input to continue.

This replaces walls of text and `AskUserQuestion` prompts with actual UI.

## Templates

Generating full HTML from scratch is slow — Claude has to produce thousands of tokens of markup, CSS, and JavaScript before anything renders. Templates solve this by moving the boilerplate server-side. Claude passes a small JSON `data` payload (~100–200 tokens) and the server renders the complete HTML.

| Template | Mode | Purpose |
|---|---|---|
| `options` | interactive | Clickable choice list. Returns `{selected, label}`. |
| `table` | immediate | Sortable data table. |
| `markdown` | immediate | Rendered markdown with code highlighting. |
| `form` | interactive | Labeled inputs with a submit button. Returns `{field: value, ...}`. |
| `chart` | immediate | Bar, line, or pie chart via Chart.js. |

All templates load CSS and JS from CDN (Tailwind, Chart.js, marked.js, highlight.js) rather than inlining them, so Claude never needs to write a single line of styling.

### Template schemas

**`options`**
```json
{
  "title": "Pick a deployment strategy",
  "description": "Optional subheading",
  "options": [
    {"value": "blue_green", "label": "Blue/Green", "description": "Zero-downtime swap.", "icon": "🔵"}
  ]
}
```

**`table`**
```json
{
  "title": "Q3 Pipeline",
  "columns": ["Deal", "Stage", "Value"],
  "rows": [["Acme", "Proposal", "$42k"]],
  "sortable": true
}
```

**`markdown`**
```json
{"content": "# Heading\n\nSome **markdown** content.", "theme": "dark"}
```

**`form`**
```json
{
  "title": "New Project",
  "fields": [
    {"name": "name", "label": "Project Name", "type": "text", "required": true},
    {"name": "lang", "label": "Language", "type": "select", "options": ["Python", "Go"]},
    {"name": "private", "label": "Private", "type": "checkbox"}
  ],
  "submit_label": "Create"
}
```
Field types: `text` · `textarea` · `select` · `checkbox` · `number` · `email` · `password`

**`chart`**
```json
{
  "type": "bar",
  "title": "Monthly Revenue",
  "labels": ["Jan", "Feb", "Mar"],
  "datasets": [{"label": "2026", "data": [42000, 38000, 51000]}],
  "y_label": "USD"
}
```
Chart types: `bar` · `line` · `pie`

Raw HTML is still supported via the `html` field for anything that doesn't fit a template.

## Architecture

Two components run together in a single process:

```
Claude Code  ──stdio JSON-RPC──▶  MCP server (server.py)
                                       │
                              call_tool() handler
                              ├── templates.py  (renders HTML from data)
                              └── /tmp/artifact_ui/{id}.html  (written to disk)
                                       │
                              webbrowser.open()
                                       │
Browser  ◀──GET /artifact/{id}──  FastAPI :8765
Browser  ──POST /artifact/event──▶  FastAPI  ──event.set()──▶  MCP response
```

The MCP stdio server and the FastAPI HTTP server share the same asyncio event loop via `asyncio.gather()`. This matters for interactive mode: when the browser POSTs a submit event, FastAPI sets an `asyncio.Event` that directly unblocks the waiting MCP tool call — no inter-process communication needed.

Claude Code manages the server lifecycle. Each session spawns a fresh `server.py` process that starts the HTTP server if port 8765 is free (or reuses an existing one if it's already bound from a previous session).

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

To kill a stale server from a previous session:

```bash
./restart.sh
```

Then reconnect via `/mcp` in Claude Code.
