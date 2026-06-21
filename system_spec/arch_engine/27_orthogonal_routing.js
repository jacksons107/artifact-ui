/* ── Orthogonal ("grid") edge routing ──
 * Alternative to curve() for edges that should render with only
 * horizontal/vertical segments. Reuses the same `points` array drawDiagram
 * already builds (source anchor, via centers from edgeVia, target anchor)
 * instead of building a general maze router.
 *
 * Every non-straight hop between two consecutive points uses the same
 * shape: escape vertically off of each endpoint's own row (toward the
 * other endpoint) into the empty band beyond it, jog sideways to a lane
 * column, travel the long vertical run there, then jog back and escape
 * into the far endpoint. Two unrelated edges can otherwise need the same
 * territory for that run — not just at a shared anchor (a real node
 * port), but anywhere two anchors happen to land on the same x by
 * coincidence of the layout, or where two jogs simply cross paths — so
 * every hop is routed by a single global pass (routeHopsAvoidingOverlap)
 * that checks each new hop's actual shape against every previously placed
 * hop's, growing its lane column until clear, rather than guessing from a
 * heuristic interval grouping.
 */
var ORTHO_EPS = 0.5;
// Two REAL anchor x's (computed from independent fractions of possibly
// different node widths) can land within ORTHO_EPS of each other without
// truly being the same column — collapsing the bend in that case would
// draw a hairline diagonal instead of a genuinely vertical line. Deciding
// "skip the bend, this is one straight line" needs near-exact equality;
// ORTHO_EPS stays for dedup/significance checks on coordinates THIS file
// itself constructs, where tiny float drift from chained arithmetic is
// expected and fine to collapse.
var ORTHO_COORD_EPS = 1e-6;
var ORTHO_LANE_MARGIN = 16;
var ORTHO_ESCAPE = NODE_H; // far enough from a row-center via, or a row
                            // boundary anchor, to always land in the V_GAP
                            // band beyond that row (V_GAP=72 > NODE_H=60).
var ORTHO_DETOUR_MAX_TRIES = 6;
// Growing a lane column by ORTHO_LANE_MARGIN (16px) a mere 6 times only
// reaches 96px past the start — not enough to clear a real node, which can
// be up to NODE_W_MAX (260px) wide. This budget is used wherever a search
// is just walking a lane column rightward past whatever's in the way
// (obstacles or another hop's already-claimed column), as opposed to the
// bounded combo searches (escape distance x sign) that use
// ORTHO_DETOUR_MAX_TRIES on purpose to stay cheap.
var ORTHO_LANE_GROWTH_TRIES = 40;

function segmentHitsObstacle(a, b, rect) {
  var x0 = Math.min(a.x, b.x), x1 = Math.max(a.x, b.x);
  var y0 = Math.min(a.y, b.y), y1 = Math.max(a.y, b.y);
  return x0 < rect.x1 && rect.x0 < x1 && y0 < rect.y1 && rect.y0 < y1;
}

function elbowHitsAnyObstacle(elbow, obstacles) {
  for (var i = 0; i < elbow.length - 1; i++) {
    for (var j = 0; j < obstacles.length; j++) {
      if (segmentHitsObstacle(elbow[i], elbow[i + 1], obstacles[j])) return true;
    }
  }
  return false;
}

// Two segments "overlap" (rather than merely touch or cross at a point)
// when they're collinear and share a real, positive-length range — e.g.
// two hops whose lane columns differ but whose jog segments still cross
// the same height over an overlapping x-range. Touching at a single shared
// endpoint (the common case for edges sharing a real anchor) is fine and
// deliberately not flagged.
function segmentsOverlap(a0, a1, b0, b1) {
  // ORTHO_EPS (0.5px) is fine, even deliberately generous, for deciding
  // "are these two segments on the same column/row" — a false positive
  // there only costs an unnecessary extra lane, never a missed conflict.
  // The overlap AMOUNT, once on the same line, needs a much tighter
  // threshold: a real sub-pixel overlap (e.g. 0.3px, from two anchors'
  // independently computed fractions landing almost but not quite at the
  // same point) is still a real overlap, not "just touching" — only a
  // truly zero-length shared range (segments meeting at one exact shared
  // endpoint, the common case for edges sharing a real anchor) should pass.
  var aVert = Math.abs(a0.x - a1.x) < ORTHO_EPS, bVert = Math.abs(b0.x - b1.x) < ORTHO_EPS;
  var aHoriz = Math.abs(a0.y - a1.y) < ORTHO_EPS, bHoriz = Math.abs(b0.y - b1.y) < ORTHO_EPS;
  if (aVert && bVert && Math.abs(a0.x - b0.x) < ORTHO_EPS) {
    var ay0 = Math.min(a0.y, a1.y), ay1 = Math.max(a0.y, a1.y);
    var by0 = Math.min(b0.y, b1.y), by1 = Math.max(b0.y, b1.y);
    return Math.min(ay1, by1) - Math.max(ay0, by0) > ORTHO_COORD_EPS;
  }
  if (aHoriz && bHoriz && Math.abs(a0.y - b0.y) < ORTHO_EPS) {
    var ax0 = Math.min(a0.x, a1.x), ax1 = Math.max(a0.x, a1.x);
    var bx0 = Math.min(b0.x, b1.x), bx1 = Math.max(b0.x, b1.x);
    return Math.min(ax1, bx1) - Math.max(ax0, bx0) > ORTHO_COORD_EPS;
  }
  return false;
}

