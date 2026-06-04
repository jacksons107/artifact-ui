import ast
import asyncio
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import template_loader
from template_loader import BUILTIN_NAMES, LEARNED_DIR, PROJECT_DIR, REGISTRY_PATH


def _ensure_learned_dir() -> None:
    LEARNED_DIR.mkdir(exist_ok=True)
    if not REGISTRY_PATH.exists():
        REGISTRY_PATH.write_text(
            json.dumps({"version": 1, "templates": {}}, indent=2),
            encoding="utf-8",
        )


def _validate_template_code(name: str, code: str) -> tuple[bool, str]:
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"
    namespace: dict = {}
    try:
        exec(compile(code, f"<{name}>", "exec"), namespace)
    except Exception as e:
        return False, f"exec failed: {e}"
    fn_name = f"render_{name}"
    if fn_name not in namespace:
        return False, f"Function {fn_name!r} not found in generated code"
    try:
        result = namespace[fn_name]({})
    except Exception as e:
        return False, f"smoke-test call failed: {e}"
    if not isinstance(result, str) or "</body>" not in result:
        return False, "result is not a string or missing </body>"
    return True, ""


def save_template(
    name: str,
    description: str,
    schema_example: dict,
    code: str,
    reasoning: str = "",
) -> tuple[bool, str]:
    name = name.strip().lower().replace("-", "_").replace(" ", "_")

    if name in BUILTIN_NAMES:
        return False, f"{name!r} conflicts with a built-in template name"

    valid, reason = _validate_template_code(name, code)
    if not valid:
        return False, reason

    _ensure_learned_dir()
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    if name in registry["templates"]:
        return False, f"Template {name!r} already exists"

    module_path = LEARNED_DIR / f"{name}.py"
    module_path.write_text(code, encoding="utf-8")

    registry["templates"][name] = {
        "name": name,
        "description": description,
        "schema_example": schema_example,
        "reasoning": reasoning,
        "module": f"learned_templates/{name}.py",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    tmp = REGISTRY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    tmp.rename(REGISTRY_PATH)

    template_loader.reload_learned_templates()
    return True, ""


def _build_extraction_prompt(html: str, reserved_names: list[str]) -> str:
    reserved = ", ".join(reserved_names) if reserved_names else "none"
    return f"""You are extracting a reusable UI template from HTML. Complete this task autonomously — do not ask questions.

TASK: Analyze the HTML, identify the repeating UI pattern, write a parameterized Python render function, validate it, then save it.

RESERVED NAMES (do not use): {reserved}

RULES for the Python render function:
- Signature exactly: def render_{{name}}(data: dict) -> str:
- Returns a complete HTML document (DOCTYPE through </html>)
- Use the project design system: from design_system import page_wrapper, BASE_CSS
- Ivory/slate/clay color palette (no Tailwind); all tokens and component CSS are in design_system.BASE_CSS
- You may also call functions from primitives.py (e.g. from primitives import stat_card, table)
- Must contain </body> tag (required by the server)
- Escape all literal JS/CSS braces as {{{{ and }}}}
- Use data.get() with sensible defaults — never assume a key exists
- Only stdlib imports (json, html) plus design_system and primitives from this project
- Keep the function under 80 lines

STEPS — do all of these in order:
1. Choose a short snake_case name for the pattern (2-4 words, e.g. "stat_cards", "timeline_feed")
2. Write the Python function to: {LEARNED_DIR}/{{name}}.py
3. Validate it runs correctly:
   Run: python3 -c "exec(open('{LEARNED_DIR}/{{name}}.py').read()); print(list(globals().keys()))"
   If it errors, fix {LEARNED_DIR}/{{name}}.py and re-validate before continuing.
4. Read the current registry at: {REGISTRY_PATH}
5. Add your entry to the "templates" object and write the full updated JSON back to: {REGISTRY_PATH}

REGISTRY ENTRY to add (replace {{name}} and fill in real values):
{{
  "name": "{{name}}",
  "description": "One sentence describing what this UI pattern is and when to use it.",
  "schema_example": {{...minimal realistic example of the data dict...}},
  "reasoning": "1-2 sentences: why this pattern warrants a reusable template rather than being one-off.",
  "module": "learned_templates/{{name}}.py",
  "created_at": "{{current ISO timestamp}}"
}}

HTML TO ANALYZE:
{html[:6000]}
"""


async def _wait_and_reload(process: asyncio.subprocess.Process) -> None:
    try:
        await asyncio.wait_for(process.wait(), timeout=120)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass
    template_loader.reload_learned_templates()


async def spawn_extractor_agent(html: str) -> None:
    claude_path = shutil.which("claude")
    if not claude_path:
        return
    try:
        _ensure_learned_dir()
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        reserved = list(registry.get("templates", {}).keys()) + list(BUILTIN_NAMES)
        prompt = _build_extraction_prompt(html, reserved)

        process = await asyncio.create_subprocess_exec(
            claude_path,
            "-p", prompt,
            "--allowedTools", "Bash,Read,Write",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        asyncio.create_task(_wait_and_reload(process))
    except Exception:
        pass
