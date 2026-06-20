# ── Foundational CSS/JS used by virtually every view ──────────────────────
# Tab bar, the architecture layout shell, the shared filter-chip base look
# (reused by both the architecture filters and the component-list filters),
# detail panel/node interaction/hint/legend/description styling, the
# expand-collapse glyphs drawn by arch_engine.js — plus tab switching, node
# click → detail panel, jump-to-node-from-link, and the sequence-step
# example/before-after panel toggle (shared by the Architecture and
# Sequences tabs' detail panels).

CSS = """
/* ── Tabs ─────────────────────────────────────── */
.sys-tabs { display: flex; gap: 0; border-bottom: 1.5px solid var(--gray-300); margin-bottom: 20px; }
.sys-tab { font-family: var(--mono); font-size: 12px; background: none; border: none;
           padding: 7px 16px; cursor: pointer; color: var(--gray-500);
           border-bottom: 2px solid transparent; margin-bottom: -1.5px; transition: color 0.1s; }
.sys-tab:hover { color: var(--slate); }
.sys-tab.active { color: var(--slate); border-bottom-color: var(--clay); font-weight: 500; }

/* ── Architecture view ────────────────────────── */
.sys-wrap { display: flex; gap: 20px; align-items: flex-start; }
.sys-main { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; gap: 12px; }
.sys-diagram { background: var(--white); border: var(--border); border-radius: 12px; padding: 20px; overflow-x: auto; }
.sys-sidebar { flex: 0 0 260px; display: flex; flex-direction: column; gap: 12px; }

/* ── Filter chips (shared) ────────────────────── */
.sys-fl { font-family: var(--mono); font-size: 10px; color: var(--gray-500); }
.sys-fc { font-family: var(--mono); font-size: 11px; border: 1.5px solid currentColor;
          background: none; border-radius: 100px; padding: 2px 10px;
          cursor: pointer; opacity: 0.3; transition: opacity 0.1s; }
.sys-fc.active { opacity: 1; background: rgba(0,0,0,0.03); }

/* ── Detail panel ─────────────────────────────── */
.sys-panel { background: var(--white); border: var(--border); border-radius: 12px; padding: 18px; }
.sys-ph { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.sys-plabel { font-family: var(--serif); font-size: 15px; font-weight: 600; flex: 1; }
.sys-kbadge { font-family: var(--mono); font-size: 10px; border: 1px solid; border-radius: 4px; padding: 2px 6px; }
.sys-pdesc { font-size: 13px; color: var(--gray-700); margin: 0 0 10px; line-height: 1.5; }
.sys-meta { display: grid; grid-template-columns: auto 1fr; gap: 3px 12px; font-size: 12px; margin: 0 0 10px; }
.sys-meta dt { color: var(--gray-500); font-family: var(--mono); }
.sys-meta dd { color: var(--slate); margin: 0; }
.sys-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px; }
.sys-tag { font-family: var(--mono); font-size: 10px; background: var(--gray-100); color: var(--gray-700); border-radius: 4px; padding: 2px 7px; }
.sys-edges { border-top: 1px solid var(--gray-100); padding-top: 10px; }
.sys-eg-label { font-family: var(--mono); font-size: 10px; color: var(--gray-500); margin: 6px 0 3px; }
.sys-er { font-size: 12px; color: var(--gray-700); display: flex; gap: 8px; align-items: baseline; padding: 2px 0; }
.sys-ek { font-family: var(--mono); font-size: 10px; color: var(--gray-500); }
.sys-er-link { color: var(--clay); cursor: pointer; text-decoration: none; }
.sys-er-link:hover { text-decoration: underline; }

/* ── Node interaction ─────────────────────────── */
.sys-nr { transition: filter 0.12s; }
.sys-node:hover .sys-nr { filter: brightness(0.94); }
.sys-node.active .sys-nr { stroke-width: 2.5px !important; filter: brightness(0.91); }
.sys-node.filtered-out,
.sys-edge.filtered-out,
.sys-group.filtered-out,
.sys-node.seq-unrelated,
.sys-edge.seq-unrelated { opacity: 0.12; pointer-events: none; }

/* ── Hint / placeholder ───────────────────────── */
.sys-hint { color: var(--gray-500); font-size: 12px; text-align: center; padding: 32px 16px;
            font-family: var(--mono); background: var(--white); border: var(--border);
            border-radius: 12px; border-style: dashed; }

/* ── Legend ───────────────────────────────────── */
.sys-legend { background: var(--white); border: var(--border); border-radius: 12px; padding: 14px 18px; }
.sys-leg-group { margin-bottom: 10px; }
.sys-leg-group:last-child { margin-bottom: 0; }
.sys-leg-title { font-family: var(--mono); font-size: 10px; color: var(--gray-500); margin-bottom: 5px; }
.sys-leg-row { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--gray-700); padding: 2px 0; }
.sys-leg-row span:first-child { width: 16px; text-align: center; font-size: 12px; }
.sys-leg-line { display: inline-block; width: 20px; border-top: 2px solid; height: 0; }

/* ── Description ──────────────────────────────── */
.sys-desc { font-size: 14px; color: var(--gray-700); margin: 0 0 20px; line-height: 1.6; }

/* ── Expand-in-place / collapse glyphs (drawn by arch_engine.js) ── */
.sys-expand-btn { opacity: 0.55; transition: opacity 0.1s; }
.sys-expand-btn:hover { opacity: 1; }

/* ── Appears-in-sequences (node detail panel) ─── */
.sys-seq-refs { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
"""

