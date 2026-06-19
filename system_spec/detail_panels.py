from collections import defaultdict

from .styles import (
    NODE_KIND_STYLES, _DEFAULT_NODE_STYLE, EDGE_KIND_STYLES, _DEFAULT_EDGE_STYLE,
    GROUP_KIND_STYLES, _DEFAULT_GROUP_STYLE, _infer_lang, _e,
)

# ── Detail panels ─────────────────────────────────────────────────────────────

def render_detail_panels(spec: dict, id_prefix: str = "", node_sequences: dict = None) -> str:
    nodes  = spec["nodes"]
    edges  = spec["edges"]
    by_id  = {n["id"]: n for n in nodes}
    node_sequences = node_sequences or {}

    outgoing: dict[str, list] = defaultdict(list)
    incoming: dict[str, list] = defaultdict(list)
    for edge in edges:
        outgoing[edge["from"]].append(edge)
        incoming[edge["to"]].append(edge)

    panels = []
    for node in nodes:
        nid  = node["id"]
        kind = node.get("kind", "")
        nst  = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)

        html = f'<div class="sys-panel" id="panel-{_e(id_prefix + nid)}" style="display:none">'
        html += '<div class="sys-ph">'
        html += f'<span style="color:{nst["stroke"]};font-size:14px">{nst["icon"]}</span>'
        html += f'<span class="sys-plabel">{_e(node.get("label", nid))}</span>'
        if kind:
            html += f'<span class="sys-kbadge" style="color:{nst["stroke"]};border-color:{nst["stroke"]}">{_e(kind)}</span>'
        html += '</div>'

        desc = node.get("description", "")
        if desc:
            html += f'<p class="sys-pdesc">{_e(desc)}</p>'

        meta = []
        for key, field in [("Tech", "tech"), ("Owner", "owner"), ("Status", "status")]:
            val = node.get(field, "")
            if val:
                meta.append((key, val))
        file_path  = node.get("file_path", "")
        line_range = node.get("line_range")
        if file_path:
            loc = file_path
            if line_range and len(line_range) == 2:
                loc += f":{line_range[0]}–{line_range[1]}"
            meta.append(("Location", loc))
        if meta:
            html += '<dl class="sys-meta">'
            for k, v in meta:
                html += f'<dt>{k}</dt><dd>{_e(v)}</dd>'
            html += '</dl>'

        tags = node.get("tags", [])
        if tags:
            html += '<div class="sys-tags">'
            for tag in tags:
                html += f'<span class="sys-tag">{_e(tag)}</span>'
            html += '</div>'

        out = outgoing[nid]
        inc = incoming[nid]
        if out or inc:
            html += '<div class="sys-edges">'
            if out:
                html += '<div class="sys-eg-label">Calls / Sends</div>'
                for e in out:
                    peer_id = id_prefix + e["to"]
                    peer  = _e(by_id.get(e["to"], {}).get("label", e["to"]))
                    ekind = _e(e.get("kind", ""))
                    elbl  = _e(e.get("label", ""))
                    detail = f"{ekind} · {elbl}" if elbl else ekind
                    html += (
                        f'<div class="sys-er">→ '
                        f'<a class="sys-er-link" data-target="{_e(peer_id)}" onclick="sysGoTo(this)">{peer}</a> '
                        f'<span class="sys-ek">{detail}</span></div>'
                    )
            if inc:
                html += '<div class="sys-eg-label">Receives From</div>'
                for e in inc:
                    peer_id = id_prefix + e["from"]
                    peer  = _e(by_id.get(e["from"], {}).get("label", e["from"]))
                    ekind = _e(e.get("kind", ""))
                    elbl  = _e(e.get("label", ""))
                    detail = f"{ekind} · {elbl}" if elbl else ekind
                    html += (
                        f'<div class="sys-er">← '
                        f'<a class="sys-er-link" data-target="{_e(peer_id)}" onclick="sysGoTo(this)">{peer}</a> '
                        f'<span class="sys-ek">{detail}</span></div>'
                    )
            html += '</div>'

        seqs = node_sequences.get(nid, [])
        if seqs:
            html += '<div class="sys-edges">'
            html += '<div class="sys-eg-label">Appears in Sequences</div>'
            html += '<div class="sys-seq-refs">'
            for s in seqs:
                html += (
                    f'<button class="sys-fc" data-seq="{_e(s["id"])}" data-step="{s["first_step"]}" '
                    f'onclick="sysPlaySeqFromNode(this)">{_e(s["label"])}</button>'
                )
            html += '</div></div>'

        signature = node.get("signature", "")
        if signature:
            html += f'<div class="sys-sig"><code>{_e(signature)}</code></div>'

        code_snippet = node.get("code_snippet", "")
        if code_snippet:
            lang = _infer_lang(node)
            html += f'<div class="sys-snippet"><pre><code class="language-{lang}">{_e(code_snippet)}</code></pre></div>'

        html += '</div>'
        panels.append(html)

    return "\n".join(panels)


