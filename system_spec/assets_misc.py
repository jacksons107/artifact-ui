# ── Small, standalone CSS/JS support for other render modules ─────────────
# Layer diagram (layer_diagram.py), dependency matrix (matrix.py), code
# snippets in detail panels (detail_panels.py), the Changes tab
# (changes.py), and the Code Detail tab's own module dropdown
# (code_detail.py) — none of these need much (or any) JS of their own, so
# they're grouped together rather than each getting a near-empty file.

CSS = """
/* ── Layer diagram view ───────────────────────── */
.sys-layer-wrap { background: var(--white); border: var(--border); border-radius: 12px; padding: 20px; overflow-x: auto; }

/* ── Code detail view ──────────────────────────── */
.sys-cd-wrap { display: flex; flex-direction: column; gap: 14px; }
.sys-cd-controls { display: flex; align-items: center; gap: 10px; }
.sys-cd-sel { font-family: var(--mono); font-size: 12px; border: var(--border); border-radius: 6px;
              padding: 5px 12px; background: var(--white); color: var(--slate); cursor: pointer;
              appearance: none; -webkit-appearance: none; }
.sys-cd-panel { display: flex; flex-direction: column; gap: 12px; }

/* ── Dependency matrix ────────────────────────── */
.sys-matrix-wrap { overflow-x: auto; background: var(--white); border: var(--border); border-radius: 12px; }
.sys-mtx { border-collapse: collapse; font-size: 12px; white-space: nowrap; }
.sys-mh0 { min-width: 160px; }
.sys-mth { padding: 0; vertical-align: bottom; border-left: 1px solid var(--gray-100); }
.sys-mth-inner { writing-mode: vertical-rl; transform: rotate(180deg); padding: 12px 8px 8px;
                  font-family: var(--mono); font-size: 11px; display: flex; align-items: center;
                  gap: 4px; color: var(--gray-700); }
.sys-mrh { padding: 8px 14px; font-family: var(--mono); font-size: 12px; white-space: nowrap;
           border-right: 1.5px solid var(--gray-300); color: var(--gray-700); border-bottom: 1px solid var(--gray-100); }
.sys-mc  { padding: 7px 10px; text-align: center; border-left: 1px solid var(--gray-100);
           border-bottom: 1px solid var(--gray-100); font-family: var(--mono); font-size: 10px; min-width: 64px; }
.sys-mc-hit { font-weight: 500; }
.sys-mtx thead tr { border-bottom: 1.5px solid var(--gray-300); }
.sys-mtx thead th { border-bottom: 1.5px solid var(--gray-300); }

/* ── Code snippet in detail panel ─────────────── */
.sys-sig { margin: 10px 0 6px; padding: 6px 10px; background: var(--gray-100); border-left: 3px solid var(--clay); border-radius: 0 4px 4px 0; }
.sys-sig code { font-family: var(--mono); font-size: 12px; color: var(--slate); }
.sys-snippet { margin: 6px 0 0; }
.sys-snippet pre { margin: 0; padding: 10px 12px; background: var(--ivory); border: var(--border); border-radius: 8px; overflow-x: auto; max-height: 320px; font-size: 0.78rem; line-height: 1.5; }
.sys-snippet pre code { font-family: var(--mono); }

/* ── Changes tab ──────────────────────────────── */
.sys-changes { display: flex; flex-direction: column; gap: 24px; }
.sys-chg-section { background: var(--white); border: var(--border); border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.sys-chg-header { font-family: var(--mono); font-size: 12px; font-weight: 600; padding: 4px 0 4px 10px; border-left: 3px solid; letter-spacing: 0.04em; text-transform: uppercase; }
.sys-chg-node { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.sys-chg-label { font-family: var(--serif); font-size: 14px; }
.sys-chg-fp { font-family: var(--mono); font-size: 11px; color: var(--gray-500); }
.sys-chg-pre { margin: 4px 0 0; padding: 10px 12px; background: var(--ivory); border: var(--border); border-radius: 8px; overflow-x: auto; max-height: 360px; font-size: 0.78rem; line-height: 1.5; }
.sys-chg-pre code { font-family: var(--mono); }
.sys-chg-diff { display: flex; gap: 12px; flex-wrap: wrap; }
.sys-chg-side { flex: 1 1 340px; display: flex; flex-direction: column; gap: 4px; }
.sys-chg-side-label { font-family: var(--mono); font-size: 10px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; }
"""

JS = """
/* ── Code detail selector ──────────────────────── */
function sysCodeDetailChange(sel) {
    var val = sel.value;
    document.querySelectorAll('.sys-cd-panel').forEach(function(p) {
        p.style.display = (p.id === 'cdp-' + val) ? '' : 'none';
    });
}
"""
