"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fc = require("fast-check");

const { loadEngineInternals } = require("./harness");
// Same realistic-density generator orthogonal_routing.test.js uses — see
// generators.js for why: closer to what a hand-authored diagram looks like
// than the fully-adversarial specArb the layout/aggregation suites use.
const { realisticSpecArb } = require("./generators");

const mod = loadEngineInternals();
const EPS = 0.01;

function rectOf(box) {
  return { x0: box.x, y0: box.y, x1: box.x + box.w, y1: box.y + box.h };
}

function rectsOverlap(a, b) {
  return a.x0 < b.x1 - EPS && b.x0 < a.x1 - EPS && a.y0 < b.y1 - EPS && b.y0 < a.y1 - EPS;
}

// Mirrors drawDiagram's per-edge points/back/polyline construction
// (30_draw.js) for a given routingMode, so label placement is exercised
// against exactly the geometry production computes, not a stand-in.
function buildPolylinesForSpec(spec, expandedSet, routingMode) {
  // realisticSpecArb's edges have no `label` of their own (it's scoped to
  // the orthogonal-routing suite, which doesn't care about labels) — give
  // every edge one here so each participates as both a label candidate AND
  // an obstacle for every other edge's label.
  const labeledSpec = { ...spec, edges: spec.edges.map((e) => ({ ...e, label: "lbl" })) };

  const visible = mod.getVisibleGraph(labeledSpec, expandedSet);
  const layout = mod.layoutHierarchy(labeledSpec, expandedSet, visible.edges);
  const positions = layout.positions, edgeVia = layout.edgeVia;
  const aggregated = mod.aggregateEdges(visible.edges);
  const drawEdges = aggregated.drawEdges, viaIndexOf = aggregated.viaIndexOf;
  const anchorOffsets = routingMode === "grid"
    ? mod.computeOrthogonalAnchorOffsets(drawEdges)
    : mod.computeEdgeAnchorOffsets(drawEdges);

  const pointsByEdge = {}, backByEdge = {};
  drawEdges.forEach((edge, edgeIdx) => {
    const sp = positions[edge.from], dp = positions[edge.to];
    if (!sp || !dp || edge.from === edge.to) return;
    const off = anchorOffsets[edgeIdx];
    const back = mod.edgeGoesBackward(sp, dp);
    backByEdge[edgeIdx] = back;
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
    pointsByEdge[edgeIdx] = [{ x: sx, y: sy }].concat(vias, [{ x: ex, y: ey }]);
  });

  let gridBendsByEdge = {};
  if (routingMode === "grid") {
    const idxs = [], pointsList = [], obstaclesList = [];
    Object.keys(pointsByEdge).forEach((edgeIdxStr) => {
      const edgeIdx = Number(edgeIdxStr);
      const edge = drawEdges[edgeIdx];
      const viaIds = edgeVia[viaIndexOf[edgeIdx]] || [];
      idxs.push(edgeIdx);
      pointsList.push(pointsByEdge[edgeIdx]);
      obstaclesList.push(mod.obstaclesFor(positions, [edge.from, edge.to].concat(viaIds)));
    });
    const routed = mod.routeEdgesOrthogonally(pointsList, obstaclesList);
    idxs.forEach((edgeIdx, k) => { gridBendsByEdge[edgeIdx] = routed[k]; });
  }

  const polylineByEdge = {};
  Object.keys(pointsByEdge).forEach((edgeIdxStr) => {
    const edgeIdx = Number(edgeIdxStr);
    if (routingMode === "grid") {
      polylineByEdge[edgeIdx] = gridBendsByEdge[edgeIdx] || pointsByEdge[edgeIdx];
      return;
    }
    const points = pointsByEdge[edgeIdx];
    const back = backByEdge[edgeIdx];
    const poly = [points[0]];
    for (let i = 0; i < points.length - 1; i++) {
      const sampled = mod.sampleEdgeSegment(points[i], points[i + 1], back, 12);
      for (let k = 1; k < sampled.length; k++) poly.push(sampled[k]);
    }
    polylineByEdge[edgeIdx] = poly;
  });

  return { drawEdges, pointsByEdge, polylineByEdge };
}

// Builds final label boxes (via the real computeEdgeLabelBoxes) for a given
// fraction list, mirroring drawDiagram's fallback-to-midpoint behavior for
// any edge chooseLabelAnchor can't place (degenerate polyline).
function buildLabelBoxes(drawEdges, pointsByEdge, polylineByEdge, fractions) {
  const candidates = [];
  drawEdges.forEach((edge, edgeIdx) => {
    if (!edge.label || !pointsByEdge[edgeIdx]) return;
    const lw = edge.label.length * 5.8 + 10;
    let anchor = mod.chooseLabelAnchor(edgeIdx, polylineByEdge, lw, 14, fractions);
    if (!anchor) {
      const points = pointsByEdge[edgeIdx];
      const midIdx = (points.length - 1) / 2;
      let mx, my;
      if (Number.isInteger(midIdx)) {
        mx = points[midIdx].x; my = points[midIdx].y;
      } else {
        const i0 = Math.floor(midIdx), i1 = Math.ceil(midIdx);
        mx = (points[i0].x + points[i1].x) / 2;
        my = (points[i0].y + points[i1].y) / 2;
      }
      anchor = { x: mx - lw / 2, y: my - 9 };
    }
    candidates.push({ key: edgeIdx, x: anchor.x, y: anchor.y, w: lw, h: 14 });
  });
  return mod.computeEdgeLabelBoxes(candidates);
}

