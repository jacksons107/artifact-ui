import html as _html
import json
import os
from collections import defaultdict, deque
from design_system import page_wrapper

# ── Visual vocabulary ─────────────────────────────────────────────────────────

NODE_KIND_STYLES = {
    "service":  {"stroke": "#D97757", "fill": "rgba(217,119,87,0.07)",  "icon": "◈"},
    "db":       {"stroke": "#788C5D", "fill": "rgba(120,140,93,0.07)",  "icon": "⬡"},
    "queue":    {"stroke": "#B04A3F", "fill": "rgba(176,74,63,0.07)",   "icon": "≋"},
    "external": {"stroke": "#87867F", "fill": "rgba(135,134,127,0.07)", "icon": "◇"},
    "module":   {"stroke": "#87867F", "fill": "rgba(135,134,127,0.05)", "icon": "□"},
    "class":    {"stroke": "#D1CFC5", "fill": "#FFFFFF",                "icon": "⟨⟩"},
    "function": {"stroke": "#D1CFC5", "fill": "#FFFFFF",                "icon": "ƒ"},
    "package":  {"stroke": "#87867F", "fill": "rgba(135,134,127,0.05)", "icon": "⊡"},
    "file":     {"stroke": "#D1CFC5", "fill": "#FFFFFF",                "icon": "≡"},
    "cache":    {"stroke": "#B8860B", "fill": "rgba(184,134,11,0.07)",  "icon": "⚡"},
}

_DEFAULT_NODE_STYLE = {"stroke": "#D1CFC5", "fill": "#FFFFFF", "icon": "○"}

_NODE_KIND_STYLES_JSON = json.dumps({**NODE_KIND_STYLES, "__default__": _DEFAULT_NODE_STYLE})

EDGE_KIND_STYLES = {
    "calls":        {"color": "#D97757", "dashed": False},
    "imports":      {"color": "#87867F", "dashed": False},
    "depends":      {"color": "#87867F", "dashed": True},
    "emits":        {"color": "#788C5D", "dashed": True},
    "subscribes":   {"color": "#788C5D", "dashed": True},
    "reads":        {"color": "#788C5D", "dashed": False},
    "writes":       {"color": "#B04A3F", "dashed": False},
    "deploys":      {"color": "#87867F", "dashed": True},
    "owns":         {"color": "#D1CFC5", "dashed": False},
    "returns":      {"color": "#87867F", "dashed": False},
    "throws":       {"color": "#B04A3F", "dashed": True},
    "overrides":    {"color": "#D1CFC5", "dashed": False},
    "implements":   {"color": "#D1CFC5", "dashed": True},
    "instantiates": {"color": "#D97757", "dashed": False},
}

_DEFAULT_EDGE_STYLE = {"color": "#C8C5BC", "dashed": False}

CHANGE_STATUS_STYLES = {
    "added":    {"stroke": "#4A7C59", "fill": "rgba(74,124,89,0.10)"},
    "modified": {"stroke": "#B8860B", "fill": "rgba(184,134,11,0.10)"},
    "deleted":  {"stroke": "#B04A3F", "fill": "rgba(176,74,63,0.10)"},
}

_CHANGE_STATUS_COLORS = {"added": "#4A7C59", "modified": "#B8860B", "deleted": "#B04A3F"}

_TECH_LANG_MAP = [
    ("python", "python"), ("go", "go"), ("typescript", "typescript"),
    ("javascript", "javascript"), ("ruby", "ruby"), ("java", "java"),
    ("rust", "rust"), ("c++", "cpp"), ("c#", "csharp"), ("kotlin", "kotlin"),
    ("swift", "swift"), ("php", "php"), ("bash", "bash"), ("shell", "bash"),
    ("sql", "sql"),
]

def _infer_lang(node: dict) -> str:
    tech = node.get("tech", "").lower()
    for key, val in _TECH_LANG_MAP:
        if key in tech:
            return val
    return "plaintext"

GROUP_KIND_STYLES = {
    "layer":      {"stroke": "#D1CFC5", "fill": "rgba(209,207,197,0.08)"},
    "package":    {"stroke": "#D97757", "fill": "rgba(217,119,87,0.04)"},
    "team":       {"stroke": "#788C5D", "fill": "rgba(120,140,93,0.04)"},
    "domain":     {"stroke": "#87867F", "fill": "rgba(135,134,127,0.06)"},
    "deployment": {"stroke": "#B04A3F", "fill": "rgba(176,74,63,0.04)"},
}

_DEFAULT_GROUP_STYLE = {"stroke": "#D1CFC5", "fill": "rgba(209,207,197,0.06)"}

# Layout constants
NODE_W = 180
NODE_H = 60
H_GAP  = 56
V_GAP  = 72
PAD    = 56

PROBABILITY_STYLES = {
    "common":   {"color": "#788C5D"},
    "uncommon": {"color": "#B8860B"},
    "rare":     {"color": "#B04A3F"},
}
_DEFAULT_PROBABILITY_STYLE = {"color": "#87867F"}


def _load_archetypes() -> list:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archetypes.json")
    try:
        with open(path) as f:
            return json.load(f).get("archetypes", [])
    except (OSError, json.JSONDecodeError):
        return []


_ARCHETYPES = _load_archetypes()


def _substitute(obj, component_id: str, component_label: str):
    """Recursively substitute {component} / {component_label} placeholders in strings."""
    if isinstance(obj, str):
        return obj.replace("{component_label}", component_label).replace("{component}", component_id)
    if isinstance(obj, list):
        return [_substitute(v, component_id, component_label) for v in obj]
    if isinstance(obj, dict):
        return {k: _substitute(v, component_id, component_label) for k, v in obj.items()}
    return obj


def _apply_archetypes(actions: list, node_by_id: dict) -> None:
    """Mutates each action's outcomes list in-place, injecting archetype-based
    failure outcomes for every component it touches."""
    by_kind: dict[str, list] = defaultdict(list)
    by_id:   dict[str, list] = defaultdict(list)
    for arch in _ARCHETYPES:
        if arch.get("applies_to_kind"):
            by_kind[arch["applies_to_kind"]].append(arch)
        by_id[arch["id"]].append(arch)

    for action in actions:
        touches = action.get("touches", [])
        seen_outcome_ids = {o["id"] for o in action.get("outcomes", [])}
        for comp_id in touches:
            comp = node_by_id.get(comp_id)
            if not comp:
                continue
            archetypes = list(by_kind.get(comp.get("kind", ""), []))
            for arch_id in comp.get("archetypes", []):
                archetypes.extend(by_id.get(arch_id, []))
            for arch in archetypes:
                for template in arch.get("inject_outcomes", []):
                    new_outcome = _substitute(template, comp_id, comp.get("label", comp_id))
                    if new_outcome["id"] in seen_outcome_ids:
                        continue
                    new_outcome["_origin"] = f"archetype:{arch['id']}@{comp_id}"
                    action.setdefault("outcomes", []).append(new_outcome)
                    seen_outcome_ids.add(new_outcome["id"])


# ── Validation ────────────────────────────────────────────────────────────────

def _validate_nodes_edges(nodes: list, edges: list, context: str) -> set:
    node_ids = set()
    for i, node in enumerate(nodes):
        if "id" not in node:
            raise ValueError(f"{context}nodes[{i}] is missing required field 'id'.")
        if "label" not in node:
            raise ValueError(f"{context}nodes[{i}] (id={node['id']!r}) is missing required field 'label'.")
        if node["id"] in node_ids:
            raise ValueError(f"{context}nodes[{i}]: duplicate node id {node['id']!r}.")
        node_ids.add(node["id"])

    for i, edge in enumerate(edges):
        src = edge.get("from")
        dst = edge.get("to")
        if src is None:
            raise ValueError(f"{context}edges[{i}] is missing required field 'from'.")
        if dst is None:
            raise ValueError(f"{context}edges[{i}] is missing required field 'to'.")
        if src not in node_ids:
            raise ValueError(f"{context}edges[{i}]: 'from' references unknown node id {src!r}.")
        if dst not in node_ids:
            raise ValueError(f"{context}edges[{i}]: 'to' references unknown node id {dst!r}.")

    return node_ids


def _validate_behavior(nodes: list, node_ids: set, actions: list, facts: list, data_types: list) -> set:
    """Validates actions/facts/data_types and returns the set of fact ids
    (declared explicitly or referenced implicitly by actions)."""
    data_type_ids = set()
    for i, dt in enumerate(data_types):
        if "id" not in dt:
            raise ValueError(f"data_types[{i}] is missing required field 'id'.")
        data_type_ids.add(dt["id"])

    fact_ids = {f["id"] for f in facts if "id" in f}
    for i, f in enumerate(facts):
        if "id" not in f:
            raise ValueError(f"facts[{i}] is missing required field 'id'.")

    action_ids = set()
    for i, action in enumerate(actions):
        if "id" not in action:
            raise ValueError(f"actions[{i}] is missing required field 'id'.")
        aid = action["id"]
        if aid in action_ids:
            raise ValueError(f"actions[{i}]: duplicate action id {aid!r}.")
        action_ids.add(aid)

        component = action.get("component")
        if component is not None and component not in node_ids:
            raise ValueError(f"actions[{i}] (id={aid!r}): 'component' references unknown node id {component!r}.")

        for comp in action.get("touches", []):
            if comp not in node_ids:
                raise ValueError(f"actions[{i}] (id={aid!r}): 'touches' references unknown node id {comp!r}.")

        for f in action.get("preconditions", []):
            fact_ids.add(f)

        outcomes = action.get("outcomes", [])
        outcome_ids = set()
        for j, outcome in enumerate(outcomes):
            if "id" not in outcome:
                raise ValueError(f"actions[{i}] (id={aid!r}).outcomes[{j}] is missing required field 'id'.")
            oid = outcome["id"]
            if oid in outcome_ids:
                raise ValueError(f"actions[{i}] (id={aid!r}): duplicate outcome id {oid!r}.")
            outcome_ids.add(oid)
            for f in outcome.get("requires", []):
                fact_ids.add(f)
            effects = outcome.get("effects", {})
            for f in effects.get("add", []):
                fact_ids.add(f)
            for f in effects.get("remove", []):
                fact_ids.add(f)

    return fact_ids


def parse_spec(data: dict) -> dict:
    title      = data.get("title", "Untitled System")
    nodes      = data.get("nodes", [])
    edges      = data.get("edges", [])
    groups     = data.get("groups", [])
    actions    = data.get("actions", [])
    facts      = data.get("facts", [])
    data_types = data.get("data_types", [])
    scenarios  = data.get("scenarios", [])

    if not nodes:
        raise ValueError("system_spec requires at least one node in 'nodes'.")

    node_ids = _validate_nodes_edges(nodes, edges, "")

    for i, group in enumerate(groups):
        if "id" not in group:
            raise ValueError(f"groups[{i}] is missing required field 'id'.")
        if "label" not in group:
            raise ValueError(f"groups[{i}] (id={group['id']!r}) is missing required field 'label'.")
        for member in group.get("members", []):
            if member not in node_ids:
                raise ValueError(
                    f"groups[{i}] (id={group['id']!r}): member {member!r} is not a known node id."
                )
        detail = group.get("detail")
        if detail:
            _validate_nodes_edges(
                detail.get("nodes", []), detail.get("edges", []),
                f"groups[{i}] (id={group['id']!r}).detail."
            )

    for i, sc in enumerate(scenarios):
        if "id" not in sc:
            raise ValueError(f"scenarios[{i}] is missing required field 'id'.")
        if "label" not in sc:
            raise ValueError(f"scenarios[{i}] (id={sc['id']!r}) is missing required field 'label'.")

    fact_ids = _validate_behavior(nodes, node_ids, actions, facts, data_types)

    # Build a fact registry covering both explicitly declared and implicitly-referenced facts
    declared_facts = {f["id"]: f for f in facts}
    fact_registry = []
    for fid in fact_ids:
        if fid in declared_facts:
            fact_registry.append(declared_facts[fid])
        else:
            fact_registry.append({"id": fid, "label": fid, "initial": False})

    node_by_id = {n["id"]: n for n in nodes}
    _apply_archetypes(actions, node_by_id)

    return {
        "title":       title,
        "description": data.get("description", ""),
        "nodes":       nodes,
        "edges":       edges,
        "groups":      groups,
        "actions":     actions,
        "facts":       fact_registry,
        "data_types":  data_types,
        "scenarios":   scenarios,
        "node_ids":    node_ids,
    }


# ── Layout ────────────────────────────────────────────────────────────────────

def layout_graph(nodes: list, edges: list, groups: list) -> dict:
    """
    Assign (x, y, w, h) to each node using longest-path layering (Kahn's).
    Nodes in the same group are placed adjacent within their layer.
    Returns {node_id: {x, y, w, h}}.
    """
    node_ids = [n["id"] for n in nodes]

    # Group membership: node_id -> group_id (first group wins)
    node_group: dict[str, str] = {}
    for g in groups:
        for member in g.get("members", []):
            if member not in node_group:
                node_group[member] = g["id"]

    # Build adjacency
    in_deg = {nid: 0 for nid in node_ids}
    succs  = {nid: [] for nid in node_ids}
    for edge in edges:
        src, dst = edge["from"], edge["to"]
        if src != dst:
            succs[src].append(dst)
            in_deg[dst] += 1

    # Longest-path layer assignment
    layer: dict[str, int] = {}
    queue: deque = deque()
    for nid in node_ids:
        if in_deg[nid] == 0:
            layer[nid] = 0
            queue.append(nid)

    while queue:
        nid = queue.popleft()
        for succ in succs[nid]:
            new_l = layer[nid] + 1
            layer[succ] = max(layer.get(succ, 0), new_l)
            in_deg[succ] -= 1
            if in_deg[succ] == 0:
                queue.append(succ)

    # Nodes in cycles were never enqueued — place at max_layer + 1
    max_l = max(layer.values()) if layer else 0
    for nid in node_ids:
        if nid not in layer:
            max_l += 1
            layer[nid] = max_l

    # Group by layer, sort within each layer by (group_id, node_id) for co-location
    layers_map: dict[int, list] = defaultdict(list)
    for nid in node_ids:
        layers_map[layer[nid]].append(nid)
    for l in layers_map:
        layers_map[l].sort(key=lambda nid: (node_group.get(nid, "\xff"), nid))

    # Find the widest layer to center narrower layers
    max_layer_w = max(
        len(ns) * NODE_W + max(0, len(ns) - 1) * H_GAP
        for ns in layers_map.values()
    )

    positions: dict[str, dict] = {}
    for l_idx in sorted(layers_map):
        ns = layers_map[l_idx]
        layer_w = len(ns) * NODE_W + max(0, len(ns) - 1) * H_GAP
        start_x = PAD + (max_layer_w - layer_w) / 2
        y = PAD + l_idx * (NODE_H + V_GAP)
        for i, nid in enumerate(ns):
            x = start_x + i * (NODE_W + H_GAP)
            positions[nid] = {"x": x, "y": y, "w": NODE_W, "h": NODE_H}

    return positions


