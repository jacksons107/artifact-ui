/* ── Same-kind parallel-edge aggregation ──
 * Multiple edges can resolve to the exact same (from, to, kind) once
 * collapsed-group redirection has run — most often several hidden members
 * of a collapsed group all connecting to the same external node with the
 * same edge kind. Drawing them as separate, fully overlapping lines is
 * pure clutter (there's no second endpoint to spread them apart toward,
 * unlike computeEdgeAnchorOffsets' fan-out for edges that share a box but
 * have *different* from/to pairs). This collapses each such bucket into a
 * single line before anything is drawn — singles pass straight through
 * (same object reference, so callers can rely on reference equality).
 *
 * Layout (10_layout.js) already ran on the full, pre-aggregation edge
 * list, so via-lane dummies (layout.edgeVia) are keyed by index into THAT
 * list, not into the aggregated result this function returns. Returns
 * `viaIndexOf`, parallel to `drawEdges`, giving the original index whose
 * via-lane should be used for each drawn edge — every member of a bucket
 * shares the same (from, to), hence the same layer span, so any one
 * member's reserved via-lane is a valid route for the merged line;
 * the first member's is used. */
function aggregateEdges(edges) {
  var buckets = {}, order = [];
  edges.forEach(function (e, i) {
    var key = e.from + " " + e.to + " " + (e.kind || "");
    if (!buckets[key]) { buckets[key] = []; order.push(key); }
    buckets[key].push({ edge: e, idx: i });
  });
  var drawEdges = [], viaIndexOf = [];
  order.forEach(function (key) {
    var members = buckets[key];
    viaIndexOf.push(members[0].idx);
    if (members.length === 1) { drawEdges.push(members[0].edge); return; }
    var allDashed = members.every(function (m) { return !!m.edge.async; });
    drawEdges.push({
      from: members[0].edge.from, to: members[0].edge.to, kind: members[0].edge.kind,
      async: allDashed, _aggregate: true, _members: members.map(function (m) { return m.edge; }),
    });
  });
  return { drawEdges: drawEdges, viaIndexOf: viaIndexOf };
}
