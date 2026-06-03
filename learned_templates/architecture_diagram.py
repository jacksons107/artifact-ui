
def render_architecture_diagram(data: dict) -> str:
    import json, html

    title = html.escape(data.get("title", "SYSTEM"))
    subtitle = html.escape(data.get("subtitle", ""))
    layers = data.get("layers", [])
    legend = data.get("legend", [])

    COLOR_THEMES = {
        "blue":   {"border": "#1f6feb", "text": "#58a6ff"},
        "green":  {"border": "#238636", "text": "#3fb950"},
        "purple": {"border": "#6e40c9", "text": "#bc8cff"},
        "orange": {"border": "#bd5d0a", "text": "#f0883e"},
        "teal":   {"border": "#1b6f6f", "text": "#39d3d3"},
        "pink":   {"border": "#8e2a6e", "text": "#f778ba"},
        "gray":   {"border": "#30363d", "text": "#e6edf3"},
    }

    def render_box(box):
        color = box.get("color", "gray")
        theme = COLOR_THEMES.get(color, COLOR_THEMES["gray"])
        span = box.get("span", 1)
        title_text = html.escape(box.get("title", ""))
        items = box.get("items", [])
        file_path = html.escape(box.get("file", ""))
        badge = box.get("badge", "")
        desc = html.escape(box.get("desc", ""))

        span_style = f"grid-column: span {span};" if span > 1 else ""
        badge_html = f'<span style="display:inline-block;font-size:8px;padding:1px 5px;border-radius:3px;margin-left:6px;font-weight:700;letter-spacing:0.5px;background:{theme["border"]}33;color:{theme["text"]};border:1px solid {theme["border"]}">{html.escape(badge)}</span>' if badge else ""

        items_html = "".join(f"<li>{html.escape(i)}</li>" for i in items)
        desc_html = f'<div style="font-size:10px;color:#8b949e;line-height:1.6;margin-top:4px">{desc}</div>' if desc else ""
        file_html = f'<div style="font-size:9px;color:#6e7681;margin-top:6px;font-style:italic">{file_path}</div>' if file_path else ""

        return f'''<div style="border-radius:8px;padding:14px 16px;border:1px solid {theme["border"]};background:#0d1117;{span_style}">
          <div style="font-size:12px;font-weight:700;letter-spacing:0.5px;color:{theme["text"]};margin-bottom:6px">{title_text}{badge_html}</div>
          {desc_html}
          <ul style="list-style:none;margin-top:4px">{"".join(f'<li style="font-size:10px;color:#8b949e;line-height:1.7"><span style="color:#58a6ff">→ </span>{html.escape(i)}</li>' for i in items)}</ul>
          {file_html}
        </div>'''

    def render_arrows(arrows):
        if not arrows:
            return ""
        arrow_items = "".join(f'''<div style="display:flex;flex-direction:column;align-items:center;gap:2px">
          <div style="font-size:9px;color:#8b949e;letter-spacing:0.5px;text-align:center;max-width:90px">{html.escape(a.get("label",""))}</div>
          <div style="width:2px;height:28px;background:linear-gradient(to bottom,#30363d,#58a6ff)"></div>
          <div style="color:#58a6ff;font-size:14px">▼</div>
        </div>''' for a in arrows)
        return f'<div style="grid-column:1/-1;display:flex;justify-content:space-around;align-items:center;padding:0 40px">{arrow_items}</div>'

    layers_html = ""
    for layer in layers:
        label = html.escape(layer.get("label", ""))
        arrows = layer.get("arrows", [])
        boxes = layer.get("boxes", [])

        layers_html += f'<div style="grid-column:1/-1;font-size:10px;font-weight:700;letter-spacing:2px;color:#8b949e;text-transform:uppercase;padding:6px 0 2px;border-top:1px solid #21262d">{label}</div>'
        if arrows:
            layers_html += render_arrows(arrows)
        for box in boxes:
            layers_html += render_box(box)

    legend_html = "".join(f'<div style="display:flex;align-items:center;gap:6px;font-size:10px;color:#8b949e"><div style="width:10px;height:10px;border-radius:2px;border:1px solid {html.escape(item["color"])};background:{html.escape(item.get("bg","transparent"))}"></div>{html.escape(item.get("label",""))}</div>' for item in legend)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'SF Mono','Fira Code',monospace; background:#0d1117; color:#e6edf3; padding:32px; min-height:100vh; }}
</style>
</head>
<body>
<h1 style="text-align:center;font-size:22px;font-weight:700;letter-spacing:2px;color:#58a6ff;margin-bottom:4px">{title}</h1>
<div style="text-align:center;font-size:12px;color:#8b949e;margin-bottom:36px;letter-spacing:1px">{subtitle}</div>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;max-width:1100px;margin:0 auto">
  {layers_html}
  <div style="grid-column:1/-1;display:flex;gap:24px;padding:12px 0 0;border-top:1px solid #21262d;flex-wrap:wrap">
    {legend_html}
  </div>
</div>
</body>
</html>'''
