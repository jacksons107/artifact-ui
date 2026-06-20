/* ── Edge label collision resolution ──
 * Each candidate is a label's *desired* box, top-left + size — exactly
 * what the caller would have drawn at with no other labels present.
 * Returns adjusted boxes with no pairwise overlap, keyed by whatever `key`
 * the caller supplied (an edge index, typically).
 *
 * Deterministic single-direction resolution: process candidates sorted
 * top-to-bottom/left-to-right, and only ever push a box DOWN just far
 * enough to clear whatever's already been placed above it. Because
 * placement only ever increases y and only checks against already-placed
 * (earlier-sorted) boxes, this always terminates and never oscillates —
 * unlike a bidirectional "push apart" pass, which is exactly the kind of
 * reactive patch that caused a runaway regression earlier for group-box
 * overlap (see layoutHierarchy's history). */
function computeEdgeLabelBoxes(candidates, gap) {
  gap = gap || 2;
  var sorted = candidates.slice().sort(function (a, b) { return (a.y - b.y) || (a.x - b.x); });
  var placed = [];
  var out = {};
  sorted.forEach(function (c) {
    var x0 = c.x, x1 = c.x + c.w;
    var y0 = c.y, y1 = c.y + c.h;
    var moved = true;
    var guard = 0;
    while (moved && guard++ < placed.length + 5) {
      moved = false;
      for (var i = 0; i < placed.length; i++) {
        var p = placed[i];
        var overlapsX = x0 < p.x1 + gap && p.x0 < x1 + gap;
        var overlapsY = y0 < p.y1 + gap && p.y0 < y1 + gap;
        if (overlapsX && overlapsY) {
          var dy = p.y1 + gap - y0;
          y0 += dy; y1 += dy;
          moved = true;
        }
      }
    }
    var box = { x0: x0, y0: y0, x1: x1, y1: y1 };
    placed.push(box);
    out[c.key] = { x: x0, y: y0, w: c.w, h: c.h };
  });
  return out;
}
