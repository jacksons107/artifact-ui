"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fc = require("fast-check");

const { loadSpec, toggleFilter, expandGroup, collapseGroup, snapshot } = require("./harness");
const { specWithActionsArb } = require("./generators");

async function applyAction(document, action) {
  if (action.type === "toggleKind") toggleFilter(document, "ak", action.value);
  else if (action.type === "toggleStatus") toggleFilter(document, "as", action.value);
  else if (action.type === "toggleEKind") toggleFilter(document, "aek", action.value);
  else if (action.type === "toggleGroup") toggleFilter(document, "ag", action.value);
  else if (action.type === "expand") expandGroup(document, action.value);
  else if (action.type === "collapse") collapseGroup(document, action.value);
}

// Independent re-implementation of the *intended* filter semantics
// (mirrors the documented behavior of _applyArchFilter in
// system_spec/assets.py), computed fresh from a DOM snapshot — deliberately
// NOT calling _applyArchFilter itself, so this can't pass just because a
// bug is shared between the engine and the check.
function expectedFilteredOut(snap) {
  const kinds = new Set(snap.active.kinds);
  const statuses = new Set(snap.active.statuses);
  const ekinds = new Set(snap.active.ekinds);
  const agroups = new Set(snap.active.groups);
  const inactiveGroups = new Set(snap.has.groups ? snap.allGroupButtons.filter((g) => !agroups.has(g)) : []);

  function inInactiveGroup(groups) {
    if (!inactiveGroups.size) return false;
    return groups.some((g) => inactiveGroups.has(g));
  }

  const nodeHidden = {};
  snap.nodes.forEach((n) => {
    // A collapsed group's placeholder isn't a real instance of any
    // selectable kind/status — it's exempt from kind/status filtering and
    // instead governed by the group filter on its own id, not by which
    // OTHER group it happens to be nested under (n.groups, used below).
    if (n.isGroupPlaceholder) {
      const ownGroupFaded = inactiveGroups.size > 0 && inactiveGroups.has(n.groupId);
      const nestedGroupFaded = inInactiveGroup(n.groups);
      nodeHidden[n.id] = ownGroupFaded || nestedGroupFaded;
      return;
    }
    const kOk = !snap.has.kinds || (kinds.size > 0 && kinds.has(n.kind));
    const sOk = !snap.has.statuses || !n.status || (statuses.size > 0 && statuses.has(n.status));
    const groupFaded = inInactiveGroup(n.groups);
    nodeHidden[n.id] = !(kOk && sOk) || groupFaded;
  });

  const edgesExpected = snap.edges.map((e) => {
    const eOk = !snap.has.ekinds || (ekinds.size > 0 && ekinds.has(e.kind));
    const groupFaded = inInactiveGroup(e.srcGroups) || inInactiveGroup(e.dstGroups);
    const endpointHidden = nodeHidden[e.from] || nodeHidden[e.to];
    return !eOk || groupFaded || endpointHidden;
  });

  const groupsExpected = snap.groups.map((g) => {
    const gOk = !snap.has.groups || (agroups.size > 0 && agroups.has(g.id));
    return !gOk;
  });

  return { nodeHidden, edgesExpected, groupsExpected };
}

function assertMatchesExpected(snap, label) {
  const expected = expectedFilteredOut(snap);
  snap.nodes.forEach((n) => {
    assert.equal(n.filteredOut, expected.nodeHidden[n.id], `${label}: node ${n.id} filtered-out mismatch`);
  });
  snap.edges.forEach((e, i) => {
    assert.equal(e.filteredOut, expected.edgesExpected[i], `${label}: edge ${e.from}->${e.to} filtered-out mismatch`);
  });
  snap.groups.forEach((g, i) => {
    assert.equal(g.filteredOut, expected.groupsExpected[i], `${label}: group ${g.id} filtered-out mismatch`);
  });
}

const TOGGLE_TYPES = new Set(["toggleKind", "toggleStatus", "toggleEKind", "toggleGroup"]);

// _applyArchFilter only ever runs reactively, from the 4 filter-button
// click handlers (system_spec/assets.py:574-589) — never automatically on
// initial load or after a structural re-render (group expand/collapse, via
// arch_engine.js's renderDiagram, fully destroys and recreates the SVG
// elements). So "filtered-out matches the active buttons" is only a
// guarantee *at the moment a filter button is clicked* — we assert right
// after every such click, while still interleaving expand/collapse actions
// beforehand on every run, to catch staleness introduced by a re-render
// that happened since the last filter click.
test("property: filtered-out state matches active filters immediately after every filter click", async () => {
  await fc.assert(
    fc.asyncProperty(specWithActionsArb, async ({ spec, actions }) => {
      const { document, errors } = await loadSpec(spec);
      assert.equal(errors.length, 0, "no runtime errors: " + errors.join(" | "));

      const applied = [];
      for (const action of actions) {
        await applyAction(document, action);
        applied.push(action);
        if (TOGGLE_TYPES.has(action.type)) {
          assertMatchesExpected(snapshot(document), "after " + JSON.stringify(applied));
        }
      }
    }),
    { numRuns: 100 }
  );
});