# ── SVG rendering ─────────────────────────────────────────────────────────────

def _e(s) -> str:
    return _html.escape(str(s))


def render_architecture_svg(spec: dict, positions: dict, id_prefix: str = "") -> str:
    nodes  = spec["nodes"]
    edges  = spec["edges"]
    groups = spec["groups"]
    pos    = positions

    if not pos:
        return '<svg viewBox="0 0 400 200"><text x="200" y="100" text-anchor="middle" fill="#87867F">No nodes</text></svg>'

    W = int(max(p["x"] + p["w"] for p in pos.values()) + PAD)
    H = int(max(p["y"] + p["h"] for p in pos.values()) + PAD)

    parts = [f'<svg viewBox="0 0 {W} {H}" style="display:block;width:100%;height:auto;max-height:680px" id="{_e(id_prefix)}sys-svg">']

    # Arrow markers — one per edge color in use
    parts.append("<defs>")
    colors_used = set()
    for edge in edges:
        kind   = edge.get("kind", "")
        estyle = EDGE_KIND_STYLES.get(kind, _DEFAULT_EDGE_STYLE)
        colors_used.add(estyle["color"])
    colors_used.add(_DEFAULT_EDGE_STYLE["color"])  # ensure default is always available

    for color in colors_used:
        cid = color.replace("#", "")
        parts.append(
            f'<marker id="arr-{cid}" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">'
            f'<path d="M0,0 L0,7 L7,3.5 z" fill="{color}"/></marker>'
        )
    parts.append("</defs>")

    parts.append(f'<g id="{_e(id_prefix)}sys-viewport">')

    # Group bounding boxes (rendered first so nodes appear on top)
    for group in groups:
        members = [m for m in group.get("members", []) if m in pos]
        if not members:
            continue
        gx0 = min(pos[m]["x"] for m in members) - 16
        gy0 = min(pos[m]["y"] for m in members) - 28
        gx1 = max(pos[m]["x"] + pos[m]["w"] for m in members) + 16
        gy1 = max(pos[m]["y"] + pos[m]["h"] for m in members) + 16
        gw, gh = gx1 - gx0, gy1 - gy0
        gkind  = group.get("kind", "")
        gst    = GROUP_KIND_STYLES.get(gkind, _DEFAULT_GROUP_STYLE)
        label  = _e(group.get("label", group["id"]))
        parts.append(
            f'<rect x="{gx0:.1f}" y="{gy0:.1f}" width="{gw:.1f}" height="{gh:.1f}" rx="12" '
            f'fill="{gst["fill"]}" stroke="{gst["stroke"]}" stroke-width="1" stroke-dasharray="5,3"/>'
        )
        parts.append(
            f'<text x="{gx0+10:.1f}" y="{gy0+17:.1f}" '
            f'font-family="ui-monospace,monospace" font-size="10" fill="{gst["stroke"]}" opacity="0.9">'
            f'{label}</text>'
        )

    # Edges
    for edge in edges:
        src, dst = edge.get("from"), edge.get("to")
        if src not in pos or dst not in pos:
            continue
        if src == dst:
            continue
        sp, dp   = pos[src], pos[dst]
        sx       = sp["x"] + sp["w"] / 2
        sy       = sp["y"] + sp["h"]
        ex       = dp["x"] + dp["w"] / 2
        ey       = dp["y"]
        dy       = ey - sy
        cx1, cy1 = sx, sy + dy * 0.45
        cx2, cy2 = ex, ey - dy * 0.45

        kind   = edge.get("kind", "")
        estyle = EDGE_KIND_STYLES.get(kind, _DEFAULT_EDGE_STYLE)
        color  = estyle["color"]
        dashed = estyle["dashed"] or bool(edge.get("async", False))
        dash   = ' stroke-dasharray="6,4"' if dashed else ""
        cid    = color.replace("#", "")

        parts.append(
            f'<g class="sys-edge" data-from="{_e(id_prefix + src)}" data-to="{_e(id_prefix + dst)}" data-kind="{_e(kind)}">'
        )
        parts.append(
            f'<path d="M{sx:.1f},{sy:.1f} C{cx1:.1f},{cy1:.1f} {cx2:.1f},{cy2:.1f} {ex:.1f},{ey:.1f}" '
            f'fill="none" stroke="{color}" stroke-width="1.5"{dash} marker-end="url(#arr-{cid})" class="sys-er-path"/>'
        )

        label = edge.get("label", "")
        if label:
            mx  = (sx + ex) / 2
            my  = (sy + ey) / 2
            lw  = len(label) * 5.8 + 10
            lx  = mx - lw / 2
            parts.append(
                f'<rect x="{lx:.1f}" y="{my-9:.1f}" width="{lw:.1f}" height="14" rx="3" '
                f'fill="rgba(250,249,245,0.92)"/>'
            )
            parts.append(
                f'<text x="{mx:.1f}" y="{my+2:.1f}" text-anchor="middle" '
                f'font-family="ui-monospace,monospace" font-size="10" fill="{color}">'
                f'{_e(label)}</text>'
            )

        parts.append("</g>")  # close sys-edge

    # Nodes
    for node in nodes:
        nid    = node["id"]
        if nid not in pos:
            continue
        p      = pos[nid]
        x, y, w, h = p["x"], p["y"], p["w"], p["h"]
        kind   = node.get("kind", "")
        status = node.get("status", "")
        nst    = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)
        if status in CHANGE_STATUS_STYLES:
            cst    = CHANGE_STATUS_STYLES[status]
            stroke = cst["stroke"]
            fill   = cst["fill"]
        else:
            stroke = nst["stroke"]
            fill   = nst["fill"]
        icon = nst["icon"]
        opacity_attr = ' opacity="0.5"' if status == "deleted" else ""
        parts.append(
            f'<g class="sys-node" data-id="{_e(id_prefix + nid)}" data-kind="{_e(kind)}" data-status="{_e(status)}" '
            f'style="cursor:pointer"{opacity_attr} onclick="sysClick(this)">'
        )
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="10" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.5" class="sys-nr"/>'
        )
        # Icon
        parts.append(
            f'<text x="{x+11:.1f}" y="{y+h/2-3:.1f}" dominant-baseline="middle" '
            f'font-family="ui-monospace,monospace" font-size="10" fill="{stroke}" opacity="0.75">'
            f'{icon}</text>'
        )
        # Label
        parts.append(
            f'<text x="{x+27:.1f}" y="{y+h/2-6:.1f}" '
            f'font-family="ui-serif,Georgia,serif" font-size="13" font-weight="500" fill="#141413">'
            f'{_e(node.get("label", nid))}</text>'
        )
        # Tech sublabel
        tech = node.get("tech", "")
        if tech:
            parts.append(
                f'<text x="{x+27:.1f}" y="{y+h/2+10:.1f}" '
                f'font-family="ui-monospace,monospace" font-size="10" fill="#87867F">'
                f'{_e(tech)}</text>'
            )
        parts.append("</g>")

    parts.append("</g>")  # close sys-viewport
    parts.append(f'<g id="{_e(id_prefix)}sys-anim-layer"></g>')

    parts.append("</svg>")
    return "\n".join(parts)


def _graph_data_json(spec: dict, positions: dict) -> str:
    """JSON blob of node/edge/position data for client-side query, overlay and
    animation use: {positions: {id -> {x,y,w,h}}, nodes: [...], edges: [...]}."""
    centers = {
        nid: {"x": p["x"] + p["w"] / 2, "y": p["y"] + p["h"] / 2, "w": p["w"], "h": p["h"]}
        for nid, p in positions.items()
    }
    nodes = [
        {"id": n["id"], "label": n.get("label", n["id"]), "kind": n.get("kind", "")}
        for n in spec["nodes"]
    ]
    edges = [
        {"from": e.get("from"), "to": e.get("to"), "kind": e.get("kind", ""), "label": e.get("label", "")}
        for e in spec["edges"]
    ]
    return json.dumps({"positions": centers, "nodes": nodes, "edges": edges})


# ── Detail panels ─────────────────────────────────────────────────────────────

def render_detail_panels(spec: dict, id_prefix: str = "") -> str:
    nodes  = spec["nodes"]
    edges  = spec["edges"]
    by_id  = {n["id"]: n for n in nodes}

    outgoing: dict[str, list] = defaultdict(list)
    incoming: dict[str, list] = defaultdict(list)
    for edge in edges:
        outgoing[edge["from"]].append(edge)
        incoming[edge["to"]].append(edge)

    panels = []
    for node in nodes:
        nid  = node["id"]
        kind = node.get("kind", "")
        nst  = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)

        html = f'<div class="sys-panel" id="panel-{_e(id_prefix + nid)}" style="display:none">'
        html += '<div class="sys-ph">'
        html += f'<span style="color:{nst["stroke"]};font-size:14px">{nst["icon"]}</span>'
        html += f'<span class="sys-plabel">{_e(node.get("label", nid))}</span>'
        if kind:
            html += f'<span class="sys-kbadge" style="color:{nst["stroke"]};border-color:{nst["stroke"]}">{_e(kind)}</span>'
        html += '</div>'

        desc = node.get("description", "")
        if desc:
            html += f'<p class="sys-pdesc">{_e(desc)}</p>'

        meta = []
        for key, field in [("Tech", "tech"), ("Owner", "owner"), ("Status", "status")]:
            val = node.get(field, "")
            if val:
                meta.append((key, val))
        file_path  = node.get("file_path", "")
        line_range = node.get("line_range")
        if file_path:
            loc = file_path
            if line_range and len(line_range) == 2:
                loc += f":{line_range[0]}–{line_range[1]}"
            meta.append(("Location", loc))
        if meta:
            html += '<dl class="sys-meta">'
            for k, v in meta:
                html += f'<dt>{k}</dt><dd>{_e(v)}</dd>'
            html += '</dl>'

        tags = node.get("tags", [])
        if tags:
            html += '<div class="sys-tags">'
            for tag in tags:
                html += f'<span class="sys-tag">{_e(tag)}</span>'
            html += '</div>'

        out = outgoing[nid]
        inc = incoming[nid]
        if out or inc:
            html += '<div class="sys-edges">'
            if out:
                html += '<div class="sys-eg-label">Calls / Sends</div>'
                for e in out:
                    peer  = _e(by_id.get(e["to"], {}).get("label", e["to"]))
                    ekind = _e(e.get("kind", ""))
                    elbl  = _e(e.get("label", ""))
                    detail = f"{ekind} · {elbl}" if elbl else ekind
                    html += f'<div class="sys-er">→ {peer} <span class="sys-ek">{detail}</span></div>'
            if inc:
                html += '<div class="sys-eg-label">Receives From</div>'
                for e in inc:
                    peer  = _e(by_id.get(e["from"], {}).get("label", e["from"]))
                    ekind = _e(e.get("kind", ""))
                    elbl  = _e(e.get("label", ""))
                    detail = f"{ekind} · {elbl}" if elbl else ekind
                    html += f'<div class="sys-er">← {peer} <span class="sys-ek">{detail}</span></div>'
            html += '</div>'

        signature = node.get("signature", "")
        if signature:
            html += f'<div class="sys-sig"><code>{_e(signature)}</code></div>'

        code_snippet = node.get("code_snippet", "")
        if code_snippet:
            lang = _infer_lang(node)
            html += f'<div class="sys-snippet"><pre><code class="language-{lang}">{_e(code_snippet)}</code></pre></div>'

        html += '</div>'
        panels.append(html)

    return "\n".join(panels)


# ── Legend ────────────────────────────────────────────────────────────────────

def render_legend(spec: dict) -> str:
    nodes = spec["nodes"]
    edges = spec["edges"]

    kinds_used  = {n.get("kind", "") for n in nodes if n.get("kind")}
    ekind_used  = {e.get("kind", "") for e in edges if e.get("kind")}

    parts = ['<div class="sys-legend">']

    if kinds_used:
        parts.append('<div class="sys-leg-group">')
        parts.append('<div class="sys-leg-title">Nodes</div>')
        for kind in sorted(kinds_used):
            nst = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)
            parts.append(
                f'<div class="sys-leg-row">'
                f'<span style="color:{nst["stroke"]}">{nst["icon"]}</span>'
                f'<span>{_e(kind)}</span>'
                f'</div>'
            )
        parts.append('</div>')

    if ekind_used:
        parts.append('<div class="sys-leg-group">')
        parts.append('<div class="sys-leg-title">Edges</div>')
        for kind in sorted(ekind_used):
            est = EDGE_KIND_STYLES.get(kind, _DEFAULT_EDGE_STYLE)
            dash = "border-top-style:dashed" if est["dashed"] else ""
            parts.append(
                f'<div class="sys-leg-row">'
                f'<span class="sys-leg-line" style="border-color:{est["color"]};{dash}"></span>'
                f'<span>{_e(kind)}</span>'
                f'</div>'
            )
        parts.append('</div>')

    parts.append('</div>')
    return "".join(parts)


