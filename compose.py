import re
from typing import Callable


def _extract_head_assets(html: str) -> list[str]:
    head_match = re.search(r"<head[^>]*>(.*?)</head>", html, re.DOTALL | re.IGNORECASE)
    if not head_match:
        return []
    head = head_match.group(1)
    tags = re.findall(
        r'<(?:script|link)\s[^>]*(?:src|href)=["\'][^"\']+["\'][^>]*(?:/>|></script>|>)',
        head,
        re.IGNORECASE,
    )
    return tags


def _extract_body_content(html: str) -> str:
    match = re.search(r"<body[^>]*>(.*)</body>", html, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else html


def render_compose(data: dict, get_renderer: Callable) -> str:
    title = data.get("title", "Composed View")
    layout = data.get("layout", "stack")
    items = data.get("items", [])

    all_assets: list[str] = []
    seen_assets: set[str] = set()
    body_fragments: list[str] = []

    for item in items:
        template_name = item.get("template", "")
        item_data = item.get("data", {})
        renderer = get_renderer(template_name)
        if renderer is None:
            body_fragments.append(
                f'<div class="p-4 text-red-400 font-mono text-sm">Unknown template: {template_name}</div>'
            )
            continue
        sub_html = renderer(item_data)
        for asset in _extract_head_assets(sub_html):
            if asset not in seen_assets:
                all_assets.append(asset)
                seen_assets.add(asset)
        body_fragments.append(_extract_body_content(sub_html))

    grid_class = "grid grid-cols-2 gap-6" if layout == "grid" else "flex flex-col gap-6"

    items_html = "\n".join(
        f'<div class="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">{frag}</div>'
        for frag in body_fragments
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  {"".join(all_assets)}
</head>
<body class="bg-slate-900 min-h-screen p-6">
  <div class="{grid_class} max-w-7xl mx-auto">
    {items_html}
  </div>
</body>
</html>"""
