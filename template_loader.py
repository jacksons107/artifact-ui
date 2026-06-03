import asyncio
import importlib.util
import json
from pathlib import Path
from typing import Callable

PROJECT_DIR = Path(__file__).parent
LEARNED_DIR = PROJECT_DIR / "learned_templates"
REGISTRY_PATH = LEARNED_DIR / "registry.json"

BUILTIN_NAMES = {"options", "table", "markdown", "form", "chart", "compose"}

_learned_renderers: dict[str, Callable] = {}
_registry_meta: dict[str, dict] = {}
_registry_lock: asyncio.Lock | None = None


def get_registry_lock() -> asyncio.Lock:
    global _registry_lock
    if _registry_lock is None:
        _registry_lock = asyncio.Lock()
    return _registry_lock


def _import_template_module(path: Path, name: str) -> Callable:
    spec = importlib.util.spec_from_file_location(f"learned_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, f"render_{name}")


def load_learned_templates() -> None:
    global _learned_renderers, _registry_meta
    if not REGISTRY_PATH.exists():
        return
    try:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return
    renderers: dict[str, Callable] = {}
    meta: dict[str, dict] = {}
    for name, entry in registry.get("templates", {}).items():
        module_path = PROJECT_DIR / entry.get("module", f"learned_templates/{name}.py")
        if not module_path.exists():
            continue
        try:
            renderers[name] = _import_template_module(module_path, name)
            meta[name] = entry
        except Exception:
            pass
    _learned_renderers = renderers
    _registry_meta = meta


def reload_learned_templates() -> None:
    load_learned_templates()


def get_all_renderers() -> dict[str, Callable]:
    return dict(_learned_renderers)


def get_learned_meta() -> dict[str, dict]:
    return dict(_registry_meta)


def build_tool_description() -> str:
    base = (
        "Render an artifact in a browser tab.\n\n"
        "PREFER templates over raw html — they require ~200 tokens of JSON vs 5000 tokens of HTML.\n\n"
        "BUILT-IN TEMPLATES (use template + data):\n"
        "• options  — interactive list of choices; user clicks one, returns {selected, label}\n"
        "  data: {title, description?, options: [{value, label, description?, icon?}]}\n"
        "• table    — sortable data table (immediate)\n"
        "  data: {title?, columns: [...], rows: [[...], ...], sortable?}\n"
        "• markdown — rendered markdown with code highlighting (immediate)\n"
        "  data: {content: '# md string', theme?: 'dark'|'light'}\n"
        "• form     — labeled inputs with submit button (interactive); returns {field_name: value, ...}\n"
        "  data: {title?, description?, fields: [{name, label, type, placeholder?, options?, required?, default?}], submit_label?}\n"
        "  field types: text | textarea | select | checkbox | number | email | password\n"
        "• chart    — bar/line/pie chart via Chart.js (immediate)\n"
        "  data: {type: 'bar'|'line'|'pie', title?, labels: [...], datasets: [{label, data: [...]}], y_label?}\n"
        "• compose  — combine multiple templates into one page (best with immediate-mode sub-templates)\n"
        "  data: {title?, layout: 'stack'|'grid', items: [{template, data}]}\n\n"
    )

    meta = get_learned_meta()
    if meta:
        base += "LEARNED TEMPLATES (extracted from past raw HTML calls — use these before writing raw HTML):\n"
        for entry in meta.values():
            base += (
                f"• {entry['name']}  — {entry['description']}\n"
                f"  schema_example: {json.dumps(entry['schema_example'])}\n"
            )
        base += "\n"

    base += (
        "RAW HTML (use html field): Only when no template fits. "
        "window.artifact.submit(payload) is injected automatically. "
        "Raw HTML calls trigger background extraction to learn a new template.\n\n"
        "mode: 'immediate' returns at once. 'interactive' blocks until window.artifact.submit(payload) is called in browser.\n"
        "Prefer render_artifact(mode='interactive') over AskUserQuestion for decisions."
    )
    return base


def build_template_schema_property() -> dict:
    learned_names = list(_learned_renderers.keys())
    learned_str = (", ".join(learned_names) + " (learned)") if learned_names else "none yet"
    return {
        "type": "string",
        "description": (
            f"Template name. Built-ins: options, table, markdown, form, chart, compose. "
            f"Learned: {learned_str}. "
            "Use the 'data' field with this."
        ),
    }
