"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fc = require("fast-check");

const { loadEngineInternals } = require("./harness");
const { graphArb, specArb } = require("./generators");

const mod = loadEngineInternals();

// Independent cycle detector — deliberately NOT reusing findBackEdgeSet's
// own DFS, so property 1 below can't pass just because both share a bug.
function hasCycle(nodeIds, edges) {
  const adj = {};
  nodeIds.forEach((id) => { adj[id] = []; });
  edges.forEach((e) => { if (e.from !== e.to) adj[e.from].push(e.to); });
  const WHITE = 0, GRAY = 1, BLACK = 2;
  const color = {};
  nodeIds.forEach((id) => { color[id] = WHITE; });
  let found = false;
  function dfs(id) {
    color[id] = GRAY;
    for (const next of adj[id]) {
      if (color[next] === GRAY) { found = true; return; }
      if (color[next] === WHITE) dfs(next);
      if (found) return;
    }
    color[id] = BLACK;
  }
  nodeIds.forEach((id) => { if (color[id] === WHITE && !found) dfs(id); });
  return found;
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
function contains(outer, inner, eps = 0.01) {
  return inner.x0 >= outer.x0 - eps && inner.x1 <= outer.x1 + eps &&
         inner.y0 >= outer.y0 - eps && inner.y1 <= outer.y1 + eps;
}

test("property: cycle removal yields a true DAG", () => {
  fc.assert(
    fc.property(graphArb, ({ nodeIds, edges }) => {
      const nodeIdSet = {};
      nodeIds.forEach((id) => { nodeIdSet[id] = true; });
      const back = mod.findBackEdgeSet(nodeIds, edges, nodeIdSet);
      const remaining = edges.filter((_, i) => !back[i]);
      assert.equal(hasCycle(nodeIds, remaining), false);
    })
  );
});

test("property: layering terminates with finite, bounded coordinates", () => {
  fc.assert(
    fc.property(graphArb, ({ nodeIds, edges }) => {
      const size = { w: 100, h: 60 };
      const flat = mod.layoutFlat(nodeIds, () => size, edges);
      const maxLayers = nodeIds.length + 1;
      const yCeiling = mod.PAD + maxLayers * (size.h + mod.V_GAP) + 1;
      nodeIds.forEach((id) => {
        const p = flat.positions[id];
        assert.ok(p, "every node must have a position");
        assert.ok(Number.isFinite(p.x) && Number.isFinite(p.y), "coordinates must be finite");
        assert.ok(p.y <= yCeiling, `layer count must stay bounded by node count (y=${p.y}, ceiling=${yCeiling})`);
      });
    })
  );
});

test("property: no overlap between unrelated drawn boxes", () => {
  fc.assert(
    fc.property(specArb, ({ spec, expandedSet }) => {
      const visible = mod.getVisibleGraph(spec, expandedSet);
      const layout = mod.layoutHierarchy(spec, expandedSet, visible.edges);
      const parentOf = mod.buildParentMap(spec.groups);
      const drawnIds = new Set([
        ...Object.keys(layout.positions).filter((id) => !id.startsWith("__via_")),
        ...Object.keys(layout.groupBoxes),
      ]);
      const ids = [...drawnIds];
      for (let i = 0; i < ids.length; i++) {
        for (let j = i + 1; j < ids.length; j++) {
          if (related(ids[i], ids[j], parentOf)) continue;
          const overlap = overlaps(
            rectOf(ids[i], layout.positions, layout.groupBoxes),
            rectOf(ids[j], layout.positions, layout.groupBoxes)
          );
          assert.equal(overlap, false, `unrelated boxes ${ids[i]} and ${ids[j]} must not overlap`);
        }
      }
    })
  );
});

test("property: every expanded group fully contains its visible descendants", () => {
  fc.assert(
    fc.property(specArb, ({ spec, expandedSet }) => {
      const visible = mod.getVisibleGraph(spec, expandedSet);
      const layout = mod.layoutHierarchy(spec, expandedSet, visible.edges);
      const parentOf = mod.buildParentMap(spec.groups);
      const drawnIds = new Set([
        ...Object.keys(layout.positions).filter((id) => !id.startsWith("__via_")),
        ...Object.keys(layout.groupBoxes),
      ]);
      const memo = {};
      expandedSet.forEach((gid) => {
        // A group only actually gets drawn (and thus boxed) if it's both
        // expanded AND visible (every ancestor in its chain is also
        // expanded) — expandedSet can contain a now-invisible leftover
        // (e.g. the user expanded a nested group, then collapsed its
        // parent without that toggle pruning the child's entry), and that
        // case is *supposed* to draw nothing for it, by design.
        if (!mod.isVisible(gid, parentOf, expandedSet, memo)) return;
        const box = layout.groupBoxes[gid];
        assert.ok(box, `visible expanded group ${gid} must have a box`);
        drawnIds.forEach((id) => {
          if (id === gid) return;
          if (!ancestorsOf(id, parentOf).includes(gid)) return;
          const inner = contains(box, rectOf(id, layout.positions, layout.groupBoxes));
          assert.ok(inner, `${id} must be fully contained within its ancestor ${gid}'s box`);
        });
      });
    })
  );
});

test("property: every spec id resolves to exactly one drawn box", () => {
  fc.assert(
    fc.property(specArb, ({ spec, expandedSet }) => {
      const visible = mod.getVisibleGraph(spec, expandedSet);
      const layout = mod.layoutHierarchy(spec, expandedSet, visible.edges);
      const drawnIds = new Set([
        ...Object.keys(layout.positions).filter((id) => !id.startsWith("__via_")),
        ...Object.keys(layout.groupBoxes),
      ]);
      const universe = [...spec.nodes.map((n) => n.id), ...spec.groups.map((g) => g.id)];
      universe.forEach((id) => {
        const landing = visible.resolve(id);
        assert.ok(drawnIds.has(landing), `${id} must resolve to something actually drawn (got ${landing})`);
      });
    })
  );
});

test("property: edges from/to different hidden members never share an anchor point", () => {
  fc.assert(
    fc.property(specArb, ({ spec, expandedSet }) => {
      const visible = mod.getVisibleGraph(spec, expandedSet);
      const layout = mod.layoutHierarchy(spec, expandedSet, visible.edges);
      const offsets = mod.computeEdgeAnchorOffsets(visible.edges);
      visible.edges.forEach((edge, i) => {
        const sp = layout.positions[edge.from], dp = layout.positions[edge.to];
        if (!sp || !dp || edge.from === edge.to) return;
        const off = offsets[i];
        visible.edges.forEach((other, j) => {
          if (j <= i) return;
          const osp = layout.positions[other.from], odp = layout.positions[other.to];
          if (!osp || !odp || other.from === other.to) return;
          const ooff = offsets[j];
          if (edge.from === other.from && edge._origFrom !== other._origFrom) {
            const sx = sp.x + sp.w * off.fromFrac;
            const osx = osp.x + osp.w * ooff.fromFrac;
            assert.notEqual(sx, osx, `edges ${i} and ${j} share box ${edge.from} but different hidden origins`);
          }
          if (edge.to === other.to && edge._origTo !== other._origTo) {
            const ex = dp.x + dp.w * off.toFrac;
            const oex = odp.x + odp.w * ooff.toFrac;
            assert.notEqual(ex, oex, `edges ${i} and ${j} share box ${edge.to} but different hidden destinations`);
          }
        });
      });
    })
  );
});

test("regression: edges from distinct hidden members fan out across the collapsed box", () => {
  const spec = {
    nodes: [{ id: "n0" }, { id: "n1" }, { id: "n2" }],
    groups: [{ id: "g0", label: "g0", kind: "layer", members: ["n0", "n1"] }],
    edges: [{ from: "n0", to: "n2" }, { from: "n1", to: "n2" }],
  };
  const expandedSet = new Set();
  const visible = mod.getVisibleGraph(spec, expandedSet);
  const offsets = mod.computeEdgeAnchorOffsets(visible.edges);
  assert.deepEqual(offsets.map((o) => o.fromFrac), [1 / 3, 2 / 3]);
});

test("regression: edges into distinct hidden members fan out across the collapsed box", () => {
  const spec = {
    nodes: [{ id: "n0" }, { id: "n1" }, { id: "n2" }],
    groups: [{ id: "g0", label: "g0", kind: "layer", members: ["n0", "n1"] }],
    edges: [{ from: "n2", to: "n0" }, { from: "n2", to: "n1" }],
  };
  const expandedSet = new Set();
  const visible = mod.getVisibleGraph(spec, expandedSet);
  const offsets = mod.computeEdgeAnchorOffsets(visible.edges);
  assert.deepEqual(offsets.map((o) => o.toFrac), [1 / 3, 2 / 3]);
});

test("property: layout is deterministic for identical input", () => {
  fc.assert(
    fc.property(specArb, ({ spec, expandedSet }) => {
      const visible = mod.getVisibleGraph(spec, expandedSet);
      const a = mod.layoutHierarchy(spec, expandedSet, visible.edges);
      const b = mod.layoutHierarchy(spec, new Set(expandedSet), visible.edges);
      assert.equal(JSON.stringify(a), JSON.stringify(b));
    })
  );
});
