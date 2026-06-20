"use strict";
const fs = require("fs");
const path = require("path");

const ENGINE_DIR = path.join(__dirname, "..", "..", "system_spec", "arch_engine");

// Loads the real, shipped engine source — the same plain (non-IIFE-wrapped)
// fragments under system_spec/arch_engine/, concatenated in the same
// sorted-filename order arch_block.py uses to build the real IIFE — and
// exposes its internal (otherwise un-exported) pure functions for testing
// by appending a `return {...}` before evaluating it. This is the only
// place that knows about the engine's internal function names — if a
// rename breaks this, that's the harness reminding you to update the test
// names, not a real engine bug.
function loadEngineInternals() {
  const files = fs.readdirSync(ENGINE_DIR).filter((f) => f.endsWith(".js")).sort();
  const body = files.map((f) => fs.readFileSync(path.join(ENGINE_DIR, f), "utf8")).join("\n");
  const exposed = body + `
    return {
      findBackEdgeSet,
      orderLayersByBarycenter,
      layoutFlat,
      layoutHierarchy,
      buildParentMap,
      isVisible,
      getVisibleGraph,
      computeEdgeLabelBoxes,
      computeEdgeAnchorOffsets,
      aggregateEdges,
      PAD, NODE_H, V_GAP, H_GAP, GROUP_PAD_X, GROUP_PAD_TOP, GROUP_PAD_BOTTOM,
    };
  `;

  // Minimal stand-ins: the functions under test are pure graph/layout math
  // and never touch the DOM, but the bottom of the file (drawDiagram,
  // renderDiagram, the DOMContentLoaded bootstrap) references document/
  // window at parse time, so these just need to exist, not actually work.
  const fakeDocument = {
    createElementNS: () => ({ setAttribute() {}, appendChild() {}, addEventListener() {} }),
    addEventListener() {},
    querySelectorAll: () => [],
  };
  const fakeWindow = {};

  const fn = new Function("document", "window", exposed);
  return fn(fakeDocument, fakeWindow);
}

module.exports = { loadEngineInternals, ENGINE_DIR };