function elbowsOverlap(elbowA, elbowB) {
  for (var i = 0; i < elbowA.length - 1; i++) {
    for (var j = 0; j < elbowB.length - 1; j++) {
      if (segmentsOverlap(elbowA[i], elbowA[i + 1], elbowB[j], elbowB[j + 1])) return true;
    }
  }
  return false;
}

// Collapses consecutive coincident points (e.g. when an escape point and
// the lane jog's start happen to land in the same place) so the rendered
// path never carries redundant zero-length segments.
function dedupePoints(points) {
  var out = [points[0]];
  for (var i = 1; i < points.length; i++) {
    var prev = out[out.length - 1], cur = points[i];
    // Tight tolerance deliberately: a genuine but tiny (sub-pixel) gap
    // between two real anchor x's must still get its own segment, or the
    // collapsed point would leave the next segment quietly diagonal.
    if (Math.abs(prev.x - cur.x) > ORTHO_COORD_EPS || Math.abs(prev.y - cur.y) > ORTHO_COORD_EPS) out.push(cur);
  }
  return out;
}

/* For a normal downward hop (p1 strictly below p0), ANY height strictly
 * between p0.y and p1.y sits in empty inter-layer space — not just the
 * literal midpoint — so a conflicting bend has real freedom to move to a
 * different height entirely, which simultaneously resolves both a
 * horizontal-jog overlap (now at a different y) and a vertical-leg
 * coincidence (now spanning a disjoint range). Generates candidates
 * nearest the natural midpoint first, alternating outward, so the common
 * unconflicted case still bends at (or very near) the midpoint. */
function gapHeightCandidates(p0, p1) {
  var lo = Math.min(p0.y, p1.y), hi = Math.max(p0.y, p1.y);
  var mid = (lo + hi) / 2;
  var candidates = [mid];
  var maxOffset = (hi - lo) / 2 - ORTHO_EPS;
  for (var k = 1; k * ORTHO_LANE_MARGIN < maxOffset && candidates.length < 12; k++) {
    candidates.push(mid + k * ORTHO_LANE_MARGIN);
    candidates.push(mid - k * ORTHO_LANE_MARGIN);
  }
  return candidates;
}

function simpleGapElbow(p0, p1, h) {
  return dedupePoints([p0, { x: p0.x, y: h }, { x: p1.x, y: h }, p1]);
}

/* Escape distance/direction for each endpoint of a hop: always escape p0
 * toward p1's side (and p1 back toward p0's side), so a normal downward
 * hop escapes p0 down into the gap below it and p1 up into the gap above
 * it, while a back/feedback hop (p1 above p0) escapes symmetrically
 * upward/downward instead — one shape covers both. `escape` is a tunable
 * distance — passing 0 jogs immediately at each anchor's own y (still
 * safe for real obstacles: a fresh anchor's y already sits exactly on its
 * row's boundary, so a sideways line there only ever grazes a sibling's
 * edge, never its interior), used as the first, simplest attempt; a
 * larger escape is tried later only if that's not enough to clear a real
 * conflict. Clamped to the midpoint for a very short hop so the two
 * escape points never cross. */
function escapePoints(p0, p1, escape) {
  var sign = p1.y - p0.y >= 0 ? 1 : -1;
  var e0y = p0.y + sign * escape;
  var e1y = p1.y - sign * escape;
  if ((sign > 0 && e0y > e1y) || (sign < 0 && e0y < e1y)) {
    var mid = (p0.y + p1.y) / 2;
    e0y = mid; e1y = mid;
  }
  return [{ x: p0.x, y: e0y }, { x: p1.x, y: e1y }];
}

