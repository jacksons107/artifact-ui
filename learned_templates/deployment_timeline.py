import html as _html

def render_deployment_timeline(data: dict) -> str:
    title = _html.escape(data.get("title", "Deployment Timeline"))
    events = data.get("events", [])

    STATUS_COLORS = {
        "success":     ("emerald", "emerald"),
        "in progress": ("blue",    "blue"),
        "queued":      ("amber",   "amber"),
        "failed":      ("red",     "red"),
        "pending":     ("slate",   "slate"),
    }

    def status_classes(status):
        key = status.lower()
        color = STATUS_COLORS.get(key, ("slate", "slate"))[0]
        return (
            f"bg-{color}-500/20 border-{color}-500",
            f"bg-{color}-400",
            f"bg-{color}-500/10 text-{color}-400 border border-{color}-500/20",
        )

    rows = []
    for ev in events:
        label   = _html.escape(str(ev.get("title", "")))
        ts      = _html.escape(str(ev.get("timestamp", "")))
        desc    = _html.escape(str(ev.get("description", "")))
        status  = ev.get("status", "pending")
        s_label = _html.escape(status)
        dot_ring, dot_fill, badge = status_classes(status)
        rows.append(f"""
      <div class="relative flex gap-4">
        <div class="w-8 h-8 rounded-full {dot_ring} flex items-center justify-center flex-shrink-0 z-10">
          <div class="w-2 h-2 rounded-full {dot_fill}"></div>
        </div>
        <div class="flex-1 bg-slate-800 border border-slate-700 rounded-xl p-4 min-w-0">
          <div class="flex items-center justify-between gap-2 mb-1">
            <span class="text-slate-100 font-medium text-sm">{label}</span>
            <span class="text-slate-500 text-xs whitespace-nowrap">{ts}</span>
          </div>
          <p class="text-slate-400 text-sm">{desc}</p>
          <span class="inline-block mt-2 px-2 py-0.5 rounded-full text-xs font-medium {badge}">{s_label}</span>
        </div>
      </div>""")

    rows_html = "\n".join(rows)
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{title}</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 min-h-screen p-8">
<div class="max-w-2xl mx-auto">
  <h1 class="text-slate-100 text-2xl font-semibold mb-8">{title}</h1>
  <div class="relative">
    <div class="absolute left-4 top-0 bottom-0 w-px bg-slate-700"></div>
    <div class="space-y-6">
{rows_html}
    </div>
  </div>
</div>
</body>
</html>"""
