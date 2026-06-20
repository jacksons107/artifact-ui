"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fc = require("fast-check");

const { loadEngineInternals } = require("./harness");

const mod = loadEngineInternals();

function overlaps(a, b, eps = 0.01) {
  return a.x0 < b.x1 - eps && b.x0 < a.x1 - eps && a.y0 < b.y1 - eps && b.y0 < a.y1 - eps;
}
function rectOf(box) {
  return { x0: box.x, y0: box.y, x1: box.x + box.w, y1: box.y + box.h };
}

// Candidates clustered within a small area on purpose, so the generator
// reliably produces lots of overlapping input (the case that matters) and
// not just already-disjoint boxes.
const candidateArb = fc.array(
  fc.record({
    x: fc.integer({ min: 0, max: 60 }),
    y: fc.integer({ min: 0, max: 60 }),
    labelLen: fc.integer({ min: 1, max: 20 }),
  }),
  { minLength: 1, maxLength: 15 }
).map((items, idx) =>
  items.map((it, i) => ({ key: i, x: it.x, y: it.y, w: it.labelLen * 5.8 + 10, h: 14 }))
);

test("property: label boxes never pairwise overlap, for any candidate set", () => {
  fc.assert(
    fc.property(candidateArb, (candidates) => {
      const boxes = mod.computeEdgeLabelBoxes(candidates);
      const keys = Object.keys(boxes);
      for (let i = 0; i < keys.length; i++) {
        for (let j = i + 1; j < keys.length; j++) {
          assert.equal(
            overlaps(rectOf(boxes[keys[i]]), rectOf(boxes[keys[j]])),
            false,
            `labels ${keys[i]} and ${keys[j]} must not overlap`
          );
        }
      }
    })
  );
});

test("property: every candidate key is present exactly once, none dropped or duplicated", () => {
  fc.assert(
    fc.property(candidateArb, (candidates) => {
      const boxes = mod.computeEdgeLabelBoxes(candidates);
      const expectedKeys = candidates.map((c) => String(c.key)).sort();
      const actualKeys = Object.keys(boxes).sort();
      assert.deepEqual(actualKeys, expectedKeys);
    })
  );
});

test("property: vertical displacement is bounded by the total height of all candidates", () => {
  fc.assert(
    fc.property(candidateArb, (candidates) => {
      const boxes = mod.computeEdgeLabelBoxes(candidates);
      const totalHeight = candidates.reduce((s, c) => s + c.h, 0) + candidates.length * 2 /* gap */;
      candidates.forEach((c) => {
        const box = boxes[c.key];
        const displacement = box.y - c.y;
        assert.ok(displacement >= 0, "boxes only ever move down, never up");
        assert.ok(displacement <= totalHeight, `displacement ${displacement} must stay bounded (<= ${totalHeight})`);
      });
    })
  );
});

test("regression: 4 candidates at the identical point end up stacked with no overlap", () => {
  const candidates = [0, 1, 2, 3].map((i) => ({ key: i, x: 100, y: 100, w: 40, h: 14 }));
  const boxes = mod.computeEdgeLabelBoxes(candidates);
  const rects = Object.values(boxes).map(rectOf);
  for (let i = 0; i < rects.length; i++) {
    for (let j = i + 1; j < rects.length; j++) {
      assert.equal(overlaps(rects[i], rects[j]), false);
    }
  }
  // deterministic: same input always produces the same output
  const boxes2 = mod.computeEdgeLabelBoxes(candidates);
  assert.deepEqual(boxes, boxes2);
});

// End-to-end: a real spec with several edges spanning the same pair of
// layers (so their label midpoints land in the same row), run through the
// actual layout + the same midpoint formula drawDiagram uses, fed into
// computeEdgeLabelBoxes — catches integration mistakes a pure unit test
// of computeEdgeLabelBoxes alone wouldn't.
test("regression: real spec with several same-band labeled edges produces no overlapping labels", () => {
  const spec = {
    nodes: [
      { id: "src", label: "Source" },
      { id: "a", label: "A" },
      { id: "b", label: "B" },
      { id: "c", label: "C" },
    ],
    groups: [],
    edges: [
      { from: "src", to: "a", label: "handle request" },
      { from: "src", to: "b", label: "handle request" },
      { from: "src", to: "c", label: "handle request" },
    ],
  };
  const expandedSet = new Set();
  const visible = mod.getVisibleGraph(spec, expandedSet);
  const layout = mod.layoutHierarchy(spec, expandedSet, visible.edges);

  const candidates = [];
  visible.edges.forEach((edge, edgeIdx) => {
    const sp = layout.positions[edge.from], dp = layout.positions[edge.to];
    if (!sp || !dp || edge.from === edge.to || !edge.label) return;
    const mx = (sp.x + sp.w / 2 + dp.x + dp.w / 2) / 2;
    const my = (sp.y + sp.h + dp.y) / 2;
    const lw = edge.label.length * 5.8 + 10;
    candidates.push({ key: edgeIdx, x: mx - lw / 2, y: my - 9, w: lw, h: 14 });
  });

  const boxes = mod.computeEdgeLabelBoxes(candidates);
  const rects = Object.values(boxes).map(rectOf);
  for (let i = 0; i < rects.length; i++) {
    for (let j = i + 1; j < rects.length; j++) {
      assert.equal(overlaps(rects[i], rects[j]), false, "real-spec edge labels must not overlap");
    }
  }
});
