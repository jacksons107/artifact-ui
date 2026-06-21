/* ── Architecture diagram engine ──────────────────────────────────────────
 * Client-side port of layout.py + svg_architecture.py + seq_overlay.py.
 * This is the ONLY place node/edge/group positions are computed for the
 * Architecture tab and every Code Detail module — both the first paint and
 * every later expand/collapse call the same renderDiagram(), so there is
 * never a second layout implementation to keep in sync.
 *
 * Groups are collapsible nodes, not a separate "detail" concept: every
 * group starts collapsed (drawn as one placeholder box) and can be expanded
 * to reveal its real members in place. A node/group has at most one parent
 * group (enforced server-side), so every edge endpoint has exactly one
 * "nearest visible ancestor" to redirect to when something along its
 * parent chain is collapsed — no manual boundary map needed.
 *
 * Layout is HIERARCHICAL, not one flat pass: an expanded group's own
 * members are laid out as a completely independent Sugiyama problem first
 * (bottom-up, so nested expansions are sized before their parent), and the
 * resulting bounding box is then treated as a single (large) opaque node
 * when laying out whatever level it lives at. Expanding something only
 * ever inserts a bigger box into its existing slot and reflows spacing
 * around it — nothing outside the box gets reordered, and nothing can ever
 * end up positioned "inside" a box it isn't a member of, because the
 * outer layout reserves exactly the box's real size from the start.
 *
 * This file is one of several plain (non-IIFE-wrapped) fragments under
 * system_spec/arch_engine/, concatenated in sorted-filename order and
 * wrapped in a single IIFE at build time by arch_block.py — see that file
 * for the assembly step. tests/arch_engine/harness.js assembles the same
 * files the same way for testing.
 */

var NODE_W_MIN = 140, NODE_W_MAX = 260, NODE_H = 60, H_GAP = 56, V_GAP = 72, PAD = 56;
var CHAR_W = 7.2, LABEL_PAD = 38;
var GROUP_PAD_X = 16, GROUP_PAD_TOP = 28, GROUP_PAD_BOTTOM = 16;

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  });
}

function truncate(s, maxChars) {
  s = String(s == null ? "" : s);
  if (s.length <= maxChars) return s;
  return s.slice(0, Math.max(1, maxChars - 1)) + "…";
}

function estWidth(node) {
  var longest = Math.max((node.label || node.id || "").length, (node.tech || "").length);
  return Math.min(NODE_W_MAX, Math.max(NODE_W_MIN, longest * CHAR_W + LABEL_PAD));
}

function maxCharsFor(w) {
  return Math.max(4, Math.floor((w - LABEL_PAD) / CHAR_W));
}

/* An edge whose target box doesn't sit cleanly below the source box's
 * bottom (a same-row edge, or a real feedback/back edge from cycle-
 * breaking) has no usable inter-layer gap to anchor through top/bottom —
 * forcing it through bottom-to-top anchors anyway is exactly what made
 * back edges and ordinary forward edges fight over the same vertical
 * territory (the inter-layer V_GAP band) in grid mode, and loop oddly back
 * up through the diagram in curve mode. Anchoring on the right side
 * instead (see drawDiagram/drawOverlay) keeps these in their own lane,
 * off to the side, regardless of rendering mode. */
function edgeGoesBackward(sp, dp) {
  return dp.y < sp.y + sp.h - 0.5;
}
