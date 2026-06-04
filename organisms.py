import html as _html
from typing import Any
import primitives
from design_system import BASE_CSS


def _e(s: Any) -> str:
    return _html.escape(str(s))


# ── 1. event_timeline ─────────────────────────────────────────────────────────

_DOT_COLORS = {
    "impact":    "var(--clay)",
    "mitigated": "var(--olive)",
    "neutral":   "var(--gray-300)",
    "success":   "var(--olive)",
    "warning":   "var(--clay)",
    "error":     "var(--rust)",
}

def event_timeline(data: dict) -> str:
    entries = data.get("entries", [])
    rows = []
    for entry in entries:
        time  = entry.get("time", "")
        body  = entry.get("body", "")
        state = entry.get("state", "neutral")
        color = _DOT_COLORS.get(state, "var(--gray-300)")
        rows.append(
            f'<div class="event-entry">'
            f'<div class="event-time">{_e(time)}</div>'
            f'<div class="event-dot-wrap"><div class="event-dot" style="background:{color}"></div></div>'
            f'<div class="event-body">{_e(body)}</div>'
            f'</div>'
        )
    return f'<div class="event-timeline">{"".join(rows)}</div>'


# ── 2. milestone_timeline ─────────────────────────────────────────────────────

def milestone_timeline(data: dict) -> str:
    milestones = data.get("milestones", [])
    rows = []
    for m in milestones:
        date        = m.get("date", "")
        title       = m.get("title", "")
        description = m.get("description", "")
        tags        = m.get("tags", [])
        done        = m.get("done", False)

        dot_style = (
            "background:var(--clay);border:2px solid var(--clay)" if done
            else "background:var(--white);border:2px solid var(--gray-300)"
        )
        chips = "".join(f'<span class="chip">{_e(t)}</span>' for t in tags)
        tags_html = f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px">{chips}</div>' if tags else ""
        desc_html = f'<p style="font-size:13px;color:var(--gray-500);margin:4px 0 0">{_e(description)}</p>' if description else ""

        rows.append(
            f'<div class="milestone">'
            f'<div class="milestone-date">{_e(date)}</div>'
            f'<div class="milestone-track"><div class="milestone-dot" style="{dot_style}"></div></div>'
            f'<div class="milestone-content"><h4>{_e(title)}</h4>{desc_html}{tags_html}</div>'
            f'</div>'
        )
    return f'<div class="milestone-timeline">{"".join(rows)}</div>'


# ── 3. bar_chart ──────────────────────────────────────────────────────────────

def bar_chart(data: dict) -> str:
    bars    = data.get("bars", [])
    y_max   = data.get("y_max")
    caption = data.get("caption", "")

    if not bars:
        return '<div class="chart-panel"><p class="text-muted text-sm">No data</p></div>'

    max_val = max((b.get("value", 0) for b in bars), default=1)
    if y_max is None:
        y_max = max_val or 1

    W, H = 640, 200
    PL, PR, PT, PB = 48, 12, 24, 40
    cw = W - PL - PR
    ch = H - PT - PB
    n = len(bars)
    bar_gap = 8
    bar_w = max(8, cw / n - bar_gap)

    lines = []
    for i in range(5):
        frac = i / 4
        y = H - PB - ch * frac
        color = "#D1CFC5" if i == 0 else "#F0EEE6"
        lines.append(f'<line x1="{PL}" y1="{y:.1f}" x2="{W-PR}" y2="{y:.1f}" stroke="{color}" stroke-width="1"/>')
        val_label = int(y_max * frac)
        lines.append(f'<text x="{PL-6}" y="{y+4:.1f}" text-anchor="end" font-family="system-ui" font-size="11" fill="#87867F">{val_label}</text>')

    rects = []
    for i, bar in enumerate(bars):
        val       = bar.get("value", 0)
        label     = bar.get("label", "")
        highlight = bar.get("highlight", False)
        fill      = "#D97757" if highlight else "#E3DACC"
        lbl_fill  = "#3D3D3A" if highlight else "#87867F"
        lbl_wt    = "600" if highlight else "400"

        bh = ch * (val / y_max) if y_max else 0
        x  = PL + i * (bar_w + bar_gap) + bar_gap / 2
        y  = H - PB - bh
        cx = x + bar_w / 2

        rects.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" rx="4" fill="{fill}"/>')
        if val:
            rects.append(f'<text x="{cx:.1f}" y="{y-4:.1f}" text-anchor="middle" font-family="system-ui" font-size="11" fill="{lbl_fill}" font-weight="{lbl_wt}">{val}</text>')
        rects.append(f'<text x="{cx:.1f}" y="{H-PB+16:.1f}" text-anchor="middle" font-family="system-ui" font-size="11" fill="#87867F">{_e(label)}</text>')

    cap = f'<p class="text-xs text-muted" style="margin-top:10px">{_e(caption)}</p>' if caption else ""
    svg = f'<svg viewBox="0 0 {W} {H}" style="display:block;width:100%;height:auto">{"".join(lines)}{"".join(rects)}</svg>'
    return f'<div class="chart-panel">{svg}{cap}</div>'