/* Builds the escape -> lane -> escape elbow for a hop, given an already-
 * assigned lane column and escape distance. Collapses to a plain
 * straight/2-point line when the lane equals both endpoints' x (nothing
 * to jog around). */
function laneElbow(p0, p1, laneX, escape) {
  if (Math.abs(p0.x - p1.x) < ORTHO_COORD_EPS && Math.abs(laneX - p0.x) < ORTHO_COORD_EPS) {
    return [p0, p1];
  }
  var esc = escapePoints(p0, p1, escape === undefined ? ORTHO_ESCAPE : escape);
  var e0 = esc[0], e1 = esc[1];
  return dedupePoints([p0, e0, { x: laneX, y: e0.y }, { x: laneX, y: e1.y }, e1, p1]);
}

/* Merges every obstacle's y-range into the y-intervals that ARE occupied,
 * then returns the gaps between them — a "free y band" is a height range
 * with no obstacle anywhere in it, for the FULL x axis, so a horizontal
 * sweep at any height inside one is safe no matter how far in x it travels
 * (unlike assuming a fixed V_GAP between every row: a group's own internal
 * rows can pack tighter than the diagram's nominal V_GAP, or a node from an
 * unrelated branch can land right alongside a row with no gap at all, so a
 * hardcoded "anything under V_GAP is safe" assumption is wrong in general —
 * this derives the actual safe range from the real obstacle list instead). */
function freeYBands(obstacles) {
  if (!obstacles.length) return [[-Infinity, Infinity]];
  var intervals = obstacles.map(function (o) { return [o.y0, o.y1]; }).sort(function (a, b) { return a[0] - b[0]; });
  var merged = [];
  intervals.forEach(function (iv) {
    if (merged.length && iv[0] <= merged[merged.length - 1][1] + ORTHO_EPS) {
      merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], iv[1]);
    } else {
      merged.push(iv.slice());
    }
  });
  var bands = [];
  var prevEnd = -Infinity;
  merged.forEach(function (iv) { bands.push([prevEnd, iv[0]]); prevEnd = iv[1]; });
  bands.push([prevEnd, Infinity]);
  return bands;
}

function bandContaining(bands, y) {
  for (var i = 0; i < bands.length; i++) {
    if (y >= bands[i][0] - ORTHO_EPS && y <= bands[i][1] + ORTHO_EPS) return bands[i];
  }
  return bands[bands.length - 1];
}

/* Candidate y-values to escape point `p` toward, in direction `sign`,
 * staying inside the free band that already contains p.y — so every
 * candidate here is real-obstacle-safe regardless of how far the eventual
 * horizontal jog travels in x. Generated nearest the default ORTHO_ESCAPE
 * first (unaffected common case), then spread across the rest of the band
 * so a placed-hop conflict at one height has somewhere else to go. */
function escapeYCandidates(p, sign, obstacles) {
  var band = bandContaining(freeYBands(obstacles), p.y);
  var edge = sign > 0
    ? (band[1] === Infinity ? p.y + ORTHO_ESCAPE * 4 : band[1])
    : (band[0] === -Infinity ? p.y - ORTHO_ESCAPE * 4 : band[0]);
  var margin = 4;
  var span = Math.abs(edge - p.y);
  if (span <= margin) return [p.y + sign * span * 0.5];
  var maxOffset = span - margin;
  var base = Math.min(ORTHO_ESCAPE, maxOffset);
  var seen = {}, out = [];
  function add(d) {
    d = Math.max(1, Math.min(d, maxOffset));
    var v = Math.round((p.y + sign * d) * 1000) / 1000;
    if (!seen[v]) { seen[v] = true; out.push(v); }
  }
  add(base);
  add(maxOffset / 2);
  for (var k = 1; k < 8; k++) { add(base - k * 8); add(base + k * 8); }
  return out;
}

function escapeYOptions(p, obstacles) {
  return escapeYCandidates(p, 1, obstacles).concat(escapeYCandidates(p, -1, obstacles));
}

