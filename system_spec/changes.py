from .styles import NODE_KIND_STYLES, _DEFAULT_NODE_STYLE, _infer_lang, _e

# ── Changes tab ──────────────────────────────────────────────────────────────

def render_changes_html(nodes: list) -> str:
    added    = [n for n in nodes if n.get("status") == "added"]
    modified = [n for n in nodes if n.get("status") == "modified"]
    deleted  = [n for n in nodes if n.get("status") == "deleted"]
    if not (added or modified or deleted):
        return ""

    def _node_header(node: dict) -> str:
        kind = node.get("kind", "")
        nst  = NODE_KIND_STYLES.get(kind, _DEFAULT_NODE_STYLE)
        fp   = node.get("file_path", "")
        lr   = node.get("line_range")
        loc  = fp
        if loc and lr and len(lr) == 2:
            loc += f":{lr[0]}–{lr[1]}"
        h  = '<div class="sys-chg-node">'
        if kind:
            h += f'<span class="sys-kbadge" style="color:{nst["stroke"]};border-color:{nst["stroke"]}">{_e(kind)}</span>'
        h += f'<strong class="sys-chg-label">{_e(node.get("label", node["id"]))}</strong>'
        if loc:
            h += f'<span class="sys-chg-fp">{_e(loc)}</span>'
        h += '</div>'
        return h

    def _pre(code: str, lang: str) -> str:
        return f'<pre class="sys-chg-pre"><code class="language-{lang}">{_e(code)}</code></pre>'

    html = '<div class="sys-changes">'

    if added:
        html += '<div class="sys-chg-section">'
        html += '<div class="sys-chg-header" style="color:#4A7C59;border-left-color:#4A7C59">Added</div>'
        for node in added:
            html += _node_header(node)
            snippet = node.get("code_snippet", "")
            if snippet:
                html += _pre(snippet, _infer_lang(node))
        html += '</div>'

    if modified:
        html += '<div class="sys-chg-section">'
        html += '<div class="sys-chg-header" style="color:#B8860B;border-left-color:#B8860B">Modified</div>'
        for node in modified:
            html += _node_header(node)
            prev = node.get("previous_code_snippet", "")
            curr = node.get("code_snippet", "")
            lang = _infer_lang(node)
            if prev and curr:
                html += '<div class="sys-chg-diff">'
                html += '<div class="sys-chg-side"><div class="sys-chg-side-label" style="color:#B04A3F">Before</div>'
                html += _pre(prev, lang)
                html += '</div>'
                html += '<div class="sys-chg-side"><div class="sys-chg-side-label" style="color:#4A7C59">After</div>'
                html += _pre(curr, lang)
                html += '</div></div>'
            elif curr:
                html += _pre(curr, lang)
            elif prev:
                html += _pre(prev, lang)
        html += '</div>'

    if deleted:
        html += '<div class="sys-chg-section">'
        html += '<div class="sys-chg-header" style="color:#B04A3F;border-left-color:#B04A3F">Deleted</div>'
        for node in deleted:
            html += _node_header(node)
            snippet = node.get("previous_code_snippet", "")
            if snippet:
                html += _pre(snippet, _infer_lang(node))
        html += '</div>'

    html += '</div>'
    return html