# ── 4. file_section ───────────────────────────────────────────────────────────

_RISK = {
    "safe":   ("safe", "safe"),
    "medium": ("worth a look", "medium"),
    "high":   ("needs attention", "attention"),
}

def file_section(data: dict) -> str:
    path      = data.get("path", "")
    additions = data.get("additions", 0)
    deletions = data.get("deletions", 0)
    risk      = data.get("risk", "safe")
    hunks     = data.get("hunks", [])
    comments  = data.get("comments", [])

    risk_label, risk_cls = _RISK.get(risk, (risk, "safe"))
    diff_html     = primitives.diff_block({"hunks": hunks}) if hunks else ""
    comments_html = primitives.comment_thread({"comments": comments}) if comments else ""

    return (
        f'<div class="file-card">'
        f'<div class="file-head">'
        f'<span class="file-path">{_e(path)}</span>'
        f'<span class="file-delta"><span style="color:var(--olive)">+{additions}</span> '
        f'<span style="color:var(--rust)">-{deletions}</span></span>'
        f'<span class="risk-tag {risk_cls}">{_e(risk_label)}</span>'
        f'</div>'
        f'{diff_html}{comments_html}'
        f'</div>'
    )


# ── 5. shipped_item_list ──────────────────────────────────────────────────────

def shipped_item_list(data: dict) -> str:
    items = data.get("items", [])
    rows = []
    for item in items:
        title     = item.get("title", "")
        desc      = item.get("description", "")
        reference = item.get("reference", "")
        color     = item.get("color", "var(--clay)")
        rows.append(
            f'<div class="shipped-item">'
            f'<span class="shipped-dot" style="background:{_e(color)}"></span>'
            f'<div class="shipped-body">'
            f'<div class="shipped-title">{_e(title)}</div>'
            f'<div class="shipped-desc">{_e(desc)}</div>'
            f'</div>'
            f'<span class="shipped-ref">{_e(reference)}</span>'
            f'</div>'
        )
    return f'<div class="shipped-list">{"".join(rows)}</div>'


# ── 6. callout ────────────────────────────────────────────────────────────────

def callout(data: dict) -> str:
    content = data.get("content", "")
    variant = data.get("variant", "tinted")  # dark | tinted
    label   = data.get("label", "")
    label_html = f'<div class="callout-label">{_e(label)}</div>' if label else ""
    return f'<div class="callout callout-{_e(variant)}">{label_html}<div class="callout-content">{content}</div></div>'


# ── 7. action_checklist ───────────────────────────────────────────────────────

def action_checklist(data: dict) -> str:
    items = data.get("items", [])
    rows = []
    for item in items:
        avatar = item.get("avatar", "")
        desc   = item.get("description", "")
        due    = item.get("due", "")
        done   = item.get("done", False)

        check_style = "background:var(--olive);color:var(--white);border-color:var(--olive)" if done else ""
        check_mark  = "✓" if done else ""
        done_cls    = " done" if done else ""
        body_style  = ' style="text-decoration:line-through;color:var(--gray-500)"' if done else ""

        rows.append(
            f'<div class="action-item{done_cls}">'
            f'<div class="action-check" style="{check_style}">{check_mark}</div>'
            f'<div class="avatar text-xs">{_e(avatar)}</div>'
            f'<div class="action-body"{body_style}>{_e(desc)}</div>'
            f'<div class="action-due">{_e(due)}</div>'
            f'</div>'
        )
    return f'<div class="action-list">{"".join(rows)}</div>'


