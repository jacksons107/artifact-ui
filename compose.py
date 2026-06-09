import html as _html
import primitives
import organisms
from design_system import page_wrapper

PRIMITIVE_RENDERERS = {
    # ── Atoms / Molecules (primitives.py) ──
    "page_header":    primitives.page_header,
    "section_header": primitives.section_header,
    "divider":        primitives.divider,
    "badge":          primitives.badge,
    "avatar":         primitives.avatar,
    "button":         primitives.button,
    "chip":           primitives.chip,
    "prose":          primitives.prose,
    "card":           primitives.card,
    "stat_card":      primitives.stat_card,
    "table":          primitives.table,
    "bullet_list":    primitives.bullet_list,
    "inset_panel":    primitives.inset_panel,
    "diff_block":     primitives.diff_block,
    "diff_comment":   primitives.diff_comment,
    "comment_thread": primitives.comment_thread,
    "ticket":         primitives.ticket,
    "kanban_column":  primitives.kanban_column,
    "kanban_board":   primitives.kanban_board,

    # ── Organisms (organisms.py) ──
    "event_timeline":    organisms.event_timeline,
    "milestone_timeline": organisms.milestone_timeline,
    "bar_chart":         organisms.bar_chart,
    "file_section":      organisms.file_section,
    "shipped_item_list": organisms.shipped_item_list,
    "callout":           organisms.callout,
    "action_checklist":  organisms.action_checklist,
    "decision_card":     organisms.decision_card,
    "code_block":        organisms.code_block,
    "drag_list":         organisms.drag_list,
    "step_list":         organisms.step_list,
    "flow_diagram":      organisms.flow_diagram,
}


def _render_item(item: dict | str, render_fn) -> str:
    if isinstance(item, str):
        return item

    primitive = item.get("primitive", "")

    if primitive == "v_stack":
        items_html = "".join(render_fn(i) for i in item.get("items", []))
        gap = item.get("gap", 16)
        return f'<div class="layout-stack" style="gap:{gap}px">{items_html}</div>'

    if primitive == "grid":
        items_html = "".join(render_fn(i) for i in item.get("items", []))
        cols = item.get("cols", 3)
        gap  = item.get("gap")
        style = f' style="gap:{gap}px"' if gap else ""
        return f'<div class="layout-grid-{_e(cols)}"{style}>{items_html}</div>'

    if primitive == "sidebar_layout":
        main_html    = "".join(render_fn(i) for i in item.get("main", []))
        sidebar_html = "".join(render_fn(i) for i in item.get("sidebar", []))
        return (
            '<div class="layout-sidebar">'
            f'<div class="main-content">{main_html}</div>'
            f'<div class="sidebar">{sidebar_html}</div>'
            '</div>'
        )

    if primitive == "two_col_compare":
        cols = item.get("cols", [{}, {}])
        left, right = cols[0] if len(cols) > 0 else {}, cols[1] if len(cols) > 1 else {}
        left_html  = "".join(render_fn(i) for i in left.get("items", []))
        right_html = "".join(render_fn(i) for i in right.get("items", []))
        return organisms.two_col_compare_from_html(
            left.get("header", ""), left_html,
            right.get("header", ""), right_html,
        )

    if "html" in item:
        return item["html"]

    renderer = PRIMITIVE_RENDERERS.get(primitive)
    if renderer:
        return renderer(item)

    return f'<div class="text-sm mono text-muted" style="color:var(--rust)">unknown primitive: {_html.escape(primitive)}</div>'


def _e(v) -> str:
    return str(v)


def _render_section(section: dict, render_fn) -> str:
    header  = section.get("header", "")
    items   = section.get("items", [])
    layout  = section.get("layout", "stack")
    cols    = section.get("cols", 3)
    gap     = section.get("gap")

    header_html = primitives.section_header({"title": header}) if header else ""
    style = f' style="gap:{gap}px"' if gap else ""

    if layout == "grid":
        items_html = "".join(render_fn(i) for i in items)
        content = f'<div class="layout-grid-{cols}"{style}>{items_html}</div>'

    elif layout == "sidebar":
        main_items    = section.get("main", items)
        sidebar_items = section.get("sidebar", [])
        main_html    = "".join(render_fn(i) for i in main_items)
        sidebar_html = "".join(render_fn(i) for i in sidebar_items)
        content = (
            '<div class="layout-sidebar">'
            f'<div class="main-content">{main_html}</div>'
            f'<div class="sidebar">{sidebar_html}</div>'
            '</div>'
        )

    elif layout == "kanban":
        items_html = "".join(render_fn(i) for i in items)
        content = items_html

    else:  # stack (default)
        items_html = "".join(render_fn(i) for i in items)
        content = f'<div class="layout-stack"{style}>{items_html}</div>'

    return f'<div class="section">{header_html}{content}</div>'


def render_compose(data: dict) -> str:
    title        = data.get("title", "Untitled")
    header_data  = data.get("header")
    sections_data = data.get("sections", [])
    wide         = data.get("wide", False)
    extra_css    = data.get("css", "")

    if not header_data and not sections_data:
        raise ValueError(
            "compose data has no 'header' and no 'sections' — this produces a blank page. "
            "The compose template expects {title?, header?, sections:[{layout, items:[<primitive>...]}]}. "
            "If you have a single primitive/organism payload (e.g. a flow_diagram with nodes/edges), "
            "wrap it: {sections: [{layout: 'stack', items: [<that payload with 'primitive': '...'>]}]}. "
            "Call get_example(name) to see a working reference."
        )

    def render_fn(item):
        return _render_item(item, render_fn)

    header_html   = primitives.page_header(header_data) if header_data else ""
    sections_html = "".join(_render_section(s, render_fn) for s in sections_data)

    return page_wrapper(title, header_html + sections_html, extra_css=extra_css, wide=wide)