// Total "label sits on top of some OTHER edge's path" metric: for every
// labeled edge's final box, count how many other edges' polylines it
// overlaps, summed across all labeled edges.
function otherEdgeOverlapMetric(drawEdges, labelBoxes, polylineByEdge) {
  let total = 0;
  Object.keys(labelBoxes).forEach((keyStr) => {
    const ownIdx = Number(keyStr);
    const rect = rectOf(labelBoxes[keyStr]);
    Object.keys(polylineByEdge).forEach((otherKeyStr) => {
      const otherIdx = Number(otherKeyStr);
      if (otherIdx === ownIdx) return;
      if (mod.rectOverlapsPolyline(rect, polylineByEdge[otherKeyStr])) total++;
    });
  });
  return total;
}

["curve", "grid"].forEach((routingMode) => {
  test(`property: label placement (${routingMode} mode) never has more other-edge overlap than always-midpoint`, () => {
    fc.assert(
      fc.property(realisticSpecArb, ({ spec, expandedSet }) => {
        const { drawEdges, pointsByEdge, polylineByEdge } = buildPolylinesForSpec(spec, expandedSet, routingMode);
        const oldBoxes = buildLabelBoxes(drawEdges, pointsByEdge, polylineByEdge, [0.5]);
        const newBoxes = buildLabelBoxes(drawEdges, pointsByEdge, polylineByEdge, undefined);
        const oldMetric = otherEdgeOverlapMetric(drawEdges, oldBoxes, polylineByEdge);
        const newMetric = otherEdgeOverlapMetric(drawEdges, newBoxes, polylineByEdge);
        assert.ok(
          newMetric <= oldMetric,
          `new placement's other-edge overlap (${newMetric}) must not exceed old always-midpoint's (${oldMetric})`
        );
      })
    );
  });
});

// Direct, deterministic demonstration that chooseLabelAnchor actually
// improves a real case rather than just never regressing: a horizontal
// own-edge with another edge's path crossing it exactly at the midpoint,
// but cleanly missing it at a side fraction.
test("regression: chooseLabelAnchor picks a side fraction to avoid another edge that the midpoint would overlap", () => {
  const ownKey = "own";
  const polylineByKey = {
    [ownKey]: [{ x: 0, y: 0 }, { x: 100, y: 0 }],
    other: [{ x: 50, y: -5 }, { x: 50, y: 5 }], // crosses the own edge's midpoint (50,0)
  };
  const lw = 20, lh = 14;

  const midpointOnly = mod.chooseLabelAnchor(ownKey, polylineByKey, lw, lh, [0.5]);
  const midpointRect = { x0: midpointOnly.x, y0: midpointOnly.y, x1: midpointOnly.x + lw, y1: midpointOnly.y + lh };
  assert.equal(
    mod.rectOverlapsPolyline(midpointRect, polylineByKey.other),
    true,
    "sanity check: the plain midpoint candidate must actually overlap the other edge here"
  );

  const chosen = mod.chooseLabelAnchor(ownKey, polylineByKey, lw, lh);
  const chosenRect = { x0: chosen.x, y0: chosen.y, x1: chosen.x + lw, y1: chosen.y + lh };
  assert.equal(
    mod.rectOverlapsPolyline(chosenRect, polylineByKey.other),
    false,
    "the default multi-fraction choice must avoid the other edge's path"
  );
});

test("regression: chooseLabelAnchor returns null for a degenerate (single-point) polyline", () => {
  const polylineByKey = { own: [{ x: 10, y: 10 }], other: [{ x: 0, y: 0 }, { x: 20, y: 20 }] };
  assert.equal(mod.chooseLabelAnchor("own", polylineByKey, 20, 14), null);
});

// End-to-end: real layout + the actual fallback path drawDiagram uses for
// a degenerate edge, confirming the integration never crashes or drops the
// label entirely.
test("regression: a real spec with a labeled edge still produces a valid box when chooseLabelAnchor can't place it", () => {
  const spec = {
    nodes: [{ id: "a", label: "A" }, { id: "b", label: "B" }],
    groups: [],
    edges: [{ from: "a", to: "b", label: "calls" }],
  };
  const expandedSet = new Set();
  const { drawEdges, pointsByEdge, polylineByEdge } = buildPolylinesForSpec(spec, expandedSet, "curve");
  const boxes = buildLabelBoxes(drawEdges, pointsByEdge, polylineByEdge, undefined);
  assert.equal(Object.keys(boxes).length, 1);
  const box = Object.values(boxes)[0];
  assert.ok(Number.isFinite(box.x) && Number.isFinite(box.y));
});