# ── 8. decision_card ──────────────────────────────────────────────────────────

def decision_card(data: dict) -> str:
    question = data.get("question", "")
    context  = data.get("context", "")
    options  = data.get("options", [])

    opts = []
    for opt in options:
        label     = opt.get("label", "")
        suggested = opt.get("suggested", False)
        style = "background:var(--clay);color:var(--white)" if suggested else ""
        opts.append(f'<span class="chip" style="{style}">{_e(label)}</span>')

    return (
        f'<div class="decision-card">'
        f'<div class="decision-question">{_e(question)}</div>'
        f'<p style="font-size:13px;color:var(--gray-700);margin:8px 0 14px">{_e(context)}</p>'
        f'<div style="display:flex;gap:8px;flex-wrap:wrap">{"".join(opts)}</div>'
        f'</div>'
    )


# ── 9. code_block ─────────────────────────────────────────────────────────────

def code_block(data: dict) -> str:
    filename = data.get("filename", "")
    language = data.get("language", "")
    code     = data.get("code", "")
    tabs     = data.get("tabs", [])  # [{label, code, active?}]

    if tabs:
        # Tabbed code block — inline JS for tab switching
        tab_id = f"cb-{abs(hash(filename or tabs[0].get('label','')))}".replace("-", "")
        tab_headers = "".join(
            f'<button onclick="__tab(\'{tab_id}\',{i})" '
            f'id="{tab_id}-btn-{i}" '
            f'style="font-family:var(--mono);font-size:11px;padding:8px 14px;border:none;border-bottom:2px solid '
            f'{"var(--clay)" if t.get("active") or i==0 else "transparent"};'
            f'background:none;cursor:pointer;color:{"var(--slate)" if t.get("active") or i==0 else "var(--gray-500)"}">'
            f'{_e(t.get("label",""))}</button>'
            for i, t in enumerate(tabs)
        )
        pres = "".join(
            f'<pre id="{tab_id}-pre-{i}" class="code-block-body" '
            f'style="{"" if t.get("active") or i==0 else "display:none"}">{_e(t.get("code",""))}</pre>'
            for i, t in enumerate(tabs)
        )
        js = (
            f'<script>function __tab(id,idx){{'
            f'document.querySelectorAll("[id^=\'"+id+"-pre\']").forEach(function(el,i){{'
            f'el.style.display=i===idx?"block":"none";'
            f'}});'
            f'document.querySelectorAll("[id^=\'"+id+"-btn\']").forEach(function(el,i){{'
            f'el.style.borderBottomColor=i===idx?"var(--clay)":"transparent";'
            f'el.style.color=i===idx?"var(--slate)":"var(--gray-500)";'
            f'}});'
            f'}}</script>'
        )
        return (
            f'<div class="code-block-wrap">'
            f'<div class="code-block-head" style="padding:0;gap:0">{tab_headers}</div>'
            f'{pres}{js}'
            f'</div>'
        )

    head_parts = []
    if filename:
        head_parts.append(f'<span class="file-path" style="font-size:12px">{_e(filename)}</span>')
    if language:
        head_parts.append(f'<span class="text-xs mono text-muted">{_e(language)}</span>')

    head_html = f'<div class="code-block-head">{"".join(head_parts)}</div>' if head_parts else ""
    return (
        f'<div class="code-block-wrap">'
        f'{head_html}'
        f'<pre class="code-block-body">{_e(code)}</pre>'
        f'</div>'
    )


# ── 10. drag_list ─────────────────────────────────────────────────────────────

_DRAG_LIST_JS = """<script>
(function(){
  document.querySelectorAll('.drag-list').forEach(function(list){
    var dragging=null;
    list.addEventListener('dragstart',function(e){
      dragging=e.target.closest('.drag-item');
      if(dragging) setTimeout(function(){dragging.classList.add('dragging');},0);
    });
    list.addEventListener('dragend',function(){
      if(dragging){dragging.classList.remove('dragging');dragging=null;}
    });
    list.addEventListener('dragover',function(e){
      e.preventDefault();
      if(!dragging) return;
      var t=e.target.closest('.drag-item');
      if(t&&t!==dragging){
        var r=t.getBoundingClientRect();
        list.insertBefore(dragging,e.clientY<r.top+r.height/2?t:t.nextSibling);
      }
    });
  });
})();
</script>"""