/* Last-resort fallback when even a freshly assigned lane still collides
 * with something — a real obstacle, or another hop already placed.
 * `isBlocked(elbow)` covers both, so this search naturally skips a combo
 * that's real-obstacle-free but still lands on a height/column another
 * edge is already using, rather than returning the first real-obstacle-
 * free candidate and leaving the caller to detect and retry a CONFLICT
 * it can't actually fix by only moving the lane column (a height conflict
 * needs a different escape height, not just a wider lane search).
 * Pushes the lane past every obstacle's right edge — nothing extends that
 * far right, so the long vertical run there is guaranteed clear of real
 * obstacles — growing the lane position across retries, with every
 * obstacle-derived safe escape height for each endpoint tried at each.
 * Returns null if every combo within the bounded search is still blocked —
 * the caller, which has visibility into everything placed so far, is
 * responsible for a guaranteed-clear last resort in that case (see
 * escapeEverythingDetour). */
function obstacleSafeDetour(p0, p1, obstacles, isBlocked, minClearX) {
  var baseClearX = Math.max(p0.x, p1.x, minClearX || 0);
  obstacles.forEach(function (o) { baseClearX = Math.max(baseClearX, o.x1); });
  var e0options = escapeYOptions(p0, obstacles);
  var e1options = escapeYOptions(p1, obstacles);
  for (var tries = 0; tries < ORTHO_DETOUR_MAX_TRIES; tries++) {
    var clearX = baseClearX + ORTHO_LANE_MARGIN * (tries + 1);
    for (var i = 0; i < e0options.length; i++) {
      for (var j = 0; j < e1options.length; j++) {
        var e0 = { x: p0.x, y: e0options[i] };
        var e1 = { x: p1.x, y: e1options[j] };
        var elbow = dedupePoints([p0, e0, { x: clearX, y: e0.y }, { x: clearX, y: e1.y }, e1, p1]);
        if (!isBlocked(elbow)) return elbow;
      }
    }
  }
  return null;
}

/* Absolute last resort, used only when obstacleSafeDetour's bounded combo
 * search comes up empty (rare: a genuinely contentious diagram with many
 * hops already claiming nearby territory). Uses the exact same obstacle-
 * derived-safe-escape + far lane column shape — escaping beyond the free
 * y-band surrounding an endpoint would cross into a real obstacle along
 * the way, so growing the escape height past what escapeYOptions already
 * offers can't be how this searches further; only the lane column
 * (`clearX`) may keep growing. Since real obstacles and every previously
 * placed hop both have bounded x, growing clearX far enough always
 * eventually clears everything that currently exists — this just runs
 * that search much further than the bounded obstacleSafeDetour does,
 * guaranteeing termination rather than elegance. */
function escapeEverythingDetour(p0, p1, obstacles, isBlocked, minClearX) {
  var baseClearX = Math.max(p0.x, p1.x, minClearX || 0);
  obstacles.forEach(function (o) { baseClearX = Math.max(baseClearX, o.x1); });
  var e0options = escapeYOptions(p0, obstacles);
  var e1options = escapeYOptions(p1, obstacles);
  var ESCAPE_EVERYTHING_TRIES = 400;
  for (var tries = 0; tries < ESCAPE_EVERYTHING_TRIES; tries++) {
    var clearX = baseClearX + ORTHO_LANE_MARGIN * (tries + 1);
    for (var i = 0; i < e0options.length; i++) {
      for (var j = 0; j < e1options.length; j++) {
        var e0 = { x: p0.x, y: e0options[i] };
        var e1 = { x: p1.x, y: e1options[j] };
        var elbow = dedupePoints([p0, e0, { x: clearX, y: e0.y }, { x: clearX, y: e1.y }, e1, p1]);
        if (!isBlocked(elbow)) return elbow;
      }
    }
  }
  // Should be unreachable given the size of the search above, but never
  // hand back an unverified shape — growing clearX far past anything any
  // previous combo could have claimed is the only remaining lever.
  var hugeClearX = baseClearX + ORTHO_LANE_MARGIN * (ESCAPE_EVERYTHING_TRIES + 1);
  var e0f = { x: p0.x, y: e0options[0] }, e1f = { x: p1.x, y: e1options[0] };
  return dedupePoints([p0, e0f, { x: hugeClearX, y: e0f.y }, { x: hugeClearX, y: e1f.y }, e1f, p1]);
}

