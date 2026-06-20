/* ── Expand/collapse: visible-graph computation ──
 * A node/group is visible iff every ancestor in its parent chain is
 * expanded. A group that is itself visible but not expanded is drawn as
 * a single placeholder node standing in for its whole subtree. Every
 * edge endpoint is resolved to its nearest visible ancestor — always
 * unambiguous, since each id has at most one parent (validated
 * server-side). */
function buildParentMap(groups) {
  var parentOf = {};
  (groups || []).forEach(function (g) {
    (g.members || []).forEach(function (m) { parentOf[m] = g.id; });
  });
  return parentOf;
}

function isVisible(id, parentOf, expandedSet, memo) {
  if (memo.hasOwnProperty(id)) return memo[id];
  var p = parentOf[id];
  var result;
  if (p === undefined) result = true;
  else if (!expandedSet.has(p)) result = false;
  else result = isVisible(p, parentOf, expandedSet, memo);
  memo[id] = result;
  return result;
}

function drawnAncestorFor(leafId, parentOf, expandedSet, memo) {
  if (isVisible(leafId, parentOf, expandedSet, memo)) return leafId;
  var cur = parentOf[leafId];
  while (cur !== undefined) {
    if (isVisible(cur, parentOf, expandedSet, memo) && !expandedSet.has(cur)) return cur;
    cur = parentOf[cur];
  }
  return leafId; // shouldn't happen given the single-parent invariant
}

function getVisibleGraph(spec, expandedSet) {
  var groupsById = {};
  (spec.groups || []).forEach(function (g) { groupsById[g.id] = g; });
  var parentOf = buildParentMap(spec.groups);
  var memo = {};

  var nodes = (spec.nodes || []).filter(function (n) {
    return isVisible(n.id, parentOf, expandedSet, memo);
  });

  (spec.groups || []).forEach(function (g) {
    if (isVisible(g.id, parentOf, expandedSet, memo) && !expandedSet.has(g.id)) {
      var count = (g.members || []).length;
      nodes.push({
        id: g.id, label: g.label || g.id, kind: g.kind,
        tech: count + (count === 1 ? " member" : " members"),
        _isGroupPlaceholder: true, _groupKind: g.kind,
      });
    }
  });

  var edges = [];
  (spec.edges || []).forEach(function (e) {
    var from = drawnAncestorFor(e.from, parentOf, expandedSet, memo);
    var to = drawnAncestorFor(e.to, parentOf, expandedSet, memo);
    if (from === to) return; // both endpoints collapsed into the same visible box
    edges.push(Object.assign({}, e, { from: from, to: to }));
  });

  function resolve(id) { return drawnAncestorFor(id, parentOf, expandedSet, memo); }

  return { nodes: nodes, edges: edges, groupsById: groupsById, parentOf: parentOf, resolve: resolve };
}
