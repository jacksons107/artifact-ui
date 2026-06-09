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
  "sequences": [{"id": "login", "label": "Login", "steps": [{"from": "ui", "to": "api", "label": "POST /login"}]}]
}
```

**Node kinds:** `service` `module` `class` `db` `queue` `external` `package` `file` `function`  
**Edge kinds:** `calls` `imports` `depends` `emits` `subscribes` `reads` `writes` `deploys` `owns`  
**Group kinds:** `layer` `package` `team` `domain` `deployment`

## Do not

- Use `AskUserQuestion` for option selection — prefer `render_artifact(mode='interactive')`.
- Skip calling `get_example` — the schema has details that aren't obvious from the quick reference.
