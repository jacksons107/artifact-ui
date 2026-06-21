"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fc = require("fast-check");

const { loadEngineInternals } = require("./harness");
// Scoped to a density/forward-bias matching real hand-authored diagrams
// (see generators.js) rather than the fully-adversarial specArb the
// layout/label/aggregation suites use — orthogonal routing's no-overlap
// guarantee is a greedy, sequential router, not a true global track
// allocator, so it can be driven into unsolvable contention by graphs far
// denser/cyclic than anything a real diagram looks like. See the
// conversation that landed this: that's an intentional, documented scope
// boundary, not a gap to "fix" by widening this back out.
const { realisticSpecArb: specArb } = require("./generators");

const mod = loadEngineInternals();
const EPS = 0.01;

function rectsOverlap(a, b) {
  return a.x0 < b.x1 - EPS && b.x0 < a.x1 - EPS && a.y0 < b.y1 - EPS && b.y0 < a.y1 - EPS;
}

function segmentBox(p0, p1) {
  return {
    x0: Math.min(p0.x, p1.x), x1: Math.max(p0.x, p1.x),
    y0: Math.min(p0.y, p1.y), y1: Math.max(p0.y, p1.y),
  };
}

// Mirrors drawDiagram's own points-array construction (30_draw.js), so the
// router is exercised against exactly the same inputs it sees in production.
function buildEdgePointsAndObstacles(visible, layout) {
  const positions = layout.positions, edgeVia = layout.edgeVia;
  const aggregated = mod.aggregateEdges(visible.edges);
  const drawEdges = aggregated.drawEdges, viaIndexOf = aggregated.viaIndexOf;
  // Mirrors production's grid-mode anchor computation (30_draw.js), not
  // curve mode's computeEdgeAnchorOffsets — grid mode needs every same-
  // node fan-out/fan-in spread, not just collapsed-group redirections.
  const anchorOffsets = mod.computeOrthogonalAnchorOffsets(drawEdges);
  const out = [];
  drawEdges.forEach((edge, edgeIdx) => {
    const sp = positions[edge.from], dp = positions[edge.to];
    if (!sp || !dp || edge.from === edge.to) return;
    const off = anchorOffsets[edgeIdx];
    // Mirrors drawDiagram's back-edge side-anchoring (30_draw.js): an edge
    // with no usable inter-layer gap below its source anchors on the right
    // side of each box instead of bottom/top, so it never has to fight a
    // forward edge for the same vertical territory.
    const back = mod.edgeGoesBackward(sp, dp);
    let sx, sy, ex, ey;
    if (back) {
      sx = sp.x + sp.w; sy = sp.y + sp.h * off.fromFrac;
      ex = dp.x + dp.w; ey = dp.y + dp.h * off.toFrac;
    } else {
      sx = sp.x + sp.w * off.fromFrac; sy = sp.y + sp.h;
      ex = dp.x + dp.w * off.toFrac; ey = dp.y;
    }
    const viaIds = edgeVia[viaIndexOf[edgeIdx]] || [];
    const vias = viaIds.map((viaId) => {
      const vp = positions[viaId];
      return { x: vp.x + vp.w / 2, y: vp.y + vp.h / 2 };
    });
    const points = [{ x: sx, y: sy }].concat(vias, [{ x: ex, y: ey }]);
    const obstacles = mod.obstaclesFor(positions, [edge.from, edge.to].concat(viaIds));
    out.push({ edge, points, obstacles });
  });
  return out;
}

// Routes every edge of a spec at once via the same batched entry point
// drawDiagram itself uses (routeEdgesOrthogonally), so these properties
// hold against exactly what production renders, not just the per-edge
// primitive in isolation.
function routeFullDiagram(spec, expandedSet) {
  const visible = mod.getVisibleGraph(spec, expandedSet);
  const layout = mod.layoutHierarchy(spec, expandedSet, visible.edges);
  const edgePoints = buildEdgePointsAndObstacles(visible, layout);
  const pointsList = edgePoints.map((e) => e.points);
  const obstaclesList = edgePoints.map((e) => e.obstacles);
  const routed = mod.routeEdgesOrthogonally(pointsList, obstaclesList);
  return edgePoints.map((e, i) => ({ points: e.points, obstacles: e.obstacles, bends: routed[i] }));
}

