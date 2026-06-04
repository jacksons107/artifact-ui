import html as _html
from typing import Any


def _e(s: Any) -> str:
    return _html.escape(str(s))


# ── Structural ─────────────────────────────────────────────────────────────────

def page_header(data: dict) -> str:
    eyebrow    = data.get("eyebrow", "")
    title      = data.get("title", "")
    description = data.get("description", "")
    pill       = data.get("pill", "")

    eyebrow_html = f'<div class="eyebrow">{_e(eyebrow)}</div>' if eyebrow else ""
    pill_html    = f'<span class="badge badge-outlined" style="margin-left:12px">{_e(pill)}</span>' if pill else ""
    desc_html    = f'<p class="description">{_e(description)}</p>' if description else ""

    return f'''<div class="page-header">
  {eyebrow_html}
  <h1>{_e(title)}{pill_html}</h1>
  {desc_html}
</div>'''


def section_header(data: dict) -> str:
    title = data.get("title", "")
    if not title:
        return ""
    return f'''<div class="section-header">
  <h2>{_e(title)}</h2>
  <div class="section-divider"></div>
</div>'''


def divider(data: dict) -> str:
    return '<hr class="divider">'


# ── Core components ────────────────────────────────────────────────────────────

def badge(data: dict) -> str:
    text = data.get("text", "")
    tone = data.get("tone", "neutral")
    return f'<span class="badge badge-{_e(tone)}">{_e(text)}</span>'


def avatar(data: dict) -> str:
    initials = data.get("initials", "")
    color    = data.get("color", "")
    bordered = data.get("bordered", False)
    cls = "avatar" + (f" {_e(color)}" if color else "") + (" bordered" if bordered else "")
    return f'<div class="{cls}">{_e(initials)}</div>'


def button(data: dict) -> str:
    text    = data.get("text", "")
    variant = data.get("variant", "ghost")
    return f'<button class="btn btn-{_e(variant)}">{_e(text)}</button>'


def chip(data: dict) -> str:
    text = data.get("text", "")
    tone = data.get("tone", "")
    cls  = "chip" + (f" {_e(tone)}" if tone else "")
    return f'<span class="{cls}">{_e(text)}</span>'


def prose(data: dict) -> str:
    text  = data.get("text", "")
    items = data.get("items", [])
    html  = f"<p>{_e(text)}</p>" if text else ""
    if items:
        lis = "".join(f"<li>{_e(item)}</li>" for item in items)
        html += f"<ul>{lis}</ul>"
    return f'<div class="prose">{html}</div>'


# ── Cards ──────────────────────────────────────────────────────────────────────

def card(data: dict) -> str:
    variant  = data.get("variant", "outlined")
    title    = data.get("title", "")
    subtitle = data.get("subtitle", "")
    tags     = data.get("tags", [])
    initials = data.get("initials", "")
    actions  = data.get("actions", [])
    content  = data.get("content", "")

    av_html = f'<div class="avatar">{_e(initials)}</div>' if initials else ""
    sub_html = f'<p class="card-sub">{_e(subtitle)}</p>' if subtitle else ""
    head_html = ""
    if title:
        head_html = f'''<div class="card-head">
    {av_html}
    <div class="card-titles">
      <p class="card-title">{_e(title)}</p>
      {sub_html}
    </div>
  </div>'''

    chips_html = ""
    if tags:
        chips = "".join(f'<span class="chip">{_e(t)}</span>' for t in tags)
        chips_html = f'<div class="card-chips">{chips}</div>'

    actions_html = "".join(button(a) for a in actions)

    return f'<div class="card {_e(variant)}">{head_html}{chips_html}{content}{actions_html}</div>'


# ── Stat card ──────────────────────────────────────────────────────────────────