def drag_list(data: dict) -> str:
    items   = data.get("items", [])
    title   = data.get("title", "")
    title_html = f'<div class="eyebrow" style="margin-bottom:10px">{_e(title)}</div>' if title else ""

    rows = []
    for item in items:
        label = item.get("label", "")
        count = item.get("count")
        count_html = f'<span class="drag-count">{_e(count)}</span>' if count is not None else ""
        grip = '<span class="drag-grip">' + '<i></i>' * 6 + '</span>'
        rows.append(f'<li class="drag-item" draggable="true">{grip}<span class="drag-label">{_e(label)}</span>{count_html}</li>')

    return f'{title_html}<ul class="drag-list">{"".join(rows)}</ul>{_DRAG_LIST_JS}'


# ── 11. step_list ─────────────────────────────────────────────────────────────

def step_list(data: dict) -> str:
    steps = data.get("steps", [])
    rows  = []
    for i, step in enumerate(steps, 1):
        title  = step.get("title", "")
        body   = step.get("body", "")
        code   = step.get("code", "")
        body_h = f'<p style="font-size:13px;color:var(--gray-700);margin:6px 0 0;line-height:1.6">{_e(body)}</p>' if body else ""
        code_h = f'<pre class="code-block-body" style="margin-top:10px;border-radius:6px">{_e(code)}</pre>' if code else ""
        rows.append(
            f'<div class="step">'
            f'<div class="step-num">{i}</div>'
            f'<div><div class="step-title">{_e(title)}</div>{body_h}{code_h}</div>'
            f'</div>'
        )
    return f'<div class="step-list">{"".join(rows)}</div>'


# ── 12. two_col_compare ───────────────────────────────────────────────────────
# NOTE: items inside each column are pre-rendered HTML strings by compose.py
# This function is called directly from compose._render_item with pre-rendered content.

def two_col_compare_from_html(left_header: str, left_html: str,
                               right_header: str, right_html: str) -> str:
    return (
        f'<div class="two-col-compare">'
        f'<div><div class="compare-col-head">{_e(left_header)}</div><div>{left_html}</div></div>'
        f'<div><div class="compare-col-head">{_e(right_header)}</div><div>{right_html}</div></div>'
        f'</div>'
    )


# ── 13. flow_diagram ──────────────────────────────────────────────────────────

_ACCENT_COLORS = {
    "clay":  {"stroke": "#D97757", "fill": "rgba(217,119,87,0.07)"},
    "olive": {"stroke": "#788C5D", "fill": "rgba(120,140,93,0.07)"},
    "rust":  {"stroke": "#B04A3F", "fill": "rgba(176,74,63,0.07)"},
    "gray":  {"stroke": "#87867F", "fill": "rgba(135,134,127,0.07)"},
    "none":  {"stroke": "#D1CFC5", "fill": "#FFFFFF"},
}