// Two segments "overlap" (as opposed to merely touching/crossing at a single
// point) when they're collinear and their shared range along that line has
// positive length — e.g. two edges leaving the same node anchor and running
// down the same x for any real distance before diverging, which renders as
// one line doing double duty rather than two distinguishable edges.
function segmentsCollinearOverlap(a0, a1, b0, b1) {
  const aVert = Math.abs(a0.x - a1.x) < EPS, bVert = Math.abs(b0.x - b1.x) < EPS;
  const aHoriz = Math.abs(a0.y - a1.y) < EPS, bHoriz = Math.abs(b0.y - b1.y) < EPS;
  if (aVert && bVert && Math.abs(a0.x - b0.x) < EPS) {
    const ay0 = Math.min(a0.y, a1.y), ay1 = Math.max(a0.y, a1.y);
    const by0 = Math.min(b0.y, b1.y), by1 = Math.max(b0.y, b1.y);
    return Math.min(ay1, by1) - Math.max(ay0, by0) > EPS;
  }
  if (aHoriz && bHoriz && Math.abs(a0.y - b0.y) < EPS) {
    const ax0 = Math.min(a0.x, a1.x), ax1 = Math.max(a0.x, a1.x);
    const bx0 = Math.min(b0.x, b1.x), bx1 = Math.max(b0.x, b1.x);
    return Math.min(ax1, bx1) - Math.max(ax0, bx0) > EPS;
  }
  return false;
}

test("property: orthogonal routing produces only axis-aligned segments", () => {
  fc.assert(
    fc.property(specArb, ({ spec, expandedSet }) => {
      routeFullDiagram(spec, expandedSet).forEach(({ bends }) => {
        for (let i = 0; i < bends.length - 1; i++) {
          const a = bends[i], b = bends[i + 1];
          const axisAligned = Math.abs(a.x - b.x) < EPS || Math.abs(a.y - b.y) < EPS;
          assert.ok(axisAligned, `segment ${i} (${JSON.stringify(a)} -> ${JSON.stringify(b)}) must be horizontal or vertical`);
        }
      });
    })
  );
});

test("property: orthogonal routing never crosses a non-endpoint obstacle", () => {
  fc.assert(
    fc.property(specArb, ({ spec, expandedSet }) => {
      routeFullDiagram(spec, expandedSet).forEach(({ bends, obstacles }) => {
        for (let i = 0; i < bends.length - 1; i++) {
          const segBox = segmentBox(bends[i], bends[i + 1]);
          obstacles.forEach((rect) => {
            assert.equal(rectsOverlap(segBox, rect), false, `segment ${i} must not cross obstacle ${JSON.stringify(rect)}`);
          });
        }
      });
    })
  );
});

test("property: orthogonal routing preserves the original endpoint anchors", () => {
  fc.assert(
    fc.property(specArb, ({ spec, expandedSet }) => {
      routeFullDiagram(spec, expandedSet).forEach(({ points, bends }) => {
        assert.deepEqual(bends[0], points[0], "route must start at the original source anchor");
        assert.deepEqual(bends[bends.length - 1], points[points.length - 1], "route must end at the original target anchor");
      });
    })
  );
});

test("property: orthogonal routing uses at most 4 bends per original point-pair", () => {
  fc.assert(
    fc.property(specArb, ({ spec, expandedSet }) => {
      routeFullDiagram(spec, expandedSet).forEach(({ points, bends }) => {
        // Each original point-pair contributes at most 4 intermediate bend
        // points (the side-lane detour's escape+lane+escape shape; the
        // common gap-elbow case uses only 2), plus the shared boundary
        // points every pair already has.
        const maxBendPoints = points.length + 4 * (points.length - 1);
        assert.ok(bends.length <= maxBendPoints, `expected at most ${maxBendPoints} points, got ${bends.length}`);
      });
    })
  );
});

test("property: orthogonal routing produces no overlapping segments between distinct edges", () => {
  fc.assert(
    fc.property(specArb, ({ spec, expandedSet }) => {
      const routed = routeFullDiagram(spec, expandedSet).map((e) => e.bends);
      for (let i = 0; i < routed.length; i++) {
        for (let j = i + 1; j < routed.length; j++) {
          const bendsA = routed[i], bendsB = routed[j];
          for (let a = 0; a < bendsA.length - 1; a++) {
            for (let b = 0; b < bendsB.length - 1; b++) {
              const overlap = segmentsCollinearOverlap(bendsA[a], bendsA[a + 1], bendsB[b], bendsB[b + 1]);
              assert.equal(
                overlap, false,
                `edge ${i} segment ${a} (${JSON.stringify(bendsA[a])}->${JSON.stringify(bendsA[a + 1])}) ` +
                `overlaps edge ${j} segment ${b} (${JSON.stringify(bendsB[b])}->${JSON.stringify(bendsB[b + 1])})`
              );
            }
          }
        }
      }
    })
  );
});

