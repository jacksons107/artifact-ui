from .styles import _e
from .validation import parse_spec
from .arch_block import render_diagram_block

# ── Code detail tab ───────────────────────────────────────────────────────────
# Each module gets the exact same diagram type as the Architecture tab
# (filter bar, sequence animation overlay, detail panels) — just scoped to
# that group's own nodes/edges/groups/sequences, switched via a dropdown.

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
            "title":      g.get("label", g["id"]),
            "nodes":      detail["nodes"],
            "edges":      detail.get("edges", []),
            "groups":     detail.get("groups", []),
            "sequences":  detail.get("sequences", []),
        })
        prefix = f'cd-{g["id"]}-'
        block  = render_diagram_block(sub, id_prefix=prefix)

        display = '' if i == 0 else ' style="display:none"'
        html += f'<div id="cdp-{_e(g["id"])}" class="sys-cd-panel"{display}>{block}</div>'

    html += '</div>'
    return html