def _flow_layout(nodes: list, edges: list, def_nw: int, def_nh: int,
                 h_gap: int, v_gap: int, direction: str) -> tuple:
    node_ids = [n["id"] for n in nodes]
    in_deg   = {nid: 0 for nid in node_ids}
    succs    = {nid: [] for nid in node_ids}

    for e in edges:
        src, dst = e.get("from", ""), e.get("to", "")
        if src in succs and dst in in_deg:
            succs[src].append(dst)
            in_deg[dst] += 1

    # Kahn's longest-path layer assignment
    layers: dict[str, int] = {}
    queue = [nid for nid in node_ids if in_deg[nid] == 0]
    for nid in queue:
        layers[nid] = 0
    while queue:
        nid = queue.pop(0)
        for s in succs[nid]:
            in_deg[s] -= 1
            layers[s] = max(layers.get(s, 0), layers[nid] + 1)
            if in_deg[s] == 0:
                queue.append(s)

    # Nodes not reached (cycles) → last layer + 1
    max_l = max(layers.values(), default=0)
    for n in nodes:
        if n["id"] not in layers:
            layers[n["id"]] = max_l + 1

    # Node size map
    def _nw(n): return n.get("width",  220 if n.get("primitive") else def_nw)
    def _nh(n): return n.get("height",  90 if n.get("primitive") else def_nh)
    nw_map = {n["id"]: _nw(n) for n in nodes}
    nh_map = {n["id"]: _nh(n) for n in nodes}

    # Group by layer, compute centre positions
    groups: dict[int, list] = {}
    for nid, l in layers.items():
        groups.setdefault(l, []).append(nid)

    pos: dict[str, tuple] = {}  # id → (cx, cy, w, h)
    for li, layer_nodes in sorted(groups.items()):
        widths   = [nw_map[nid] for nid in layer_nodes]
        total_w  = sum(widths) + h_gap * (len(layer_nodes) - 1)
        x        = -total_w / 2
        for nid in layer_nodes:
            nw, nh = nw_map[nid], nh_map[nid]
            pos[nid] = (x + nw / 2, li * (def_nh + v_gap) + nh / 2, nw, nh)
            x += nw + h_gap

    # Normalise so minimum is (padding, padding)
    pad = 48
    if pos:
        min_x = min(cx - nw / 2 for cx, cy, nw, nh in pos.values()) - pad
        min_y = min(cy - nh / 2 for cx, cy, nw, nh in pos.values()) - pad
        pos = {nid: (cx - min_x, cy - min_y, nw, nh) for nid, (cx, cy, nw, nh) in pos.items()}

    # LR: transpose
    if direction == "LR":
        pos = {nid: (cy, cx, nh, nw) for nid, (cx, cy, nw, nh) in pos.items()}

    canvas_w = (max(cx + nw / 2 for cx, cy, nw, nh in pos.values()) + pad) if pos else 200
    canvas_h = (max(cy + nh / 2 for cx, cy, nw, nh in pos.values()) + pad) if pos else 100
    return pos, canvas_w, canvas_h