# ── Legend ────────────────────────────────────────────────────────────────────

def render_legend(spec: dict) -> str:
    nodes = spec["nodes"]
    edges = spec["edges"]

    kinds_used  = {n.get("kind", "") for n in nodes if n.get("kind")}
    ekind_used  = {e.get("kind", "") for e in edges if e.get("kind")}

    parts = ['<div class="sys-legend">']

    if kinds_used:
        parts.append('<div class="sys-leg-group">')
        parts.append('<div class="sys-leg-title">Nodes</div>')
        for kind in sorted(kinds_used):
            nst = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)
            parts.append(
                f'<div class="sys-leg-row">'
                f'<span style="color:{nst["stroke"]}">{nst["icon"]}</span>'
                f'<span>{_e(kind)}</span>'
                f'</div>'
            )
        parts.append('</div>')

    if ekind_used:
        parts.append('<div class="sys-leg-group">')
        parts.append('<div class="sys-leg-title">Edges</div>')
        for kind in sorted(ekind_used):
            est = EDGE_KIND_STYLES.get(kind, _DEFAULT_EDGE_STYLE)
            dash = "border-top-style:dashed" if est["dashed"] else ""
            parts.append(
                f'<div class="sys-leg-row">'
                f'<span class="sys-leg-line" style="border-color:{est["color"]};{dash}"></span>'
                f'<span>{_e(kind)}</span>'
                f'</div>'
            )
        parts.append('</div>')

    parts.append('</div>')
    return "".join(parts)


# ── Group panels ──────────────────────────────────────────────────────────────
# Every group is a collapsible node — clicking its placeholder box (or its
# expanded bounding box) needs a panel in the DOM the same way a real node
# does, just describing the group's kind and its own members instead.

def render_group_panels(spec: dict, id_prefix: str = "") -> str:
    groups = spec.get("groups", [])
    if not groups:
        return ""

    node_by_id  = {n["id"]: n for n in spec.get("nodes", [])}
    group_by_id = {g["id"]: g for g in groups}

    def member_label(mid: str) -> str:
        if mid in node_by_id:
            return node_by_id[mid].get("label", mid)
        if mid in group_by_id:
            return group_by_id[mid].get("label", mid)
        return mid

    panels = []
    for group in groups:
        gid  = group["id"]
        kind = group.get("kind", "")
        gst  = GROUP_KIND_STYLES.get(kind, _DEFAULT_GROUP_STYLE)
        members = group.get("members", [])

        html = f'<div class="sys-panel" id="panel-{_e(id_prefix + gid)}" style="display:none">'
        html += '<div class="sys-ph">'
        html += f'<span style="color:{gst["stroke"]};font-size:14px">▣</span>'
        html += f'<span class="sys-plabel">{_e(group.get("label", gid))}</span>'
        if kind:
            html += f'<span class="sys-kbadge" style="color:{gst["stroke"]};border-color:{gst["stroke"]}">{_e(kind)}</span>'
        html += '</div>'

        html += '<dl class="sys-meta">'
        html += f'<dt>Members</dt><dd>{len(members)}</dd>'
        html += '</dl>'

        if members:
            html += '<div class="sys-tags">'
            for m in members:
                html += f'<span class="sys-tag">{_e(member_label(m))}</span>'
            html += '</div>'

        html += '</div>'
        panels.append(html)

    return "\n".join(panels)
