from .styles import NODE_KIND_STYLES, _DEFAULT_NODE_STYLE, _e

# ── Sequence diagram ─────────────────────────────────────────────────────────

_SEQ_COL_W    = 140
_SEQ_COL_GAP  = 56
_SEQ_HEADER_H = 52
_SEQ_STEP_H   = 64
_SEQ_TOP_PAD  = 20
_SEQ_SIDE_PAD = 40


def _render_seq_svg(seq: dict, node_by_id: dict) -> str:
    steps = seq.get("steps", [])
    if not steps:
        return ""

    # Collect participants in order of first appearance
    seen: dict[str, bool] = {}
    participants: list[str] = []
    for step in steps:
        for fld in ("from", "to"):
            nid = step.get(fld)
            if nid and nid not in seen:
                seen[nid] = True
                participants.append(nid)

    n     = len(participants)
    SVG_W = 2 * _SEQ_SIDE_PAD + n * _SEQ_COL_W + max(0, n - 1) * _SEQ_COL_GAP
    SVG_H = _SEQ_TOP_PAD + _SEQ_HEADER_H + len(steps) * _SEQ_STEP_H + 32

    # Center-x per participant
    col_cx: dict[str, float] = {}
    for i, nid in enumerate(participants):
        col_cx[nid] = _SEQ_SIDE_PAD + i * (_SEQ_COL_W + _SEQ_COL_GAP) + _SEQ_COL_W / 2

    LIFELINE_TOP = _SEQ_TOP_PAD + _SEQ_HEADER_H
    LIFELINE_BOT = SVG_H - 16

    parts = [
        f'<svg viewBox="0 0 {SVG_W:.0f} {SVG_H:.0f}" '
        f'style="display:block;width:100%;height:auto;max-height:720px">'
    ]

    # Participant boxes and lifelines
    for nid in participants:
        node = node_by_id.get(nid, {})
        cx   = col_cx[nid]
        x    = cx - _SEQ_COL_W / 2
        kind = node.get("kind", "")
        nst  = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)
        label = _e(node.get("label", nid))
        tech  = _e(node.get("tech", ""))

        parts.append(
            f'<rect x="{x:.1f}" y="{_SEQ_TOP_PAD}" width="{_SEQ_COL_W}" height="{_SEQ_HEADER_H}" rx="8" '
            f'fill="{nst["fill"]}" stroke="{nst["stroke"]}" stroke-width="1.5"/>'
        )
        lbl_y = _SEQ_TOP_PAD + _SEQ_HEADER_H / 2 - (6 if tech else 0)
        parts.append(
            f'<text x="{cx:.1f}" y="{lbl_y:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'font-family="ui-serif,Georgia,serif" font-size="12" font-weight="500" fill="#141413">'
            f'{nst["icon"]} {label}</text>'
        )
        if tech:
            parts.append(
                f'<text x="{cx:.1f}" y="{_SEQ_TOP_PAD + _SEQ_HEADER_H / 2 + 10:.1f}" '
                f'text-anchor="middle" font-family="ui-monospace,monospace" font-size="10" fill="#87867F">'
                f'{tech}</text>'
            )
        # Lifeline
        parts.append(
            f'<line x1="{cx:.1f}" y1="{LIFELINE_TOP}" x2="{cx:.1f}" y2="{LIFELINE_BOT}" '
            f'stroke="#D1CFC5" stroke-width="1" stroke-dasharray="4,4"/>'
        )

    # Steps
    seq_id = seq.get("id", "")
    for i, step in enumerate(steps):
        src = step.get("from")
        dst = step.get("to")
        if not src or not dst or src not in col_cx or dst not in col_cx:
            continue

        sx    = col_cx[src]
        ex    = col_cx[dst]
        y     = LIFELINE_TOP + (i + 0.5) * _SEQ_STEP_H
        label = step.get("label", "")
        has_example = bool(step.get("example") or step.get("example_before") or step.get("example_after"))

        if has_example:
            target = f'step-panel-{_e(seq_id)}-{i}'
            parts.append(
                f'<g class="sys-seq-step" data-target="{target}" '
                f'style="cursor:pointer" onclick="sysSeqStepClick(this)">'
            )

        if src == dst:
            # Self-loop: small arc to the right
            r  = 20
            lx = sx + _SEQ_COL_W / 2 - 10
            parts.append(
                f'<path d="M{sx:.1f},{y-10:.1f} Q{lx:.1f},{y-10:.1f} {lx:.1f},{y:.1f} '
                f'Q{lx:.1f},{y+10:.1f} {sx:.1f},{y+10:.1f}" '
                f'fill="none" stroke="#D97757" stroke-width="1.5" class="sys-seq-line"/>'
            )
            if label:
                parts.append(
                    f'<text x="{lx+6:.1f}" y="{y+3:.1f}" '
                    f'font-family="ui-monospace,monospace" font-size="10" fill="#D97757">'
                    f'{_e(label)}</text>'
                )
            if has_example:
                parts.append(
                    f'<circle cx="{lx+6:.1f}" cy="{y-14:.1f}" r="3" fill="#D97757"/>'
                )
                parts.append("</g>")
            continue

        going_right = ex > sx

        # Draw line body (stops short to leave room for arrowhead)
        tip_x   = ex
        arrow_d = 7
        body_ex = ex - arrow_d if going_right else ex + arrow_d
        parts.append(
            f'<line x1="{sx:.1f}" y1="{y:.1f}" x2="{body_ex:.1f}" y2="{y:.1f}" '
            f'stroke="#D97757" stroke-width="1.5" class="sys-seq-line"/>'
        )

        # Explicit arrowhead polygon (avoids SVG marker rotation ambiguity)
        if going_right:
            pts = f"{tip_x},{y} {tip_x-arrow_d},{y-4} {tip_x-arrow_d},{y+4}"
        else:
            pts = f"{tip_x},{y} {tip_x+arrow_d},{y-4} {tip_x+arrow_d},{y+4}"
        parts.append(f'<polygon points="{pts}" fill="#D97757"/>')

        # Step label above the arrow
        if label:
            mx = (sx + ex) / 2
            parts.append(
                f'<text x="{mx:.1f}" y="{y - 7:.1f}" text-anchor="middle" '
                f'font-family="ui-monospace,monospace" font-size="10" fill="#D97757">'
                f'{_e(label)}</text>'
            )

        # Step index at left margin
        parts.append(
            f'<text x="{_SEQ_SIDE_PAD - 8:.1f}" y="{y + 4:.1f}" text-anchor="end" '
            f'font-family="ui-monospace,monospace" font-size="9" fill="#D1CFC5">{i+1}</text>'
        )

        if has_example:
            # Marker dot indicating an example is available for this step
            mx = (sx + ex) / 2
            parts.append(f'<circle cx="{mx:.1f}" cy="{y - 14:.1f}" r="3" fill="#D97757"/>')
            parts.append("</g>")

    parts.append("</svg>")
    return "\n".join(parts)


