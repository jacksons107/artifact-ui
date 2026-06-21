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

/* ── Label anchor placement (avoid OTHER edges, not just other labels) ──
 * computeEdgeLabelBoxes above only ever sees label boxes — it has no idea
 * an edge's actual drawn path even exists, so it can (and does) push a
 * label down right on top of some unrelated edge's line. These functions
 * pick a smarter STARTING point along a label's own edge before that
 * resolution pass ever runs, by trying a few candidate points along the
 * edge's real rendered path (not just its straight-line midpoint) and
 * keeping whichever has the least overlap with every OTHER edge's path.
 * The label-vs-label resolution above is untouched — this only changes
 * what each candidate's desired (x,y) is before that pass sees it. */

// Walks a polyline's cumulative arc length and returns the point at
// fraction t (0..1) along it — works the same whether `polyline` is a
// grid-mode bend list or a curve-sampled approximation (sampleEdgeSegment,
// 30_draw.js), since both are just {x,y}[] in drawing order.
function pointAtFraction(polyline, t) {
  if (polyline.length === 1) return polyline[0];
  var lengths = [], total = 0;
  for (var i = 0; i < polyline.length - 1; i++) {
    var dx = polyline[i + 1].x - polyline[i].x, dy = polyline[i + 1].y - polyline[i].y;
    var len = Math.sqrt(dx * dx + dy * dy);
    lengths.push(len);
    total += len;
  }
  if (total === 0) return polyline[0];
  var target = Math.max(0, Math.min(1, t)) * total;
  var acc = 0;
  for (var k = 0; k < lengths.length; k++) {
    var segLen = lengths[k];
    if (acc + segLen >= target || k === lengths.length - 1) {
      var localT = segLen > 0 ? (target - acc) / segLen : 0;
      localT = Math.max(0, Math.min(1, localT));
      return {
        x: polyline[k].x + (polyline[k + 1].x - polyline[k].x) * localT,
        y: polyline[k].y + (polyline[k + 1].y - polyline[k].y) * localT,
      };
    }
    acc += segLen;
  }
  return polyline[polyline.length - 1];
}

// AABB test of `rect` ({x0,y0,x1,y1}) against every consecutive segment's
// bounding box in `polyline` — same style as segmentHitsObstacle
// (27_orthogonal_routing.js), just against a rect instead of another rect
// pair, since a polyline segment's own bbox is what a straight axis-aligned
// label rect can actually be tested against cheaply.
function rectOverlapsPolyline(rect, polyline, eps) {
  eps = eps || 0;
  for (var i = 0; i < polyline.length - 1; i++) {
    var a = polyline[i], b = polyline[i + 1];
    var x0 = Math.min(a.x, b.x), x1 = Math.max(a.x, b.x);
    var y0 = Math.min(a.y, b.y), y1 = Math.max(a.y, b.y);
    if (rect.x0 < x1 + eps && x0 < rect.x1 + eps && rect.y0 < y1 + eps && y0 < rect.y1 + eps) return true;
  }
  return false;
}

var LABEL_ANCHOR_FRACTIONS = [0.5, 0.35, 0.65, 0.2, 0.8];

/* Picks the best of a few candidate points along `ownKey`'s own polyline
 * for a label box of size lw x lh, scored by how many OTHER edges'
 * polylines (in `polylineByKey`) it would overlap. Always evaluates 0.5
 * (today's plain midpoint) first/among the candidates, so the result can
 * never be WORSE than always using the midpoint — only equal or better —
 * and ties prefer whichever candidate is closest to 0.5, so a label only
 * moves when doing so actually avoids an edge it would otherwise sit on.
 * Returns {x,y} (top-left of the box) or null if `ownKey`'s polyline is
 * degenerate (a single point — e.g. a zero-length edge) — the caller is
 * expected to fall back to its own simple midpoint math in that case. */
function chooseLabelAnchor(ownKey, polylineByKey, lw, lh, fractions) {
  fractions = fractions || LABEL_ANCHOR_FRACTIONS;
  var ownPolyline = polylineByKey[ownKey];
  if (!ownPolyline || ownPolyline.length < 2) return null;
  var otherKeys = Object.keys(polylineByKey).filter(function (k) { return k !== String(ownKey); });
  var best = null, bestScore = Infinity, bestDist = Infinity;
  fractions.forEach(function (t) {
    var p = pointAtFraction(ownPolyline, t);
    var rect = { x0: p.x - lw / 2, y0: p.y - lh / 2, x1: p.x + lw / 2, y1: p.y + lh / 2 };
    var score = 0;
    otherKeys.forEach(function (k) {
      if (rectOverlapsPolyline(rect, polylineByKey[k])) score++;
    });
    var dist = Math.abs(t - 0.5);
    if (score < bestScore || (score === bestScore && dist < bestDist)) {
      best = { x: rect.x0, y: rect.y0 };
      bestScore = score;
      bestDist = dist;
    }
  });
  return best;
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
