from .styles import _e
from .validation import parse_spec
from .layout import layout_graph
from .svg_architecture import render_architecture_svg
from .detail_panels import render_detail_panels, render_legend

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
