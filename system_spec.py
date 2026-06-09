import html as _html
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
}

_DEFAULT_NODE_STYLE = {"stroke": "#D1CFC5", "fill": "#FFFFFF", "icon": "○"}

EDGE_KIND_STYLES = {
    "calls":      {"color": "#D97757", "dashed": False},
    "imports":    {"color": "#87867F", "dashed": False},
    "depends":    {"color": "#87867F", "dashed": True},
    "emits":      {"color": "#788C5D", "dashed": True},
    "subscribes": {"color": "#788C5D", "dashed": True},
    "reads":      {"color": "#788C5D", "dashed": False},
    "writes":     {"color": "#B04A3F", "dashed": False},
    "deploys":    {"color": "#87867F", "dashed": True},
    "owns":       {"color": "#D1CFC5", "dashed": False},
}

_DEFAULT_EDGE_STYLE = {"color": "#C8C5BC", "dashed": False}

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


# ── Validation ────────────────────────────────────────────────────────────────

def parse_spec(data: dict) -> dict:
    title  = data.get("title", "Untitled System")
    nodes  = data.get("nodes", [])
    edges  = data.get("edges", [])
    groups = data.get("groups", [])
    seqs   = data.get("sequences", [])

    if not nodes:
        raise ValueError("system_spec requires at least one node in 'nodes'.")

    node_ids = set()
    for i, node in enumerate(nodes):
        if "id" not in node:
            raise ValueError(f"nodes[{i}] is missing required field 'id'.")
        if "label" not in node:
            raise ValueError(f"nodes[{i}] (id={node['id']!r}) is missing required field 'label'.")
        if node["id"] in node_ids:
            raise ValueError(f"nodes[{i}]: duplicate node id {node['id']!r}.")
        node_ids.add(node["id"])

    for i, edge in enumerate(edges):
        src = edge.get("from")
        dst = edge.get("to")
        if src is None:
            raise ValueError(f"edges[{i}] is missing required field 'from'.")
        if dst is None:
            raise ValueError(f"edges[{i}] is missing required field 'to'.")
        if src not in node_ids:
            raise ValueError(f"edges[{i}]: 'from' references unknown node id {src!r}.")
        if dst not in node_ids:
            raise ValueError(f"edges[{i}]: 'to' references unknown node id {dst!r}.")

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

    for i, seq in enumerate(seqs):
        if "id" not in seq:
            raise ValueError(f"sequences[{i}] is missing required field 'id'.")
        if "label" not in seq:
            raise ValueError(f"sequences[{i}] (id={seq['id']!r}) is missing required field 'label'.")
        for j, step in enumerate(seq.get("steps", [])):
            for field in ("from", "to"):
                val = step.get(field)
                if val and val not in node_ids:
                    raise ValueError(
                        f"sequences[{i}].steps[{j}]: {field!r} references unknown node id {val!r}."
                    )

    return {
        "title":       title,
        "description": data.get("description", ""),
        "nodes":       nodes,
        "edges":       edges,
        "groups":      groups,
        "sequences":   seqs,
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


def render_architecture_svg(spec: dict, positions: dict) -> str:
    nodes  = spec["nodes"]
    edges  = spec["edges"]
    groups = spec["groups"]
    pos    = positions

    if not pos:
        return '<svg viewBox="0 0 400 200"><text x="200" y="100" text-anchor="middle" fill="#87867F">No nodes</text></svg>'

    W = int(max(p["x"] + p["w"] for p in pos.values()) + PAD)
    H = int(max(p["y"] + p["h"] for p in pos.values()) + PAD)

    parts = [f'<svg viewBox="0 0 {W} {H}" style="display:block;width:100%;height:auto;max-height:680px" id="sys-svg">']

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
            f'<path d="M{sx:.1f},{sy:.1f} C{cx1:.1f},{cy1:.1f} {cx2:.1f},{cy2:.1f} {ex:.1f},{ey:.1f}" '
            f'fill="none" stroke="{color}" stroke-width="1.5"{dash} marker-end="url(#arr-{cid})"/>'
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

    # Nodes
    for node in nodes:
        nid   = node["id"]
        if nid not in pos:
            continue
        p     = pos[nid]
        x, y, w, h = p["x"], p["y"], p["w"], p["h"]
        kind  = node.get("kind", "")
        nst   = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)
        icon  = nst["icon"]
        parts.append(
            f'<g class="sys-node" data-id="{_e(nid)}" data-kind="{_e(kind)}" '
            f'style="cursor:pointer" onclick="sysClick(this)">'
        )
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="10" '
            f'fill="{nst["fill"]}" stroke="{nst["stroke"]}" stroke-width="1.5" class="sys-nr"/>'
        )
        # Icon
        parts.append(
            f'<text x="{x+11:.1f}" y="{y+h/2-3:.1f}" dominant-baseline="middle" '
            f'font-family="ui-monospace,monospace" font-size="10" fill="{nst["stroke"]}" opacity="0.75">'
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

    parts.append("</svg>")
    return "\n".join(parts)


# ── Detail panels ─────────────────────────────────────────────────────────────

def render_detail_panels(spec: dict) -> str:
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

        html = f'<div class="sys-panel" id="panel-{_e(nid)}" style="display:none">'
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


# ── Component list ────────────────────────────────────────────────────────────

def render_component_list_html(spec: dict) -> str:
    nodes = spec["nodes"]
    kinds    = sorted({n.get("kind", "") for n in nodes if n.get("kind")})
    statuses = sorted({n.get("status", "") for n in nodes if n.get("status")})

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
    for col in ["Name", "Kind", "Tech", "Owner", "Status", "Tags", "Description"]:
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
            f'</tr>'
        )

    html += '</tbody></table></div></div>'
    return html