def stat_card(data: dict) -> str:
    number    = data.get("number", "")
    label     = data.get("label", "")
    delta     = data.get("delta", "")
    delta_dir = data.get("delta_direction", "flat")
    warn      = data.get("warning", False)

    cls        = "stat-card" + (" warn" if warn else "")
    delta_html = f'<div class="stat-delta {_e(delta_dir)}">{_e(delta)}</div>' if delta else ""

    return f'''<div class="{cls}">
  <div class="stat-num">{_e(number)}</div>
  <div class="stat-label">{_e(label)}</div>
  {delta_html}
</div>'''


# ── Data table ─────────────────────────────────────────────────────────────────

def table(data: dict) -> str:
    columns = data.get("columns", [])
    rows    = data.get("rows", [])

    header = "".join(f"<th>{_e(c)}</th>" for c in columns)

    body_rows = []
    for row in rows:
        cells = []
        for cell in row:
            if isinstance(cell, dict):
                kind = cell.get("type", "text")
                if kind == "link":
                    cells.append(f'<td><a class="pr-link" href="#">{_e(cell.get("text",""))}</a></td>')
                elif kind == "risk":
                    lvl = cell.get("level", "low")
                    lbl = cell.get("label", lvl.capitalize())
                    cells.append(f'<td><span class="risk"><span class="risk-dot {_e(lvl)}"></span>{_e(lbl)}</span></td>')
                elif kind == "badge":
                    tone = cell.get("tone", "neutral")
                    cells.append(f'<td><span class="badge badge-{_e(tone)}">{_e(cell.get("text",""))}</span></td>')
                elif kind == "mono":
                    cells.append(f'<td class="mono text-sm">{_e(cell.get("text",""))}</td>')
                else:
                    cells.append(f'<td>{_e(cell.get("text",""))}</td>')
            else:
                cells.append(f"<td>{_e(cell)}</td>")
        body_rows.append(f'<tr>{"".join(cells)}</tr>')

    return f'''<table class="data-table">
  <thead><tr>{header}</tr></thead>
  <tbody>{"".join(body_rows)}</tbody>
</table>'''


# ── Bullet list ────────────────────────────────────────────────────────────────

def bullet_list(data: dict) -> str:
    items = data.get("items", [])
    lis = []
    for item in items:
        if isinstance(item, dict):
            strong = item.get("strong", "")
            text   = item.get("text", "")
            lis.append(f'<li>{f"<strong>{_e(strong)}</strong> " if strong else ""}{_e(text)}</li>')
        else:
            lis.append(f"<li>{_e(item)}</li>")
    return f'<ul class="bullet-list">{"".join(lis)}</ul>'


# ── Inset panel ────────────────────────────────────────────────────────────────

def inset_panel(data: dict) -> str:
    items = data.get("items", [])
    parts = []
    for item in items:
        tag  = item.get("tag", "")
        text = item.get("text", "")
        note = item.get("note", "")
        note_html = f' <span class="inset-note">· {_e(note)}</span>' if note else ""
        parts.append(f'''<div class="inset-item">
  <span class="inset-tag">{_e(tag)}</span>
  <div class="inset-body">{_e(text)}{note_html}</div>
</div>''')
    return f'<div class="inset-panel">{"".join(parts)}</div>'


# ── Diff block ─────────────────────────────────────────────────────────────────

def diff_block(data: dict) -> str:
    hunks = data.get("hunks", [])
    MARKS = {"add": "+", "del": "-", "hunk": "@@", "ctx": ""}
    rows = []
    for h in hunks:
        row_type = h.get("type", "ctx")
        ln       = _e(h.get("line", "")) if h.get("line") is not None else ""
        mark     = MARKS.get(row_type, "")
        code     = _e(h.get("code", ""))
        rows.append(
            f'<div class="diff-row {row_type}">'
            f'<span class="ln">{ln}</span>'
            f'<span class="mark">{mark}</span>'
            f'<span class="code">{code}</span></div>'
        )
    return f'<div class="diff">{"".join(rows)}</div>'


