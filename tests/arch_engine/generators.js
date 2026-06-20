"use strict";
const fc = require("fast-check");

const MAX_NODES = 8;
const MAX_GROUPS = 4;
const MAX_EDGES = 14;

// A plain node/edge graph, no groups — for testing findBackEdgeSet/layoutFlat
// directly against arbitrary (possibly cyclic, possibly self-looping) graphs.
const graphArb = fc
  .record({
    nodeCount: fc.integer({ min: 1, max: MAX_NODES }),
    edgeEndpoints: fc.array(
      fc.tuple(fc.integer({ min: 0, max: MAX_NODES - 1 }), fc.integer({ min: 0, max: MAX_NODES - 1 })),
      { maxLength: MAX_EDGES }
    ),
  })
  .map(({ nodeCount, edgeEndpoints }) => {
    const nodeIds = Array.from({ length: nodeCount }, (_, i) => "n" + i);
    const seen = new Set();
    const edges = [];
    edgeEndpoints.forEach(([a, b]) => {
      if (a >= nodeCount || b >= nodeCount) return;
      const from = nodeIds[a], to = nodeIds[b];
      const key = from + ">" + to;
      if (seen.has(key)) return;
      seen.add(key);
      edges.push({ from, to });
    });
    return { nodeIds, edges };
  });

// A full system_spec-shaped {nodes, groups, edges} plus an expandedSet,
// generated so the single-parent / forest invariant holds *by construction*
// rather than being filtered for after the fact: each group's parent (if
// any) is picked only from groups at a strictly lower index in a fixed
// id order, which trivially rules out cycles in group nesting.
const specArb = fc
  .record({
    nodeCount: fc.integer({ min: 1, max: MAX_NODES }),
    groupCount: fc.integer({ min: 0, max: MAX_GROUPS }),
    groupParentPicks: fc.array(fc.integer({ min: -1, max: MAX_GROUPS - 1 }), {
      minLength: MAX_GROUPS,
      maxLength: MAX_GROUPS,
    }),
    nodeParentPicks: fc.array(fc.integer({ min: -1, max: MAX_GROUPS - 1 }), {
      minLength: MAX_NODES,
      maxLength: MAX_NODES,
    }),
    edgeEndpoints: fc.array(
      fc.tuple(fc.integer({ min: 0, max: MAX_NODES - 1 }), fc.integer({ min: 0, max: MAX_NODES - 1 })),
      { maxLength: MAX_EDGES }
    ),
    expandedPicks: fc.array(fc.boolean(), { minLength: MAX_GROUPS, maxLength: MAX_GROUPS }),
  })
  .map(({ nodeCount, groupCount, groupParentPicks, nodeParentPicks, edgeEndpoints, expandedPicks }) => {
    const nodeIds = Array.from({ length: nodeCount }, (_, i) => "n" + i);
    const groupIds = Array.from({ length: groupCount }, (_, i) => "g" + i);

    const parentOf = {};
    groupIds.forEach((gid, i) => {
      const pick = groupParentPicks[i];
      if (pick >= 0 && pick < i) parentOf[gid] = groupIds[pick]; // only a lower-index group -> forest
    });
    nodeIds.forEach((nid, i) => {
      const pick = nodeParentPicks[i];
      if (pick >= 0 && pick < groupCount) parentOf[nid] = groupIds[pick];
    });

    const members = {};
    groupIds.forEach((gid) => { members[gid] = []; });
    nodeIds.forEach((nid) => { if (parentOf[nid] !== undefined) members[parentOf[nid]].push(nid); });
    groupIds.forEach((gid) => { if (parentOf[gid] !== undefined) members[parentOf[gid]].push(gid); });

    const groups = groupIds.map((gid) => ({ id: gid, label: gid, kind: "layer", members: members[gid] }));
    const nodes = nodeIds.map((nid) => ({ id: nid, label: nid }));

    const seen = new Set();
    const edges = [];
    edgeEndpoints.forEach(([a, b]) => {
      if (a >= nodeCount || b >= nodeCount) return;
      const from = nodeIds[a], to = nodeIds[b];
      const key = from + ">" + to;
      if (seen.has(key)) return;
      seen.add(key);
      edges.push({ from, to });
    });

    const expandedSet = new Set(groupIds.filter((_, i) => expandedPicks[i]));

    return { spec: { nodes, groups, edges }, expandedSet };
  });

module.exports = { graphArb, specArb, MAX_NODES, MAX_GROUPS, MAX_EDGES };
