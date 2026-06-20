"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");

const { loadSpec, toggleFilter, expandGroup, snapshot } = require("./harness");

// The exact bug: "I toggle a node type/edge/group filter off, then back on,
// and the corresponding components stay faded — but it only happens when
// some group is collapsed; fully expanded, filters work correctly."
//
// Root cause: a collapsed group's placeholder is drawn with data-kind set
// to the GROUP's own kind (e.g. "layer"), which the kind-filter bar never
// offers as a selectable option (it's built only from real node kinds —
// system_spec/filter_bar.py:14). So the instant ANY kind filter button is
// clicked, every collapsed-group placeholder fails the kind check
// unconditionally and gets hidden — and toggling that SAME kind button
// back off-and-on, or toggling the group's own filter button (which only
// affects *expanded* .sys-group boxes, not collapsed placeholders), never
// restores it. Any edge touching that placeholder cascades into looking
// "stuck faded" too, even though the edge's own filter is untouched.
// Fixed in system_spec/arch_engine.js (data-is-group/data-group-id
// markers) + system_spec/assets.py (_applyArchFilter exempts placeholders
// from kind/status filtering, applying the group filter to their own id
// instead).
const SPEC = {
  title: "t",
  nodes: [
    { id: "n0", label: "n0", kind: "service" },
    { id: "n1", label: "n1", kind: "service" },
    { id: "n2", label: "n2", kind: "db" },
  ],
  edges: [{ from: "n0", to: "n2", kind: "calls" }],
  groups: [{ id: "g0", label: "Group 0", kind: "layer", members: ["n0", "n1"] }],
};

test("regression: collapsed group placeholder survives a kind-filter toggle off/on", async () => {
  const { document } = await loadSpec(SPEC);

  toggleFilter(document, "ak", "service"); // off
  toggleFilter(document, "ak", "service"); // back on

  const snap = snapshot(document);
  const placeholder = snap.nodes.find((n) => n.id === "g0");
  assert.ok(placeholder, "collapsed group g0 must still be drawn as a placeholder");
  assert.equal(placeholder.filteredOut, false, "g0 placeholder must not be stuck faded after a kind filter round-trip");
});

test("regression: collapsed group placeholder unaffected by an unrelated kind filter", async () => {
  const { document } = await loadSpec(SPEC);

  toggleFilter(document, "ak", "db"); // toggle off a kind g0's members don't even have

  const snap = snapshot(document);
  const placeholder = snap.nodes.find((n) => n.id === "g0");
  assert.equal(placeholder.filteredOut, false, "g0 must not be hidden by a kind filter that was never its own");
});

test("regression: edge touching a collapsed group survives an edge-kind filter toggle off/on", async () => {
  const { document } = await loadSpec(SPEC);

  toggleFilter(document, "ak", "service"); // first touch the kind filter (this is what triggered the cascade)
  toggleFilter(document, "aek", "calls"); // off
  toggleFilter(document, "aek", "calls"); // back on

  const snap = snapshot(document);
  const edge = snap.edges.find((e) => e.to === "n2" || e.to === "g0");
  assert.ok(edge);
  assert.equal(edge.filteredOut, false, "edge must not be stuck faded after its own filter round-trips, even with a group collapsed");
});

test("regression: a real member node revealed by expand re-syncs correctly on the next filter click", async () => {
  const { document } = await loadSpec(SPEC);

  toggleFilter(document, "ak", "service"); // off — no real "service" nodes exist yet (g0 still collapsed)
  expandGroup(document, "g0"); // n0/n1 (kind=service) now exist as real nodes, freshly drawn, unfiltered
  toggleFilter(document, "ak", "service"); // back on — this click must resync everything, including n0/n1

  const snap = snapshot(document);
  const n0 = snap.nodes.find((n) => n.id === "n0");
  assert.equal(n0.filteredOut, false, "real member node revealed by expand must end up correctly unfaded once a filter click resyncs");
});