# ── Layer diagram ────────────────────────────────────────────────────────────

_LANE_LABEL_W = 108
_LANE_NODE_W  = 160
_LANE_NODE_H  = 52
_LANE_H_GAP   = 20
_LANE_PAD_X   = 24
_LANE_PAD_Y   = 14
_LANE_GAP     = 14


def render_layer_svg(spec: dict) -> str:
    nodes  = spec["nodes"]
    edges  = spec["edges"]
    groups = spec["groups"]

    layer_groups = [g for g in groups if g.get("kind") == "layer"]
    if not layer_groups:
        return ""

    node_by_id = {n["id"]: n for n in nodes}

    # Nodes in at least one layer group
    in_layer: set[str] = set()
    for g in layer_groups:
        in_layer.update(m for m in g.get("members", []) if m in node_by_id)

    # Ungrouped nodes get their own lane
    ungrouped = [n["id"] for n in nodes if n["id"] not in in_layer]
    lanes = list(layer_groups)
    if ungrouped:
        lanes.append({"id": "_other", "label": "Other", "kind": "layer", "members": ungrouped})

    # Compute max nodes in any lane → SVG width
    max_n = max((len([m for m in g.get("members", []) if m in node_by_id or m in [n["id"] for n in nodes]]) for g in lanes), default=1)
    content_w = max_n * _LANE_NODE_W + max(0, max_n - 1) * _LANE_H_GAP
    SVG_W = _LANE_LABEL_W + 2 * _LANE_PAD_X + content_w
    LANE_H = _LANE_NODE_H + 2 * _LANE_PAD_Y

    # Assign positions
    node_pos: dict[str, dict] = {}
    node_lane_idx: dict[str, int] = {}
    valid_lanes = []

    for lane_idx, lane in enumerate(lanes):
        members = [m for m in lane.get("members", []) if m in node_by_id]
        if not members:
            continue
        valid_lanes.append(lane)
        y_top = len(valid_lanes) * _LANE_GAP + (len(valid_lanes) - 1) * LANE_H
        n = len(members)
        total_w = n * _LANE_NODE_W + max(0, n - 1) * _LANE_H_GAP
        start_x = _LANE_LABEL_W + _LANE_PAD_X + (content_w - total_w) / 2
        for i, nid in enumerate(members):
            x = start_x + i * (_LANE_NODE_W + _LANE_H_GAP)
            y = y_top + _LANE_PAD_Y
            node_pos[nid] = {"x": x, "y": y, "w": _LANE_NODE_W, "h": _LANE_NODE_H}
            node_lane_idx[nid] = len(valid_lanes) - 1

    if not valid_lanes:
        return ""

    SVG_H = len(valid_lanes) * (LANE_H + _LANE_GAP) + _LANE_GAP

    parts = [
        f'<svg viewBox="0 0 {SVG_W:.0f} {SVG_H:.0f}" '
        f'style="display:block;width:100%;height:auto;max-height:700px" id="sys-layer-svg">'
    ]
    parts.append('<defs>')
    parts.append(
        '<marker id="larr" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">'
        '<path d="M0,0 L0,7 L7,3.5 z" fill="#C8C5BC"/></marker>'
    )
    parts.append('</defs>')

    # Lane bands
    for li, lane in enumerate(valid_lanes):
        y_top = _LANE_GAP + li * (LANE_H + _LANE_GAP)
        gst   = GROUP_KIND_STYLES.get(lane.get("kind", ""), _DEFAULT_GROUP_STYLE)
        label = _e(lane.get("label", lane["id"]))
        parts.append(
            f'<rect x="0" y="{y_top:.1f}" width="{SVG_W:.0f}" height="{LANE_H}" rx="8" '
            f'fill="{gst["fill"]}" stroke="{gst["stroke"]}" stroke-width="1"/>'
        )
        # Vertical separator
        parts.append(
            f'<line x1="{_LANE_LABEL_W}" y1="{y_top:.1f}" '
            f'x2="{_LANE_LABEL_W}" y2="{y_top+LANE_H:.1f}" '
            f'stroke="{gst["stroke"]}" stroke-width="0.5" opacity="0.35"/>'
        )
        # Lane label
        parts.append(
            f'<text x="{_LANE_LABEL_W/2:.1f}" y="{y_top+LANE_H/2:.1f}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'font-family="ui-monospace,monospace" font-size="11" '
            f'fill="{gst["stroke"]}" font-weight="500">{label}</text>'
        )

    # Edges (cross-lane only — same-lane as small arcs)
    for edge in edges:
        src, dst = edge.get("from"), edge.get("to")
        if src not in node_pos or dst not in node_pos or src == dst:
            continue
        sp, dp     = node_pos[src], node_pos[dst]
        src_li     = node_lane_idx[src]
        dst_li     = node_lane_idx[dst]

        if src_li == dst_li:
            # Same lane: subtle arc above nodes
            sx = sp["x"] + sp["w"] / 2
            sy = sp["y"]
            ex = dp["x"] + dp["w"] / 2
            ey = dp["y"]
            mx = (sx + ex) / 2
            arc_y = sy - 16
            parts.append(
                f'<path d="M{sx:.1f},{sy:.1f} Q{mx:.1f},{arc_y:.1f} {ex:.1f},{ey:.1f}" '
                f'fill="none" stroke="#D1CFC5" stroke-width="1" stroke-dasharray="4,3" '
                f'marker-end="url(#larr)"/>'
            )
        else:
            # Cross-lane: bezier from bottom to top
            sx       = sp["x"] + sp["w"] / 2
            sy       = sp["y"] + sp["h"]
            ex       = dp["x"] + dp["w"] / 2
            ey       = dp["y"]
            dy       = ey - sy
            cx1, cy1 = sx, sy + dy * 0.4
            cx2, cy2 = ex, ey - dy * 0.4
            parts.append(
                f'<path d="M{sx:.1f},{sy:.1f} C{cx1:.1f},{cy1:.1f} {cx2:.1f},{cy2:.1f} {ex:.1f},{ey:.1f}" '
                f'fill="none" stroke="#C8C5BC" stroke-width="1.3" marker-end="url(#larr)"/>'
            )
            label = edge.get("label", "")
            if label:
                mx = (sx + ex) / 2
                my = (sy + ey) / 2
                lw = len(label) * 5.4 + 8
                parts.append(
                    f'<rect x="{mx-lw/2:.1f}" y="{my-8:.1f}" width="{lw:.1f}" height="13" rx="3" '
                    f'fill="rgba(250,249,245,0.9)"/>'
                )
                parts.append(
                    f'<text x="{mx:.1f}" y="{my+2:.1f}" text-anchor="middle" '
                    f'font-family="ui-monospace,monospace" font-size="9" fill="#87867F">'
                    f'{_e(label)}</text>'
                )

    # Nodes
    for nid, p in node_pos.items():
        node = node_by_id[nid]
        x, y, w, h = p["x"], p["y"], p["w"], p["h"]
        kind  = node.get("kind", "")
        nst   = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)
        label = _e(node.get("label", nid))
        tech  = _e(node.get("tech", ""))
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="8" '
            f'fill="{nst["fill"]}" stroke="{nst["stroke"]}" stroke-width="1.5"/>'
        )
        label_y = f"{y + h/2 - (6 if tech else 0):.1f}"
        parts.append(
            f'<text x="{x + w/2:.1f}" y="{label_y}" text-anchor="middle" dominant-baseline="middle" '
            f'font-family="ui-serif,Georgia,serif" font-size="12" font-weight="500" fill="#141413">'
            f'{nst["icon"]} {label}</text>'
        )
        if tech:
            parts.append(
                f'<text x="{x + w/2:.1f}" y="{y + h/2 + 10:.1f}" text-anchor="middle" '
                f'font-family="ui-monospace,monospace" font-size="10" fill="#87867F">'
                f'{tech}</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


# ── Behavior / traces view ───────────────────────────────────────────────────

def render_behavior_html(spec: dict) -> str:
    actions = spec.get("actions", [])
    if not actions:
        return ""

    scenarios = spec.get("scenarios", [])
    facts     = spec.get("facts", [])
    nodes     = spec["nodes"]
    node_by_id = {
        n["id"]: {"label": n.get("label", n["id"]), "kind": n.get("kind", ""), "tech": n.get("tech", "")}
        for n in nodes
    }

    payload = {
        "actions":    actions,
        "facts":      facts,
        "scenarios":  scenarios,
        "data_types": spec.get("data_types", []),
        "nodes":      node_by_id,
    }
    payload_json = json.dumps(payload).replace("</", "<\\/")

    html = '<div class="sys-behavior-wrap">'
    if scenarios:
        html += '<div class="sys-behavior-controls">'
        html += '<span class="sys-fl">Scenario</span>'
        html += '<select class="sys-behavior-sel" onchange="sysBehaviorRender()" id="sys-behavior-sel">'
        for sc in scenarios:
            html += f'<option value="{_e(sc["id"])}">{_e(sc["label"])}</option>'
        html += '</select>'
        html += (
            '<label class="sys-behavior-toggle">'
            '<input type="checkbox" id="sys-behavior-failures" onchange="sysBehaviorRender()"> '
            'Failure traces only</label>'
        )
        html += '</div>'
    else:
        html += (
            '<p class="sys-mono" style="color:var(--gray-500);padding:20px 0">'
            'No scenarios defined. Add a "scenarios" array (id, label, initial_facts, goal_fact) '
            'to derive execution traces.</p>'
        )

    html += '<div id="sys-behavior-traces" class="sys-behavior-traces"></div>'
    html += f'<script type="application/json" id="sys-behavior-data">{payload_json}</script>'
    html += '</div>'
    return html


# ── Dependency matrix ─────────────────────────────────────────────────────────

def render_matrix_html(spec: dict) -> str:
    nodes = spec["nodes"]
    edges = spec["edges"]

    if not edges:
        return '<p class="sys-mono" style="color:var(--gray-500);padding:20px 0">No edges to display.</p>'

    node_by_id = {n["id"]: n for n in nodes}

    # Sources and targets, preserving spec node order
    src_ids: list[str] = []
    tgt_ids: list[str] = []
    seen_s: set[str] = set()
    seen_t: set[str] = set()
    for node in nodes:
        nid = node["id"]
        if any(e["from"] == nid for e in edges) and nid not in seen_s:
            src_ids.append(nid)
            seen_s.add(nid)
        if any(e["to"] == nid for e in edges) and nid not in seen_t:
            tgt_ids.append(nid)
            seen_t.add(nid)

    # Edge map (src, tgt) → list of edges
    edge_map: dict[tuple, list] = defaultdict(list)
    for e in edges:
        edge_map[(e["from"], e["to"])].append(e)

    html  = '<div class="sys-matrix-wrap"><table class="sys-mtx">'

    # Header row — rotated column labels
    html += '<thead><tr><th class="sys-mh0"></th>'
    for tgt in tgt_ids:
        node  = node_by_id.get(tgt, {})
        label = _e(node.get("label", tgt))
        kind  = node.get("kind", "")
        nst   = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)
        html += (
            f'<th class="sys-mth">'
            f'<div class="sys-mth-inner">'
            f'<span style="color:{nst["stroke"]}">{nst["icon"]}</span>'
            f'<span>{label}</span>'
            f'</div></th>'
        )
    html += '</tr></thead><tbody>'

    # Data rows
    for src in src_ids:
        node  = node_by_id.get(src, {})
        label = _e(node.get("label", src))
        kind  = node.get("kind", "")
        nst   = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)

        html += (
            f'<tr><td class="sys-mrh">'
            f'<span style="color:{nst["stroke"]};margin-right:4px">{nst["icon"]}</span>'
            f'{label}</td>'
        )
        for tgt in tgt_ids:
            cell_edges = edge_map.get((src, tgt), [])
            if cell_edges:
                e0    = cell_edges[0]
                ekind = e0.get("kind", "")
                est   = EDGE_KIND_STYLES.get(ekind, _DEFAULT_EDGE_STYLE)
                color = est["color"]
                kinds_str = " · ".join(_e(e.get("kind", "→")) for e in cell_edges)
                bg    = f"background:rgba({','.join(str(int(int(color[i:i+2],16))) for i in (1,3,5))},0.07)"
                html += (
                    f'<td class="sys-mc sys-mc-hit" style="color:{color};{bg}" '
                    f'title="{_e(src)} → {_e(tgt)}">{kinds_str}</td>'
                )
            else:
                html += '<td class="sys-mc"></td>'
        html += '</tr>'

    html += '</tbody></table></div>'
    return html


# ── Component list ────────────────────────────────────────────────────────────