def flow_diagram(data: dict) -> str:
    nodes     = data.get("nodes", [])
    edges     = data.get("edges", [])
    direction = data.get("direction", "TB").upper()
    def_nw    = data.get("node_width",  160)
    def_nh    = data.get("node_height",  56)
    h_gap     = data.get("h_gap", 48)
    v_gap     = data.get("v_gap", 64)
    caption   = data.get("caption", "")

    if not nodes:
        return '<div class="diagram-wrap"><p class="text-muted text-sm">No nodes defined.</p></div>'

    pos, W, H = _flow_layout(nodes, edges, def_nw, def_nh, h_gap, v_gap, direction)

    # Node lookup
    node_map = {n["id"]: n for n in nodes}

    has_primitives = any(n.get("primitive") for n in nodes)

    # ── Arrow marker ──────────────────────────────────────────────────────────
    arrow_marker = (
        '<marker id="arr" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">'
        '<path d="M0,0 L0,6 L8,3 z" fill="#B8B5AC"/>'
        '</marker>'
    )
    style_block = f'<style>{BASE_CSS}</style>' if has_primitives else ''

    # ── Edges ─────────────────────────────────────────────────────────────────
    edge_svgs = []
    for e in edges:
        src_id, dst_id = e.get("from", ""), e.get("to", "")
        if src_id not in pos or dst_id not in pos:
            continue
        sx, sy, sw, sh = pos[src_id]
        dx, dy, dw, dh = pos[dst_id]
        lbl   = e.get("label", "")
        dashed = e.get("style", "solid") == "dashed"
        dash_attr = ' stroke-dasharray="6,4"' if dashed else ''

        # Edge ports: bottom→top (TB) or right→left (LR)
        if direction == "TB":
            x1, y1 = sx, sy + sh / 2
            x2, y2 = dx, dy - dh / 2
        else:
            x1, y1 = sx + sw / 2, sy
            x2, y2 = dx - dw / 2, dy

        # Cubic bezier control points
        cp_offset = abs(y2 - y1) * 0.45 if direction == "TB" else abs(x2 - x1) * 0.45
        if direction == "TB":
            c1x, c1y = x1, y1 + cp_offset
            c2x, c2y = x2, y2 - cp_offset
        else:
            c1x, c1y = x1 + cp_offset, y1
            c2x, c2y = x2 - cp_offset, y2

        path = (
            f'<path d="M{x1:.1f},{y1:.1f} C{c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} {x2:.1f},{y2:.1f}"'
            f' fill="none" stroke="#C8C5BC" stroke-width="1.5"{dash_attr} marker-end="url(#arr)"/>'
        )
        edge_svgs.append(path)

        # Edge label at midpoint
        if lbl:
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            edge_svgs.append(
                f'<rect x="{mx - len(lbl)*3.2:.1f}" y="{my - 9:.1f}" '
                f'width="{len(lbl)*6.4:.1f}" height="14" rx="3" fill="#FAF9F5" opacity="0.9"/>'
                f'<text x="{mx:.1f}" y="{my + 1:.1f}" text-anchor="middle" '
                f'font-family="ui-monospace,\'SF Mono\',Menlo,monospace" font-size="9.5" fill="#87867F">'
                f'{_e(lbl)}</text>'
            )

    # ── Nodes ─────────────────────────────────────────────────────────────────
    node_svgs = []
    fo_blocks = []  # foreignObject elements go after SVG is closed (for HTML primitives)

    for n in nodes:
        nid = n["id"]
        if nid not in pos:
            continue
        cx, cy, nw, nh = pos[nid]
        x0, y0 = cx - nw / 2, cy - nh / 2
        accent  = _ACCENT_COLORS.get(n.get("accent", "none"), _ACCENT_COLORS["none"])
        label   = n.get("label", nid)
        sublabel = n.get("sublabel", "")
        prim    = n.get("primitive")

        if prim:
            # Render primitive, embed in foreignObject
            try:
                import compose as _compose
                prim_html = _compose.PRIMITIVE_RENDERERS.get(
                    prim.get("primitive", ""), lambda d: ""
                )(prim)
            except Exception:
                prim_html = f'<div style="font-size:12px">{_e(label)}</div>'

            # Rect backdrop
            node_svgs.append(
                f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{nw}" height="{nh}" rx="10"'
                f' fill="{accent["fill"]}" stroke="{accent["stroke"]}" stroke-width="1.5"/>'
            )
            # foreignObject
            node_svgs.append(
                f'<foreignObject x="{x0:.1f}" y="{y0:.1f}" width="{nw}" height="{nh}">'
                f'<div xmlns="http://www.w3.org/1999/xhtml" style="width:{nw}px;height:{nh}px;overflow:hidden">'
                f'{prim_html}'
                f'</div></foreignObject>'
            )
        else:
            # Text node
            r = 10
            node_svgs.append(
                f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{nw}" height="{nh}" rx="{r}"'
                f' fill="{accent["fill"]}" stroke="{accent["stroke"]}" stroke-width="1.5"/>'
            )
            # Label
            label_y = cy + (0 if not sublabel else -8)
            node_svgs.append(
                f'<text x="{cx:.1f}" y="{label_y:.1f}" text-anchor="middle" dominant-baseline="middle"'
                f' font-family="ui-serif,Georgia,serif" font-size="13" font-weight="500" fill="#141413">'
                f'{_e(label)}</text>'
            )
            if sublabel:
                node_svgs.append(
                    f'<text x="{cx:.1f}" y="{cy + 10:.1f}" text-anchor="middle" dominant-baseline="middle"'
                    f' font-family="ui-monospace,\'SF Mono\',Menlo,monospace" font-size="10" fill="#87867F">'
                    f'{_e(sublabel)}</text>'
                )

    svg = (
        f'<svg viewBox="0 0 {W:.0f} {H:.0f}" '
        f'style="display:block;width:100%;height:auto;max-height:600px">'
        f'<defs>{style_block}{arrow_marker}</defs>'
        + "".join(edge_svgs)
        + "".join(node_svgs)
        + '</svg>'
    )

    cap_html = f'<p class="diagram-caption">{_e(caption)}</p>' if caption else ""
    return f'<div class="diagram-wrap">{svg}{cap_html}</div>'