# ── Architecture filter bar ───────────────────────────────────────────────────

def render_filter_bar(spec: dict) -> str:
    kinds = sorted({n.get("kind", "") for n in spec["nodes"] if n.get("kind")})
    if not kinds:
        return ""
    html = '<div class="sys-arch-filters">'
    html += '<span class="sys-fl">Show</span>'
    for kind in kinds:
        nst = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)
        html += (
            f'<button class="sys-fc active" data-ak="{_e(kind)}" '
            f'style="color:{nst["stroke"]};border-color:{nst["stroke"]}" '
            f'onclick="sysAKind(this)">{nst["icon"]} {_e(kind)}</button>'
        )
    html += '</div>'
    return html


# ── Page assembly ─────────────────────────────────────────────────────────────

_CSS = """
/* ── Tabs ─────────────────────────────────────── */
.sys-tabs { display: flex; gap: 0; border-bottom: 1.5px solid var(--gray-300); margin-bottom: 20px; }
.sys-tab { font-family: var(--mono); font-size: 12px; background: none; border: none;
           padding: 7px 16px; cursor: pointer; color: var(--gray-500);
           border-bottom: 2px solid transparent; margin-bottom: -1.5px; transition: color 0.1s; }
.sys-tab:hover { color: var(--slate); }
.sys-tab.active { color: var(--slate); border-bottom-color: var(--clay); font-weight: 500; }

/* ── Architecture view ────────────────────────── */
.sys-wrap { display: flex; gap: 20px; align-items: flex-start; }
.sys-main { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; gap: 12px; }
.sys-diagram { background: var(--white); border: var(--border); border-radius: 12px; padding: 20px; overflow-x: auto; }
.sys-sidebar { flex: 0 0 260px; display: flex; flex-direction: column; gap: 12px; }

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

/* ── Description ──────────────────────────────── */
.sys-desc { font-size: 14px; color: var(--gray-700); margin: 0 0 20px; line-height: 1.6; }
"""