def diff_comment(data: dict) -> str:
    severity = data.get("severity", "nit")
    anchor   = data.get("anchor", "")
    text     = data.get("text", "")
    anchor_html = f'<div class="anchor">{_e(anchor)}</div>' if anchor else ""
    label = severity.capitalize()
    return f'''<div class="bubble {_e(severity)}">
  {anchor_html}
  <p><span class="label">{_e(label)}</span>{_e(text)}</p>
</div>'''


def comment_thread(data: dict) -> str:
    comments = data.get("comments", [])
    parts = "".join(diff_comment(c) for c in comments)
    return f'<div class="comment-thread">{parts}</div>'


# ── Kanban ─────────────────────────────────────────────────────────────────────

_KANBAN_JS = """<script>
(function() {
  var dragging = null;
  var board = document.querySelector('.kanban-board');
  if (!board) return;
  board.addEventListener('dragstart', function(e) {
    var t = e.target.closest('.ticket');
    if (!t) return;
    dragging = t;
    setTimeout(function() { t.classList.add('dragging'); }, 0);
  });
  board.addEventListener('dragend', function() {
    if (dragging) { dragging.classList.remove('dragging'); dragging = null; }
    board.querySelectorAll('.kanban-col').forEach(function(c) { c.classList.remove('dragover'); });
  });
  board.addEventListener('dragover', function(e) {
    e.preventDefault();
    var col = e.target.closest('.kanban-col');
    if (col) {
      board.querySelectorAll('.kanban-col').forEach(function(c) { c.classList.remove('dragover'); });
      col.classList.add('dragover');
    }
  });
  board.addEventListener('drop', function(e) {
    e.preventDefault();
    var col = e.target.closest('.kanban-col');
    if (col && dragging) {
      col.querySelector('.kanban-col-body').appendChild(dragging);
      col.classList.remove('dragover');
      board.querySelectorAll('.kanban-col').forEach(function(c) {
        c.querySelector('.count').textContent = c.querySelectorAll('.ticket').length;
      });
    }
  });
})();
</script>"""


def ticket(data: dict) -> str:
    tid      = data.get("id", "")
    title    = data.get("title", "")
    tag      = data.get("tag", "")
    estimate = data.get("estimate", "")
    owner    = data.get("owner_initials", "")
    o_class  = data.get("owner_class", "")

    tag_html  = f'<span class="tag tag-{_e(tag)}">{_e(tag)}</span>' if tag else ""
    est_html  = f'<span class="est">{_e(estimate)}</span>' if estimate else ""
    o_cls     = "owner" + (f" {_e(o_class)}" if o_class else "")
    owner_html = f'<span class="{o_cls}">{_e(owner)}</span>' if owner else ""

    return f'''<article class="ticket" draggable="true" data-id="{_e(tid)}">
  <div class="ticket-top"><span class="tid">{_e(tid)}</span>{tag_html}{est_html}</div>
  <div class="ttitle">{_e(title)}</div>
  <div class="ticket-bot">{owner_html}</div>
</article>'''


def kanban_column(data: dict) -> str:
    title        = data.get("title", "")
    tickets_data = data.get("tickets", [])
    accent       = data.get("accent", "gray")
    col_id       = data.get("id", "")

    tickets_html = "".join(ticket(t) for t in tickets_data)
    return f'''<div class="kanban-col accent-{_e(accent)}" data-col="{_e(col_id)}">
  <div class="kanban-col-head">
    <h3>{_e(title)}</h3>
    <span class="count">{len(tickets_data)}</span>
  </div>
  <div class="kanban-col-body">{tickets_html}</div>
</div>'''


def kanban_board(data: dict) -> str:
    cols_data = data.get("columns", [])
    cols_html = "".join(kanban_column(c) for c in cols_data)
    return f'<div class="kanban-board">{cols_html}</div>{_KANBAN_JS}'
