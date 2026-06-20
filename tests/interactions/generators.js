"use strict";
const fc = require("fast-check");

const KIND_POOL = ["service", "db", "external"];
const STATUS_POOL = ["added", "modified", "deleted"];
const EKIND_POOL = ["calls", "emits"];

// Small synthetic specs with a controlled, exhaustive mix of node kinds,
// change statuses, edge kinds, and (at most 2) groups — deliberately small
// (3-6 nodes) so fast-check shrinking lands on a short, readable repro.
const specArb = fc
  .record({
    nodeCount: fc.integer({ min: 3, max: 6 }),
    kindPicks: fc.array(fc.integer({ min: 0, max: KIND_POOL.length - 1 }), { minLength: 6, maxLength: 6 }),
    statusPicks: fc.array(fc.integer({ min: -1, max: STATUS_POOL.length - 1 }), { minLength: 6, maxLength: 6 }),
    groupPicks: fc.array(fc.integer({ min: -1, max: 1 }), { minLength: 6, maxLength: 6 }), // -1 = no group, else group index 0/1
    edgeEndpoints: fc.array(fc.tuple(fc.integer({ min: 0, max: 5 }), fc.integer({ min: 0, max: 5 }), fc.integer({ min: 0, max: EKIND_POOL.length - 1 })), { maxLength: 6 }),
  })
  .map(({ nodeCount, kindPicks, statusPicks, groupPicks, edgeEndpoints }) => {
    const nodeIds = Array.from({ length: nodeCount }, (_, i) => "n" + i);
    const usedKinds = new Set();
    const usedStatuses = new Set();
    const usedGroups = new Set();

    const groupMembers = { g0: [], g1: [] };
    const nodes = nodeIds.map((id, i) => {
      const kind = KIND_POOL[kindPicks[i]];
      usedKinds.add(kind);
      const statusIdx = statusPicks[i];
      const status = statusIdx >= 0 ? STATUS_POOL[statusIdx] : undefined;
      if (status) usedStatuses.add(status);
      const groupIdx = groupPicks[i];
      if (groupIdx === 0) { groupMembers.g0.push(id); usedGroups.add("g0"); }
      if (groupIdx === 1) { groupMembers.g1.push(id); usedGroups.add("g1"); }
      return { id, label: id, kind, status };
    });

    // A single-member group is rejected by parse_spec (no value over
    // referencing the member directly) — only keep groups with 2+ members,
    // since render_helper.js shells out to python3 and would otherwise fail.
    const groups = [];
    if (groupMembers.g0.length >= 2) groups.push({ id: "g0", label: "Group 0", kind: "layer", members: groupMembers.g0 });
    if (groupMembers.g1.length >= 2) groups.push({ id: "g1", label: "Group 1", kind: "layer", members: groupMembers.g1 });

    const seen = new Set();
    const edges = [];
    const usedEKinds = new Set();
    edgeEndpoints.forEach(([a, b, ekIdx]) => {
      if (a === b || a >= nodeCount || b >= nodeCount) return;
      const from = nodeIds[a], to = nodeIds[b];
      const key = from + ">" + to;
      if (seen.has(key)) return;
      seen.add(key);
      const kind = EKIND_POOL[ekIdx];
      usedEKinds.add(kind);
      edges.push({ from, to, kind });
    });

    return {
      spec: { title: "t", nodes, edges, groups },
      pools: {
        kinds: [...usedKinds],
        statuses: [...usedStatuses],
        ekinds: [...usedEKinds],
        groups: groups.map((g) => g.id),
      },
    };
  });

const actionTypeArb = fc.constantFrom("toggleKind", "toggleStatus", "toggleEKind", "toggleGroup", "expand", "collapse");

// Given a generated spec's actual pools, build a random sequence of valid
// actions (toggle filters in any category, expand/collapse any group).
function actionsArbFor(pools) {
  const choices = [];
  if (pools.kinds.length) choices.push(fc.record({ type: fc.constant("toggleKind"), value: fc.constantFrom(...pools.kinds) }));
  if (pools.statuses.length) choices.push(fc.record({ type: fc.constant("toggleStatus"), value: fc.constantFrom(...pools.statuses) }));
  if (pools.ekinds.length) choices.push(fc.record({ type: fc.constant("toggleEKind"), value: fc.constantFrom(...pools.ekinds) }));
  if (pools.groups.length) {
    choices.push(fc.record({ type: fc.constant("toggleGroup"), value: fc.constantFrom(...pools.groups) }));
    choices.push(fc.record({ type: fc.constant("expand"), value: fc.constantFrom(...pools.groups) }));
    choices.push(fc.record({ type: fc.constant("collapse"), value: fc.constantFrom(...pools.groups) }));
  }
  if (!choices.length) return fc.constant([]);
  return fc.array(fc.oneof(...choices), { minLength: 1, maxLength: 16 });
}

// specArb plus a dependent, valid action sequence for that spec's pools.
const specWithActionsArb = specArb.chain(({ spec, pools }) =>
  actionsArbFor(pools).map((actions) => ({ spec, pools, actions }))
);

module.exports = { specArb, specWithActionsArb, KIND_POOL, STATUS_POOL, EKIND_POOL };