def render_component_list_html(spec: dict) -> str:
    nodes = spec["nodes"]
    actions = spec.get("actions", [])
    kinds    = sorted({n.get("kind", "") for n in nodes if n.get("kind")})
    statuses = sorted({n.get("status", "") for n in nodes if n.get("status")})

    actions_by_component: dict[str, list] = defaultdict(list)
    for action in actions:
        comp = action.get("component")
        if comp:
            actions_by_component[comp].append(action)

    html = '<div class="sys-clist">'

    # Filter chips
    html += '<div class="sys-filters">'
    html += '<span class="sys-fl">Kind</span>'
    for kind in kinds:
        nst = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)
        html += (
            f'<button class="sys-fc active" data-fk="{_e(kind)}" '
            f'style="color:{nst["stroke"]};border-color:{nst["stroke"]}" '
            f'onclick="sysFKind(this)">{nst["icon"]} {_e(kind)}</button>'
        )
    if statuses:
        html += '<span class="sys-fl" style="margin-left:12px">Status</span>'
        for st in statuses:
            html += (
                f'<button class="sys-fc active" data-fs="{_e(st)}" '
                f'onclick="sysFStatus(this)">{_e(st)}</button>'
            )
    html += '</div>'

    # Table
    html += (
        '<div class="sys-tbl-wrap">'
        '<table class="sys-ctable"><thead><tr>'
    )
    cols = ["Name", "Kind", "Tech", "Owner", "Status", "Tags", "Description"]
    if actions:
        cols.append("Actions")
    for col in cols:
        html += f'<th>{col}</th>'
    html += '</tr></thead><tbody>'

    for node in nodes:
        nid    = node["id"]
        kind   = node.get("kind", "")
        nst    = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)
        status = node.get("status", "")
        tags   = node.get("tags", [])
        tags_h = "".join(f'<span class="sys-tag">{_e(t)}</span>' for t in tags)

        html += (
            f'<tr class="sys-cr" data-rkind="{_e(kind)}" data-rstatus="{_e(status)}">'
            f'<td><span style="color:{nst["stroke"]};margin-right:4px">{nst["icon"]}</span>'
            f'<strong>{_e(node.get("label", nid))}</strong></td>'
            f'<td><span class="sys-kbadge" style="color:{nst["stroke"]};border-color:{nst["stroke"]}">{_e(kind)}</span></td>'
            f'<td class="sys-mono">{_e(node.get("tech", ""))}</td>'
            f'<td class="sys-mono">{_e(node.get("owner", ""))}</td>'
            f'<td class="sys-mono">{_e(status)}</td>'
            f'<td>{tags_h}</td>'
            f'<td class="sys-dc">{_e(node.get("description", ""))}</td>'
        )
        if actions:
            owned = actions_by_component.get(nid, [])
            owned_h = "".join(
                f'<span class="sys-tag">{_e(a.get("label", a["id"]))}</span>' for a in owned
            ) or "—"
            html += f'<td>{owned_h}</td>'
        html += '</tr>'

    html += '</tbody></table></div></div>'
    return html


# ── Architecture filter bar ───────────────────────────────────────────────────

def render_filter_bar(spec: dict) -> str:
    nodes  = spec["nodes"]
    kinds  = sorted({n.get("kind", "") for n in nodes if n.get("kind")})
    change_statuses = [s for s in ("added", "modified", "deleted") if any(n.get("status") == s for n in nodes)]
    if not kinds and not change_statuses:
        return ""
    html = '<div class="sys-arch-filters">'
    if kinds:
        html += '<span class="sys-fl">Show</span>'
        for kind in kinds:
            nst = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)
            html += (
                f'<button class="sys-fc active" data-ak="{_e(kind)}" '
                f'style="color:{nst["stroke"]};border-color:{nst["stroke"]}" '
                f'onclick="sysAKind(this)">{nst["icon"]} {_e(kind)}</button>'
            )
    if change_statuses:
        if kinds:
            html += '<span class="sys-fl-sep"></span>'
        html += '<span class="sys-fl">Changes</span>'
        for st in change_statuses:
            color = _CHANGE_STATUS_COLORS[st]
            html += (
                f'<button class="sys-fc active" data-as="{_e(st)}" '
                f'style="color:{color};border-color:{color}" '
                f'onclick="sysAStatus(this)">{_e(st)}</button>'
            )
    html += '</div>'
    return html


# ── Code detail tab ───────────────────────────────────────────────────────────

def render_code_detail_html(spec: dict) -> str:
    detail_groups = [g for g in spec["groups"] if g.get("detail", {}).get("nodes")]
    if not detail_groups:
        return ""

    html = '<div class="sys-cd-wrap"><div class="sys-cd-controls">'
    html += '<span class="sys-fl">Module</span>'
    html += '<select class="sys-cd-sel" onchange="sysCodeDetailChange(this)">'
    for g in detail_groups:
        html += f'<option value="{_e(g["id"])}">{_e(g.get("label", g["id"]))}</option>'
    html += '</select>'
    html += '</div>'

    for i, g in enumerate(detail_groups):
        detail = g["detail"]
        sub = parse_spec({
            "title": g.get("label", g["id"]),
            "nodes": detail["nodes"],
            "edges": detail.get("edges", []),
        })
        positions = layout_graph(sub["nodes"], sub["edges"], [])
        prefix = f'cd-{g["id"]}-'
        svg    = render_architecture_svg(sub, positions, id_prefix=prefix)
        panels = render_detail_panels(sub, id_prefix=prefix)
        legend = render_legend(sub)

        display = '' if i == 0 else ' style="display:none"'
        html += f'<div id="cdp-{_e(g["id"])}" class="sys-cd-panel"{display}>'
        html += '<div class="sys-wrap">'
        html += '<div class="sys-main"><div class="sys-diagram">' + svg + '</div></div>'
        html += '<div class="sys-sidebar">'
        html += '<div class="sys-hint">Click a node<br>to see details</div>'
        html += panels
        html += legend
        html += '</div>'
        html += '</div>'
        html += '</div>'

    html += '</div>'
    return html


# ── Changes tab ──────────────────────────────────────────────────────────────

def render_changes_html(nodes: list) -> str:
    added    = [n for n in nodes if n.get("status") == "added"]
    modified = [n for n in nodes if n.get("status") == "modified"]
    deleted  = [n for n in nodes if n.get("status") == "deleted"]
    if not (added or modified or deleted):
        return ""

    def _node_header(node: dict) -> str:
        kind = node.get("kind", "")
        nst  = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)
        fp   = node.get("file_path", "")
        lr   = node.get("line_range")
        loc  = fp
        if loc and lr and len(lr) == 2:
            loc += f":{lr[0]}–{lr[1]}"
        h  = '<div class="sys-chg-node">'
        if kind:
            h += f'<span class="sys-kbadge" style="color:{nst["stroke"]};border-color:{nst["stroke"]}">{_e(kind)}</span>'
        h += f'<strong class="sys-chg-label">{_e(node.get("label", node["id"]))}</strong>'
        if loc:
            h += f'<span class="sys-chg-fp">{_e(loc)}</span>'
        h += '</div>'
        return h

    def _pre(code: str, lang: str) -> str:
        return f'<pre class="sys-chg-pre"><code class="language-{lang}">{_e(code)}</code></pre>'

    html = '<div class="sys-changes">'

    if added:
        html += '<div class="sys-chg-section">'
        html += '<div class="sys-chg-header" style="color:#4A7C59;border-left-color:#4A7C59">Added</div>'
        for node in added:
            html += _node_header(node)
            snippet = node.get("code_snippet", "")
            if snippet:
                html += _pre(snippet, _infer_lang(node))
        html += '</div>'

    if modified:
        html += '<div class="sys-chg-section">'
        html += '<div class="sys-chg-header" style="color:#B8860B;border-left-color:#B8860B">Modified</div>'
        for node in modified:
            html += _node_header(node)
            prev = node.get("previous_code_snippet", "")
            curr = node.get("code_snippet", "")
            lang = _infer_lang(node)
            if prev and curr:
                html += '<div class="sys-chg-diff">'
                html += '<div class="sys-chg-side"><div class="sys-chg-side-label" style="color:#B04A3F">Before</div>'
                html += _pre(prev, lang)
                html += '</div>'
                html += '<div class="sys-chg-side"><div class="sys-chg-side-label" style="color:#4A7C59">After</div>'
                html += _pre(curr, lang)
                html += '</div></div>'
            elif curr:
                html += _pre(curr, lang)
            elif prev:
                html += _pre(prev, lang)
        html += '</div>'

    if deleted:
        html += '<div class="sys-chg-section">'
        html += '<div class="sys-chg-header" style="color:#B04A3F;border-left-color:#B04A3F">Deleted</div>'
        for node in deleted:
            html += _node_header(node)
            snippet = node.get("previous_code_snippet", "")
            if snippet:
                html += _pre(snippet, _infer_lang(node))
        html += '</div>'

    html += '</div>'
    return html


# ── Page assembly ─────────────────────────────────────────────────────────────

