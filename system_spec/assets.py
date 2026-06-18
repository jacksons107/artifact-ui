# ── Page assembly: embedded CSS / JS ──────────────────────────────────────────

_CSS = """
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

/* ── Filter bar (architecture) ────────────────── */
.sys-arch-filters { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }

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

/* ── Node interaction ─────────────────────────── */
.sys-nr { transition: filter 0.12s; }
.sys-node:hover .sys-nr { filter: brightness(0.94); }
.sys-node.active .sys-nr { stroke-width: 2.5px !important; filter: brightness(0.91); }
.sys-node.filtered-out,
.sys-edge.filtered-out,
.sys-group.filtered-out { opacity: 0.12; pointer-events: none; }

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

/* ── Component list ───────────────────────────── */
.sys-clist { display: flex; flex-direction: column; gap: 14px; }
.sys-filters { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.sys-tbl-wrap { overflow-x: auto; background: var(--white); border: var(--border); border-radius: 12px; }
.sys-ctable { width: 100%; border-collapse: collapse; font-size: 13px; }
.sys-ctable th { font-family: var(--mono); font-size: 10px; color: var(--gray-500); text-align: left;
                 padding: 10px 14px; border-bottom: 1.5px solid var(--gray-300); white-space: nowrap; }
.sys-ctable td { padding: 9px 14px; border-bottom: 1px solid var(--gray-100); vertical-align: top; }
.sys-ctable tbody tr:last-child td { border-bottom: none; }
.sys-cr:hover td { background: var(--gray-100); }
.sys-mono { font-family: var(--mono); font-size: 12px; color: var(--gray-700); }
.sys-dc { font-size: 12px; color: var(--gray-500); max-width: 280px; }

/* ── Layer diagram view ───────────────────────── */
.sys-layer-wrap { background: var(--white); border: var(--border); border-radius: 12px; padding: 20px; overflow-x: auto; }

/* ── Sequence diagram view ────────────────────── */
.sys-seq-wrap { display: flex; flex-direction: column; gap: 14px; }
.sys-seq-controls { display: flex; align-items: center; gap: 10px; }
.sys-seq-sel { font-family: var(--mono); font-size: 12px; border: var(--border); border-radius: 6px;
               padding: 5px 12px; background: var(--white); color: var(--slate); cursor: pointer;
               appearance: none; -webkit-appearance: none; }
.sys-seq-panel { background: var(--white); border: var(--border); border-radius: 12px; padding: 20px; overflow-x: auto; }

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

/* ── Description ──────────────────────────────── */
.sys-desc { font-size: 14px; color: var(--gray-700); margin: 0 0 20px; line-height: 1.6; }

/* ── Filter bar separator ─────────────────────── */
.sys-fl-sep { display: inline-block; width: 1px; height: 16px; background: var(--gray-300); margin: 0 6px; vertical-align: middle; }

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

_JS = """
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
function sysClick(el) {
    var nid = el.getAttribute('data-id');
    var panel = document.getElementById('panel-' + nid);
    var wrap = el.closest('.sys-wrap');
    var hint = wrap ? wrap.querySelector('.sys-hint') : null;

    if (_active === el) {
        el.classList.remove('active');
        _active = null;
        if (wrap) wrap.querySelectorAll('.sys-panel').forEach(function(p) { p.style.display = 'none'; });
        if (hint) hint.style.display = 'block';
        return;
    }

    if (_active) _active.classList.remove('active');
    if (wrap) wrap.querySelectorAll('.sys-panel').forEach(function(p) { p.style.display = 'none'; });

    el.classList.add('active');
    _active = el;
    if (hint) hint.style.display = 'none';
    if (panel) panel.style.display = 'block';
}

