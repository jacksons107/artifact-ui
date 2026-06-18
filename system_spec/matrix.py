from collections import defaultdict

from .styles import NODE_KIND_STYLES, _DEFAULT_NODE_STYLE, EDGE_KIND_STYLES, _DEFAULT_EDGE_STYLE, _e

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