/* ── Global hop routing ──
 * Resolves each hop's elbow so it never overlaps a real obstacle OR any
 * previously placed hop's actual geometry (elbowsOverlap) — checked
 * directly against the built shape rather than guessed from a heuristic
 * envelope, since conflicts can come from a shared anchor column, two
 * jogs crossing the same height, or both at once. Tries, in order:
 *   1. For a normal downward hop, every candidate bend height in the
 *      empty inter-layer gap (gapHeightCandidates) — cheapest fix, and
 *      resolves both jog-overlap and vertical-leg-coincidence at once by
 *      simply not sharing a height/range with whatever's already placed.
 *   2. Growing the lane column of the escape->lane->escape shape — for
 *      back/feedback hops (no usable gap), or if no height candidate
 *      cleared a normal hop (rare: e.g. two hops sharing both x AND no
 *      free height left).
 *   3. The far-right obstacle-safe detour, pushed further right if it
 *      still overlaps a placed hop — last resort.
 * Bounded retries throughout; deterministic processing order. */
function routeHopsAvoidingOverlap(hops) {
  var placed = [];
  var elbowOf = {};
  hops.forEach(function (h) {
    var obstacles = h.obstacles || [];
    function blocked(e) {
      return elbowHitsAnyObstacle(e, obstacles) || placed.some(function (pl) { return elbowsOverlap(e, pl); });
    }

    var elbow = null;
    var isGap = h.p1.y - h.p0.y > ORTHO_EPS;
    var sameX = Math.abs(h.p0.x - h.p1.x) < ORTHO_COORD_EPS;
    if (sameX) {
      // No height choice changes a same-column line's geometry, so there's
      // nothing to gain from height search here — either it's already
      // clear, or it needs a real sideways jog (handled below).
      var straight = [h.p0, h.p1];
      if (!blocked(straight)) elbow = straight;
    } else if (isGap) {
      var heights = gapHeightCandidates(h.p0, h.p1);
      for (var hi = 0; hi < heights.length && elbow === null; hi++) {
        var candidate = simpleGapElbow(h.p0, h.p1, heights[hi]);
        if (!blocked(candidate)) elbow = candidate;
      }
    }

    if (elbow === null) {
      // Lane growth alone can't help while the escape segment itself
      // (fixed at the literal anchor x) is what's conflicting — try a
      // zero-escape jog (sideways immediately at the anchor's own y) first,
      // since that's most often enough on its own; only escalate to a real
      // escape distance if even growing the column that way never clears.
      var escapes = [0, ORTHO_ESCAPE];
      for (var ei = 0; ei < escapes.length && elbow === null; ei++) {
        var x = h.p0.x;
        var laneCandidate = laneElbow(h.p0, h.p1, x, escapes[ei]);
        var tries = 0;
        while (blocked(laneCandidate) && tries < ORTHO_LANE_GROWTH_TRIES) {
          x += ORTHO_LANE_MARGIN;
          laneCandidate = laneElbow(h.p0, h.p1, x, escapes[ei]);
          tries++;
        }
        if (!blocked(laneCandidate)) elbow = laneCandidate;
      }
      if (elbow === null) {
        // Column growth alone couldn't clear it (most likely a real
        // obstacle, not just another edge) — fall back to the far-right
        // detour. `blocked` (real obstacles + placed hops) is threaded
        // through so its own internal escape/clearX/up-down search skips
        // any combo that's merely real-obstacle-free but still collides
        // with something already placed, instead of returning that combo
        // and leaving a conflict no amount of outer retrying could fix.
        elbow = obstacleSafeDetour(h.p0, h.p1, obstacles, blocked, x);
      }
      if (elbow === null) {
        // Even that bounded search came up empty (rare, contentious
        // diagram) — search much further out for a lane column, still
        // using only gap-safe escape distances throughout.
        elbow = escapeEverythingDetour(h.p0, h.p1, obstacles, blocked, x);
      }
    }

    placed.push(elbow);
    elbowOf[h.key] = elbow;
  });
  return elbowOf;
}

/* ── Per-edge anchor spreading for grid mode ──
 * Orthogonal routing draws a straight vertical run immediately out of an
 * edge's anchor point, so two edges sharing the exact same anchor (e.g.
 * several edges fanning out from, or converging into, the same real node —
 * the common "hub" case, no group-collapse redirection involved) would
 * otherwise draw on top of each other for that entire run, not just touch
 * at a point the way diverging Bezier curves do. Spreads every edge
 * touching a node — as either its `from` OR its `to`, in one shared pool,
 * not two separate ones — evenly across that node's width, always: a node
 * that's the source of one edge and the destination of another would
 * otherwise default BOTH anchors to dead-center (each alone in its own
 * from-only / to-only group), landing on the same column and forcing the
 * router to route both edges' approach/escape through that single shared
 * column near the node — unlike computeEdgeAnchorOffsets (15_label_layout.js),
 * which only spreads collapsed-group-redirected edges and keeps from/to
 * separate, since curve mode never needed this for ordinary fan-out/fan-in. */
