# ── Page assembly: embedded CSS / JS ──────────────────────────────────────────
# Thin assembler — the real CSS/JS content lives in feature-scoped sibling
# modules (assets_common.py, assets_sequences.py, assets_filters.py,
# assets_misc.py), each co-locating one feature's CSS with its own JS.
# Concatenated here, in the same order they used to appear in this file, so
# render.py's `from .assets import _CSS, _JS` needs no changes.

from .assets_common import CSS as _CSS_COMMON, JS as _JS_COMMON
from .assets_sequences import CSS as _CSS_SEQ, JS as _JS_SEQ
from .assets_filters import CSS as _CSS_FILTERS, JS as _JS_FILTERS
from .assets_misc import CSS as _CSS_MISC, JS as _JS_MISC

_CSS = _CSS_COMMON + _CSS_SEQ + _CSS_FILTERS + _CSS_MISC
_JS = _JS_COMMON + _JS_SEQ + _JS_FILTERS + _JS_MISC
