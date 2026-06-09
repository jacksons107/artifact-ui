def build_tool_description() -> str:
    return (
        "Render an interactive, multi-view system architecture diagram in a browser tab.\n\n"

        "Use this tool when explaining a codebase, service architecture, or system design.\n"
        "The LLM describes WHAT exists (nodes, edges, groups, sequences); the tool handles\n"
        "all layout, colors, interactivity, and view switching automatically.\n\n"

        "── ALWAYS START HERE ──────────────────────────────────────────────────────────\n"
        "Call get_example('sys_microservices') before building your first spec.\n"
        "Read the full example to understand the schema, then adapt it for your system.\n\n"

        "── SPEC SCHEMA ────────────────────────────────────────────────────────────────\n"
        "{\n"
        '  "title": "My System",\n'
        '  "description": "optional one-liner",\n'
        '  "nodes": [\n'
        "    {\n"
        '      "id": "api",           // unique — used in edges / groups / sequences\n'
        '      "label": "API Server",\n'
        '      "kind": "service",     // service | module | class | db | queue | external | package | file | function\n'
        '      "description": "...",  // optional — shown in the detail panel on click\n'
        '      "tech": "Go",          // optional — rendered as sub-label\n'
        '      "owner": "team-name",  // optional\n'
        '      "status": "stable",    // optional — stable | experimental | deprecated | planned\n'
        '      "tags": ["critical"]   // optional\n'
        "    }\n"
        "  ],\n"
        '  "edges": [\n'
        "    {\n"
        '      "from": "ui",\n'
        '      "to": "api",\n'
        '      "kind": "calls",       // calls | imports | depends | emits | subscribes | reads | writes | deploys | owns\n'
        '      "label": "REST",       // optional\n'
        '      "async": false,        // optional — true → dashed line\n'
        '      "protocol": "HTTP"     // optional — informational\n'
        "    }\n"
        "  ],\n"
        '  "groups": [                // optional — creates labeled bounding boxes + a Layers tab\n'
        "    {\n"
        '      "id": "frontend",\n'
        '      "label": "Frontend",\n'
        '      "kind": "layer",       // layer | package | team | domain | deployment\n'
        '      "members": ["ui", "client"]\n'
        "    }\n"
        "  ],\n"
        '  "sequences": [             // optional — creates a Sequences tab with swim-lane diagrams\n'
        "    {\n"
        '      "id": "login",\n'
        '      "label": "Login Flow",\n'
        '      "steps": [\n'
        '        {"from": "client", "to": "api", "label": "POST /login"},\n'
        '        {"from": "api", "to": "db", "label": "lookup user"}\n'
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n\n"

        "── WHAT THE TOOL PRODUCES ─────────────────────────────────────────────────────\n"
        "Architecture tab   Box-and-arrow diagram. Click any node for a detail panel.\n"
        "                   Filter bar lets users hide/show node kinds.\n"
        "Layers tab         Horizontal swim-lanes (only if groups with kind='layer' exist).\n"
        "Sequences tab      Sequence diagrams with dropdown selector (only if sequences exist).\n"
        "Matrix tab         Adjacency matrix — who calls whom at a glance.\n"
        "Components tab     Filterable table of all nodes with all metadata.\n\n"

        "── INVOCATION ─────────────────────────────────────────────────────────────────\n"
        "render_artifact(\n"
        '  artifact_id="my-system",\n'
        '  title="My System — Architecture",\n'
        '  mode="immediate",\n'
        '  template="system_spec",\n'
        "  data={ ...spec... }\n"
        ")\n\n"

        "mode: 'immediate' returns at once. 'interactive' blocks until window.artifact.submit(payload) is called.\n"
        "Prefer render_artifact(mode='interactive') over AskUserQuestion for decisions."
    )


def build_template_schema_property() -> dict:
    return {
        "type": "string",
        "description": "Template name. Only valid value: 'system_spec'.",
        "enum": ["system_spec"],
    }