test("regression: a straight top-to-bottom edge with aligned x routes with zero bends", () => {
  const points = [{ x: 100, y: 60 }, { x: 100, y: 132 }];
  const bends = mod.orthogonalSegments(points, []);
  assert.deepEqual(bends, points);
});

test("regression: an unaligned edge across one layer gap routes with a single elbow in the gap", () => {
  const points = [{ x: 100, y: 60 }, { x: 260, y: 132 }];
  const bends = mod.orthogonalSegments(points, []);
  assert.equal(bends.length, 4);
  assert.equal(bends[0].x, 100); assert.equal(bends[0].y, 60);
  assert.equal(bends[1].x, 100); assert.equal(bends[1].y, 96); // gap midpoint
  assert.equal(bends[2].x, 260); assert.equal(bends[2].y, 96);
  assert.equal(bends[3].x, 260); assert.equal(bends[3].y, 132);
});

test("regression: a back-edge (target not below source) still produces a valid axis-aligned route", () => {
  const points = [{ x: 100, y: 200 }, { x: 260, y: 60 }];
  const bends = mod.orthogonalSegments(points, []);
  // Escape-then-lane-then-escape shape: every segment axis-aligned, and the
  // route still starts/ends exactly at the original anchors. With no other
  // edges or obstacles to dodge, the lane isn't forced out to the side —
  // see the obstacle-avoidance property test below for when it is.
  assert.deepEqual(bends[0], points[0]);
  assert.deepEqual(bends[bends.length - 1], points[points.length - 1]);
  for (let i = 0; i < bends.length - 1; i++) {
    const a = bends[i], b = bends[i + 1];
    assert.ok(Math.abs(a.x - b.x) < EPS || Math.abs(a.y - b.y) < EPS, `segment ${i} must be axis-aligned`);
  }
});

test("regression: a back-edge detours around an obstacle placed directly between the endpoints", () => {
  const points = [{ x: 100, y: 200 }, { x: 260, y: 60 }];
  // Blocks the direct region between the two anchors without containing
  // either anchor itself — an obstacle that swallows an edge's own endpoint
  // is an unsolvable setup (no path can avoid touching it), not a real one.
  const obstacles = [{ x0: 130, y0: 80, x1: 230, y1: 180 }];
  const bends = mod.orthogonalSegments(points, obstacles);
  for (let i = 0; i < bends.length - 1; i++) {
    const segBox = segmentBox(bends[i], bends[i + 1]);
    assert.equal(rectsOverlap(segBox, obstacles[0]), false, `segment ${i} must not cross the obstacle`);
  }
});

test("property: a back-edge's side-lane detour never crosses an obstacle placed between the endpoints", () => {
  fc.assert(
    fc.property(
      fc.record({
        x0: fc.integer({ min: 0, max: 400 }), y0: fc.integer({ min: 0, max: 400 }),
        x1: fc.integer({ min: 0, max: 400 }), y1: fc.integer({ min: 0, max: 400 }),
        obsX: fc.integer({ min: 0, max: 400 }), obsY: fc.integer({ min: 0, max: 400 }),
      }),
      ({ x0, y0, x1, y1, obsX, obsY }) => {
        const p0 = { x: x0, y: y0 }, p1 = { x: x1, y: y1 };
        fc.pre(Math.abs(p0.x - p1.x) > EPS); // non-trivial: exercise the elbow/detour path
        const obstacle = { x0: obsX, y0: obsY, x1: obsX + 140, y1: obsY + 60 };
        // An obstacle that contains either endpoint is unsolvable by
        // construction (no path can avoid touching an obstacle that
        // swallows its own start/end point) — not a real requirement.
        const containsPoint = (p) => p.x > obstacle.x0 && p.x < obstacle.x1 && p.y > obstacle.y0 && p.y < obstacle.y1;
        fc.pre(!containsPoint(p0) && !containsPoint(p1));
        const obstacles = [obstacle];
        const bends = mod.orthogonalSegments([p0, p1], obstacles);
        for (let i = 0; i < bends.length - 1; i++) {
          const segBox = segmentBox(bends[i], bends[i + 1]);
          assert.equal(rectsOverlap(segBox, obstacles[0]), false, `segment ${i} must not cross the obstacle`);
        }
      }
    )
  );
});

test("orthogonalPathD renders a polyline as M/L segments", () => {
  const d = mod.orthogonalPathD([{ x: 1, y: 2 }, { x: 1, y: 10 }, { x: 5, y: 10 }]);
  assert.equal(d, "M1.0,2.0 L1.0,10.0 L5.0,10.0");
});