function computeOrthogonalAnchorOffsets(edges) {
  var byNode = {};
  edges.forEach(function (e, i) {
    (byNode[e.from] = byNode[e.from] || []).push({ i: i, role: "from", other: e.to });
    (byNode[e.to] = byNode[e.to] || []).push({ i: i, role: "to", other: e.from });
  });
  var fromFracOf = {}, toFracOf = {};
  Object.keys(byNode).forEach(function (node) {
    var list = byNode[node];
    var target = function (item) { return item.role === "from" ? fromFracOf : toFracOf; };
    if (list.length === 1) { target(list[0])[list[0].i] = 0.5; return; }
    list = list.slice().sort(function (a, b) {
      if (a.other !== b.other) return a.other < b.other ? -1 : 1;
      if (a.role !== b.role) return a.role === "from" ? -1 : 1;
      return a.i - b.i;
    });
    list.forEach(function (item, k) { target(item)[item.i] = (k + 1) / (list.length + 1); });
  });
  return edges.map(function (e, i) {
    return {
      fromFrac: fromFracOf[i] !== undefined ? fromFracOf[i] : 0.5,
      toFrac: toFracOf[i] !== undefined ? toFracOf[i] : 0.5,
    };
  });
}

/* Per-edge entry point (no cross-edge overlap awareness — each hop only
 * avoids its own obstacles, not other edges). Used directly by simple/
 * regression callers; production drawing goes through routeEdgesOrthogonally
 * instead, since it needs every edge's hops visible at once to keep them
 * from overlapping each other. */
function orthogonalSegments(points, obstacles) {
  obstacles = obstacles || [];
  var hops = [];
  for (var i = 0; i < points.length - 1; i++) {
    hops.push({ key: String(i), p0: points[i], p1: points[i + 1], obstacles: obstacles });
  }
  var elbowOf = routeHopsAvoidingOverlap(hops);
  var out = [points[0]];
  hops.forEach(function (h) {
    var elbow = elbowOf[h.key];
    for (var k = 1; k < elbow.length; k++) out.push(elbow[k]);
  });
  return out;
}

/* Multi-edge entry point: routes every edge's full points array at once so
 * overlap-avoidance has visibility across all of them — a single edge's
 * own hops never collide with each other, only with OTHER edges.
 * `pointsList`/`obstaclesList` are parallel arrays, one entry per edge —
 * same shape orthogonalSegments takes per-edge, just batched. */
function routeEdgesOrthogonally(pointsList, obstaclesList) {
  var hops = [];
  pointsList.forEach(function (points, e) {
    var obstacles = obstaclesList[e] || [];
    for (var i = 0; i < points.length - 1; i++) {
      hops.push({ key: e + "_" + i, p0: points[i], p1: points[i + 1], obstacles: obstacles });
    }
  });
  var elbowOf = routeHopsAvoidingOverlap(hops);

  return pointsList.map(function (points, e) {
    var out = [points[0]];
    for (var i = 0; i < points.length - 1; i++) {
      var elbow = elbowOf[e + "_" + i];
      for (var k = 1; k < elbow.length; k++) out.push(elbow[k]);
    }
    return out;
  });
}

function orthogonalPathD(bendPoints) {
  if (!bendPoints.length) return "";
  var d = "M" + bendPoints[0].x.toFixed(1) + "," + bendPoints[0].y.toFixed(1);
  for (var i = 1; i < bendPoints.length; i++) {
    d += " L" + bendPoints[i].x.toFixed(1) + "," + bendPoints[i].y.toFixed(1);
  }
  return d;
}

/* Obstacle rects for routing a given edge: every other position (real
 * node, collapsed-group placeholder, or another edge's via lane) except
 * the ids this edge actually terminates at or passes through itself. */
function obstaclesFor(positions, excludeIds) {
  var exclude = {};
  (excludeIds || []).forEach(function (id) { exclude[id] = true; });
  var rects = [];
  Object.keys(positions).forEach(function (id) {
    if (exclude[id]) return;
    var p = positions[id];
    rects.push({ x0: p.x, y0: p.y, x1: p.x + p.w, y1: p.y + p.h });
  });
  return rects;
}
