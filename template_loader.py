import asyncio
import importlib.util
import json
from pathlib import Path
from typing import Callable

PROJECT_DIR = Path(__file__).parent
LEARNED_DIR = PROJECT_DIR / "learned_templates"
REGISTRY_PATH = LEARNED_DIR / "registry.json"

BUILTIN_NAMES = {"compose", "system_spec"}

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
        "Render an artifact in a browser tab using the Acme design system "
        "(ivory/slate/clay palette, serif headings, no Tailwind).\n\n"

        "── WORKFLOW ──────────────────────────────────────────────────────────────\n"
        "1. Call get_example(name) to find the closest example → inspect + adapt it.\n"
        "2. Call render_artifact(template='compose', data={...}) with your payload.\n"
        "3. For interactive JS inside a compose page: use {html: '<div>...</div><script>...</script>'} items.\n"
        "4. Raw html field: ONLY for a genuinely novel atom (new visual component that doesn't\n"
        "   exist in the primitive/organism vocabulary). Never for full page layouts.\n\n"

        "── ORGANISMS — prefer these, they handle the heavy lifting ───────────────\n"
        "  event_timeline   {entries: [{time, body, state: neutral|impact|mitigated|success|warning|error}]}\n"
        "  milestone_timeline {milestones: [{date, title, description?, tags?, done?}]}\n"
        "  bar_chart        {bars: [{label, value, highlight?}], y_max?, caption?}\n"
        "  file_section     {path, additions, deletions, risk: safe|medium|high, hunks, comments}\n"
        "  shipped_item_list {items: [{title, description, reference, color?}]}\n"
        "  callout          {content, variant: dark|tinted, label?}\n"
        "  action_checklist {items: [{avatar, description, due?, done?}]}\n"
        "  decision_card    {question, context, options: [{label, suggested?}]}\n"
        "  code_block       {filename?, language?, code} or {tabs: [{label, code, active?}]}\n"
        "  drag_list        {title?, items: [{label, count?}]}  // native drag-to-reorder\n"
        "  step_list        {steps: [{title, body?, code?}]}\n"
        "  two_col_compare  {cols: [{header, items:[...]}, {header, items:[...]}]}  // recursive\n"
        "  flow_diagram     {nodes:[{id,label,sublabel?,accent?:clay|olive|rust|gray,primitive?,width?,height?}],\n"
        "                    edges:[{from,to,label?,style?:solid|dashed}],\n"
        "                    direction?:TB|LR, node_width?,node_height?,h_gap?,v_gap?,caption?}\n\n"

        "── PRIMITIVES — lower-level building blocks ──────────────────────────────\n"
        "  Layouts (recursive):  v_stack {items,gap?} · grid {items,cols:2|3|4,gap?} · sidebar_layout {main:[],sidebar:[]}\n"
        "  Content:   page_header {title,eyebrow?,description?,pill?} · section_header {title} · divider\n"
        "             prose {text?,items?} · bullet_list {items:[str|{strong,text}]}\n"
        "             badge {text,tone:neutral|accent|success|warning|danger|outlined}\n"
        "             avatar {initials,color?:o2|o3|o4,bordered?} · button {text,variant:primary|secondary|ghost|danger}\n"
        "             chip {text,tone?:olive|clay|rust}\n"
        "  Data:      stat_card {number,label,delta?,delta_direction?:up|flat|down,warning?}\n"
        "             card {variant:flat|outlined|elevated|stripe|inset|horizontal,title?,subtitle?,\n"
        "                   tags?,initials?,actions?:[{text,variant}],content?:html_str}\n"
        "             table {columns:[str],rows:[[cell,...]]}  cell: str or {type:link|risk|badge|mono,...}\n"
        "             inset_panel {items:[{tag,text,note?}]}\n"
        "  Code review: diff_block {hunks:[{type:ctx|add|del|hunk,line?,code}]}\n"
        "               comment_thread {comments:[{severity:blocking|nit|suggest,anchor?,text}]}\n"
        "  Kanban:    kanban_board {columns:[{title,accent?:clay|olive|gray|light,id?,tickets:[...]}]}\n"
        "             ticket {id,title,tag?:bug|feat|chore|debt,estimate?:S|M|L,owner_initials?,owner_class?}\n"
        "  Escape:    {html:'<div>...</div><script>...</script>'}  // inline any HTML+JS fragment\n\n"

        "── COMPOSE DATA SCHEMA ───────────────────────────────────────────────────\n"
        "  {title, wide?:bool, header?:{eyebrow?,title,description?,pill?},\n"
        "   sections:[{header?:str, layout:'stack'|'grid'|'sidebar'|'kanban',\n"
        "              cols?:2|3|4, gap?:int,\n"
        "              items?:[<item>],          // stack|grid|kanban\n"
        "              main?:[<item>], sidebar?:[<item>]}]}  // sidebar layout\n"
        "  Every <item> must be {primitive:'<name>', ...fields} or a layout wrapper or {html:'...'}.\n"
        "  A bare organism payload is NOT valid top-level data — always wrap in sections[].items[].\n\n"

        "── SYSTEM SPEC (template='system_spec') ──────────────────────────────────\n"
        "  Use for standalone codebase/architecture explainers. The LLM describes what exists;\n"
        "  the renderer handles all layout, colors, and interactivity automatically.\n"
        "  Call get_example('sys_microservices') or get_example('sys_event_driven') to see full examples.\n\n"
        "  node kinds:  service | module | class | db | queue | external | package | file | function\n"
        "  edge kinds:  calls | imports | depends | emits | subscribes | reads | writes | deploys | owns\n"
        "  group kinds: layer | package | team | domain | deployment\n\n"
        "  Schema:\n"
        "  {title, description?,\n"
        "   nodes: [{id, label, kind?, description?, tech?, tags?:[], status?, owner?}],\n"
        "   edges: [{from, to, kind?, label?, async?:bool, protocol?}],\n"
        "   groups?: [{id, label, kind?, members:[node_id,...]}],\n"
        "   sequences?: [{id, label, steps:[{from, to, label?}]}]}\n\n"
    )

    meta = get_learned_meta()
    if meta:
        base += "── LEARNED TEMPLATES ─────────────────────────────────────────────────────\n"
        for entry in meta.values():
            base += (
                f"  {entry['name']}  — {entry['description']}\n"
                f"    schema: {json.dumps(entry['schema_example'])}\n"
            )
        base += "\n"

    base += (
        "── RAW HTML ──────────────────────────────────────────────────────────────\n"
        "Use html field only for a novel low-level component (a new atom not in the vocabulary above).\n"
        "Never for whole page layouts — use compose + {html:...} items instead.\n"
        "window.artifact.submit(payload) is injected automatically.\n\n"
        "mode: 'immediate' returns at once. 'interactive' blocks until window.artifact.submit(payload) is called.\n"
        "Prefer render_artifact(mode='interactive') over AskUserQuestion for decisions."
    )
    return base


def build_template_schema_property() -> dict:
    learned_names = list(_learned_renderers.keys())
    learned_str = (", ".join(learned_names) + " (learned)") if learned_names else "none yet"
    return {
        "type": "string",
        "description": (
            f"Template name. Built-in: compose, system_spec. "
            f"Learned: {learned_str}. "
            "Use the 'data' field with this."
        ),
    }
