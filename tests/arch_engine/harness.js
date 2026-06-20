"use strict";
const fs = require("fs");
const path = require("path");

const ENGINE_PATH = path.join(__dirname, "..", "..", "system_spec", "arch_engine.js");

// Loads the real, shipped arch_engine.js and exposes its internal (otherwise
// un-exported) pure functions for testing, by stripping the outer IIFE
// wrapper and appending a `return {...}` before evaluating it. This is the
// only place that knows about the engine's internal function names — if a
// rename breaks this, that's the harness reminding you to update the test
// names, not a real engine bug.
function loadEngineInternals() {
  const src = fs.readFileSync(ENGINE_PATH, "utf8");
  const body = src
    .replace(/\(function \(\) \{\s*"use strict";/, "")
    .replace(/\}\)\(\);\s*$/, "");
  const exposed = body + `
    return {
      findBackEdgeSet,
      orderLayersByBarycenter,
      layoutFlat,
      layoutHierarchy,
      buildParentMap,
      isVisible,
      getVisibleGraph,
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

module.exports = { loadEngineInternals, ENGINE_PATH };
