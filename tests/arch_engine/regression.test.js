"use strict";
const fs = require("fs");
const path = require("path");
const test = require("node:test");
const assert = require("node:assert/strict");

const { loadEngineInternals } = require("./harness");

const mod = loadEngineInternals();

const EXAMPLES_DIR = path.join(__dirname, "..", "..", "system_spec", "examples");

function rectOf(id, positions, groupBoxes) {
  if (groupBoxes[id]) {
    const b = groupBoxes[id];
    return { x0: b.x0, y0: b.y0, x1: b.x1, y1: b.y1 };
  }
  const p = positions[id];
  return { x0: p.x, y0: p.y, x1: p.x + p.w, y1: p.y + p.h };
}
function overlaps(r1, r2, eps = 0.01) {
  return r1.x0 < r2.x1 - eps && r2.x0 < r1.x1 - eps && r1.y0 < r2.y1 - eps && r2.y0 < r1.y1 - eps;
}
function ancestorsOf(id, parentOf) {
  const out = [];
  let cur = parentOf[id];
  while (cur !== undefined) { out.push(cur); cur = parentOf[cur]; }
  return out;
}
function related(a, b, parentOf) {
  if (a === b) return true;
  return ancestorsOf(a, parentOf).includes(b) || ancestorsOf(b, parentOf).includes(a);
}

function assertNoIllegitimateOverlap(spec, expandedSet) {
  const visible = mod.getVisibleGraph(spec, expandedSet);
  const layout = mod.layoutHierarchy(spec, expandedSet, visible.edges);
  const parentOf = mod.buildParentMap(spec.groups);
  const ids = [...new Set([
    ...Object.keys(layout.positions).filter((id) => !id.startsWith("__via_")),
    ...Object.keys(layout.groupBoxes),
  ])];
  for (let i = 0; i < ids.length; i++) {
    for (let j = i + 1; j < ids.length; j++) {
      if (related(ids[i], ids[j], parentOf)) continue;
      assert.equal(
        overlaps(rectOf(ids[i], layout.positions, layout.groupBoxes), rectOf(ids[j], layout.positions, layout.groupBoxes)),
        false,
        `${ids[i]} and ${ids[j]} must not overlap`
      );
    }
  }
  return layout;
}

// The literal AmEx shape that produced all three bugs fixed this session:
// a feedback edge forming a cycle, a sibling group ending up inside the
// expanded group's box, and an external node landing beside (rather than
// below) an internal member.
test("regression: AmEx cell_a/cell_b/external shape", () => {
  const spec = {
    nodes: [
      { id: "client", label: "Client" },
      { id: "external", label: "External" },
      { id: "a1", label: "A1" }, { id: "a2", label: "A2" }, { id: "a3", label: "A3" },
      { id: "b1", label: "B1" },
    ],
    groups: [
      { id: "cell_a", label: "Cell A", members: ["a1", "a2", "a3"] },
      { id: "cell_b", label: "Cell B", members: ["b1"] },
    ],
    edges: [
      { from: "client", to: "cell_a" },
      { from: "client", to: "cell_b" },
      { from: "a1", to: "a2" },
      { from: "a2", to: "a3" },
      { from: "a3", to: "external" },
      { from: "a1", to: "client" }, // feedback edge — closes a cycle with client -> cell_a -> a1
    ],
  };
  const expandedSet = new Set(["cell_a"]);
  const layout = assertNoIllegitimateOverlap(spec, expandedSet);

  const box = layout.groupBoxes["cell_a"];
  assert.ok(box);

  const cellB = layout.positions["cell_b"];
  const insideBox = cellB.x >= box.x0 && cellB.x + cellB.w <= box.x1 && cellB.y >= box.y0 && cellB.y + cellB.h <= box.y1;
  assert.equal(insideBox, false, "cell_b must not be contained inside cell_a's box");

  const ext = layout.positions["external"];
  assert.ok(ext.y >= box.y1, "external must be below the entire expanded box, not beside one member");
});

test("regression: 3-node cycle breaks at the closing edge, layers a=0,b=1,c=2", () => {
  const nodeIds = ["a", "b", "c"];
  const edges = [{ from: "a", to: "b" }, { from: "b", to: "c" }, { from: "c", to: "a" }];
  const nodeIdSet = { a: true, b: true, c: true };
  const back = mod.findBackEdgeSet(nodeIds, edges, nodeIdSet);
  assert.equal(!!back[2], true);

  const flat = mod.layoutFlat(nodeIds, () => ({ w: 100, h: 60 }), edges);
  assert.ok(flat.positions.a.y < flat.positions.b.y);
  assert.ok(flat.positions.b.y < flat.positions.c.y);
});

test("regression: self-loop doesn't crash and isn't flagged as a back edge", () => {
  const nodeIds = ["a"];
  const edges = [{ from: "a", to: "a" }];
  const back = mod.findBackEdgeSet(nodeIds, edges, { a: true });
  assert.equal(Object.keys(back).length, 0);
  const flat = mod.layoutFlat(nodeIds, () => ({ w: 100, h: 60 }), edges);
  assert.ok(Number.isFinite(flat.positions.a.x));
});

// All 7 bundled examples (read from the same JSON files system_spec_examples.py
// loads from — one source of truth, see CLAUDE.md), expanded one group at a
// time, asserting no thrown errors and no illegitimate overlap.
const exampleFiles = fs.readdirSync(EXAMPLES_DIR).filter((f) => f.endsWith(".json"));

exampleFiles.forEach((file) => {
  test(`regression: bundled example "${file}" expands cleanly with no overlap`, () => {
    const spec = JSON.parse(fs.readFileSync(path.join(EXAMPLES_DIR, file), "utf8"));
    const allGroupIds = (spec.groups || []).map((g) => g.id);

    // collapsed
    assertNoIllegitimateOverlap(spec, new Set());

    // every group expanded one at a time
    allGroupIds.forEach((gid) => {
      assertNoIllegitimateOverlap(spec, new Set([gid]));
    });

    // fully expanded
    assertNoIllegitimateOverlap(spec, new Set(allGroupIds));
  });
});