_JS = """
/* ── Tab switching ─────────────────────────────── */
function sysTab(el) {
    document.querySelectorAll('.sys-tab').forEach(function(t) { t.classList.remove('active'); });
    document.querySelectorAll('.sys-view').forEach(function(v) { v.style.display = 'none'; });
    el.classList.add('active');
    var view = document.getElementById('view-' + el.getAttribute('data-view'));
    if (view) view.style.display = 'block';
}

/* ── Node click (architecture detail panel) ─────── */
var _active = null;
function sysClick(el) {
    var nid = el.getAttribute('data-id');
    var panel = document.getElementById('panel-' + nid);
    var hint = document.getElementById('sys-hint');

    if (_active === el) {
        el.classList.remove('active');
        _active = null;
        document.querySelectorAll('.sys-panel').forEach(function(p) { p.style.display = 'none'; });
        if (hint) hint.style.display = 'block';
        return;
    }

    if (_active) _active.classList.remove('active');
    document.querySelectorAll('.sys-panel').forEach(function(p) { p.style.display = 'none'; });

    el.classList.add('active');
    _active = el;
    if (hint) hint.style.display = 'none';
    if (panel) panel.style.display = 'block';
}

/* ── Architecture kind filter ──────────────────── */
function sysAKind(btn) {
    btn.classList.toggle('active');
    _applyArchFilter();
}
function _applyArchFilter() {
    var active = new Set();
    document.querySelectorAll('.sys-fc[data-ak].active').forEach(function(b) {
        active.add(b.getAttribute('data-ak'));
    });
    var all = document.querySelectorAll('.sys-fc[data-ak]').length === 0;
    document.querySelectorAll('.sys-node').forEach(function(n) {
        var k = n.getAttribute('data-kind');
        var show = all || active.size === 0 || active.has(k);
        n.classList.toggle('filtered-out', !show);
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
"""


def render_system_spec(data: dict) -> str:
    spec      = parse_spec(data)
    positions = layout_graph(spec["nodes"], spec["edges"], spec["groups"])
    arch_svg  = render_architecture_svg(spec, positions)
    panels    = render_detail_panels(spec)
    legend    = render_legend(spec)
    filter_bar = render_filter_bar(spec)
    comp_list  = render_component_list_html(spec)

    has_layers = any(g.get("kind") == "layer" for g in spec["groups"])
    layer_svg  = render_layer_svg(spec) if has_layers else ""

    desc_html = f'<p class="sys-desc">{_e(spec["description"])}</p>' if spec["description"] else ""

    # Tab bar
    tabs = '<div class="sys-tabs">'
    tabs += '<button class="sys-tab active" data-view="arch" onclick="sysTab(this)">Architecture</button>'
    if has_layers:
        tabs += '<button class="sys-tab" data-view="layers" onclick="sysTab(this)">Layers</button>'
    tabs += '<button class="sys-tab" data-view="components" onclick="sysTab(this)">Components</button>'
    tabs += '</div>'

    # Architecture view
    arch_view = f"""
<div id="view-arch" class="sys-view">
  {filter_bar}
  <div class="sys-wrap">
    <div class="sys-main">
      <div class="sys-diagram">{arch_svg}</div>
    </div>
    <div class="sys-sidebar">
      <div id="sys-hint" class="sys-hint">Click a node<br>to see details</div>
      {panels}
      {legend}
    </div>
  </div>
</div>"""

    # Layer view (only if layer groups exist)
    layer_view = ""
    if has_layers:
        layer_view = f"""
<div id="view-layers" class="sys-view" style="display:none">
  <div class="sys-layer-wrap">{layer_svg}</div>
</div>"""

    # Components view
    comp_view = f"""
<div id="view-components" class="sys-view" style="display:none">
  {comp_list}
</div>"""

    body = f"""
{desc_html}
{tabs}
{arch_view}
{layer_view}
{comp_view}
<script>{_JS}</script>
"""

    return page_wrapper(spec["title"], body, extra_css=_CSS, wide=True)
