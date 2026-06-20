/* ── Edge label collision resolution ──
 * Each candidate is a label's *desired* box, top-left + size — exactly
 * what the caller would have drawn at with no other labels present.
 * Returns adjusted boxes with no pairwise overlap, keyed by whatever `key`
 * the caller supplied (an edge index, typically).
 *
 * Deterministic single-direction resolution: process candidates sorted
 * top-to-bottom/left-to-right, and only ever push a box DOWN just far
 * enough to clear whatever's already been placed above it. Because
 * placement only ever increases y and only checks against already-placed
 * (earlier-sorted) boxes, this always terminates and never oscillates —
 * unlike a bidirectional "push apart" pass, which is exactly the kind of
 * reactive patch that caused a runaway regression earlier for group-box
 * overlap (see layoutHierarchy's history). */
function computeEdgeLabelBoxes(candidates, gap) {
  gap = gap || 2;
  var sorted = candidates.slice().sort(function (a, b) { return (a.y - b.y) || (a.x - b.x); });
  var placed = [];
  var out = {};
  sorted.forEach(function (c) {
    var x0 = c.x, x1 = c.x + c.w;
    var y0 = c.y, y1 = c.y + c.h;
    var moved = true;
    var guard = 0;
    while (moved && guard++ < placed.length + 5) {
      moved = false;
      for (var i = 0; i < placed.length; i++) {
        var p = placed[i];
        var overlapsX = x0 < p.x1 + gap && p.x0 < x1 + gap;
        var overlapsY = y0 < p.y1 + gap && p.y0 < y1 + gap;
        if (overlapsX && overlapsY) {
          var dy = p.y1 + gap - y0;
          y0 += dy; y1 += dy;
          moved = true;
        }
      }
    }
    var box = { x0: x0, y0: y0, x1: x1, y1: y1 };
    placed.push(box);
    out[c.key] = { x: x0, y: y0, w: c.w, h: c.h };
  });
  return out;
}

/* ── Collapsed-box edge anchor spreading ──
 * When an edge's endpoint is hidden inside a collapsed group, it gets
 * redirected (drawnAncestorFor, 20_visibility.js) to land on that group's
 * placeholder box. If two edges originally ran to/from *different* hidden
 * members, redirecting them both to the same box's center would draw them
 * exactly on top of each other with no visual indication they ever had
 * distinct endpoints. This spreads such edges across the box's width —
 * one fraction per distinct original member, evenly spaced — while edges
 * that share the same original (hidden) member still land on the same
 * point, since there's nothing to disambiguate there. Edges that aren't
 * redirected at all (the common case) keep the plain center anchor. */
function computeEdgeAnchorOffsets(edges) {
  function distinctOriginsByAnchor(sideKey, origKey) {
    var byAnchor = {};
    edges.forEach(function (e) {
      var anchor = e[sideKey];
      var orig = e[origKey] !== undefined ? e[origKey] : anchor;
      if (orig === anchor) return; // not redirected — no spreading needed
      if (!byAnchor[anchor]) byAnchor[anchor] = [];
      if (byAnchor[anchor].indexOf(orig) === -1) byAnchor[anchor].push(orig);
    });
    Object.keys(byAnchor).forEach(function (k) { byAnchor[k].sort(); });
    return byAnchor;
  }
  var fromOrigins = distinctOriginsByAnchor("from", "_origFrom");
  var toOrigins = distinctOriginsByAnchor("to", "_origTo");

  var offsets = edges.map(function (e) {
    var fromFrac = 0.5, toFrac = 0.5;
    var origFrom = e._origFrom !== undefined ? e._origFrom : e.from;
    var origTo = e._origTo !== undefined ? e._origTo : e.to;
    var fg = fromOrigins[e.from];
    if (fg && fg.length > 1) fromFrac = (fg.indexOf(origFrom) + 1) / (fg.length + 1);
    var tg = toOrigins[e.to];
    if (tg && tg.length > 1) toFrac = (tg.indexOf(origTo) + 1) / (tg.length + 1);
    return { fromFrac: fromFrac, toFrac: toFrac };
  });

  // aggregateEdges' synthetic edge has no _origFrom/_origTo of its own (it
  // summarizes several original members at once, not one), so the spreading
  // above treats it as an ordinary, non-redirected edge and leaves it at
  // dead center — same as any differently-kinded edge that happens to run
  // between the exact same (from,to) pair. That used to be harmless (just
  // two thin, differently-colored lines stacked exactly on top of each
  // other), but an aggregate edge also gets a thicker stroke and a wide
  // invisible click-target, so stacked like that it fully occludes the
  // other line and steals its clicks. Nudge every aggregate off-center
  // whenever it shares its exact (from,to) pair with another edge.
  var byPair = {};
  edges.forEach(function (e, i) {
    var key = e.from + "|" + e.to;
    (byPair[key] || (byPair[key] = [])).push(i);
  });
  Object.keys(byPair).forEach(function (key) {
    var idxs = byPair[key];
    if (idxs.length < 2) return;
    var n = 0;
    idxs.forEach(function (i) {
      if (!edges[i]._aggregate) return;
      n++;
      offsets[i].fromFrac = Math.min(0.9, 0.5 + 0.15 * n);
      offsets[i].toFrac = Math.min(0.9, 0.5 + 0.15 * n);
    });
  });

  return offsets;
}
