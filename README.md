# artifact-ui

An MCP server that lets Claude render HTML artifacts in a browser tab and optionally collect user input back into the conversation. The template library grows automatically over time — when Claude generates raw HTML, a background sub-agent extracts the pattern into a reusable template so future similar UIs are fast.

## What it does

Claude calls the `render_artifact` tool to open a live browser tab. Two modes:

- **`immediate`** — renders and returns right away. Use for displays: charts, tables, diagrams, markdown.
- **`interactive`** — blocks until the user submits via `window.artifact.submit(payload)` in the browser, then returns that payload to Claude. Use for decisions and forms.

This replaces walls of text and `AskUserQuestion` prompts with actual UI.

## Templates

Generating full HTML from scratch is slow — Claude has to produce thousands of tokens of markup, CSS, and JavaScript before anything renders. Templates solve this: Claude passes a small JSON `data` payload (~100–200 tokens) and the server renders the complete HTML. All templates load CSS and JS from CDN rather than inlining them.

### Built-in templates

| Template | Mode | Purpose |
|---|---|---|
| `options` | interactive | Clickable choice list. Returns `{selected, label}`. |
| `table` | immediate | Sortable data table. |
| `markdown` | immediate | Rendered markdown with code highlighting. |
| `form` | interactive | Labeled inputs with submit button. Returns `{field: value, ...}`. |
| `chart` | immediate | Bar, line, or pie chart via Chart.js. |
| `compose` | immediate | Combine multiple templates into one page. |

**`options`**
```json
{
  "title": "Pick a deployment strategy",
  "description": "Optional subheading",
  "options": [{"value": "blue_green", "label": "Blue/Green", "description": "Zero-downtime swap.", "icon": "🔵"}]
}
```

**`table`**
```json
{"title": "Q3 Pipeline", "columns": ["Deal", "Stage", "Value"], "rows": [["Acme", "Proposal", "$42k"]], "sortable": true}
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

**`compose`**
```json
{
  "title": "Q2 Dashboard",
  "layout": "stack",
  "items": [
    {"template": "stat_cards", "data": {"cards": [{"label": "Revenue", "value": "$2.4M", "delta": "▲ 18%", "delta_positive": true}]}},
    {"template": "chart", "data": {"type": "line", "labels": ["Jan", "Feb"], "datasets": [{"label": "MRR", "data": [40000, 48000]}]}}
  ]
}
```
Layout: `stack` (vertical) or `grid` (2-column). Works with any mix of built-in and learned templates.

### Learned templates

When Claude uses raw HTML, a background sub-agent automatically extracts the pattern into a reusable Python render function and saves it to `learned_templates/`. From that point on, the template is available by name — just like a built-in. The tool description updates dynamically to include new learned templates with their schemas.

Learned templates are stored as plain Python files in `learned_templates/` and committed to git, so the library grows permanently across sessions.

You can also save a template manually via the `learn_template` tool (name, description, schema_example, reasoning, code).

## Architecture

```
Claude Code  ──stdio JSON-RPC──▶  server.py
                                      │
                             call_tool() handler
                             ├── template_loader.py   built-in + learned renderers
                             ├── templates.py          5 built-in render functions
                             ├── compose.py            multi-template layout renderer
                             └── /tmp/artifact_ui/{id}.html
                                      │
                             webbrowser.open()         opens browser tab
                                      │
                    ┌─────────────────┴──────────────────┐
                    ▼                                     ▼
         FastAPI :8765                          (raw HTML path only)
         GET /artifact/{id} → serves file       asyncio.create_subprocess_exec(
         POST /artifact/event → event.set()       "claude -p <extraction_prompt>"
                    │                              --allowedTools Bash,Read,Write
                    ▼                            )  ← sub-agent writes learned_templates/
         asyncio.Event unblocks
         MCP tool call response
```

The MCP stdio server and FastAPI HTTP server share one asyncio event loop via `asyncio.gather()`. Interactive mode works because the browser's POST directly sets an `asyncio.Event` in the same process — no IPC needed.

The template extraction sub-agent is a fully independent `claude -p` process. It analyzes the HTML, writes a validated Python render function to `learned_templates/{name}.py`, and updates `registry.json`. The main agent gets a clean success response and moves on; the sub-agent runs to completion in the background.

### File structure

```
server.py               MCP + FastAPI server, tool handlers
templates.py            5 built-in render functions
compose.py              compose template renderer
template_loader.py      registry management, dynamic tool description
template_extractor.py   save_template(), spawn_extractor_agent()
learned_templates/
  registry.json         metadata for all learned templates
  {name}.py             one file per learned template
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

To kill a stale server from a previous session and let Claude Code spawn a fresh one:

```bash
./restart.sh
# then /mcp in Claude Code to reconnect
```

> **Important:** Do not run `server.py` manually as a background process. Claude Code manages the lifecycle — running it separately splits the HTTP server and MCP server into different processes, which breaks interactive mode (the `asyncio.Event` signaling won't work across processes).
