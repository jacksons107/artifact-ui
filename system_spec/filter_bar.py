from .styles import NODE_KIND_STYLES, _DEFAULT_NODE_STYLE, _CHANGE_STATUS_COLORS, _e

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
