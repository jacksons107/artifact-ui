from design_system import page_wrapper

from .styles import _e
from .validation import parse_spec
from .matrix import render_matrix_html, render_component_list_html
from .layer_diagram import render_layer_svg
from .sequence_diagram import render_sequence_html
from .arch_block import render_diagram_block, _ARCH_ENGINE_JS
from .code_detail import render_code_detail_html
from .changes import render_changes_html
from .assets import _CSS, _JS


def render_system_spec(data: dict) -> str:
    spec       = parse_spec(data)

    arch_block = render_diagram_block(spec)
    comp_list  = render_component_list_html(spec)
    matrix     = render_matrix_html(spec)
    has_seqs   = bool(spec.get("sequences"))

    has_layers  = any(g.get("kind") == "layer" for g in spec["groups"])
    has_changes = any(n.get("status") in ("added", "modified", "deleted") for n in spec["nodes"])
    has_snippets = any(n.get("code_snippet") for n in spec["nodes"]) or has_changes

    layer_svg    = render_layer_svg(spec) if has_layers else ""
    seq_html     = render_sequence_html(spec) if has_seqs else ""
    code_detail_html = render_code_detail_html(spec)
    has_code_detail  = bool(code_detail_html)
    changes_html = render_changes_html(spec["nodes"]) if has_changes else ""

    desc_html = f'<p class="sys-desc">{_e(spec["description"])}</p>' if spec["description"] else ""

    # Highlight.js (only when snippets exist)
    hljs_head = ""
    if has_snippets or has_changes:
        hljs_head = (
            '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">\n'
            '  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>\n'
            '  <script>document.addEventListener("DOMContentLoaded",function(){hljs.highlightAll();});</script>'
        )

    # Tab bar — only show tabs that have content
    tabs  = '<div class="sys-tabs">'
    tabs += '<button class="sys-tab active" data-view="arch" onclick="sysTab(this)">Architecture</button>'
    if has_layers:
        tabs += '<button class="sys-tab" data-view="layers" onclick="sysTab(this)">Layers</button>'
    if has_seqs:
        tabs += '<button class="sys-tab" data-view="sequences" onclick="sysTab(this)">Sequences</button>'
    if has_code_detail:
        tabs += '<button class="sys-tab" data-view="codedetail" onclick="sysTab(this)">Code Detail</button>'
    if has_changes:
        tabs += '<button class="sys-tab" data-view="changes" onclick="sysTab(this)">Changes</button>'
    tabs += '<button class="sys-tab" data-view="matrix" onclick="sysTab(this)">Matrix</button>'
    tabs += '<button class="sys-tab" data-view="components" onclick="sysTab(this)">Components</button>'
    tabs += '</div>'

    arch_view = f"""
<div id="view-arch" class="sys-view">
  {arch_block}
</div>"""

    layer_view = f"""
<div id="view-layers" class="sys-view" style="display:none">
  <div class="sys-layer-wrap">{layer_svg}</div>
</div>""" if has_layers else ""

    seq_view = f"""
<div id="view-sequences" class="sys-view" style="display:none">
  {seq_html}
</div>""" if has_seqs else ""

    code_detail_view = f"""
<div id="view-codedetail" class="sys-view" style="display:none">
  {code_detail_html}
</div>""" if has_code_detail else ""

    changes_view = f"""
<div id="view-changes" class="sys-view" style="display:none">
  {changes_html}
</div>""" if has_changes else ""

    matrix_view = f"""
<div id="view-matrix" class="sys-view" style="display:none">
  {matrix}
</div>"""

    comp_view = f"""
<div id="view-components" class="sys-view" style="display:none">
  {comp_list}
</div>"""

    body = f"""
{desc_html}
{tabs}
{arch_view}
{layer_view}
{seq_view}
{code_detail_view}
{changes_view}
{matrix_view}
{comp_view}
<script>{_ARCH_ENGINE_JS}</script>
<script>{_JS}</script>
"""

    return page_wrapper(spec["title"], body, extra_css=_CSS, wide=True, extra_head=hljs_head)
