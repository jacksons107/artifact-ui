def build_tool_description() -> str:
    return (
        "Render an interactive, multi-view system/code diagram in a browser tab.\n\n"

        "── USE CASES ──────────────────────────────────────────────────────────────────\n"
        "System / service architecture   Use service, db, queue, external, module nodes.\n"
        "                                Add groups with kind='layer' for swim-lanes.\n"
        "                                → Examples: sys_microservices, sys_event_driven\n\n"
        "Code-level explainers           Use function, class, file, module nodes.\n"
        "  • Implementation plans          Set status='added'/'modified'/'deleted' on\n"
        "  • Bug fixes with diffs            changed nodes → triggers a Changes tab.\n"
        "  • Call graph walkthroughs       Add code_snippet + previous_code_snippet to\n"
        "  • API / schema maps               show what changed and why.\n"
        "                                → Examples: code_impl_plan, code_bug_fix\n\n"
        "System + code together          Give a group a 'detail' block (nested\n"
        "                                nodes/edges using code-level kinds) → adds\n"
        "                                a 'Code Detail' tab with a per-module drill-down.\n"
        "                                → Example: mixed_levels\n\n"

        "── ALWAYS START HERE ──────────────────────────────────────────────────────────\n"
        "Call get_example('sys_microservices') for system-level, get_example('code_bug_fix')\n"
        "for code-level, or get_example('mixed_levels') to combine both. Read the example,\n"
        "then adapt it for your system.\n\n"

        "── SPEC SCHEMA ────────────────────────────────────────────────────────────────\n"
        "{\n"
        '  "title": "My System",\n'
        '  "description": "optional one-liner",\n'
        '  "nodes": [\n'
        "    {\n"
        '      "id": "api",                    // unique — used in edges / groups / sequences\n'
        '      "label": "API Server",\n'
        '      "kind": "service",              // see node kinds below\n'
        '      "description": "...",           // optional — shown in the detail panel on click\n'
        '      "tech": "Go",                   // optional — rendered as sub-label\n'
        '      "owner": "team-name",           // optional\n'
        '      "status": "stable",             // optional — see status values below\n'
        '      "tags": ["critical"],           // optional\n'
        '      // Code-level fields (use with function / class / file nodes):\n'
        '      "signature": "func Parse(r io.Reader) (*AST, error)",  // shown above snippet\n'
        '      "code_snippet": "func Parse(...) {\\n  ...\\n}",        // shown with syntax highlight\n'
        '      "previous_code_snippet": "func Parse(...) {\\n  // old\\n}", // for diff view\n'
        '      "file_path": "src/parser/parser.go",\n'
        '      "line_range": [42, 87]\n'
        "    }\n"
        "  ],\n"
        '  "edges": [\n'
        "    {\n"
        '      "from": "ui",\n'
        '      "to": "api",\n'
        '      "kind": "calls",       // see edge kinds below\n'
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
        '      "members": ["ui", "client"],\n'
        '      // optional — nested spec for this group, shown in a "Code Detail" tab\n'
        '      // with a per-group dropdown. It is the SAME diagram type as the\n'
        '      // top-level Architecture view (filter bar, sequence animation, detail\n'
        '      // panels) — just scoped to this group\'s own nodes. Same nodes/edges/\n'
        '      // groups/sequences shape as the top level, own id namespace, typically\n'
        '      // code-level kinds/fields.\n'
        '      "detail": {\n'
        '        "nodes": [{"id": "handler", "label": "handle_request()", "kind": "function",\n'
        '                   "signature": "def handle_request(req) -> Response", "code_snippet": "..."}],\n'
        '        "edges": [{"from": "handler", "to": "handler", "kind": "calls"}],\n'
        '        "groups": [],     // optional — same shape as top-level groups\n'
        '        "sequences": []   // optional — same shape as top-level sequences\n'
        "      }\n"
        "    }\n"
        "  ],\n"
        '  "sequences": [             // optional — creates a Sequences tab\n'
        "    {\n"
        '      "id": "login",\n'
        '      "label": "Login Flow",\n'
        '      "steps": [\n'
        '        {"from": "client", "to": "api", "label": "POST /login"},\n'
        '        {\n'
        '          "from": "api", "to": "db", "label": "lookup user",\n'
        '          // optional — attach a concrete example to a step (request body,\n'
        '          // SQL query, event payload, etc.) → click-to-reveal panel.\n'
        '          "example": "SELECT * FROM users WHERE email = ?",\n'
        '          "example_lang": "sql"  // syntax highlight hint, default "plaintext"\n'
        '        },\n'
        '        {\n'
        '          "from": "api", "to": "api", "label": "hash password",\n'
        '          // optional — for transform-style steps, show data before/after\n'
        '          // (either side alone is fine too) → rendered as a side-by-side diff.\n'
        '          "example_before": "hunter2",\n'
        '          "example_after": "$2b$12$KIXQ..."\n'
        '        }\n'
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n\n"

        "── NODE KINDS ─────────────────────────────────────────────────────────────────\n"
        "  System level:  service · db · queue · external · module\n"
        "  Code level:    function · class · file · package\n\n"

        "── EDGE KINDS ─────────────────────────────────────────────────────────────────\n"
        "  System: calls · imports · depends · emits · subscribes · reads · writes · deploys · owns\n"
        "  Code:   returns · throws · overrides · implements · instantiates\n\n"

        "── STATUS VALUES ──────────────────────────────────────────────────────────────\n"
        "  General:       stable · experimental · deprecated · planned\n"
        "  Change tracking (trigger Changes tab + colored borders in Architecture view):\n"
        "                 added (green) · modified (amber) · deleted (red/faded)\n\n"

        "── WHAT THE TOOL PRODUCES ─────────────────────────────────────────────────────\n"
        "Architecture tab   Box-and-arrow diagram. Click any node for a detail panel\n"
        "                   (shows description, signature, code snippet, edges, and which\n"
        "                   sequences touch this node — click one to play it, see below).\n"
        "                   Filter bar lets users hide/show node kinds and change statuses.\n"
        "                   If sequences exist, an 'Animate' control plays any sequence as\n"
        "                   a traveling-pulse trail directly on top of the diagram.\n"
        "Layers tab         Horizontal swim-lanes (only if groups with kind='layer' exist).\n"
        "Sequences tab      Sequence diagrams with dropdown selector (only if sequences exist).\n"
        "                   Steps with example/example_before/example_after get a click-to-\n"
        "                   reveal panel (snippet or before/after diff) — optional, per step.\n"
        "                   Each diagram also has a scrub/play timeline that animates the\n"
        "                   steps in order (traveling pulse along each call, visited trail).\n"
        "Code Detail tab    Per-group drill-down with a module dropdown (only if any group\n"
        "                   has a 'detail' block) — each module is the full Architecture-\n"
        "                   tab experience (filter bar, Animate control, detail panels)\n"
        "                   scoped to that group's own nodes/edges/groups/sequences.\n"
        "Changes tab        Before/after diff view grouped by added/modified/deleted\n"
        "                   (checks top-level nodes AND group 'detail' nodes).\n"
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
        "Prefer render_artifact(mode='interactive') over AskUserQuestion for decisions.\n\n"

        "── EPHEMERAL VS PERSISTENT ARTIFACTS ───────────────────────────────────────────\n"
        "Every render_artifact call writes its spec alongside the HTML (as a sibling\n"
        "'<name>.spec.json'), even for ephemeral /tmp previews — so any artifact can be\n"
        "read back and edited later.\n\n"

        "Ephemeral (default): just call render_artifact as above. It opens a /tmp preview.\n"
        "If the user wants to keep it, call save_artifact(artifact_id, path) to copy the\n"
        "html + spec to a real path in the project — no manual Downloads-folder shuffling.\n\n"

        "Persistent (living documentation, e.g. a repo's index.html): pass an absolute\n"
        "'path' to render_artifact — it writes the HTML and '<name>.spec.json' there\n"
        "directly (in addition to the /tmp preview), with no localhost/save-button JS\n"
        "injected, so it's safe to publish (e.g. GitHub Pages).\n\n"

        "To edit a persistent artifact later: get_artifact_spec(path) returns its spec,\n"
        "edit the JSON, then render_artifact(..., data=<edited spec>, path=path) to\n"
        "update it in place."
    )


def build_template_schema_property() -> dict:
    return {
        "type": "string",
        "description": "Template name. Only valid value: 'system_spec'.",
        "enum": ["system_spec"],
    }