_CSS = """
/* ── Architecture view ────────────────────────── */
.sys-wrap { display: flex; gap: 20px; align-items: flex-start; }
.sys-main { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; gap: 12px; }
.sys-diagram { background: var(--white); border: var(--border); border-radius: 12px; padding: 20px; overflow-x: auto; }
.sys-sidebar { flex: 0 0 260px; display: flex; flex-direction: column; gap: 12px; }

/* ── Workspace (architecture home base) ───────── */
.sys-workspace { display: flex; gap: 20px; align-items: flex-start; }
.sys-left-dock { flex: 0 0 200px; display: flex; flex-direction: column; gap: 12px; }
.sys-canvas { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; gap: 12px; }
.sys-right-dock { flex: 0 0 280px; display: flex; flex-direction: column; gap: 12px; }
#sys-anim-layer { pointer-events: none; }

/* ── Inspector dock panels ─────────────────────── */
.sys-dock-empty { color: var(--gray-500); font-size: 12px; text-align: center; padding: 32px 16px;
            font-family: var(--mono); background: var(--white); border: var(--border);
            border-radius: 12px; border-style: dashed; }
.sys-dock-panel { position: relative; }
.sys-dock-panel-bar { display: flex; align-items: center; justify-content: space-between;
            font-family: var(--mono); font-size: 10px; color: var(--gray-500);
            text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 8px; }
.sys-dock-close { background: none; border: none; color: var(--gray-500); cursor: pointer;
            font-size: 14px; line-height: 1; padding: 0 4px; }
.sys-dock-close:hover { color: var(--slate); }

/* ── Toolbar (on-demand panel launchers) ───────── */
.sys-toolbar { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.sys-tool-btn { font-family: var(--mono); font-size: 11px; border: var(--border); background: var(--white);
            border-radius: 6px; padding: 5px 12px; cursor: pointer; color: var(--slate); }
.sys-tool-btn:hover { background: var(--gray-100); }

/* ── Query bar (canvas search/highlight) ────────── */
.sys-querybar { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.sys-query-input { font-family: var(--mono); font-size: 12px; border: var(--border); border-radius: 6px;
            padding: 6px 12px; background: var(--white); color: var(--slate); flex: 1 1 320px; min-width: 200px; }
.sys-query-status { font-family: var(--mono); font-size: 11px; color: var(--gray-500); }

/* ── Query/trace highlight (canvas) ─────────────── */
.sys-dim { opacity: 0.18; transition: opacity 0.15s; }
.sys-trace-highlight .sys-nr, .sys-trace-highlight .sys-er-path {
    stroke-width: 3px !important;
    filter: drop-shadow(0 0 4px rgba(217,119,87,0.6));
}

/* ── Animation tokens & pulse ───────────────────── */
.sys-token { pointer-events: none; }
@keyframes sys-pulse {
    0%, 100% { filter: none; }
    50%       { filter: drop-shadow(0 0 8px rgba(59,130,246,0.75)); }
}
.sys-pulse { animation: sys-pulse 0.55s ease; }
@keyframes sys-pulse-fail {
    0%, 100% { filter: none; }
    50%       { filter: drop-shadow(0 0 8px rgba(176,74,63,0.75)); }
}
.sys-pulse-fail { animation: sys-pulse-fail 0.55s ease; }

/* ── Playback strip ──────────────────────────────── */
#sys-playback-strip { display: none; align-items: center; gap: 10px; flex-wrap: wrap;
    padding: 10px 16px; background: var(--white); border: var(--border); border-radius: 10px;
    margin-top: 10px; font-family: var(--mono); font-size: 11px; color: var(--slate); }
#sys-playback-strip .sys-pb-title { font-weight: 600; white-space: nowrap; }
#sys-playback-strip .sys-pb-counter { color: var(--gray-500); white-space: nowrap; }
#sys-playback-scrub { flex: 1 1 120px; min-width: 80px; cursor: pointer; }
#sys-playback-label { flex: 1 1 220px; color: var(--gray-700); overflow: hidden;
    text-overflow: ellipsis; white-space: nowrap; }
.sys-anim-btn { font-size: 10px !important; padding: 3px 8px !important; }

/* ── Floating panels (on-demand views) ──────────── */
.sys-float-panel { position: fixed; background: var(--white); border: var(--border); border-radius: 12px;
            box-shadow: 0 10px 32px rgba(20,20,19,0.16); width: min(820px, 90vw); max-height: 80vh;
            display: flex; flex-direction: column; overflow: hidden; }
.sys-float-bar { display: flex; align-items: center; justify-content: space-between; cursor: move;
            font-family: var(--mono); font-size: 11px; color: var(--gray-700); font-weight: 500;
            padding: 8px 14px; border-bottom: var(--border); background: var(--gray-100);
            border-radius: 12px 12px 0 0; flex: 0 0 auto; }
.sys-float-body { padding: 16px; overflow: auto; }

/* ── Filter bar (architecture) ────────────────── */
.sys-arch-filters { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }

/* ── Filter chips (shared) ────────────────────── */
.sys-fl { font-family: var(--mono); font-size: 10px; color: var(--gray-500); }
.sys-fc { font-family: var(--mono); font-size: 11px; border: 1.5px solid currentColor;
          background: none; border-radius: 100px; padding: 2px 10px;
          cursor: pointer; opacity: 0.3; transition: opacity 0.1s; }
.sys-fc.active { opacity: 1; background: rgba(0,0,0,0.03); }

/* ── Detail panel ─────────────────────────────── */
.sys-panel { background: var(--white); border: var(--border); border-radius: 12px; padding: 18px; }
.sys-ph { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.sys-plabel { font-family: var(--serif); font-size: 15px; font-weight: 600; flex: 1; }
.sys-kbadge { font-family: var(--mono); font-size: 10px; border: 1px solid; border-radius: 4px; padding: 2px 6px; }
.sys-pdesc { font-size: 13px; color: var(--gray-700); margin: 0 0 10px; line-height: 1.5; }
.sys-meta { display: grid; grid-template-columns: auto 1fr; gap: 3px 12px; font-size: 12px; margin: 0 0 10px; }
.sys-meta dt { color: var(--gray-500); font-family: var(--mono); }
.sys-meta dd { color: var(--slate); margin: 0; }
.sys-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px; }
.sys-tag { font-family: var(--mono); font-size: 10px; background: var(--gray-100); color: var(--gray-700); border-radius: 4px; padding: 2px 7px; }
.sys-edges { border-top: 1px solid var(--gray-100); padding-top: 10px; }
.sys-eg-label { font-family: var(--mono); font-size: 10px; color: var(--gray-500); margin: 6px 0 3px; }
.sys-er { font-size: 12px; color: var(--gray-700); display: flex; gap: 8px; align-items: baseline; padding: 2px 0; }
.sys-ek { font-family: var(--mono); font-size: 10px; color: var(--gray-500); }

/* ── Node interaction ─────────────────────────── */
.sys-nr { transition: filter 0.12s; }
.sys-node:hover .sys-nr { filter: brightness(0.94); }
.sys-node.active .sys-nr { stroke-width: 2.5px !important; filter: brightness(0.91); }
.sys-node.filtered-out { opacity: 0.12; pointer-events: none; }

/* ── Hint / placeholder ───────────────────────── */
.sys-hint { color: var(--gray-500); font-size: 12px; text-align: center; padding: 32px 16px;
            font-family: var(--mono); background: var(--white); border: var(--border);
            border-radius: 12px; border-style: dashed; }

/* ── Legend ───────────────────────────────────── */
.sys-legend { background: var(--white); border: var(--border); border-radius: 12px; padding: 14px 18px; }
.sys-leg-group { margin-bottom: 10px; }
.sys-leg-group:last-child { margin-bottom: 0; }
.sys-leg-title { font-family: var(--mono); font-size: 10px; color: var(--gray-500); margin-bottom: 5px; }
.sys-leg-row { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--gray-700); padding: 2px 0; }
.sys-leg-row span:first-child { width: 16px; text-align: center; font-size: 12px; }
.sys-leg-line { display: inline-block; width: 20px; border-top: 2px solid; height: 0; }

/* ── Component list ───────────────────────────── */
.sys-clist { display: flex; flex-direction: column; gap: 14px; }
.sys-filters { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.sys-tbl-wrap { overflow-x: auto; background: var(--white); border: var(--border); border-radius: 12px; }
.sys-ctable { width: 100%; border-collapse: collapse; font-size: 13px; }
.sys-ctable th { font-family: var(--mono); font-size: 10px; color: var(--gray-500); text-align: left;
                 padding: 10px 14px; border-bottom: 1.5px solid var(--gray-300); white-space: nowrap; }
.sys-ctable td { padding: 9px 14px; border-bottom: 1px solid var(--gray-100); vertical-align: top; }
.sys-ctable tbody tr:last-child td { border-bottom: none; }
.sys-cr:hover td { background: var(--gray-100); }
.sys-mono { font-family: var(--mono); font-size: 12px; color: var(--gray-700); }
.sys-dc { font-size: 12px; color: var(--gray-500); max-width: 280px; }

/* ── Layer diagram view ───────────────────────── */
.sys-layer-wrap { background: var(--white); border: var(--border); border-radius: 12px; padding: 20px; overflow-x: auto; }

/* ── Code detail view ──────────────────────────── */
.sys-cd-wrap { display: flex; flex-direction: column; gap: 14px; }
.sys-cd-controls { display: flex; align-items: center; gap: 10px; }
.sys-cd-sel { font-family: var(--mono); font-size: 12px; border: var(--border); border-radius: 6px;
              padding: 5px 12px; background: var(--white); color: var(--slate); cursor: pointer;
              appearance: none; -webkit-appearance: none; }
.sys-cd-panel { display: flex; flex-direction: column; gap: 12px; }

/* ── Dependency matrix ────────────────────────── */
.sys-matrix-wrap { overflow-x: auto; background: var(--white); border: var(--border); border-radius: 12px; }
.sys-mtx { border-collapse: collapse; font-size: 12px; white-space: nowrap; }
.sys-mh0 { min-width: 160px; }
.sys-mth { padding: 0; vertical-align: bottom; border-left: 1px solid var(--gray-100); }
.sys-mth-inner { writing-mode: vertical-rl; transform: rotate(180deg); padding: 12px 8px 8px;
                  font-family: var(--mono); font-size: 11px; display: flex; align-items: center;
                  gap: 4px; color: var(--gray-700); }
.sys-mrh { padding: 8px 14px; font-family: var(--mono); font-size: 12px; white-space: nowrap;
           border-right: 1.5px solid var(--gray-300); color: var(--gray-700); border-bottom: 1px solid var(--gray-100); }
.sys-mc  { padding: 7px 10px; text-align: center; border-left: 1px solid var(--gray-100);
           border-bottom: 1px solid var(--gray-100); font-family: var(--mono); font-size: 10px; min-width: 64px; }
.sys-mc-hit { font-weight: 500; }
.sys-mtx thead tr { border-bottom: 1.5px solid var(--gray-300); }
.sys-mtx thead th { border-bottom: 1.5px solid var(--gray-300); }

/* ── Description ──────────────────────────────── */
.sys-desc { font-size: 14px; color: var(--gray-700); margin: 0 0 20px; line-height: 1.6; }

/* ── Filter bar separator ─────────────────────── */
.sys-fl-sep { display: inline-block; width: 1px; height: 16px; background: var(--gray-300); margin: 0 6px; vertical-align: middle; }

/* ── Code snippet in detail panel ─────────────── */
.sys-sig { margin: 10px 0 6px; padding: 6px 10px; background: var(--gray-100); border-left: 3px solid var(--clay); border-radius: 0 4px 4px 0; }
.sys-sig code { font-family: var(--mono); font-size: 12px; color: var(--slate); }
.sys-snippet { margin: 6px 0 0; }
.sys-snippet pre { margin: 0; padding: 10px 12px; background: var(--ivory); border: var(--border); border-radius: 8px; overflow-x: auto; max-height: 320px; font-size: 0.78rem; line-height: 1.5; }
.sys-snippet pre code { font-family: var(--mono); }

/* ── Behavior / traces view ───────────────────── */
.sys-behavior-wrap { display: flex; flex-direction: column; gap: 14px; }
.sys-behavior-controls { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.sys-behavior-sel { font-family: var(--mono); font-size: 12px; border: var(--border); border-radius: 6px;
                    padding: 5px 12px; background: var(--white); color: var(--slate); cursor: pointer;
                    appearance: none; -webkit-appearance: none; }
.sys-behavior-toggle { font-family: var(--mono); font-size: 11px; color: var(--gray-700);
                       display: flex; align-items: center; gap: 5px; cursor: pointer; }
.sys-behavior-traces { display: flex; flex-direction: column; gap: 16px; }
.sys-trace-panel { background: var(--white); border: var(--border); border-radius: 12px; padding: 16px 20px; display: flex; flex-direction: column; gap: 10px; }
.sys-trace-header { display: flex; align-items: center; gap: 10px; }
.sys-trace-title { font-family: var(--serif); font-size: 14px; font-weight: 600; }
.sys-trace-diagram { overflow-x: auto; }
.sys-trace-facts { border-top: 1px solid var(--gray-100); padding-top: 8px; }

/* ── Changes tab ──────────────────────────────── */
.sys-changes { display: flex; flex-direction: column; gap: 24px; }
.sys-chg-section { background: var(--white); border: var(--border); border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.sys-chg-header { font-family: var(--mono); font-size: 12px; font-weight: 600; padding: 4px 0 4px 10px; border-left: 3px solid; letter-spacing: 0.04em; text-transform: uppercase; }
.sys-chg-node { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.sys-chg-label { font-family: var(--serif); font-size: 14px; }
.sys-chg-fp { font-family: var(--mono); font-size: 11px; color: var(--gray-500); }
.sys-chg-pre { margin: 4px 0 0; padding: 10px 12px; background: var(--ivory); border: var(--border); border-radius: 8px; overflow-x: auto; max-height: 360px; font-size: 0.78rem; line-height: 1.5; }
.sys-chg-pre code { font-family: var(--mono); }
.sys-chg-diff { display: flex; gap: 12px; flex-wrap: wrap; }
.sys-chg-side { flex: 1 1 340px; display: flex; flex-direction: column; gap: 4px; }
.sys-chg-side-label { font-family: var(--mono); font-size: 10px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; }
"""

