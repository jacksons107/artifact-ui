# artifact-ui tool

This tool renders interactive system architecture diagrams in a browser tab.
It accepts a semantic spec (nodes, edges, groups, sequences) and automatically produces
five linked views: Architecture, Layers, Sequences, Matrix, and Components.

## When to use

Use `render_artifact` whenever the user asks for a diagram, architecture overview,
codebase explainer, or system visualization of any kind.

## How to use

1. **Always call `get_example` first** — inspect `sys_microservices` or another example to understand the schema before building a spec.
2. Call `render_artifact(template="system_spec", mode="immediate", data={...})` with your spec.
3. Use `mode="interactive"` when you want the user to confirm or submit something before you continue.

## Spec quick reference

```json
{
  "title": "My System",
  "nodes": [{"id": "api", "label": "API", "kind": "service", "tech": "Go"}],
  "edges": [{"from": "ui", "to": "api", "kind": "calls", "label": "REST"}],
  "groups": [{"id": "backend", "label": "Backend", "kind": "layer", "members": ["api"]}],
  "sequences": [{"id": "login", "label": "Login", "steps": [
    {"from": "ui", "to": "api", "label": "POST /login"},
    {"from": "api", "to": "db", "label": "lookup user", "example": "SELECT * FROM users WHERE email = ?", "example_lang": "sql"}
  ]}]
}
```

Steps can optionally carry `example` (a single snippet — request body, SQL, event payload) or `example_before`/`example_after` (either or both, rendered as a before/after diff) plus an optional `example_lang` hint — shown in a click-to-reveal panel. Omit entirely when a step doesn't need one.

Any sequence can be played back: each Sequences-tab diagram and the Architecture tab (via an "Animate" control) get a scrub/play timeline that walks through the steps as a traveling pulse, leaving a visited trail. Clicking a node also shows which sequences touch it.

A group's optional `detail` block (`nodes`, `edges`, and optionally its own `groups`/`sequences`) gets a Code Detail tab entry that is the exact same diagram type as the Architecture tab — filter bar, group toggles, sequence animation overlay, detail panels — just scoped to that group's own elements, selectable via a module dropdown. That same node is also expandable in place directly in the Architecture diagram (⤢ to expand, ✕ to collapse). If `detail` is set on a group, you **must** also set `detail.boundary`: a `{external_node_id: detail_node_id}` map naming exactly which inner node should receive each top-level edge that touches the group — there's no fallback, so pick the node the edge's label actually refers to (e.g. `{"gateway": "verify_token"}` if `gateway -> auth` is labeled "verify token").

**Node kinds:** `service` `module` `class` `db` `queue` `external` `package` `file` `function`  
**Edge kinds:** `calls` `imports` `depends` `emits` `subscribes` `reads` `writes` `deploys` `owns`  
**Group kinds:** `layer` `package` `team` `domain` `deployment`

## Do not

- Use `AskUserQuestion` for option selection — prefer `render_artifact(mode='interactive')`.
- Skip calling `get_example` — the schema has details that aren't obvious from the quick reference.
