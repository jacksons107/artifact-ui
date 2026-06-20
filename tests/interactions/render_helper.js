"use strict";
const { execFileSync } = require("child_process");
const path = require("path");

const REPO_ROOT = path.join(__dirname, "..", "..");

// Shells out to the real Python render pipeline so tests always exercise
// the actual, current assets.py + filter_bar.py + arch_engine.js together —
// never a JS reimplementation of what render_system_spec produces.
function renderSpec(spec) {
  const py = [
    "import sys, json",
    `sys.path.insert(0, ${JSON.stringify(REPO_ROOT)})`,
    "import system_spec.render as render",
    "spec = json.load(sys.stdin)",
    "sys.stdout.write(render.render_system_spec(spec))",
  ].join("\n");
  return execFileSync("python3", ["-c", py], {
    input: JSON.stringify(spec),
    maxBuffer: 64 * 1024 * 1024,
    encoding: "utf8",
  });
}

module.exports = { renderSpec };