def _render_step_panel(seq_id: str, i: int, step: dict) -> str:
    lang = step.get("example_lang", "plaintext")
    single   = step.get("example", "")
    before   = step.get("example_before", "")
    after    = step.get("example_after", "")
    label    = step.get("label", "")

    html  = f'<div class="sys-panel" id="step-panel-{_e(seq_id)}-{i}" style="display:none">'
    html += '<div class="sys-ph">'
    html += f'<span class="sys-plabel">Step {i + 1}{": " + _e(label) if label else ""}</span>'
    html += '</div>'

    if single:
        html += f'<div class="sys-snippet"><pre><code class="language-{lang}">{_e(single)}</code></pre></div>'

    if before and after:
        html += '<div class="sys-chg-diff">'
        html += '<div class="sys-chg-side"><div class="sys-chg-side-label" style="color:#B04A3F">Before</div>'
        html += f'<pre class="sys-chg-pre"><code class="language-{lang}">{_e(before)}</code></pre>'
        html += '</div>'
        html += '<div class="sys-chg-side"><div class="sys-chg-side-label" style="color:#4A7C59">After</div>'
        html += f'<pre class="sys-chg-pre"><code class="language-{lang}">{_e(after)}</code></pre>'
        html += '</div></div>'
    elif after:
        html += f'<pre class="sys-chg-pre"><code class="language-{lang}">{_e(after)}</code></pre>'
    elif before:
        html += f'<pre class="sys-chg-pre"><code class="language-{lang}">{_e(before)}</code></pre>'

    html += '</div>'
    return html


def render_sequence_html(spec: dict) -> str:
    sequences = spec.get("sequences", [])
    if not sequences:
        return ""

    node_by_id = {n["id"]: n for n in spec["nodes"]}
    first_id   = sequences[0]["id"]

    html  = '<div class="sys-seq-wrap">'
    html += '<div class="sys-seq-controls">'
    html += '<span class="sys-fl">Sequence</span>'
    html += '<select class="sys-seq-sel" onchange="sysSeqChange(this)">'
    for seq in sequences:
        html += f'<option value="{_e(seq["id"])}">{_e(seq["label"])}</option>'
    html += '</select>'
    html += '</div>'

    html += '<div class="sys-seq-diagrams">'
    for i, seq in enumerate(sequences):
        display = '' if i == 0 else 'style="display:none"'
        svg = _render_seq_svg(seq, node_by_id)
        steps = seq.get("steps", [])
        example_steps = [
            (j, step) for j, step in enumerate(steps)
            if step.get("example") or step.get("example_before") or step.get("example_after")
        ]

        if example_steps:
            panels = "\n".join(_render_step_panel(seq["id"], j, step) for j, step in example_steps)
            inner = (
                '<div class="sys-wrap">'
                f'<div class="sys-main"><div class="sys-diagram">{svg}</div></div>'
                '<div class="sys-sidebar">'
                '<div class="sys-hint">Click a highlighted step<br>to see an example</div>'
                f'{panels}'
                '</div>'
                '</div>'
            )
            panel_class = "sys-seq-panel sys-seq-panel-flat"
        else:
            inner = svg
            panel_class = "sys-seq-panel"

        html += f'<div id="seqp-{_e(seq["id"])}" class="{panel_class}" {display}>{inner}</div>'
    html += '</div>'

    html += '</div>'
    return html