JS = """
/* ── Tab switching ─────────────────────────────── */
function sysTab(el) {
    document.querySelectorAll('.sys-tab').forEach(function(t) { t.classList.remove('active'); });
    document.querySelectorAll('.sys-view').forEach(function(v) { v.style.display = 'none'; });
    el.classList.add('active');
    var view = document.getElementById('view-' + el.getAttribute('data-view'));
    if (view) view.style.display = 'block';
}

/* ── Node click (architecture detail panel) ─────── */
var _active = null;
function _selectNode(el) {
    var nid = el.getAttribute('data-id');
    var panel = document.getElementById('panel-' + nid);
    var wrap = el.closest('.sys-wrap');
    var hint = wrap ? wrap.querySelector('.sys-hint') : null;

    if (_active) _active.classList.remove('active');
    if (wrap) wrap.querySelectorAll('.sys-panel').forEach(function(p) { p.style.display = 'none'; });

    el.classList.add('active');
    _active = el;
    if (hint) hint.style.display = 'none';
    if (panel) panel.style.display = 'block';
}
function sysClick(el) {
    if (_active === el) {
        el.classList.remove('active');
        _active = null;
        var wrap = el.closest('.sys-wrap');
        var hint = wrap ? wrap.querySelector('.sys-hint') : null;
        if (wrap) wrap.querySelectorAll('.sys-panel').forEach(function(p) { p.style.display = 'none'; });
        if (hint) hint.style.display = 'block';
        return;
    }
    _selectNode(el);
}

/* ── Aggregate-edge click (synthesized panel, not server-rendered — ──
 * aggregate edges don't exist in the spec, so unlike every other panel
 * here there's nothing pre-rendered to toggle; this builds the content
 * client-side from the edge's data-members JSON instead.) */
function _escHtml(s) {
    return String(s).replace(/[&<>"]/g, function(c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
}
function sysEdgeAggregateClick(g) {
    var wrap = g.closest('.sys-wrap');
    if (_active === g) {
        g.classList.remove('active');
        _active = null;
        var hint0 = wrap ? wrap.querySelector('.sys-hint') : null;
        if (wrap) wrap.querySelectorAll('.sys-panel').forEach(function(p) { p.style.display = 'none'; });
        if (hint0) hint0.style.display = 'block';
        return;
    }
    var members = JSON.parse(g.getAttribute('data-members') || '[]');
    var scope = g.closest('.sys-arch-scope');
    var mount = scope ? scope.querySelector('.sys-mount') : null;
    var prefix = mount ? mount.getAttribute('data-prefix') : '';
    var panel = document.getElementById(prefix + 'sys-edge-agg-panel');
    if (!panel) return;

    var html = '<div class="sys-ph"><span class="sys-plabel">' + members.length + ' edges</span></div><dl class="sys-meta">';
    members.forEach(function(m) {
        html += '<dt>' + _escHtml(m.from) + ' → ' + _escHtml(m.to) + '</dt><dd>' + _escHtml(m.label || m.kind) + '</dd>';
    });
    panel.innerHTML = html + '</dl>';

    if (_active) _active.classList.remove('active');
    var hint = wrap ? wrap.querySelector('.sys-hint') : null;
    if (wrap) wrap.querySelectorAll('.sys-panel').forEach(function(p) { p.style.display = 'none'; });
    g.classList.add('active');
    _active = g;
    if (hint) hint.style.display = 'none';
    panel.style.display = 'block';
}

/* ── Jump to a referenced node from a detail-panel link ─ */
function sysGoTo(linkEl) {
    var targetId = linkEl.getAttribute('data-target');
    var wrap = linkEl.closest('.sys-wrap');
    if (!wrap) return;
    var targetNode = wrap.querySelector('.sys-node[data-id="' + CSS.escape(targetId) + '"]');
    if (targetNode) {
        _selectNode(targetNode);
        targetNode.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

/* ── Sequence step example panels ──────────────── */
var _activeStep = null;
function sysSeqStepClick(el) {
    var targetId = el.getAttribute('data-target');
    var panel = document.getElementById(targetId);
    var wrap = el.closest('.sys-wrap');
    var hint = wrap ? wrap.querySelector('.sys-hint') : null;

    if (_activeStep === el) {
        el.classList.remove('active');
        _activeStep = null;
        if (panel) panel.style.display = 'none';
        if (hint) hint.style.display = 'block';
        return;
    }

    if (_activeStep) {
        _activeStep.classList.remove('active');
        var prevWrap = _activeStep.closest('.sys-wrap');
        if (prevWrap) prevWrap.querySelectorAll('.sys-panel').forEach(function(p) { p.style.display = 'none'; });
    }
    if (wrap) wrap.querySelectorAll('.sys-panel').forEach(function(p) { p.style.display = 'none'; });

    el.classList.add('active');
    _activeStep = el;
    if (hint) hint.style.display = 'none';
    if (panel) panel.style.display = 'block';
}
"""
