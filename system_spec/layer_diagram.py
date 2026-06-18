from .styles import NODE_KIND_STYLES, _DEFAULT_NODE_STYLE, GROUP_KIND_STYLES, _DEFAULT_GROUP_STYLE, _e

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
