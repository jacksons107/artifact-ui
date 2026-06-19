from .styles import _e
from .validation import parse_spec
from .arch_block import render_diagram_block

# ── Code detail tab ───────────────────────────────────────────────────────────
# Every group is a collapsible node in the Architecture diagram already;
# the Code Detail tab is the same per-group view, just selectable via a
# dropdown instead of clicking expand in place — scoped to that group's own
# subtree (itself plus any nested groups/nodes it contains).

def _collect_subtree(spec: dict, root_id: str) -> tuple:
    group_by_id = {g["id"]: g for g in spec["groups"]}
    node_by_id  = {n["id"]: n for n in spec["nodes"]}

    sub_groups, leaf_nodes, seen_groups = [], [], set()

    def walk(gid: str) -> None:
        if gid in seen_groups:
            return
        seen_groups.add(gid)
        g = group_by_id[gid]
        sub_groups.append(g)
        for m in g.get("members", []):
            if m in group_by_id:
                walk(m)
            elif m in node_by_id:
                leaf_nodes.append(node_by_id[m])

    walk(root_id)
    leaf_ids = {n["id"] for n in leaf_nodes}
    edges = [e for e in spec["edges"] if e["from"] in leaf_ids and e["to"] in leaf_ids]
    return leaf_nodes, edges, sub_groups


def render_code_detail_html(spec: dict) -> str:
    groups = spec.get("groups", [])
    if not groups:
        return ""

    html = '<div class="sys-cd-wrap"><div class="sys-cd-controls">'
    html += '<span class="sys-fl">Module</span>'
    html += '<select class="sys-cd-sel" onchange="sysCodeDetailChange(this)">'
    for g in groups:
        html += f'<option value="{_e(g["id"])}">{_e(g.get("label", g["id"]))}</option>'
    html += '</select>'
    html += '</div>'

    for i, g in enumerate(groups):
        nodes, edges, sub_groups = _collect_subtree(spec, g["id"])
        sub = parse_spec({
            "title":  g.get("label", g["id"]),
            "nodes":  nodes,
            "edges":  edges,
            "groups": sub_groups,
        })
        prefix  = f'cd-{g["id"]}-'
        block   = render_diagram_block(sub, id_prefix=prefix)

        display = '' if i == 0 else ' style="display:none"'
        html += f'<div id="cdp-{_e(g["id"])}" class="sys-cd-panel"{display}>{block}</div>'

    html += '</div>'
    return html