_JS = """
/* ── Node click (architecture, opens/focuses an Inspector panel) ──────── */
/* Multiple inspector panels can be open at once — clicking a node toggles
   its own panel without closing others. */
function sysClick(el) {
    var nid = el.getAttribute('data-id');
    var existing = document.getElementById('inspector-' + nid);
    if (existing) {
        existing.remove();
        el.classList.remove('active');
        sysDockUpdateEmpty(el);
        return;
    }
    el.classList.add('active');
    sysOpenInspector(el, nid);
}

function sysDockUpdateEmpty(el) {
    var workspace = el.closest('.sys-workspace');
    if (!workspace) return;
    var dock = workspace.querySelector('.sys-right-dock');
    var empty = workspace.querySelector('.sys-dock-empty');
    if (!dock || !empty) return;
    var hasPanels = dock.querySelectorAll('.sys-dock-panel').length > 0;
    empty.style.display = hasPanels ? 'none' : 'block';
}

/* ── Panel manager: mounts Inspector instances into the right dock ─────── */
function sysOpenInspector(el, nid) {
    var workspace = el.closest('.sys-workspace');
    if (!workspace) return;
    var template = document.getElementById('panel-' + nid);
    var dock = workspace.querySelector('.sys-right-dock');
    if (!template || !dock) return;

    var clone = template.cloneNode(true);
    clone.id = 'inspector-' + nid;
    clone.classList.add('sys-dock-panel');
    clone.style.display = 'block';

    var bar = document.createElement('div');
    bar.className = 'sys-dock-panel-bar';
    bar.innerHTML = '<span>Inspector</span>';
    var closeBtn = document.createElement('button');
    closeBtn.className = 'sys-dock-close';
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.textContent = '\\u00d7';
    closeBtn.onclick = function() { sysCloseInspector(workspace, nid); };
    bar.appendChild(closeBtn);
    clone.insertBefore(bar, clone.firstChild);

    dock.appendChild(clone);
    sysDockUpdateEmpty(el);
}

function sysCloseInspector(workspace, nid) {
    var panel = workspace.querySelector('#inspector-' + nid);
    if (panel) panel.remove();
    var node = workspace.querySelector('.sys-node[data-id="' + nid + '"]');
    if (node) {
        node.classList.remove('active');
        sysDockUpdateEmpty(node);
    }
}

/* ── Architecture kind + status filters ─────────── */
function sysAKind(btn) {
    btn.classList.toggle('active');
    _applyArchFilter();
}
function sysAStatus(btn) {
    btn.classList.toggle('active');
    _applyArchFilter();
}
function _applyArchFilter() {
    var kinds = new Set();
    document.querySelectorAll('.sys-fc[data-ak].active').forEach(function(b) { kinds.add(b.getAttribute('data-ak')); });
    var statuses = new Set();
    document.querySelectorAll('.sys-fc[data-as].active').forEach(function(b) { statuses.add(b.getAttribute('data-as')); });
    var hasKindFilter   = document.querySelectorAll('.sys-fc[data-ak]').length > 0;
    var hasStatusFilter = document.querySelectorAll('.sys-fc[data-as]').length > 0;
    document.querySelectorAll('.sys-node').forEach(function(n) {
        var k = n.getAttribute('data-kind');
        var s = n.getAttribute('data-status') || '';
        var kOk = !hasKindFilter   || kinds.size === 0    || kinds.has(k);
        var sOk = !hasStatusFilter || statuses.size === 0 || !s || statuses.has(s);
        n.classList.toggle('filtered-out', !(kOk && sOk));
    });
}

/* ── Floating panels (on-demand views) ──────────── */
var _floatPanels = {};
var _floatZTop = 200;
function sysToggleFloatingPanel(type, title) {
    var existing = document.getElementById('float-' + type);
    if (existing) {
        var existingBody = existing.querySelector('.sys-float-body');
        var existingTemplate = document.getElementById('tpl-' + type);
        if (existingBody && existingTemplate) {
            while (existingBody.firstChild) existingTemplate.appendChild(existingBody.firstChild);
        }
        existing.remove();
        delete _floatPanels[type];
        return;
    }
    var template = document.getElementById('tpl-' + type);
    if (!template) return;

    var panel = document.createElement('div');
    panel.id = 'float-' + type;
    panel.className = 'sys-float-panel';
    _floatZTop += 1;
    panel.style.zIndex = _floatZTop;
    var n = Object.keys(_floatPanels).length;
    panel.style.top  = (64 + n * 28) + 'px';
    panel.style.left = (80 + n * 28) + 'px';

    var bar = document.createElement('div');
    bar.className = 'sys-float-bar';
    var titleEl = document.createElement('span');
    titleEl.textContent = title;
    bar.appendChild(titleEl);
    var closeBtn = document.createElement('button');
    closeBtn.className = 'sys-dock-close';
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.textContent = '\\u00d7';
    closeBtn.onclick = function() {
        while (body.firstChild) template.appendChild(body.firstChild);
        panel.remove();
        delete _floatPanels[type];
    };
    bar.appendChild(closeBtn);
    panel.appendChild(bar);

    var body = document.createElement('div');
    body.className = 'sys-float-body';
    while (template.firstChild) body.appendChild(template.firstChild);
    panel.appendChild(body);

    panel.addEventListener('mousedown', function() {
        _floatZTop += 1;
        panel.style.zIndex = _floatZTop;
    });
    sysMakeDraggable(panel, bar);

    document.body.appendChild(panel);
    _floatPanels[type] = panel;
}

function sysMakeDraggable(panel, handle) {
    var dragging = false, startX, startY, origX, origY;
    handle.addEventListener('mousedown', function(e) {
        dragging = true;
        startX = e.clientX;
        startY = e.clientY;
        var rect = panel.getBoundingClientRect();
        origX = rect.left;
        origY = rect.top;
        e.preventDefault();
    });
    document.addEventListener('mousemove', function(e) {
        if (!dragging) return;
        panel.style.left = (origX + e.clientX - startX) + 'px';
        panel.style.top  = (origY + e.clientY - startY) + 'px';
    });
    document.addEventListener('mouseup', function() { dragging = false; });
}

/* ── Overlay registry (scaffolding) ─────────────── */
/* Kind/status filters are the first two overlays. Additional overlays
   (failure paths, ownership, dataflow, dependencies) register here in
   later phases; each `apply` recomputes from scratch over .sys-node. */
var OVERLAYS = {
    'kind-filter':   { label: 'Kind filter',   apply: _applyArchFilter },
    'status-filter': { label: 'Status filter', apply: _applyArchFilter }
};
function sysOverlayToggle(overlayId) {
    var overlay = OVERLAYS[overlayId];
    if (overlay) overlay.apply();
}

/* ── Query bar (canvas search / trace exploration) ─────────────────────────── */
var _sysGraphData = null;
function sysGraphData() {
    if (_sysGraphData) return _sysGraphData;
    var el = document.getElementById('sys-graph-data');
    _sysGraphData = el ? JSON.parse(el.textContent) : { positions: {}, nodes: [], edges: [] };
    return _sysGraphData;
}

var _sysBehaviorData = null;
var _sysBehaviorTraces = [];
function sysBehaviorDataGet() {
    if (_sysBehaviorData) return _sysBehaviorData;
    var el = document.getElementById('sys-behavior-data');
    _sysBehaviorData = el ? JSON.parse(el.textContent) : null;
    return _sysBehaviorData;
}

function sysQueryStatus(msg) {
    var el = document.getElementById('sys-query-status');
    if (el) el.textContent = msg;
}

function sysQueryClearAll() {
    document.querySelectorAll('.sys-node, .sys-edge').forEach(function(el) {
        el.classList.remove('sys-dim', 'sys-trace-highlight');
    });
}

function sysQueryClear() {
    sysQueryClearAll();
    sysQueryStatus('');
    var input = document.getElementById('sys-query-input');
    if (input) input.value = '';
}

function sysQuerySetHighlight(nodeIds, edgeKeys) {
    document.querySelectorAll('.sys-node').forEach(function(el) {
        if (nodeIds.has(el.getAttribute('data-id'))) {
            el.classList.remove('sys-dim');
            el.classList.add('sys-trace-highlight');
        } else {
            el.classList.add('sys-dim');
            el.classList.remove('sys-trace-highlight');
        }
    });
    document.querySelectorAll('.sys-edge').forEach(function(el) {
        var key = el.getAttribute('data-from') + '|' + el.getAttribute('data-to');
        if (edgeKeys.has(key)) {
            el.classList.remove('sys-dim');
            el.classList.add('sys-trace-highlight');
        } else {
            el.classList.add('sys-dim');
            el.classList.remove('sys-trace-highlight');
        }
    });
}

function sysFindNodes(text) {
    var t = text.toLowerCase();
    return sysGraphData().nodes.filter(function(n) {
        return n.id.toLowerCase().indexOf(t) !== -1 || (n.label || '').toLowerCase().indexOf(t) !== -1;
    });
}

function sysComponentEdgeKeys(nodeIds) {
    var edgeKeys = new Set();
    sysGraphData().edges.forEach(function(e) {
        if (nodeIds.has(e.from) && nodeIds.has(e.to)) edgeKeys.add(e.from + '|' + e.to);
    });
    return edgeKeys;
}

function sysQueryComponent(text) {
    var matches = sysFindNodes(text);
    if (!matches.length) {
        sysQueryStatus('No component matching "' + text + '"');
        sysQueryClearAll();
        return;
    }
    var data = sysGraphData();
    var nodeIds = new Set(matches.map(function(n) { return n.id; }));
    var edgeKeys = new Set();
    data.edges.forEach(function(e) {
        if (nodeIds.has(e.from) || nodeIds.has(e.to)) {
            edgeKeys.add(e.from + '|' + e.to);
            nodeIds.add(e.from);
            nodeIds.add(e.to);
        }
    });
    sysQuerySetHighlight(nodeIds, edgeKeys);
    sysQueryStatus(matches.length + ' component(s), ' + edgeKeys.size + ' connection(s) highlighted');
}

function sysGraphPath(fromText, toText) {
    var data = sysGraphData();
    var fromMatches = sysFindNodes(fromText);
    var toMatches = sysFindNodes(toText);
    if (!fromMatches.length || !toMatches.length) {
        sysQueryStatus('Could not resolve "' + fromText + '" -> "' + toText + '"');
        sysQueryClearAll();
        return;
    }
    var fromId = fromMatches[0].id, toId = toMatches[0].id;

    function bfs(adj) {
        var queue = [[fromId]];
        var visited = new Set([fromId]);
        while (queue.length) {
            var p = queue.shift();
            var last = p[p.length - 1];
            if (last === toId) return p;
            (adj[last] || []).forEach(function(n) {
                if (!visited.has(n)) { visited.add(n); queue.push(p.concat([n])); }
            });
        }
        return null;
    }

    var adjDirected = {};
    data.edges.forEach(function(e) { (adjDirected[e.from] = adjDirected[e.from] || []).push(e.to); });
    var path = bfs(adjDirected);
    if (!path) {
        var adjUndirected = {};
        data.edges.forEach(function(e) {
            (adjUndirected[e.from] = adjUndirected[e.from] || []).push(e.to);
            (adjUndirected[e.to] = adjUndirected[e.to] || []).push(e.from);
        });
        path = bfs(adjUndirected);
    }
    if (!path) {
        sysQueryStatus('No path found from ' + fromId + ' to ' + toId);
        sysQueryClearAll();
        return;
    }
    var nodeIds = new Set(path);
    var edgeKeys = new Set();
    for (var i = 0; i < path.length - 1; i++) {
        edgeKeys.add(path[i] + '|' + path[i + 1]);
        edgeKeys.add(path[i + 1] + '|' + path[i]);
    }
    sysQuerySetHighlight(nodeIds, edgeKeys);
    sysQueryStatus('Path: ' + path.join(' -> '));
}

/* All traces reachable from an empty initial state, with no goal (everything
   ends up in `failed` since goal_fact is null — used here as "all explored
   traces", not as a literal failure indicator). */
function sysQueryAllTraces() {
    var data = sysBehaviorDataGet();
    if (!data || !data.actions || !data.actions.length) return null;
    var result = sysDeriveTraces(data.actions, { initial_facts: [], goal_fact: null }, 8, 200);
    return result.completed.concat(result.failed);
}

function sysTraceComponents(trace) {
    var comps = new Set();
    trace.history.forEach(function(step) {
        comps.add(step.action.component);
        (step.action.touches || []).forEach(function(c) { comps.add(c); });
    });
    return comps;
}

function sysQueryFact(name, negate) {
    var traces = sysQueryAllTraces();
    if (!traces) { sysQueryStatus('No behavior/actions defined'); sysQueryClearAll(); return; }
    var matching = traces.filter(function(tr) {
        var has = tr.state.has(name);
        return negate ? !has : has;
    });
    if (!matching.length) {
        sysQueryStatus('No traces ' + (negate ? 'excluding ' : 'including ') + '"' + name + '"');
        sysQueryClearAll();
        return;
    }
    var nodeIds = new Set();
    matching.forEach(function(tr) { sysTraceComponents(tr).forEach(function(c) { nodeIds.add(c); }); });
    sysQuerySetHighlight(nodeIds, sysComponentEdgeKeys(nodeIds));
    sysQueryStatus(matching.length + ' trace(s) ' + (negate ? 'without ' : 'with ') + '"' + name + '" — ' + nodeIds.size + ' component(s) highlighted');
}

function sysQueryFailure(text) {
    var traces = sysQueryAllTraces();
    if (!traces) { sysQueryStatus('No behavior/actions defined'); sysQueryClearAll(); return; }
    var t = text.toLowerCase();
    var matching = traces.filter(function(tr) {
        return tr.history.some(function(step) {
            var o = step.outcome;
            if (!o._origin) return false;
            if (!t) return true;
            var hay = (o.id + ' ' + o.label + ' ' + (o.emits || []).join(' ')).toLowerCase();
            return hay.indexOf(t) !== -1;
        });
    });
    if (!matching.length) {
        sysQueryStatus('No failure traces matching "' + text + '"');
        sysQueryClearAll();
        return;
    }
    var nodeIds = new Set();
    matching.forEach(function(tr) { sysTraceComponents(tr).forEach(function(c) { nodeIds.add(c); }); });
    sysQuerySetHighlight(nodeIds, sysComponentEdgeKeys(nodeIds));
    sysQueryStatus(matching.length + ' failure trace(s) matching "' + text + '" — ' + nodeIds.size + ' component(s) highlighted');
}

function sysQueryAction(text) {
    var traces = sysQueryAllTraces();
    if (!traces) { sysQueryStatus('No behavior/actions defined'); sysQueryClearAll(); return; }
    var t = text.toLowerCase();
    var matching = traces.filter(function(tr) {
        return tr.history.some(function(step) {
            return (step.action.id + ' ' + step.action.label).toLowerCase().indexOf(t) !== -1;
        });
    });
    if (!matching.length) {
        sysQueryStatus('No traces with action matching "' + text + '"');
        sysQueryClearAll();
        return;
    }
    var nodeIds = new Set();
    matching.forEach(function(tr) { sysTraceComponents(tr).forEach(function(c) { nodeIds.add(c); }); });
    sysQuerySetHighlight(nodeIds, sysComponentEdgeKeys(nodeIds));
    sysQueryStatus(matching.length + ' trace(s) with action matching "' + text + '" — ' + nodeIds.size + ' component(s) highlighted');
}

function sysQueryRun() {
    var input = document.getElementById('sys-query-input');
    if (!input) return;
    var q = input.value.trim();
    if (!q) { sysQueryClearAll(); sysQueryStatus(''); return; }
    var m;
    if ((m = q.match(/^path\\s*:\\s*(.+?)\\s*->\\s*(.+)$/i))) {
        sysGraphPath(m[1].trim(), m[2].trim());
    } else if ((m = q.match(/^component\\s*:\\s*(.+)$/i))) {
        sysQueryComponent(m[1].trim());
    } else if ((m = q.match(/^not\\s*:\\s*(.+)$/i))) {
        sysQueryFact(m[1].trim(), true);
    } else if ((m = q.match(/^fact\\s*:\\s*(.+)$/i))) {
        sysQueryFact(m[1].trim(), false);
    } else if ((m = q.match(/^failure\\s*:\\s*(.+)$/i))) {
        sysQueryFailure(m[1].trim());
    } else if ((m = q.match(/^action\\s*:\\s*(.+)$/i))) {
        sysQueryAction(m[1].trim());
    } else {
        sysQueryComponent(q);
    }
}

/* ── Animation layer helpers (Phase 4) ─────────────────────────────────────── */
function sysAnimLayer() {
    return document.getElementById('sys-anim-layer') ||
           document.querySelector('[id$="sys-anim-layer"]');
}
function sysAnimClear() {
    var layer = sysAnimLayer();
    if (layer) layer.innerHTML = '';
}

function sysBezierPt(sx, sy, cx1, cy1, cx2, cy2, ex, ey, t) {
    var mt = 1 - t;
    return {
        x: mt*mt*mt*sx + 3*mt*mt*t*cx1 + 3*mt*t*t*cx2 + t*t*t*ex,
        y: mt*mt*mt*sy + 3*mt*mt*t*cy1 + 3*mt*t*t*cy2 + t*t*t*ey
    };
}

/* Animate a single step token from step.from to step.to along the same
   bezier used by the architecture SVG edges. Calls onDone when finished. */
function sysStepAnimate(step, onDone) {
    var pos = sysGraphData().positions;
    var src = pos[step.from], dst = pos[step.to];
    if (!src || !dst) { if (onDone) onDone(); return; }
    var layer = sysAnimLayer();
    if (!layer) { if (onDone) onDone(); return; }

    /* Match Python edge coords: src center → bottom edge, dst center → top edge */
    var sx = src.x, sy = src.y + src.h / 2;
    var ex = dst.x, ey = dst.y - dst.h / 2;
    var dy = ey - sy;
    var cx1 = sx, cy1 = sy + dy * 0.45;
    var cx2 = ex, cy2 = ey - dy * 0.45;

    var isLoop = step.from === step.to;
    var fail   = !!step.failure;
    var fill   = fail ? '#B04A3F' : '#3B82F6';

    var circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('r', '6');
    circle.setAttribute('fill', fill);
    circle.setAttribute('class', 'sys-token');
    layer.appendChild(circle);

    var dur = 700, start = null;
    function frame(ts) {
        if (!start) start = ts;
        var t = Math.min((ts - start) / dur, 1);
        var pt;
        if (isLoop) {
            /* Self-loop: swing out to the right and back */
            pt = { x: src.x + src.w * 0.6 * Math.sin(Math.PI * t), y: src.y + 10 * Math.sin(2 * Math.PI * t) };
        } else {
            pt = sysBezierPt(sx, sy, cx1, cy1, cx2, cy2, ex, ey, t);
        }
        circle.setAttribute('cx', pt.x.toFixed(1));
        circle.setAttribute('cy', pt.y.toFixed(1));
        if (t < 1) {
            requestAnimationFrame(frame);
        } else {
            sysNodePulse(step.to, fail);
            setTimeout(function() {
                if (layer.contains(circle)) layer.removeChild(circle);
                if (onDone) onDone();
            }, 180);
        }
    }
    requestAnimationFrame(frame);
}

function sysNodePulse(nid, fail) {
    var node = document.querySelector('.sys-node[data-id="' + nid + '"]');
    if (!node) return;
    var cls = fail ? 'sys-pulse-fail' : 'sys-pulse';
    node.classList.remove('sys-pulse', 'sys-pulse-fail');
    void node.offsetWidth; /* force reflow to restart animation */
    node.classList.add(cls);
    setTimeout(function() { node.classList.remove(cls); }, 600);
}

/* ── Trace stepper ───────────────────────────────── */
var _stepper = { steps: [], idx: -1, playing: false, animPending: false };

function sysStepperLoad(steps, title) {
    _stepper.steps = steps;
    _stepper.idx   = -1;
    _stepper.playing     = false;
    _stepper.animPending = false;
    sysAnimClear();
    var strip = document.getElementById('sys-playback-strip');
    if (strip) strip.style.display = 'flex';
    var titleEl = document.getElementById('sys-pb-title');
    if (titleEl) titleEl.textContent = title || 'Trace';
    sysStepperUpdateUI();
    sysStepperPlay();
}

function sysStepperLoadTrace(idx) {
    var trace = _sysBehaviorTraces[idx];
    if (!trace) return;
    sysStepperLoad(sysTraceToSteps(trace.history), 'Trace ' + (idx + 1));
}

function sysStepperUpdateUI() {
    var idx   = _stepper.idx;
    var total = _stepper.steps.length;
    var counter = document.getElementById('sys-pb-counter');
    if (counter) counter.textContent = Math.max(0, idx) + ' / ' + total;
    var label = document.getElementById('sys-pb-label');
    if (label) {
        var step = _stepper.steps[idx] || null;
        label.textContent = step ? (step.label || (step.from + ' → ' + step.to)) : '';
    }
    var scrub = document.getElementById('sys-playback-scrub');
    if (scrub) { scrub.max = Math.max(0, total - 1); scrub.value = Math.max(0, idx); }
    var btn = document.getElementById('sys-play-btn');
    if (btn) btn.textContent = _stepper.playing ? '\\u23f8' : '\\u25b6';
}

function sysStepperAdvance() {
    if (_stepper.animPending) return;
    if (_stepper.idx + 1 >= _stepper.steps.length) {
        _stepper.playing = false;
        sysStepperUpdateUI();
        return;
    }
    _stepper.idx++;
    _stepper.animPending = true;
    sysStepperUpdateUI();
    sysStepAnimate(_stepper.steps[_stepper.idx], function() {
        _stepper.animPending = false;
        if (_stepper.playing) setTimeout(sysStepperAdvance, 250);
    });
}

function sysStepperPlay() {
    if (_stepper.playing) return;
    _stepper.playing = true;
    sysStepperUpdateUI();
    sysStepperAdvance();
}
function sysStepperPause() { _stepper.playing = false; sysStepperUpdateUI(); }
function sysStepperToggle() { if (_stepper.playing) sysStepperPause(); else sysStepperPlay(); }
function sysStepperPrev() {
    if (_stepper.idx <= 0) return;
    _stepper.playing = false;
    _stepper.idx--;
    sysAnimClear();
    sysStepperUpdateUI();
}
function sysStepperNext() { _stepper.playing = false; sysStepperAdvance(); }
function sysStepperSeek(val) {
    _stepper.playing = false;
    _stepper.idx = parseInt(val, 10);
    sysAnimClear();
    sysStepperUpdateUI();
}
function sysStepperClose() {
    _stepper.playing = false;
    sysAnimClear();
    var strip = document.getElementById('sys-playback-strip');
    if (strip) strip.style.display = 'none';
}

/* ── State explorer ─────────────────────────────── */
var _stateExp = { facts: null, selected: null };

function sysStateExpContainer() { return document.getElementById('sys-state-exp'); }

function sysStateExpRender() {
    var container = sysStateExpContainer();
    if (!container) return;
    var data = sysBehaviorDataGet();
    if (!data || !data.actions) {
        container.innerHTML = '<p class="sys-mono" style="color:var(--gray-500)">No behavior data.</p>';
        return;
    }

    /* Initialise with empty facts on first open */
    if (_stateExp.facts === null) _stateExp.facts = new Set();

    var html = '';

    /* Scenario reset row */
    if (data.scenarios && data.scenarios.length) {
        html += '<div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:12px">';
        html += '<span class="sys-fl">Reset to:</span>';
        data.scenarios.forEach(function(sc) {
            html += '<button class="sys-tool-btn" onclick="sysStateExpReset(\\'' + sc.id + '\\')">' + sysEsc(sc.label) + '</button>';
        });
        html += '<button class="sys-tool-btn" onclick="sysStateExpReset(null)">Empty</button>';
        html += '</div>';
    }

    /* Current facts */
    var facts = _stateExp.facts ? Array.from(_stateExp.facts).sort() : [];
    html += '<div style="margin-bottom:12px"><span class="sys-eg-label">Current facts</span>';
    html += '<div class="sys-tags" style="margin-top:6px">';
    html += facts.length
        ? facts.map(function(f) { return '<span class="sys-tag">' + sysEsc(f) + '</span>'; }).join('')
        : '<span class="sys-tag" style="color:var(--gray-500)">(none)</span>';
    html += '</div></div>';

    if (_stateExp.selected) {
        /* Outcome choices for selected action */
        var a = _stateExp.selected;
        var validOutcomes = (a.outcomes || []).filter(function(o) {
            return (o.requires || []).every(function(f) { return _stateExp.facts.has(f); });
        });
        html += '<div><span class="sys-eg-label">Outcomes for: ' + sysEsc(a.label) + '</span>';
        html += '<div style="display:flex;flex-direction:column;gap:6px;margin-top:8px">';
        validOutcomes.forEach(function(o) {
            var col = o._origin ? '#B04A3F' : '#3B6E4A';
            html += '<button class="sys-tool-btn" style="text-align:left;padding:8px 12px;border-color:' + col + '"'
                  + ' onclick="sysStateExpApply(\\'' + a.id + '\\',\\'' + o.id + '\\')">'
                  + '<span style="color:' + col + '">' + sysEsc(o.label) + '</span>';
            if (o.emits && o.emits.length)
                html += '<br><span class="sys-fl">emits: ' + o.emits.map(sysEsc).join(', ') + '</span>';
            html += '</button>';
        });
        html += '<button class="sys-tool-btn" onclick="sysStateExpCancel()">\\u2190 back</button>';
        html += '</div></div>';
    } else {
        /* Enabled actions */
        var enabled = data.actions.filter(function(a) {
            return (a.preconditions || []).every(function(f) { return _stateExp.facts.has(f); });
        });
        html += '<div><span class="sys-eg-label">Enabled actions (' + enabled.length + ')</span>';
        if (!enabled.length) {
            html += '<p class="sys-mono" style="color:var(--gray-500);margin-top:8px">No actions enabled — try resetting to a scenario.</p>';
        } else {
            html += '<div style="display:flex;flex-direction:column;gap:6px;margin-top:8px">';
            enabled.forEach(function(a) {
                var peers = (a.touches || []).filter(function(t) { return t !== a.component; });
                html += '<button class="sys-tool-btn" style="text-align:left;padding:8px 12px"'
                      + ' onclick="sysStateExpSelect(\\'' + a.id + '\\')">'
                      + '<strong>' + sysEsc(a.label) + '</strong><br>'
                      + '<span class="sys-fl">' + sysEsc(a.component)
                      + (peers.length ? ' \\u2192 ' + peers.map(sysEsc).join(', ') : '') + '</span>'
                      + '</button>';
            });
            html += '</div>';
        }
        html += '</div>';
    }

    container.innerHTML = html;
}

function sysStateExpReset(scenarioId) {
    var data = sysBehaviorDataGet();
    _stateExp.selected = null;
    if (scenarioId && data) {
        var sc = (data.scenarios || []).find(function(s) { return s.id === scenarioId; });
        _stateExp.facts = new Set(sc ? sc.initial_facts || [] : []);
    } else {
        _stateExp.facts = new Set();
    }
    sysAnimClear();
    sysStateExpRender();
}

function sysStateExpSelect(actionId) {
    var data = sysBehaviorDataGet();
    if (!data) return;
    _stateExp.selected = data.actions.find(function(a) { return a.id === actionId; }) || null;
    sysStateExpRender();
}

function sysStateExpCancel() { _stateExp.selected = null; sysStateExpRender(); }

function sysStateExpApply(actionId, outcomeId) {
    var data = sysBehaviorDataGet();
    if (!data) return;
    var action  = data.actions.find(function(a) { return a.id === actionId; });
    var outcome = action && (action.outcomes || []).find(function(o) { return o.id === outcomeId; });
    if (!action || !outcome) return;

    /* Animate the chosen step on the canvas */
    var touches = (action.touches || []).filter(function(t) { return t !== action.component; });
    var to = touches.length ? touches[0] : action.component;
    sysStepAnimate({ from: action.component, to: to, label: action.label + ' \\u2192 ' + outcome.label, failure: !!outcome._origin },
        function() { setTimeout(sysAnimClear, 900); });

    /* Apply effects to fact-set */
    var newFacts = new Set(_stateExp.facts);
    (outcome.effects && outcome.effects.remove || []).forEach(function(f) { newFacts.delete(f); });
    (outcome.effects && outcome.effects.add    || []).forEach(function(f) { newFacts.add(f); });
    _stateExp.facts    = newFacts;
    _stateExp.selected = null;
    sysStateExpRender();
}

/* ── Code detail selector ──────────────────────── */
function sysCodeDetailChange(sel) {
    var val = sel.value;
    document.querySelectorAll('.sys-cd-panel').forEach(function(p) {
        p.style.display = (p.id === 'cdp-' + val) ? '' : 'none';
    });
}

/* ── Component list filters ────────────────────── */
function sysFKind(btn) {
    btn.classList.toggle('active');
    _applyListFilter();
}
function sysFStatus(btn) {
    btn.classList.toggle('active');
    _applyListFilter();
}
function _applyListFilter() {
    var kinds = new Set();
    document.querySelectorAll('.sys-fc[data-fk].active').forEach(function(b) { kinds.add(b.getAttribute('data-fk')); });
    var statuses = new Set();
    document.querySelectorAll('.sys-fc[data-fs].active').forEach(function(b) { statuses.add(b.getAttribute('data-fs')); });
    var hasKindFilter = document.querySelectorAll('.sys-fc[data-fk]').length > 0;
    var hasStatusFilter = document.querySelectorAll('.sys-fc[data-fs]').length > 0;
    document.querySelectorAll('.sys-cr').forEach(function(row) {
        var k = row.getAttribute('data-rkind');
        var s = row.getAttribute('data-rstatus');
        var kOk = !hasKindFilter || kinds.size === 0 || kinds.has(k);
        var sOk = !hasStatusFilter || statuses.size === 0 || !s || statuses.has(s);
        row.style.display = (kOk && sOk) ? '' : 'none';
    });
}

/* ── Behavior / trace derivation ───────────────────────────────────────────── */
var SYS_NODE_STYLES = __NODE_KIND_STYLES__;

function sysEsc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/* Forward BFS over fact-sets. action.preconditions gate whether an action is
   enabled; outcome.requires further gates a specific branch. effects.add/remove
   are applied to the fact-set to produce the next state. */
function sysDeriveTraces(actions, scenario, maxDepth, maxTraces) {
    maxDepth = maxDepth || 12;
    maxTraces = maxTraces || 50;
    var initial = new Set(scenario.initial_facts || []);
    var queue = [{ state: initial, history: [] }];
    var completed = [];
    var failed = [];
    var seen = new Set();

    while (queue.length && completed.length < maxTraces && (completed.length + failed.length) < maxTraces * 4) {
        var node = queue.shift();
        if (scenario.goal_fact && node.state.has(scenario.goal_fact)) {
            completed.push(node);
            continue;
        }
        if (node.history.length >= maxDepth) {
            failed.push(node);
            continue;
        }
        var enabled = actions.filter(function(a) {
            return (a.preconditions || []).every(function(f) { return node.state.has(f); });
        });
        var branched = false;
        for (var ai = 0; ai < enabled.length; ai++) {
            var a = enabled[ai];
            var outcomes = a.outcomes || [];
            for (var oi = 0; oi < outcomes.length; oi++) {
                var o = outcomes[oi];
                if (!(o.requires || []).every(function(f) { return node.state.has(f); })) continue;
                var newState = new Set(node.state);
                (o.effects && o.effects.remove || []).forEach(function(f) { newState.delete(f); });
                (o.effects && o.effects.add || []).forEach(function(f) { newState.add(f); });
                var key = Array.from(newState).sort().join(',') + '|' + a.id + ':' + o.id;
                if (seen.has(key)) continue;
                seen.add(key);
                branched = true;
                queue.push({ state: newState, history: node.history.concat([{ action: a, outcome: o }]) });
            }
        }
        if (!branched) failed.push(node);
    }
    return { completed: completed, failed: failed };
}

/* Compile a derived trace's history into sequence-diagram steps
   (from = action.component, to = a touched component, label = outcome). */
function sysTraceToSteps(history) {
    return history.map(function(step) {
        var a = step.action, o = step.outcome;
        var touches = (a.touches || []).filter(function(t) { return t !== a.component; });
        var to = touches.length ? touches[0] : a.component;
        var label = a.label + ' → ' + o.label;
        if (o.emits && o.emits.length) label += '  [' + o.emits.join(', ') + ']';
        return { from: a.component, to: to, label: label, failure: !!o._origin };
    });
}

function sysSeqSvgJs(steps, nodeById) {
    var COL_W = 140, COL_GAP = 56, HEADER_H = 52, STEP_H = 64, TOP_PAD = 20, SIDE_PAD = 40;
    var participants = [];
    var seen = {};
    steps.forEach(function(s) {
        [s.from, s.to].forEach(function(nid) {
            if (nid && !seen[nid]) { seen[nid] = true; participants.push(nid); }
        });
    });
    var n = participants.length;
    var W = 2 * SIDE_PAD + n * COL_W + Math.max(0, n - 1) * COL_GAP;
    var H = TOP_PAD + HEADER_H + steps.length * STEP_H + 32;
    var colCx = {};
    participants.forEach(function(nid, i) {
        colCx[nid] = SIDE_PAD + i * (COL_W + COL_GAP) + COL_W / 2;
    });
    var LIFE_TOP = TOP_PAD + HEADER_H, LIFE_BOT = H - 16;
    var parts = ['<svg viewBox="0 0 ' + W + ' ' + H + '" style="display:block;width:100%;height:auto;max-height:600px">'];

    participants.forEach(function(nid) {
        var node = nodeById[nid] || {};
        var cx = colCx[nid], x = cx - COL_W / 2;
        var nst = SYS_NODE_STYLES[node.kind] || SYS_NODE_STYLES.__default__;
        var label = sysEsc(node.label || nid);
        var tech = sysEsc(node.tech || '');
        parts.push('<rect x="' + x.toFixed(1) + '" y="' + TOP_PAD + '" width="' + COL_W + '" height="' + HEADER_H +
            '" rx="8" fill="' + nst.fill + '" stroke="' + nst.stroke + '" stroke-width="1.5"/>');
        var lblY = TOP_PAD + HEADER_H / 2 - (tech ? 6 : 0);
        parts.push('<text x="' + cx.toFixed(1) + '" y="' + lblY.toFixed(1) +
            '" text-anchor="middle" dominant-baseline="middle" font-family="ui-serif,Georgia,serif" font-size="12" font-weight="500" fill="#141413">' +
            nst.icon + ' ' + label + '</text>');
        if (tech) {
            parts.push('<text x="' + cx.toFixed(1) + '" y="' + (TOP_PAD + HEADER_H / 2 + 10).toFixed(1) +
                '" text-anchor="middle" font-family="ui-monospace,monospace" font-size="10" fill="#87867F">' + tech + '</text>');
        }
        parts.push('<line x1="' + cx.toFixed(1) + '" y1="' + LIFE_TOP + '" x2="' + cx.toFixed(1) + '" y2="' + LIFE_BOT +
            '" stroke="#D1CFC5" stroke-width="1" stroke-dasharray="4,4"/>');
    });

    steps.forEach(function(step, i) {
        var src = step.from, dst = step.to;
        if (!(src in colCx) || !(dst in colCx)) return;
        var sx = colCx[src], ex = colCx[dst];
        var y = LIFE_TOP + (i + 0.5) * STEP_H;
        var label = step.label || '';
        var color = step.failure ? '#B04A3F' : '#D97757';

        if (src === dst) {
            var lx = sx + COL_W / 2 - 10;
            parts.push('<path d="M' + sx.toFixed(1) + ',' + (y - 10).toFixed(1) + ' Q' + lx.toFixed(1) + ',' + (y - 10).toFixed(1) +
                ' ' + lx.toFixed(1) + ',' + y.toFixed(1) + ' Q' + lx.toFixed(1) + ',' + (y + 10).toFixed(1) + ' ' +
                sx.toFixed(1) + ',' + (y + 10).toFixed(1) + '" fill="none" stroke="' + color + '" stroke-width="1.5"/>');
            if (label) {
                parts.push('<text x="' + (lx + 6).toFixed(1) + '" y="' + (y + 3).toFixed(1) +
                    '" font-family="ui-monospace,monospace" font-size="10" fill="' + color + '">' + sysEsc(label) + '</text>');
            }
            return;
        }

        var goingRight = ex > sx;
        var arrowD = 7;
        var bodyEx = goingRight ? ex - arrowD : ex + arrowD;
        parts.push('<line x1="' + sx.toFixed(1) + '" y1="' + y.toFixed(1) + '" x2="' + bodyEx.toFixed(1) + '" y2="' + y.toFixed(1) +
            '" stroke="' + color + '" stroke-width="1.5"/>');
        var pts = goingRight
            ? (ex + ',' + y + ' ' + (ex - arrowD) + ',' + (y - 4) + ' ' + (ex - arrowD) + ',' + (y + 4))
            : (ex + ',' + y + ' ' + (ex + arrowD) + ',' + (y - 4) + ' ' + (ex + arrowD) + ',' + (y + 4));
        parts.push('<polygon points="' + pts + '" fill="' + color + '"/>');

        if (label) {
            var mx = (sx + ex) / 2;
            parts.push('<text x="' + mx.toFixed(1) + '" y="' + (y - 7).toFixed(1) +
                '" text-anchor="middle" font-family="ui-monospace,monospace" font-size="10" fill="' + color + '">' + sysEsc(label) + '</text>');
        }
        parts.push('<text x="' + (SIDE_PAD - 8).toFixed(1) + '" y="' + (y + 4).toFixed(1) +
            '" text-anchor="end" font-family="ui-monospace,monospace" font-size="9" fill="#D1CFC5">' + (i + 1) + '</text>');
    });

    parts.push('</svg>');
    return parts.join('');
}

function sysBehaviorRender() {
    var dataEl = document.getElementById('sys-behavior-data');
    var out = document.getElementById('sys-behavior-traces');
    if (!dataEl || !out) return;
    var data = JSON.parse(dataEl.textContent);
    var sel = document.getElementById('sys-behavior-sel');
    var failuresOnly = document.getElementById('sys-behavior-failures');
    var scenario = (data.scenarios || []).find(function(s) { return s.id === (sel && sel.value); }) || (data.scenarios || [])[0];
    if (!scenario) return;

    var result = sysDeriveTraces(data.actions, scenario);
    var traces = (failuresOnly && failuresOnly.checked) ? result.failed : result.completed.concat(result.failed);
    _sysBehaviorTraces = traces;

    var html = '';
    if (!traces.length) {
        html = '<p class="sys-mono" style="color:var(--gray-500);padding:20px 0">No traces derived for this scenario.</p>';
    }
    traces.forEach(function(trace, idx) {
        var isFailure = result.failed.indexOf(trace) !== -1;
        var steps = sysTraceToSteps(trace.history);
        var svg = steps.length ? sysSeqSvgJs(steps, data.nodes) : '<p class="sys-mono" style="color:var(--gray-500)">No actions enabled from the initial state.</p>';
        var finalFacts = Array.from(trace.state).sort();
        var badge = isFailure
            ? '<span class="sys-kbadge" style="color:#B04A3F;border-color:#B04A3F">dead end</span>'
            : '<span class="sys-kbadge" style="color:#788C5D;border-color:#788C5D">goal reached</span>';
        html += '<div class="sys-trace-panel">';
        html += '<div class="sys-trace-header"><span class="sys-trace-title">Trace ' + (idx + 1) + '</span>' + badge;
        if (steps.length) html += '<button class="sys-tool-btn sys-anim-btn" style="margin-left:auto" onclick="sysStepperLoadTrace(' + idx + ')">&#9654;&nbsp;Animate</button>';
        html += '</div>';
        html += '<div class="sys-trace-diagram">' + svg + '</div>';
        html += '<div class="sys-trace-facts"><span class="sys-eg-label">Facts true after trace</span><div class="sys-tags">' +
            (finalFacts.length ? finalFacts.map(function(f) { return '<span class="sys-tag">' + sysEsc(f) + '</span>'; }).join('') : '<span class="sys-tag">(none)</span>') +
            '</div></div>';
        html += '</div>';
    });
    out.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('sys-behavior-data')) sysBehaviorRender();
});
"""


