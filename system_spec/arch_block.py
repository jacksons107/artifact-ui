import json
from pathlib import Path

from .styles import (
    _e,
    NODE_KIND_STYLES, _DEFAULT_NODE_STYLE,
    EDGE_KIND_STYLES, _DEFAULT_EDGE_STYLE,
    GROUP_KIND_STYLES, _DEFAULT_GROUP_STYLE,
    CHANGE_STATUS_STYLES,
)
from .detail_panels import render_detail_panels, render_group_panels, render_legend
from .filter_bar import render_filter_bar
from .sequence_diagram import render_timeline_widget

# ── Shared architecture-diagram block ──────────────────────────────────────
# Used both for the top-level Architecture tab and for each Code Detail
# module panel, so both get the same filter bar, sequence animation overlay,
# and detail panels — only the node/edge/sequence data differs.
#
# The diagram itself (layout + SVG drawing) is NOT rendered server-side here.
# Python validates the spec and emits it (plus the style tables) as JSON;
# arch_engine.js is the single client-side implementation that computes
# positions and draws the SVG, for both the first paint and any later
# expand/collapse of a group's placeholder node into its real members.

_ARCH_ENGINE_JS = (Path(__file__).parent / "arch_engine.js").read_text(encoding="utf-8")


def build_node_sequences(spec: dict) -> dict:
    node_sequences: dict = {}
    for seq in spec.get("sequences", []):
        seen_for_seq = set()
        for i, step in enumerate(seq.get("steps", [])):
            for nid in (step.get("from"), step.get("to")):
                if nid and nid not in seen_for_seq:
                    seen_for_seq.add(nid)
                    node_sequences.setdefault(nid, []).append(
                        {"id": seq["id"], "label": seq.get("label", seq["id"]), "first_step": i}
                    )
    return node_sequences


def build_animate_block(spec: dict) -> str:
    sequences = spec.get("sequences", [])
    if not sequences:
        return ""
    html  = '<div class="sys-arch-animate">'
    html += '<div class="sys-seq-controls">'
    html += '<span class="sys-fl">Animate</span>'
    html += '<select class="sys-seq-sel" onchange="sysArchSeqChange(this)">'
    html += '<option value="">None</option>'
    for seq in sequences:
        html += f'<option value="{_e(seq["id"])}">{_e(seq["label"])}</option>'
    html += '</select>'
    html += '</div>'
    for seq in sequences:
        tl = render_timeline_widget("arch", seq["id"], seq.get("steps", []))
        html += f'<div class="sys-atl-block" data-seq="{_e(seq["id"])}" style="display:none">{tl}</div>'
    html += '</div>'
    return html


def _style_tables() -> dict:
    return {
        "node":         {**NODE_KIND_STYLES, "_default": _DEFAULT_NODE_STYLE},
        "edge":         {**EDGE_KIND_STYLES, "_default": _DEFAULT_EDGE_STYLE},
        "group":        {**GROUP_KIND_STYLES, "_default": _DEFAULT_GROUP_STYLE},
        "changeStatus": CHANGE_STATUS_STYLES,
    }


def render_diagram_block(spec: dict, id_prefix: str = "") -> str:
    has_seqs    = bool(spec.get("sequences"))
    node_seqs   = build_node_sequences(spec) if has_seqs else {}
    panels      = render_detail_panels(spec, id_prefix=id_prefix, node_sequences=node_seqs)
    panels     += render_group_panels(spec, id_prefix=id_prefix)
    legend      = render_legend(spec)
    filter_bar  = render_filter_bar(spec)
    animate_blk = build_animate_block(spec) if has_seqs else ""

    payload = {
        "spec": {
            "nodes": spec["nodes"],
            "edges": spec["edges"],
            "groups": spec.get("groups", []),
            "sequences": spec.get("sequences", []),
        },
        "styles": _style_tables(),
    }
    payload_json = json.dumps(payload)

    return f"""
<div class="sys-arch-scope">
  {filter_bar}
  {animate_blk}
  <div class="sys-wrap">
    <div class="sys-main"><div class="sys-diagram">
      <div id="{_e(id_prefix)}sys-mount" class="sys-mount" data-prefix="{_e(id_prefix)}" data-source="{_e(id_prefix)}sys-data"></div>
    </div></div>
    <div class="sys-sidebar">
      <div class="sys-hint">Click a node<br>to see details</div>
      {panels}
      {legend}
    </div>
  </div>
  <script type="application/json" id="{_e(id_prefix)}sys-data">{payload_json}</script>
</div>"""
