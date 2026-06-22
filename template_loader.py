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
        "System + code together          Model a group's members as the real code-level\n"
        "                                nodes (functions/classes/etc) instead of a single\n"
        "                                service node → the group IS the drill-down, with\n"
        "                                no separate nested spec to keep in sync.\n"
        "                                → Example: mixed_levels\n\n"
        "Repeated/replicated subsystems   Cells, shards, replicas, regions: write the first\n"
        "                                instance's nodes/edges once, put them in a group,\n"
        "                                then give each other instance's group a 'clone_of'\n"
        "                                pointing at the first — no hand-duplicated JSON.\n"
        "                                → Example: sys_replicated_cells\n\n"

        "── ALWAYS START HERE ──────────────────────────────────────────────────────────\n"
        "Call get_example('sys_microservices') for system-level, get_example('code_bug_fix')\n"
        "for code-level, get_example('mixed_levels') to combine both, or\n"
        "get_example('sys_replicated_cells') for clone_of. Read the example, then adapt it\n"
        "for your system. For the exact required/optional fields, call get_spec_schema —\n"
        "the formal JSON Schema, useful when a field's requirement isn't clear from an example.\n\n"

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
        '  "groups": [                // optional — a group IS a node: collapsed by default\n'
        "                              // (one box), expandable in place to reveal its real\n"
        "                              // members. Also creates a Layers tab if kind='layer'.\n"
        "    {\n"
        '      "id": "frontend",\n'
        '      "label": "Frontend",\n'
        '      "kind": "layer",       // layer | package | team | domain | deployment\n'
        '      "members": ["ui", "client"],  // node ids and/or other group ids (nesting).\n'
        '                                     // A node/group may have at most ONE parent\n'
        '                                     // group — that single-parent rule is what\n'
        '                                     // makes collapse/expand unambiguous: every\n'
        '                                     // edge into a hidden member redirects to its\n'
        '                                     // one collapsed ancestor automatically, no\n'
        '                                     // manual boundary map needed. A group must\n'
        '                                     // have 2+ members (or 0) — a single-member\n'
        '                                     // group is rejected; reference that member\n'
        '                                     // directly instead.\n'
        '      // optional — reuse another group\'s entire member subtree (nodes, nested\n'
        '      // groups, and the edges among/touching them) under this group\'s own id-\n'
        '      // prefix instead of hand-duplicating it. The source must NOT itself be a\n'
        '      // clone (no chaining), and every id nested under the source must be\n'
        '      // prefixed with the source group\'s own id (e.g. cell_a_worker under group\n'
        '      // "cell_a") so the new ids can be derived mechanically (cell_b_worker).\n'
        '      "clone_of": "cell_a"\n'
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
        "Architecture tab   Box-and-arrow diagram. Every group starts collapsed — a single\n"
        "                   box with a ⤢ to expand it in place into its real members\n"
        "                   (boxed, with a ✕ to collapse back); edges into a collapsed\n"
        "                   group land on the box automatically, no manual remapping.\n"
        "                   Click any node or group for a detail panel (description,\n"
        "                   signature, code snippet, edges / members, and which sequences\n"
        "                   touch it — click one to play it, see below). Filter bar lets\n"
        "                   users hide/show node kinds, change statuses, and groups. If\n"
        "                   sequences exist, an 'Animate' control plays any sequence as a\n"
        "                   traveling-pulse trail, automatically landing on whatever's\n"
        "                   currently visible (a real node or its collapsed ancestor).\n"
        "Layers tab         Horizontal swim-lanes (only if groups with kind='layer' exist).\n"
        "Sequences tab      Sequence diagrams with dropdown selector (only if sequences exist).\n"
        "                   Steps with example/example_before/example_after get a click-to-\n"
        "                   reveal panel (snippet or before/after diff) — optional, per step.\n"
        "                   Each diagram also has a scrub/play timeline that animates the\n"
        "                   steps in order (traveling pulse along each call, visited trail).\n"
        "Code Detail tab    Per-group drill-down with a module dropdown (only if groups\n"
        "                   exist) — each module is the full Architecture-tab experience\n"
        "                   (filter bar, Animate control, detail panels) scoped to that\n"
        "                   group's own subtree (itself plus any nested groups/nodes).\n"
        "Changes tab        Before/after diff view grouped by added/modified/deleted.\n"
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