def render_system_spec(data: dict) -> str:
    spec       = parse_spec(data)
    positions  = layout_graph(spec["nodes"], spec["edges"], spec["groups"])
    arch_svg   = render_architecture_svg(spec, positions)
    panels     = render_detail_panels(spec)
    legend     = render_legend(spec)
    filter_bar = render_filter_bar(spec)
    comp_list  = render_component_list_html(spec)
    matrix     = render_matrix_html(spec)

    all_nodes = spec["nodes"] + [
        n for g in spec["groups"] for n in g.get("detail", {}).get("nodes", [])
    ]

    has_layers  = any(g.get("kind") == "layer" for g in spec["groups"])
    has_behavior = bool(spec.get("actions"))
    has_changes = any(n.get("status") in ("added", "modified", "deleted") for n in all_nodes)
    has_snippets = any(n.get("code_snippet") for n in all_nodes) or has_changes

    layer_svg    = render_layer_svg(spec) if has_layers else ""
    behavior_html = render_behavior_html(spec) if has_behavior else ""
    code_detail_html = render_code_detail_html(spec)
    has_code_detail  = bool(code_detail_html)
    changes_html = render_changes_html(all_nodes) if has_changes else ""

    desc_html = f'<p class="sys-desc">{_e(spec["description"])}</p>' if spec["description"] else ""

    # Highlight.js (only when snippets exist)
    hljs_head = ""
    if has_snippets or has_changes:
        hljs_head = (
            '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">\n'
            '  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>\n'
            '  <script>document.addEventListener("DOMContentLoaded",function(){hljs.highlightAll();});</script>'
        )

    graph_json = _graph_data_json(spec, positions)

    # Query bar — searches/highlights the canvas via sysQueryRun (Phase 3).
    querybar = '<div class="sys-querybar">'
    querybar += ('<input type="text" class="sys-query-input" id="sys-query-input" '
                  'placeholder="component: X | fact: X | not: X | failure: X | action: X | path: A -> B | text"'
                  ' onkeydown="if(event.key===\'Enter\')sysQueryRun()">')
    querybar += '<button class="sys-tool-btn" onclick="sysQueryRun()">Search</button>'
    querybar += '<button class="sys-tool-btn" onclick="sysQueryClear()">Clear</button>'
    querybar += '<span class="sys-query-status" id="sys-query-status"></span>'
    querybar += '</div>'

    # Toolbar — opens on-demand floating panels for Matrix/Components and,
    # if present, Layers/Code Detail/Changes (Phase 2).
    toolbar = '<div class="sys-toolbar">'
    toolbar += '<button class="sys-tool-btn" onclick="sysToggleFloatingPanel(\'matrix\',\'Dependency Matrix\')">Matrix</button>'
    toolbar += '<button class="sys-tool-btn" onclick="sysToggleFloatingPanel(\'components\',\'Components\')">Components</button>'
    if has_layers:
        toolbar += '<button class="sys-tool-btn" onclick="sysToggleFloatingPanel(\'layers\',\'Layers\')">Layers</button>'
    if has_code_detail:
        toolbar += '<button class="sys-tool-btn" onclick="sysToggleFloatingPanel(\'codedetail\',\'Code Detail\')">Code Detail</button>'
    if has_changes:
        toolbar += '<button class="sys-tool-btn" onclick="sysToggleFloatingPanel(\'changes\',\'Changes\')">Changes</button>'
    if has_behavior:
        toolbar += '<button class="sys-tool-btn" onclick="sysToggleFloatingPanel(\'traces\',\'Traces\')">Traces</button>'
        toolbar += '<button class="sys-tool-btn" onclick="sysToggleFloatingPanel(\'stateexplorer\',\'State Explorer\');sysStateExpRender()">Explore</button>'
    toolbar += '</div>'

    arch_view = f"""
<div id="view-arch" class="sys-view">
  {toolbar}
  {querybar}
  {filter_bar}
  <div class="sys-workspace">
    <div class="sys-left-dock">
      {legend}
    </div>
    <div class="sys-canvas">
      <div class="sys-diagram">{arch_svg}</div>
    </div>
    <div class="sys-right-dock" id="sys-right-dock">
      <div id="sys-dock-empty" class="sys-dock-empty">Click a node<br>to inspect it</div>
    </div>
  </div>
  <div id="sys-playback-strip">
    <span id="sys-pb-title" class="sys-pb-title"></span>
    <button class="sys-tool-btn" onclick="sysStepperPrev()">&#9664;</button>
    <button class="sys-tool-btn" id="sys-play-btn" onclick="sysStepperToggle()">&#9654;</button>
    <button class="sys-tool-btn" onclick="sysStepperNext()">&#9654;|</button>
    <span id="sys-pb-counter" class="sys-pb-counter">0 / 0</span>
    <input type="range" id="sys-playback-scrub" min="0" max="0" value="0" oninput="sysStepperSeek(this.value)">
    <span id="sys-pb-label"></span>
    <button class="sys-tool-btn" onclick="sysStepperClose()">&#10005;</button>
  </div>
  <div id="sys-panel-templates" style="display:none">
    {panels}
  </div>
  <script type="application/json" id="sys-graph-data">{graph_json}</script>
</div>"""

    # On-demand floating panel templates (Phase 2) — hidden until opened via toolbar.
    tpl_layers = f'<div id="tpl-layers" style="display:none"><div class="sys-layer-wrap">{layer_svg}</div></div>' if has_layers else ""
    tpl_codedetail = f'<div id="tpl-codedetail" style="display:none">{code_detail_html}</div>' if has_code_detail else ""
    tpl_changes = f'<div id="tpl-changes" style="display:none">{changes_html}</div>' if has_changes else ""
    tpl_matrix = f'<div id="tpl-matrix" style="display:none">{matrix}</div>'
    tpl_components = f'<div id="tpl-components" style="display:none">{comp_list}</div>'
    tpl_traces = f'<div id="tpl-traces" style="display:none">{behavior_html}</div>' if has_behavior else ""
    tpl_stateexplorer = ('<div id="tpl-stateexplorer" style="display:none">'
                         '<div id="sys-state-exp"></div></div>') if has_behavior else ""

    js = _JS.replace("__NODE_KIND_STYLES__", _NODE_KIND_STYLES_JSON)

    body = f"""
{desc_html}
{arch_view}
{tpl_layers}
{tpl_codedetail}
{tpl_changes}
{tpl_matrix}
{tpl_components}
{tpl_traces}
{tpl_stateexplorer}
<script>{js}</script>
"""

    return page_wrapper(spec["title"], body, extra_css=_CSS, wide=True, extra_head=hljs_head)
