import html as _html
import json


def render_options(data: dict) -> str:
    title = data.get("title", "Choose an option")
    description = data.get("description", "")
    options = data.get("options", [])

    options_html = ""
    for i, opt in enumerate(options):
        icon_html = f'<span class="text-2xl mr-3">{opt["icon"]}</span>' if opt.get("icon") else ""
        desc_html = f'<p class="text-slate-400 text-sm mt-1">{opt["description"]}</p>' if opt.get("description") else ""
        # HTML-escape the JSON so it's safe inside a double-quoted attribute
        payload_json = json.dumps({"selected": opt["value"], "label": opt["label"]})
        payload_attr = _html.escape(payload_json, quote=True)
        options_html += f"""
        <button data-payload="{payload_attr}"
          class="w-full text-left bg-slate-800 hover:bg-slate-700 border border-slate-700
                 hover:border-blue-500 rounded-xl p-4 mb-3 transition-all duration-150 group">
          <div class="flex items-center">
            {icon_html}
            <div>
              <p class="text-slate-100 font-medium group-hover:text-blue-400 transition-colors">{opt["label"]}</p>
              {desc_html}
            </div>
          </div>
        </button>"""

    desc_block = f'<p class="text-slate-400 mt-2 mb-6">{description}</p>' if description else '<div class="mb-6"></div>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{title}</title>
<script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-slate-900 min-h-screen flex items-center justify-center p-6">
  <div class="w-full max-w-xl">
    <h1 class="text-slate-100 text-2xl font-semibold">{title}</h1>
    {desc_block}
    {options_html}
  </div>
  <script>
  document.querySelectorAll('[data-payload]').forEach(btn => {{
    btn.addEventListener('click', () => window.artifact.submit(JSON.parse(btn.dataset.payload)));
  }});
  </script>
</body>
</html>"""


def render_table(data: dict) -> str:
    title = data.get("title", "")
    columns = data.get("columns", [])
    rows = data.get("rows", [])
    sortable = data.get("sortable", True)

    headers_html = ""
    for i, col in enumerate(columns):
        if sortable:
            headers_html += f'<th onclick="sortTable({i})" class="cursor-pointer select-none px-4 py-3 text-left text-slate-300 text-sm font-medium hover:text-blue-400 transition-colors">{col} <span class="sort-indicator text-slate-500"></span></th>'
        else:
            headers_html += f'<th class="px-4 py-3 text-left text-slate-300 text-sm font-medium">{col}</th>'

    rows_html = ""
    for row in rows:
        cells = "".join(f'<td class="px-4 py-3 text-slate-300 text-sm border-t border-slate-700">{cell}</td>' for cell in row)
        rows_html += f'<tr class="hover:bg-slate-700 transition-colors">{cells}</tr>'

    title_block = f'<h1 class="text-slate-100 text-xl font-semibold mb-4">{title}</h1>' if title else ""
    sort_script = """<script>
    let sortDir = {};
    function sortTable(col) {
      const tbody = document.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr'));
      sortDir[col] = !sortDir[col];
      rows.sort((a, b) => {
        const av = a.cells[col].textContent.trim();
        const bv = b.cells[col].textContent.trim();
        const an = parseFloat(av.replace(/[^0-9.-]/g,'')), bn = parseFloat(bv.replace(/[^0-9.-]/g,''));
        const cmp = (!isNaN(an) && !isNaN(bn)) ? (an - bn) : av.localeCompare(bv);
        return sortDir[col] ? cmp : -cmp;
      });
      rows.forEach(r => tbody.appendChild(r));
      document.querySelectorAll('.sort-indicator').forEach((el, i) => {
        el.textContent = i === col ? (sortDir[col] ? ' ↑' : ' ↓') : '';
      });
    }
    </script>""" if sortable else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{title or 'Table'}</title>
<script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-slate-900 min-h-screen p-6">
  <div class="max-w-5xl mx-auto">
    {title_block}
    <div class="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
      <table class="w-full">
        <thead class="bg-slate-900"><tr>{headers_html}</tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
  </div>
  {sort_script}
</body>
</html>"""


def render_markdown(data: dict) -> str:
    content = data.get("content", "")
    theme = data.get("theme", "dark")
    bg = "bg-slate-900" if theme == "dark" else "bg-white"
    text = "text-slate-200" if theme == "dark" else "text-slate-800"
    prose_invert = "prose-invert" if theme == "dark" else ""
    content_json = json.dumps(content)

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Document</title>
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body class="{bg} min-h-screen p-8">
  <div class="max-w-3xl mx-auto {text}">
    <article id="content" class="prose {prose_invert} max-w-none"></article>
  </div>
  <script>
    const raw = {content_json};
    document.getElementById('content').innerHTML = marked.parse(raw);
    document.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
  </script>