/* ── Architecture kind + status filters ─────────── */
function sysAKind(btn) {
    btn.classList.toggle('active');
    _applyArchFilter();
}
function sysAStatus(btn) {
    btn.classList.toggle('active');
    _applyArchFilter();
}
function sysAEKind(btn) {
    btn.classList.toggle('active');
    _applyArchFilter();
}
function sysAGroup(btn) {
    btn.classList.toggle('active');
    _applyArchFilter();
}
function _applyArchFilter() {
    var kinds = new Set();
    document.querySelectorAll('.sys-fc[data-ak].active').forEach(function(b) { kinds.add(b.getAttribute('data-ak')); });
    var statuses = new Set();
    document.querySelectorAll('.sys-fc[data-as].active').forEach(function(b) { statuses.add(b.getAttribute('data-as')); });
    var ekinds = new Set();
    document.querySelectorAll('.sys-fc[data-aek].active').forEach(function(b) { ekinds.add(b.getAttribute('data-aek')); });
    var agroups = new Set();
    document.querySelectorAll('.sys-fc[data-ag].active').forEach(function(b) { agroups.add(b.getAttribute('data-ag')); });
    var hasKindFilter   = document.querySelectorAll('.sys-fc[data-ak]').length > 0;
    var hasStatusFilter = document.querySelectorAll('.sys-fc[data-as]').length > 0;
    var hasEKindFilter  = document.querySelectorAll('.sys-fc[data-aek]').length > 0;
    var hasGroupFilter  = document.querySelectorAll('.sys-fc[data-ag]').length > 0;

    // Groups explicitly toggled off (not just "none active" -> show-all fallback)
    var inactiveGroups = new Set();
    if (hasGroupFilter && agroups.size > 0) {
        document.querySelectorAll('.sys-fc[data-ag]').forEach(function(b) {
            var gid = b.getAttribute('data-ag');
            if (!agroups.has(gid)) inactiveGroups.add(gid);
        });
    }
    function _inInactiveGroup(groupsAttr) {
        if (inactiveGroups.size === 0 || !groupsAttr) return false;
        return groupsAttr.split(' ').some(function(gid) { return gid && inactiveGroups.has(gid); });
    }

    document.querySelectorAll('.sys-node').forEach(function(n) {
        var k = n.getAttribute('data-kind');
        var s = n.getAttribute('data-status') || '';
        var kOk = !hasKindFilter   || kinds.size === 0    || kinds.has(k);
        var sOk = !hasStatusFilter || statuses.size === 0 || !s || statuses.has(s);
        var groupFaded = _inInactiveGroup(n.getAttribute('data-groups'));
        n.classList.toggle('filtered-out', !(kOk && sOk) || groupFaded);
    });
    document.querySelectorAll('.sys-edge').forEach(function(e) {
        var k = e.getAttribute('data-kind');
        var eOk = !hasEKindFilter || ekinds.size === 0 || ekinds.has(k);
        var groupFaded = _inInactiveGroup(e.getAttribute('data-src-groups')) ||
                          _inInactiveGroup(e.getAttribute('data-dst-groups'));
        e.classList.toggle('filtered-out', !eOk || groupFaded);
    });
    document.querySelectorAll('.sys-group').forEach(function(g) {
        var gid = g.getAttribute('data-gid');
        var gOk = !hasGroupFilter || agroups.size === 0 || agroups.has(gid);
        g.classList.toggle('filtered-out', !gOk);
    });
}

/* ── Sequence selector ─────────────────────────── */
function sysSeqChange(sel) {
    var val = sel.value;
    document.querySelectorAll('.sys-seq-panel').forEach(function(p) {
        p.style.display = (p.id === 'seqp-' + val) ? '' : 'none';
    });
}

/* ── Code detail selector ──────────────────────── */
function sysCodeDetailChange(sel) {
    var val = sel.value;
    document.querySelectorAll('.sys-cd-panel').forEach(function(p) {
        p.style.display = (p.id === 'cdp-' + val) ? '' : 'none';
    });
}

/* ── Component list filters ────────────────────── */
function sysFKind(btn) {
    btn.classList.toggle('active');
    _applyListFilter();
}
function sysFStatus(btn) {
    btn.classList.toggle('active');
    _applyListFilter();
}
function _applyListFilter() {
    var kinds = new Set();
    document.querySelectorAll('.sys-fc[data-fk].active').forEach(function(b) { kinds.add(b.getAttribute('data-fk')); });
    var statuses = new Set();
    document.querySelectorAll('.sys-fc[data-fs].active').forEach(function(b) { statuses.add(b.getAttribute('data-fs')); });
    var hasKindFilter = document.querySelectorAll('.sys-fc[data-fk]').length > 0;
    var hasStatusFilter = document.querySelectorAll('.sys-fc[data-fs]').length > 0;
    document.querySelectorAll('.sys-cr').forEach(function(row) {
        var k = row.getAttribute('data-rkind');
        var s = row.getAttribute('data-rstatus');
        var kOk = !hasKindFilter || kinds.size === 0 || kinds.has(k);
        var sOk = !hasStatusFilter || statuses.size === 0 || !s || statuses.has(s);
        row.style.display = (kOk && sOk) ? '' : 'none';
    });
}
"""
