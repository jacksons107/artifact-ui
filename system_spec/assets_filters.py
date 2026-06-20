# ── Filtering: architecture filter bar + Components-tab list filters ──────

CSS = """
/* ── Filter bar (architecture) ────────────────── */
.sys-arch-filters { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }

/* ── Filter bar separator ─────────────────────── */
.sys-fl-sep { display: inline-block; width: 1px; height: 16px; background: var(--gray-300); margin: 0 6px; vertical-align: middle; }

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
"""

JS = """
/* ── Architecture kind + status filters ─────────── */
function sysAKind(btn) {
    btn.classList.toggle('active');
    _applyArchFilter(btn.closest('.sys-arch-scope'));
}
function sysAStatus(btn) {
    btn.classList.toggle('active');
    _applyArchFilter(btn.closest('.sys-arch-scope'));
}
function sysAEKind(btn) {
    btn.classList.toggle('active');
    _applyArchFilter(btn.closest('.sys-arch-scope'));
}
function sysAGroup(btn) {
    btn.classList.toggle('active');
    _applyArchFilter(btn.closest('.sys-arch-scope'));
}
function _applyArchFilter(scope) {
    if (!scope) return;
    var kinds = new Set();
    scope.querySelectorAll('.sys-fc[data-ak].active').forEach(function(b) { kinds.add(b.getAttribute('data-ak')); });
    var statuses = new Set();
    scope.querySelectorAll('.sys-fc[data-as].active').forEach(function(b) { statuses.add(b.getAttribute('data-as')); });
    var ekinds = new Set();
    scope.querySelectorAll('.sys-fc[data-aek].active').forEach(function(b) { ekinds.add(b.getAttribute('data-aek')); });
    var agroups = new Set();
    scope.querySelectorAll('.sys-fc[data-ag].active').forEach(function(b) { agroups.add(b.getAttribute('data-ag')); });
    var hasKindFilter   = scope.querySelectorAll('.sys-fc[data-ak]').length > 0;
    var hasStatusFilter = scope.querySelectorAll('.sys-fc[data-as]').length > 0;
    var hasEKindFilter  = scope.querySelectorAll('.sys-fc[data-aek]').length > 0;
    var hasGroupFilter  = scope.querySelectorAll('.sys-fc[data-ag]').length > 0;

    // Groups not currently active — if none are active, every group counts as inactive
    // (so deselecting all group toggles fades all groups, rather than showing everything).
    var inactiveGroups = new Set();
    if (hasGroupFilter) {
        scope.querySelectorAll('.sys-fc[data-ag]').forEach(function(b) {
            var gid = b.getAttribute('data-ag');
            if (!agroups.has(gid)) inactiveGroups.add(gid);
        });
    }
    function _inInactiveGroup(groupsAttr) {
        if (inactiveGroups.size === 0 || !groupsAttr) return false;
        return groupsAttr.split(' ').some(function(gid) { return gid && inactiveGroups.has(gid); });
    }

    var hiddenNodes = new Set();
    scope.querySelectorAll('.sys-node').forEach(function(n) {
        var isGroupPlaceholder = n.getAttribute('data-is-group') === '1';
        // A collapsed group's placeholder isn't really an instance of any
        // selectable node kind/status — it stands in for the whole group,
        // so it's governed by the group filter (on its own id) instead of
        // kind/status filtering, which would otherwise hide it
        // unconditionally (its data-kind is the group's kind, never a
        // choice the kind filter bar actually offers).
        var kOk = isGroupPlaceholder || !hasKindFilter   || (kinds.size > 0 && kinds.has(n.getAttribute('data-kind')));
        var sOk = isGroupPlaceholder || !hasStatusFilter || !(n.getAttribute('data-status') || '') || (statuses.size > 0 && statuses.has(n.getAttribute('data-status')));
        var groupFaded = _inInactiveGroup(n.getAttribute('data-groups'));
        var ownGroupFaded = isGroupPlaceholder && hasGroupFilter && inactiveGroups.has(n.getAttribute('data-group-id'));
        var hidden = !(kOk && sOk) || groupFaded || ownGroupFaded;
        n.classList.toggle('filtered-out', hidden);
        if (hidden) hiddenNodes.add(n.getAttribute('data-id'));
    });
    scope.querySelectorAll('.sys-edge').forEach(function(e) {
        var k = e.getAttribute('data-kind');
        var eOk = !hasEKindFilter || (ekinds.size > 0 && ekinds.has(k));
        var groupFaded = _inInactiveGroup(e.getAttribute('data-src-groups')) ||
                          _inInactiveGroup(e.getAttribute('data-dst-groups'));
        var endpointHidden = hiddenNodes.has(e.getAttribute('data-from')) || hiddenNodes.has(e.getAttribute('data-to'));
        e.classList.toggle('filtered-out', !eOk || groupFaded || endpointHidden);
    });
    scope.querySelectorAll('.sys-group').forEach(function(g) {
        var gid = g.getAttribute('data-gid');
        var gOk = !hasGroupFilter || (agroups.size > 0 && agroups.has(gid));
        g.classList.toggle('filtered-out', !gOk);
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
