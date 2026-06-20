"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");

const { loadSpec } = require("./harness");

// Two hidden members of a collapsed group both calling the same external
// node resolve to the exact same (from, to, kind) once redirected — drawn
// today as two fully overlapping lines with no indication there's more
// than one. aggregateEdges (system_spec/arch_engine/25_edge_aggregation.js)
// collapses same-(from,to,kind) duplicates into one clickable, unlabeled
// line; a "writes" edge between the same pair has a different kind, so it
// stays a separate, normal, labeled edge.
const SPEC = {
  title: "t",
  nodes: [
    { id: "n0", label: "n0", kind: "service" },
    { id: "n1", label: "n1", kind: "service" },
    { id: "n2", label: "n2", kind: "db" },
  ],
  edges: [
    { from: "n0", to: "n2", kind: "calls", label: "A" },
    { from: "n1", to: "n2", kind: "calls", label: "B" },
    { from: "n0", to: "n2", kind: "writes", label: "persist" },
  ],
  groups: [{ id: "g0", label: "Group 0", kind: "layer", members: ["n0", "n1"] }],
};

test("regression: same-kind duplicate edges into a collapsed group draw as one unlabeled, clickable line", async () => {
  const { document } = await loadSpec(SPEC);
  const scope = document.querySelector(".sys-arch-scope");

  const callsEdges = [...scope.querySelectorAll('.sys-edge[data-kind="calls"]')];
  assert.equal(callsEdges.length, 1, "the two same-kind duplicate edges must draw as exactly one line");

  const agg = callsEdges[0];
  const members = JSON.parse(agg.getAttribute("data-members") || "null");
  assert.ok(members, "aggregated edge must carry data-members");
  assert.equal(members.length, 2);
  const froms = members.map((m) => m.from).sort();
  assert.deepEqual(froms, ["n0", "n1"], "data-members must list the real (pre-redirect) origin nodes");

  const aggLabelTexts = [...agg.querySelectorAll("text")];
  assert.equal(aggLabelTexts.length, 0, "an aggregated edge must not render any label, even though its members had one");
});

test("regression: a differently-kinded edge between the same pair is unaffected by aggregation", async () => {
  const { document } = await loadSpec(SPEC);
  const scope = document.querySelector(".sys-arch-scope");

  const writeEdges = [...scope.querySelectorAll('.sys-edge[data-kind="writes"]')];
  assert.equal(writeEdges.length, 1);
  assert.equal(writeEdges[0].hasAttribute("data-members"), false, "a non-duplicate edge must not be marked as an aggregate");
  const labelText = [...writeEdges[0].querySelectorAll("text")].map((t) => t.textContent);
  assert.ok(labelText.includes("persist"), "a normal, non-aggregated edge must keep its own label");
});

test("regression: clicking an aggregated edge shows its members in the sidebar, and clicking again closes it", async () => {
  const { document } = await loadSpec(SPEC);
  const scope = document.querySelector(".sys-arch-scope");
  const agg = scope.querySelector('.sys-edge[data-kind="calls"]');
  const panel = document.getElementById("sys-edge-agg-panel");
  assert.ok(panel, "the always-present aggregate-edge panel must be rendered server-side, even though it starts empty");

  agg.dispatchEvent(new document.defaultView.Event("click", { bubbles: true }));
  assert.equal(panel.style.display, "block", "panel must become visible on click");
  assert.match(panel.innerHTML, /2 edges/);
  assert.match(panel.innerHTML, /n0/);
  assert.match(panel.innerHTML, /n1/);

  agg.dispatchEvent(new document.defaultView.Event("click", { bubbles: true }));
  assert.equal(panel.style.display, "none", "clicking the same aggregated edge again must close the panel");
});
