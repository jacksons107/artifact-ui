def render_stat_cards(data: dict) -> str:
    title = data.get("title", "")
    cards = data.get("cards", [])
    cols = data.get("columns", 4)

    col_map = {1: "grid-cols-1", 2: "grid-cols-2", 3: "grid-cols-3", 4: "grid-cols-2 sm:grid-cols-4"}
    col_class = col_map.get(cols, "grid-cols-2 sm:grid-cols-4")

    title_html = f'<h1 class="text-slate-100 text-2xl font-semibold mb-6">{title}</h1>' if title else ""

    cards_html = ""
    for card in cards:
        label = card.get("label", "")
        value = card.get("value", "")
        delta = card.get("delta", "")
        positive = card.get("delta_positive", True)
        delta_color = "text-emerald-400" if positive else "text-red-400"
        delta_html = f'<p class="{delta_color} text-sm mt-2">{delta}</p>' if delta else ""
        cards_html += f"""<div class="bg-slate-800 border border-slate-700 rounded-xl p-5">
        <p class="text-slate-400 text-xs font-medium uppercase tracking-wide mb-1">{label}</p>
        <p class="text-slate-100 text-3xl font-bold">{value}</p>
        {delta_html}
      </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{title or 'Metrics'}</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 min-h-screen flex items-center justify-center p-8">
  <div class="w-full max-w-4xl">
    {title_html}
    <div class="grid {col_class} gap-4">
      {cards_html}
    </div>
  </div>
</body>
</html>"""
