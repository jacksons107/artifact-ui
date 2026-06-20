"use strict";
const { JSDOM } = require("jsdom");
const { renderSpec } = require("./render_helper");

// Loads a spec's real rendered HTML into jsdom with scripts running for
// real (inline onclick handlers, the DOMContentLoaded bootstrap that calls
// renderDiagram, etc.) — this is DOM-mutation testing, not pure-function
// testing, so there's no shortcut around an actual DOM.
async function loadSpec(spec) {
  const html = renderSpec(spec);
  const dom = new JSDOM(html, { runScripts: "dangerously", resources: "usable" });
  const win = dom.window;
  const errors = [];
  win.onerror = function (msg, src, line, col, err) {
    errors.push(String(msg) + (err && err.stack ? "\n" + err.stack : ""));
    return true;
  };
  // let DOMContentLoaded + the initial renderDiagram() pass run
  await new Promise((r) => setTimeout(r, 50));
  return { dom, win, document: win.document, errors };
}

function scopeOf(document) {
  return document.querySelector(".sys-arch-scope");
}

// All actions and the snapshot below operate within a single scope — the
// top-level Architecture tab's .sys-arch-scope — never the whole document.
// Code Detail panels render their own independent .sys-arch-scope per
// group (system_spec/code_detail.py, prefix "cd-<gid>-"), each with its
// own filter buttons and its own copy of nodes sharing the same raw ids;
// mixing scopes would make unrelated filter state look like a bug here.

// attr is one of "ak" (node kind), "as" (status), "aek" (edge kind), "ag" (group)
function toggleFilter(document, attr, value) {
  const scope = scopeOf(document);
  const btn = scope.querySelector(`.sys-fc[data-${attr}="${cssEscape(value)}"]`);
  if (!btn) throw new Error(`no filter button for data-${attr}="${value}"`);
  btn.dispatchEvent(new document.defaultView.Event("click", { bubbles: true }));
}

function expandGroup(document, groupId) {
  const scope = scopeOf(document);
  const placeholder = [...scope.querySelectorAll(".sys-node")].find(
    (n) => n.getAttribute("data-id") === groupId
  );
  if (!placeholder) return false; // already expanded, or not currently visible
  const btn = placeholder.querySelector(".sys-expand-btn");
  if (!btn || btn.textContent !== "⤢") return false;
  btn.dispatchEvent(new document.defaultView.Event("click", { bubbles: true }));
  return true;
}

function collapseGroup(document, groupId) {
  const scope = scopeOf(document);
  const box = [...scope.querySelectorAll(".sys-group")].find(
    (g) => g.getAttribute("data-gid") === groupId
  );
  if (!box) return false; // not currently expanded/visible
  const btn = box.querySelector(".sys-expand-btn");
  if (!btn || btn.textContent !== "✕") return false;
  btn.dispatchEvent(new document.defaultView.Event("click", { bubbles: true }));
  return true;
}

function cssEscape(s) {
  return String(s).replace(/["\\]/g, "\\$&");
}

// Snapshot of everything needed to independently judge whether the current
// `filtered-out` state is correct: the active filter buttons, plus every
// drawn node/edge/group's identifying attributes and current class state —
// scoped to the same single .sys-arch-scope as the actions above.
function snapshot(document) {
  const scope = scopeOf(document);
  const activeKinds = [...scope.querySelectorAll('.sys-fc[data-ak].active')].map((b) => b.getAttribute("data-ak"));
  const activeStatuses = [...scope.querySelectorAll('.sys-fc[data-as].active')].map((b) => b.getAttribute("data-as"));
  const activeEKinds = [...scope.querySelectorAll('.sys-fc[data-aek].active')].map((b) => b.getAttribute("data-aek"));
  const activeGroups = [...scope.querySelectorAll('.sys-fc[data-ag].active')].map((b) => b.getAttribute("data-ag"));
  const allKindButtons = [...scope.querySelectorAll('.sys-fc[data-ak]')].map((b) => b.getAttribute("data-ak"));
  const allStatusButtons = [...scope.querySelectorAll('.sys-fc[data-as]')].map((b) => b.getAttribute("data-as"));
  const allEKindButtons = [...scope.querySelectorAll('.sys-fc[data-aek]')].map((b) => b.getAttribute("data-aek"));
  const allGroupButtons = [...scope.querySelectorAll('.sys-fc[data-ag]')].map((b) => b.getAttribute("data-ag"));

  const nodes = [...scope.querySelectorAll(".sys-node")].map((n) => ({
    id: n.getAttribute("data-id"),
    kind: n.getAttribute("data-kind"),
    status: n.getAttribute("data-status") || "",
    groups: (n.getAttribute("data-groups") || "").split(" ").filter(Boolean),
    isGroupPlaceholder: n.getAttribute("data-is-group") === "1",
    groupId: n.getAttribute("data-group-id") || "",
    filteredOut: n.classList.contains("filtered-out"),
  }));
  const edges = [...scope.querySelectorAll(".sys-edge")].map((e) => ({
    from: e.getAttribute("data-from"),
    to: e.getAttribute("data-to"),
    kind: e.getAttribute("data-kind"),
    srcGroups: (e.getAttribute("data-src-groups") || "").split(" ").filter(Boolean),
    dstGroups: (e.getAttribute("data-dst-groups") || "").split(" ").filter(Boolean),
    filteredOut: e.classList.contains("filtered-out"),
  }));
  const groups = [...scope.querySelectorAll(".sys-group")].map((g) => ({
    id: g.getAttribute("data-gid"),
    filteredOut: g.classList.contains("filtered-out"),
  }));

  return {
    active: { kinds: activeKinds, statuses: activeStatuses, ekinds: activeEKinds, groups: activeGroups },
    has: { kinds: allKindButtons.length > 0, statuses: allStatusButtons.length > 0, ekinds: allEKindButtons.length > 0, groups: allGroupButtons.length > 0 },
    allGroupButtons,
    nodes,
    edges,
    groups,
  };
}

module.exports = { loadSpec, toggleFilter, expandGroup, collapseGroup, snapshot };
