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


# ── Page assembly ─────────────────────────────────────────────────────────────

_CSS = """
.sys-wrap { display: flex; gap: 20px; align-items: flex-start; }
.sys-main { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; gap: 16px; }
.sys-diagram { background: var(--white); border: var(--border); border-radius: 12px; padding: 20px; overflow-x: auto; }
.sys-sidebar { flex: 0 0 260px; display: flex; flex-direction: column; gap: 12px; }

/* Detail panel */
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

/* Node interaction */
.sys-nr { transition: filter 0.12s; }
.sys-node:hover .sys-nr { filter: brightness(0.94); }
.sys-node.active .sys-nr { stroke-width: 2.5px !important; filter: brightness(0.91); }

/* Placeholder */
.sys-hint { color: var(--gray-500); font-size: 12px; text-align: center; padding: 32px 16px;
            font-family: var(--mono); background: var(--white); border: var(--border);
            border-radius: 12px; border-style: dashed; }

/* Legend */
.sys-legend { background: var(--white); border: var(--border); border-radius: 12px; padding: 14px 18px; }
.sys-leg-group { margin-bottom: 10px; }
.sys-leg-group:last-child { margin-bottom: 0; }
.sys-leg-title { font-family: var(--mono); font-size: 10px; color: var(--gray-500); margin-bottom: 5px; }
.sys-leg-row { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--gray-700); padding: 2px 0; }
.sys-leg-row span:first-child { width: 16px; text-align: center; font-size: 12px; }
.sys-leg-line { display: inline-block; width: 20px; border-top: 2px solid; height: 0; }

/* Description */
.sys-desc { font-size: 14px; color: var(--gray-700); margin: 0; line-height: 1.6; }
"""

_JS = """
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
"""


def render_system_spec(data: dict) -> str:
    spec      = parse_spec(data)
    positions = layout_graph(spec["nodes"], spec["edges"], spec["groups"])
    arch_svg  = render_architecture_svg(spec, positions)
    panels    = render_detail_panels(spec)
    legend    = render_legend(spec)

    desc_html = ""
    if spec["description"]:
        desc_html = f'<p class="sys-desc">{_e(spec["description"])}</p>'

    body = f"""
{desc_html}
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
<script>{_JS}</script>
"""

    return page_wrapper(spec["title"], body, extra_css=_CSS, wide=True)
