import html as _html

# ── Visual vocabulary ─────────────────────────────────────────────────────────

NODE_KIND_STYLES = {
    "service":  {"stroke": "#D97757", "fill": "rgba(217,119,87,0.07)",  "icon": "◈"},
    "db":       {"stroke": "#788C5D", "fill": "rgba(120,140,93,0.07)",  "icon": "⬡"},
    "queue":    {"stroke": "#B04A3F", "fill": "rgba(176,74,63,0.07)",   "icon": "≋"},
    "external": {"stroke": "#87867F", "fill": "rgba(135,134,127,0.07)", "icon": "◇"},
    "module":   {"stroke": "#87867F", "fill": "rgba(135,134,127,0.05)", "icon": "□"},
    "class":    {"stroke": "#D1CFC5", "fill": "#FFFFFF",                "icon": "⟨⟩"},
    "function": {"stroke": "#D1CFC5", "fill": "#FFFFFF",                "icon": "ƒ"},
    "package":  {"stroke": "#87867F", "fill": "rgba(135,134,127,0.05)", "icon": "⊡"},
    "file":     {"stroke": "#D1CFC5", "fill": "#FFFFFF",                "icon": "≡"},
}

_DEFAULT_NODE_STYLE = {"stroke": "#D1CFC5", "fill": "#FFFFFF", "icon": "○"}

EDGE_KIND_STYLES = {
    "calls":        {"color": "#D97757", "dashed": False},
    "imports":      {"color": "#87867F", "dashed": False},
    "depends":      {"color": "#87867F", "dashed": True},
    "emits":        {"color": "#788C5D", "dashed": True},
    "subscribes":   {"color": "#788C5D", "dashed": True},
    "reads":        {"color": "#788C5D", "dashed": False},
    "writes":       {"color": "#B04A3F", "dashed": False},
    "deploys":      {"color": "#87867F", "dashed": True},
    "owns":         {"color": "#D1CFC5", "dashed": False},
    "returns":      {"color": "#87867F", "dashed": False},
    "throws":       {"color": "#B04A3F", "dashed": True},
    "overrides":    {"color": "#D1CFC5", "dashed": False},
    "implements":   {"color": "#D1CFC5", "dashed": True},
    "instantiates": {"color": "#D97757", "dashed": False},
}

_DEFAULT_EDGE_STYLE = {"color": "#C8C5BC", "dashed": False}

CHANGE_STATUS_STYLES = {
    "added":    {"stroke": "#4A7C59", "fill": "rgba(74,124,89,0.10)"},
    "modified": {"stroke": "#B8860B", "fill": "rgba(184,134,11,0.10)"},
    "deleted":  {"stroke": "#B04A3F", "fill": "rgba(176,74,63,0.10)"},
}

_CHANGE_STATUS_COLORS = {"added": "#4A7C59", "modified": "#B8860B", "deleted": "#B04A3F"}

_TECH_LANG_MAP = [
    ("python", "python"), ("go", "go"), ("typescript", "typescript"),
    ("javascript", "javascript"), ("ruby", "ruby"), ("java", "java"),
    ("rust", "rust"), ("c++", "cpp"), ("c#", "csharp"), ("kotlin", "kotlin"),
    ("swift", "swift"), ("php", "php"), ("bash", "bash"), ("shell", "bash"),
    ("sql", "sql"),
]

def _infer_lang(node: dict) -> str:
    tech = node.get("tech", "").lower()
    for key, val in _TECH_LANG_MAP:
        if key in tech:
            return val
    return "plaintext"

GROUP_KIND_STYLES = {
    "layer":      {"stroke": "#D1CFC5", "fill": "rgba(209,207,197,0.08)"},
    "package":    {"stroke": "#D97757", "fill": "rgba(217,119,87,0.04)"},
    "team":       {"stroke": "#788C5D", "fill": "rgba(120,140,93,0.04)"},
    "domain":     {"stroke": "#87867F", "fill": "rgba(135,134,127,0.06)"},
    "deployment": {"stroke": "#B04A3F", "fill": "rgba(176,74,63,0.04)"},
}

_DEFAULT_GROUP_STYLE = {"stroke": "#D1CFC5", "fill": "rgba(209,207,197,0.06)"}

# Layout constants
NODE_W = 180
NODE_H = 60
H_GAP  = 56
V_GAP  = 72
PAD    = 56


def _e(s) -> str:
    return _html.escape(str(s))
