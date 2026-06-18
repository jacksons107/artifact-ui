from .styles import (
    NODE_KIND_STYLES, _DEFAULT_NODE_STYLE,
    EDGE_KIND_STYLES, _DEFAULT_EDGE_STYLE,
    GROUP_KIND_STYLES, _DEFAULT_GROUP_STYLE,
    _CHANGE_STATUS_COLORS, _e,
)

# ── Architecture filter bar ───────────────────────────────────────────────────

def render_filter_bar(spec: dict) -> str:
    nodes  = spec["nodes"]
    edges  = spec["edges"]
    groups = spec["groups"]
    kinds  = sorted({n.get("kind", "") for n in nodes if n.get("kind")})
    change_statuses = [s for s in ("added", "modified", "deleted") if any(n.get("status") == s for n in nodes)]
    edge_kinds = sorted({e.get("kind", "") for e in edges if e.get("kind")})
    if not kinds and not change_statuses and not edge_kinds and not groups:
        return ""

    sections_so_far = False
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
        sections_so_far = True
    if change_statuses:
        if sections_so_far:
            html += '<span class="sys-fl-sep"></span>'
        html += '<span class="sys-fl">Changes</span>'
        for st in change_statuses:
            color = _CHANGE_STATUS_COLORS[st]
            html += (
                f'<button class="sys-fc active" data-as="{_e(st)}" '
                f'style="color:{color};border-color:{color}" '
                f'onclick="sysAStatus(this)">{_e(st)}</button>'
            )
        sections_so_far = True
    if edge_kinds:
        if sections_so_far:
            html += '<span class="sys-fl-sep"></span>'
        html += '<span class="sys-fl">Edges</span>'
        for kind in edge_kinds:
            est = EDGE_KIND_STYLES.get(kind, _DEFAULT_EDGE_STYLE)
            html += (
                f'<button class="sys-fc active" data-aek="{_e(kind)}" '
                f'style="color:{est["color"]};border-color:{est["color"]}" '
                f'onclick="sysAEKind(this)">{_e(kind)}</button>'
            )
        sections_so_far = True
    if groups:
        if sections_so_far:
            html += '<span class="sys-fl-sep"></span>'
        html += '<span class="sys-fl">Groups</span>'
        for g in groups:
            gst = GROUP_KIND_STYLES.get(g.get("kind", ""), _DEFAULT_GROUP_STYLE)
            html += (
                f'<button class="sys-fc active" data-ag="{_e(g["id"])}" '
                f'style="color:{gst["stroke"]};border-color:{gst["stroke"]}" '
                f'onclick="sysAGroup(this)">{_e(g.get("label", g["id"]))}</button>'
            )
        sections_so_far = True
    html += '</div>'
    return html
