from .styles import (
    NODE_KIND_STYLES, _DEFAULT_NODE_STYLE,
    EDGE_KIND_STYLES, _DEFAULT_EDGE_STYLE,
    CHANGE_STATUS_STYLES,
    GROUP_KIND_STYLES, _DEFAULT_GROUP_STYLE,
    PAD, _e,
)

# ── SVG rendering ─────────────────────────────────────────────────────────────

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

    parts.append("</svg>")
    return "\n".join(parts)