</body>
</html>"""


def render_form(data: dict) -> str:
    title = data.get("title", "")
    description = data.get("description", "")
    fields = data.get("fields", [])
    submit_label = data.get("submit_label", "Submit")

    input_class = "w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-slate-100 text-sm focus:outline-none focus:border-blue-500 transition-colors"

    fields_html = ""
    for field in fields:
        name = field["name"]
        label = field["label"]
        ftype = field.get("type", "text")
        placeholder = field.get("placeholder", "")
        required = field.get("required", False)
        default = field.get("default", "")
        req_attr = "required" if required else ""
        req_star = '<span class="text-red-400 ml-1">*</span>' if required else ""

        label_html = f'<label for="{name}" class="block text-sm text-slate-300 mb-1">{label}{req_star}</label>'

        if ftype == "textarea":
            input_html = f'<textarea id="{name}" name="{name}" placeholder="{placeholder}" {req_attr} class="{input_class} h-24 resize-y">{default}</textarea>'
        elif ftype == "select":
            opts = "".join(
                f'<option value="{o}"{"selected" if o == default else ""}>{o}</option>'
                for o in field.get("options", [])
            )
            input_html = f'<select id="{name}" name="{name}" {req_attr} class="{input_class}">{opts}</select>'
        elif ftype == "checkbox":
            checked = "checked" if default else ""
            input_html = f'<input type="checkbox" id="{name}" name="{name}" {checked} class="w-4 h-4 accent-blue-500">'
        else:
            input_html = f'<input type="{ftype}" id="{name}" name="{name}" placeholder="{placeholder}" value="{default}" {req_attr} class="{input_class}">'

        fields_html += f'<div class="mb-4">{label_html}{input_html}</div>'

    title_block = f'<h1 class="text-slate-100 text-xl font-semibold mb-2">{title}</h1>' if title else ""
    desc_block = f'<p class="text-slate-400 text-sm mb-6">{description}</p>' if description else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{title or 'Form'}</title>
<script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-slate-900 min-h-screen flex items-center justify-center p-6">
  <div class="w-full max-w-lg bg-slate-800 border border-slate-700 rounded-2xl p-6">
    {title_block}
    {desc_block}
    <form id="f" onsubmit="handleSubmit(event)">
      {fields_html}
      <button type="submit"
        class="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2 px-4 rounded-lg transition-colors mt-2">
        {submit_label}
      </button>
    </form>
  </div>
  <script>
  function handleSubmit(e) {{
    e.preventDefault();
    const form = document.getElementById('f');
    const data = {{}};
    form.querySelectorAll('input, select, textarea').forEach(el => {{
      if (el.name) data[el.name] = el.type === 'checkbox' ? el.checked : el.value;
    }});
    window.artifact.submit(data);
  }}
  </script>
</body>
</html>"""


def render_chart(data: dict) -> str:
    chart_type = data.get("type", "bar")
    title = data.get("title", "")
    labels = data.get("labels", [])
    datasets = data.get("datasets", [])
    y_label = data.get("y_label", "")

    colors = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#06b6d4"]
    bg_colors = ["#3b82f680", "#8b5cf680", "#10b98180", "#f59e0b80", "#ef444480", "#06b6d480"]

    ds_list = []
    for i, ds in enumerate(datasets):
        c = colors[i % len(colors)]
        bg = bg_colors[i % len(bg_colors)]
        border_color = c
        bg_color = bg if chart_type != "line" else c
        fill = "false" if chart_type == "line" else "true"
        ds_list.append(
            f'{{"label":{json.dumps(ds["label"])},"data":{json.dumps(ds["data"])},'
            f'"backgroundColor":"{bg_color}","borderColor":"{border_color}","borderWidth":2,"fill":{fill}}}'
        )

    is_pie = chart_type == "pie"
    scales_config = "{}" if is_pie else f"""{{
          x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }},
          y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }},
               title: {{ display: {'true' if y_label else 'false'}, text: {json.dumps(y_label)}, color: '#94a3b8' }} }}
        }}"""

    chart_config = f"""{{
      type: '{chart_type}',
      data: {{
        labels: {json.dumps(labels)},
        datasets: [{", ".join(ds_list)}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ labels: {{ color: '#94a3b8' }} }},
          title: {{ display: {'true' if title else 'false'}, text: {json.dumps(title)}, color: '#e2e8f0', font: {{ size: 16 }} }}
        }},
        scales: {scales_config}
      }}
    }}"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{title or 'Chart'}</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
</head>
<body class="bg-slate-900 min-h-screen flex items-center justify-center p-6">
  <div class="w-full max-w-3xl" style="height: 480px;">
    <canvas id="chart"></canvas>
  </div>
  <script>
  new Chart(document.getElementById('chart'), {chart_config});
  </script>
</body>
</html>"""
