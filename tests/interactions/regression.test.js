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

// Edge labels used to be positioned independently at each edge's own path
// midpoint, with no awareness of any other edge's label — so several
// edges spanning the same pair of layers (same row) landed their labels on
// top of each other. Fixed via a label-collision pass (computeEdgeLabelBoxes
// in system_spec/arch_engine/15_label_layout.js) that knows about every
// label at once. This is the most faithful check of that fix: it reads
// back the actual drawn <rect> boxes from drawDiagram's real output,
// rather than testing the pure function in isolation.
test("regression: several same-band labeled edges don't overlap in the rendered SVG", async () => {
  // Multiple edges between the exact same node pair share an identical
  // path (same src/dst), so their label midpoints are guaranteed
  // identical too — the most reliable way to reproduce the overlap.
  const spec = {
    title: "t",
    nodes: [
      { id: "src", label: "Source" },
      { id: "dst", label: "Destination" },
    ],
    edges: [
      // Deliberately 3 distinct kinds — same kind + same from/to is now
      // aggregated into one unlabeled line (see edge-aggregation.test.js),
      // which would defeat this test's purpose of exercising 3 separately
      // labeled edges in the same band.
      { from: "src", to: "dst", label: "request", kind: "calls" },
      { from: "src", to: "dst", label: "ack", kind: "emits" },
      { from: "src", to: "dst", label: "retry", kind: "writes" },
    ],
    groups: [],
  };
  const { document } = await loadSpec(spec);
  const scope = document.querySelector(".sys-arch-scope");
  const labelRects = [...scope.querySelectorAll(".sys-edge rect")].map((r) => ({
    x0: +r.getAttribute("x"),
    y0: +r.getAttribute("y"),
    x1: +r.getAttribute("x") + +r.getAttribute("width"),
    y1: +r.getAttribute("y") + +r.getAttribute("height"),
  }));
  assert.equal(labelRects.length, 3, "all 3 edge labels must be drawn");
  for (let i = 0; i < labelRects.length; i++) {
    for (let j = i + 1; j < labelRects.length; j++) {
      const a = labelRects[i], b = labelRects[j];
      const overlap = a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1;
      assert.equal(overlap, false, `label rects ${i} and ${j} must not overlap`);
    }
  }
});
