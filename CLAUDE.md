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

Any sequence can be played back: each Sequences-tab diagram and the Architecture tab (via an "Animate" control) get a scrub/play timeline that walks through the steps as a traveling pulse, leaving a visited trail. Clicking a node also shows which sequences touch it; the pulse always lands on whatever's currently visible (a real node, or its nearest collapsed ancestor).

**Groups are collapsible nodes.** Every group starts collapsed — drawn as a single box — and can be expanded in place (⤢) to reveal its real `members` (boxed, with a ✕ to collapse back). `members` may list node ids and/or other group ids (nesting), but **a node or group may have at most one parent group** — that single-parent rule is what makes collapse/expand unambiguous: every edge into a currently-hidden member is automatically redirected to land on its one collapsed ancestor, with no manual boundary map. There's no separate `detail` block — if you want a group to drill into real code-level content, just make its `members` the actual functions/classes (see `mixed_levels`), not a placeholder service node.

The Code Detail tab is this same per-group expanded view, just listed in a module dropdown instead of clicked open inline — one entry per group, scoped to that group's own subtree.

**`clone_of`** lets one group's entire member subtree (nested groups, nodes, and the edges among/touching them) be reused under a new id-prefix instead of hand-duplicated — useful for cells/shards/replicas/regions that are structurally identical. `{"id": "cell_b", "label": "Cell B", "kind": "deployment", "clone_of": "cell_a"}` clones everything nested under `cell_a` (e.g. `cell_a_worker` → `cell_b_worker`) plus any edge crossing into/out of it. The source group can't itself be a clone (no chaining), and every id nested under it must be prefixed with the source group's own id so the new ids can be derived mechanically. See `sys_replicated_cells`.

**Node kinds:** `service` `module` `class` `db` `queue` `external` `package` `file` `function`  
**Edge kinds:** `calls` `imports` `depends` `emits` `subscribes` `reads` `writes` `deploys` `owns`  
**Group kinds:** `layer` `package` `team` `domain` `deployment`

## Do not

- Use `AskUserQuestion` for option selection — prefer `render_artifact(mode='interactive')`.
- Skip calling `get_example` — the schema has details that aren't obvious from the quick reference.

## Code layout

The client-side diagram engine lives as several plain (non-IIFE-wrapped) fragments under `system_spec/arch_engine/`, numerically prefixed so sorted-filename order is build order (`00_constants_and_utils.js`, `10_layout.js`, `15_label_layout.js`, `20_visibility.js`, `30_draw.js`, `40_bootstrap.js`). `system_spec/arch_block.py` concatenates them and wraps the result in one IIFE at build time — that's the only place the wrapper exists, so the shipped script is unchanged; don't add a wrapper to an individual fragment file.

Edge labels are positioned via a dedicated collision-avoidance pass (`computeEdgeLabelBoxes` in `15_label_layout.js`): `drawDiagram` first computes every labeled edge's *desired* midpoint box, then resolves all of them at once (sorted top-to-bottom, each box only ever pushed down to clear what's already placed) before drawing anything — never positions a label from a single edge in isolation.

The page's embedded CSS/JS is split by feature into `system_spec/assets_common.py`, `assets_sequences.py`, `assets_filters.py`, `assets_misc.py` (each exporting `CSS`/`JS`), assembled by the thin `system_spec/assets.py`. Add new styling/JS to whichever feature module it belongs with, not back into `assets.py` itself.

## Testing the layout engine

`system_spec/arch_engine/`'s layout logic (cycle handling, crossing reduction, recursive hierarchical group-box layout) has a property + regression test suite in `tests/arch_engine/` (fast-check + Node's built-in test runner — dev-only, never bundled into rendered output):

```
cd tests/arch_engine && npm install && npm test
```

The bundled examples used by `get_example`/`system_spec_examples.py` live as JSON files under `system_spec/examples/*.json` — that's the one source of truth for both the Python loader and the test suite's regression fixtures; don't hand-duplicate example data elsewhere.

The Architecture filter bar's toggle behavior (`system_spec/assets_filters.py`'s `_applyArchFilter`, plus its interaction with the engine's expand/collapse re-renders) has its own DOM-level property + regression suite in `tests/interactions/` (fast-check + jsdom — dev-only). It renders real specs through the actual Python pipeline (`render_helper.js` shells out to `python3`), so it always exercises the real, current filter logic:

```
cd tests/interactions && npm install && npm test
```

If you ever touch `_applyArchFilter` or how/when it gets re-invoked after a re-render, run this before and after.
