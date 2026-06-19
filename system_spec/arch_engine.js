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
 */
(function () {
  "use strict";

  var NODE_W_MIN = 140, NODE_W_MAX = 260, NODE_H = 60, H_GAP = 56, V_GAP = 72, PAD = 56;
  var CHAR_W = 7.2, LABEL_PAD = 38;

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

  /* ── Sugiyama-style layered layout ──
   * Four phases: (1) cycle removal via DFS back-edge detection, so the
   * graph fed to ranking is always a DAG regardless of real feedback edges
   * (retries, callbacks, reroutes — common in real architectures); (2) rank
   * assignment via Kahn's longest-path on that acyclic subgraph; (3)
   * crossing reduction via iterative group-aware median/barycenter sweeps;
   * (4) coordinate assignment (per-layer centering + the disjoint-group
   * separation pass below). */

  // Phase 1: classic DFS back-edge detection (white/gray/black coloring,
  // iterative to avoid recursion-depth limits). An edge to a node currently
  // on the DFS stack (gray) closes a cycle — flag it by index. Removing
  // these edges from the graph used for ranking is guaranteed to yield a
  // DAG, so every node gets a real, finite rank with no "stray" fallback.
  function findBackEdgeSet(nodeIds, edges, nodeIdSet) {
    var adj = {};
    nodeIds.forEach(function (id) { adj[id] = []; });
    edges.forEach(function (e, i) {
      if (e.from !== e.to && nodeIdSet[e.from] && nodeIdSet[e.to]) {
        adj[e.from].push({ to: e.to, idx: i });
      }
    });
    var color = {}; // undefined=white, 1=gray, 2=black
    var backEdges = {};
    nodeIds.forEach(function (start) {
      if (color[start]) return;
      var stack = [{ id: start, i: 0 }];
      color[start] = 1;
      while (stack.length) {
        var frame = stack[stack.length - 1];
        var list = adj[frame.id];
        if (frame.i < list.length) {
          var edge = list[frame.i++];
          var c = color[edge.to];
          if (c === 1) backEdges[edge.idx] = true;
          else if (!c) { color[edge.to] = 1; stack.push({ id: edge.to, i: 0 }); }
        } else {
          color[frame.id] = 2;
          stack.pop();
        }
      }
    });
    return backEdges;
  }

  // Phase 3 helper: group-aware median/barycenter crossing reduction.
  // Alternates top-down (order each layer using the already-fixed layer
  // above as reference) and bottom-up (using the layer below) sweeps. A
  // currently-expanded group's members in a layer are treated as one
  // contiguous movable block — sorted internally by their own barycenter,
  // the block itself ordered among siblings by its aggregate barycenter —
  // so a group's bounding box (min/max over its members' positions) never
  // ends up enclosing unrelated nodes that got interleaved in between.
  function orderLayersByBarycenter(layersMap, layerKeys, nodeGroup, predsOf, succsOf) {
    layerKeys.forEach(function (l) {
      layersMap[l].sort(function (a, b) {
        var ga = nodeGroup[a] || "￿", gb = nodeGroup[b] || "￿";
        if (ga !== gb) return ga < gb ? -1 : 1;
        return a < b ? -1 : a > b ? 1 : 0;
      });
    });

    var posIndex = {};
    function reindex(l) { layersMap[l].forEach(function (id, i) { posIndex[id] = i; }); }
    layerKeys.forEach(reindex);

    function barycenter(id, neighbors) {
      var vals = neighbors.filter(function (n) { return posIndex[n] !== undefined; })
        .map(function (n) { return posIndex[n]; });
      if (!vals.length) return null;
      return vals.reduce(function (a, b) { return a + b; }, 0) / vals.length;
    }

    function sweepLayer(l, neighborsOf) {
      var ids = layersMap[l];
      var blockKey = function (id) { return nodeGroup[id] || ("_n_" + id); };
      var blocks = {};
      ids.forEach(function (id) { (blocks[blockKey(id)] = blocks[blockKey(id)] || []).push(id); });
      var keys = Object.keys(blocks);
      var bcOf = {};
      ids.forEach(function (id) { bcOf[id] = barycenter(id, neighborsOf(id)); });
      keys.forEach(function (key) {
        blocks[key].sort(function (a, b) {
          var ba = bcOf[a], bb = bcOf[b];
          if (ba === null && bb === null) return a < b ? -1 : a > b ? 1 : 0;
          if (ba === null) return 1;
          if (bb === null) return -1;
          return ba - bb || (a < b ? -1 : a > b ? 1 : 0);
        });
      });
      keys.sort(function (ka, kb) {
        var va = blocks[ka].map(function (id) { return bcOf[id]; }).filter(function (v) { return v !== null; });
        var vb = blocks[kb].map(function (id) { return bcOf[id]; }).filter(function (v) { return v !== null; });
        var ma = va.length ? va.reduce(function (a, b) { return a + b; }, 0) / va.length : null;
        var mb = vb.length ? vb.reduce(function (a, b) { return a + b; }, 0) / vb.length : null;
        if (ma === null && mb === null) return ka < kb ? -1 : ka > kb ? 1 : 0;
        if (ma === null) return 1;
        if (mb === null) return -1;
        return ma - mb || (ka < kb ? -1 : ka > kb ? 1 : 0);
      });
      var newOrder = [];
      keys.forEach(function (key) { newOrder = newOrder.concat(blocks[key]); });
      layersMap[l] = newOrder;
      reindex(l);
    }

    var SWEEPS = 4;
    for (var s = 0; s < SWEEPS; s++) {
      if (s % 2 === 0) {
        for (var i = 1; i < layerKeys.length; i++) sweepLayer(layerKeys[i], function (id) { return predsOf[id]; });
      } else {
        for (var j = layerKeys.length - 2; j >= 0; j--) sweepLayer(layerKeys[j], function (id) { return succsOf[id]; });
      }
    }
  }

  function layoutGraph(nodes, edges, groups) {
    edges = edges || [];
    groups = groups || [];
    var nodeIds = nodes.map(function (n) { return n.id; });
    var nodeIdSet = {}; nodeIds.forEach(function (id) { nodeIdSet[id] = true; });
    var nodeGroup = {};
    groups.forEach(function (g) {
      (g.members || []).forEach(function (m) { if (!(m in nodeGroup)) nodeGroup[m] = g.id; });
    });

    // Phase 1: cycle removal — back edges are excluded from ranking below
    // but still drawn normally (drawDiagram is direction-agnostic).
    var backEdges = findBackEdgeSet(nodeIds, edges, nodeIdSet);

    // Phase 2: rank assignment via Kahn's longest-path, on the acyclic
    // subgraph (non-back edges only) — every node is now guaranteed a
    // finite rank directly from the BFS, since removing DFS back edges
    // from a directed graph always yields a DAG.
    var inDeg = {}, succs = {};
    nodeIds.forEach(function (id) { inDeg[id] = 0; succs[id] = []; });
    edges.forEach(function (e, i) {
      if (e.from !== e.to && nodeIdSet[e.from] && nodeIdSet[e.to] && !backEdges[i]) {
        succs[e.from].push(e.to);
        inDeg[e.to]++;
      }
    });

    var layer = {};
    var queue = [];
    nodeIds.forEach(function (id) { if (inDeg[id] === 0) { layer[id] = 0; queue.push(id); } });
    while (queue.length) {
      var id = queue.shift();
      succs[id].forEach(function (s) {
        var newL = layer[id] + 1;
        layer[s] = Math.max(layer[s] === undefined ? 0 : layer[s], newL);
        inDeg[s]--;
        if (inDeg[s] === 0) queue.push(s);
      });
    }
    var maxL = 0;
    nodeIds.forEach(function (id) { if (layer[id] !== undefined) maxL = Math.max(maxL, layer[id]); });
    // Defensive only — with back edges removed, every node should already
    // have a rank from the BFS above; this should never actually trigger.
    nodeIds.forEach(function (id) { if (layer[id] === undefined) { maxL++; layer[id] = maxL; } });

    // Expanded-group floor correction: a member with no incoming edge of
    // its own (e.g. it's only ever called FROM a sibling inside the same
    // group) would otherwise get seeded as a global root at layer 0 by
    // Kahn's above, regardless of where its group actually sits — visually
    // stranding it (and the group's bounding box) at the top of the whole
    // diagram. Pull such "stray" members up to their group's floor — the
    // lowest layer among siblings that DO have a real incoming edge — then
    // re-propagate forward so anything depending on the pulled-up node
    // stays consistent. Applies to every expanded group passed in here.
    // Back edges are excluded throughout, same as the ranking above —
    // otherwise a cyclic member would be misclassified as in-degree-0, and
    // the relaxation pass below would never converge.
    function inDeg0Orig(id) {
      var n = 0;
      edges.forEach(function (e, i) { if (e.to === id && e.from !== id && nodeIdSet[e.from] && !backEdges[i]) n++; });
      return n === 0;
    }
    if (groups.length) {
      groups.forEach(function (g) {
        var members = (g.members || []).filter(function (m) { return layer[m] !== undefined; });
        var floor = null;
        members.forEach(function (m) {
          if (inDeg0Orig(m)) return;
          if (floor === null || layer[m] < floor) floor = layer[m];
        });
        if (floor === null) return; // whole group is rootless — nothing to anchor to
        members.forEach(function (m) {
          if (inDeg0Orig(m) && layer[m] < floor) layer[m] = floor;
        });
      });
      // Forward relaxation until stable (graphs here are small; bounded by node count).
      for (var pass = 0; pass < nodeIds.length; pass++) {
        var changed = false;
        edges.forEach(function (e, i) {
          if (e.from === e.to || !nodeIdSet[e.from] || !nodeIdSet[e.to] || backEdges[i]) return;
          if (layer[e.to] < layer[e.from] + 1) { layer[e.to] = layer[e.from] + 1; changed = true; }
        });
        if (!changed) break;
      }
    }

    var layersMap = {};
    nodeIds.forEach(function (id) { (layersMap[layer[id]] = layersMap[layer[id]] || []).push(id); });

    // Phase 3: crossing reduction. Uses ALL edges (including back edges —
    // they're still drawn, so still worth minimizing crossings for).
    var predsOf = {}, succsOf = {};
    nodeIds.forEach(function (id) { predsOf[id] = []; succsOf[id] = []; });
    edges.forEach(function (e) {
      if (e.from === e.to || !nodeIdSet[e.from] || !nodeIdSet[e.to]) return;
      succsOf[e.from].push(e.to);
      predsOf[e.to].push(e.from);
    });
    var rankOnlyLayerKeys = Object.keys(layersMap).map(Number).sort(function (a, b) { return a - b; });
    orderLayersByBarycenter(layersMap, rankOnlyLayerKeys, nodeGroup, predsOf, succsOf);

    // Reserve a via-lane in every intermediate layer for edges that skip
    // more than one layer, so the edge has somewhere of its own to pass
    // through instead of cutting across a real node that happens to sit
    // between its endpoints.
    var edgeVia = {}; // edge index -> [viaNodeId, ...] in layer order
    edges.forEach(function (e, i) {
      if (!nodeIdSet[e.from] || !nodeIdSet[e.to] || e.from === e.to) return;
      var l0 = layer[e.from], l1 = layer[e.to];
      if (l1 - l0 <= 1) return;
      var vias = [];
      for (var l = l0 + 1; l < l1; l++) {
        var viaId = "__via_" + i + "_" + l;
        (layersMap[l] = layersMap[l] || []).push(viaId);
        vias.push(viaId);
      }
      edgeVia[i] = vias;
    });

    var widths = {};
    nodes.forEach(function (n) { widths[n.id] = estWidth(n); });
    Object.keys(edgeVia).forEach(function (i) { edgeVia[i].forEach(function (v) { widths[v] = 24; }); });

    var layerKeys = Object.keys(layersMap).map(Number).sort(function (a, b) { return a - b; });
    var maxLayerW = 0;
    layerKeys.forEach(function (l) {
      var ns = layersMap[l];
      var w = ns.reduce(function (s, id) { return s + widths[id]; }, 0) + Math.max(0, ns.length - 1) * H_GAP;
      maxLayerW = Math.max(maxLayerW, w);
    });

    var positions = {};
    layerKeys.forEach(function (l) {
      var ns = layersMap[l];
      var layerW = ns.reduce(function (s, id) { return s + widths[id]; }, 0) + Math.max(0, ns.length - 1) * H_GAP;
      var x = PAD + (maxLayerW - layerW) / 2;
      var y = PAD + l * (NODE_H + V_GAP);
      ns.forEach(function (id) {
        positions[id] = { x: x, y: y, w: widths[id], h: NODE_H };
        x += widths[id] + H_GAP;
      });
    });

    separateDisjointGroups(positions, groups);

    return { positions: positions, edgeVia: edgeVia };
  }

  /* ── Keep groups that share no members from visually overlapping ──
   * Two groups with disjoint membership shouldn't read as one containing
   * the other just because their incidental x/y placement collided. When
   * their (padded) boxes intersect, sweep every position at or past the
   * overlap boundary further apart along whichever axis needs the smaller
   * shift — this also carries along any via-lane points and unrelated
   * nodes sitting in that same region, so edge routing stays consistent.
   */
  function separateDisjointGroups(positions, groups) {
    if (!groups || groups.length < 2) return;
    function box(g) {
      var members = (g.members || []).filter(function (m) { return positions[m]; });
      if (!members.length) return null;
      return {
        x0: Math.min.apply(null, members.map(function (m) { return positions[m].x; })) - 16,
        y0: Math.min.apply(null, members.map(function (m) { return positions[m].y; })) - 16,
        x1: Math.max.apply(null, members.map(function (m) { return positions[m].x + positions[m].w; })) + 16,
        y1: Math.max.apply(null, members.map(function (m) { return positions[m].y + positions[m].h; })) + 16,
      };
    }
    for (var pass = 0; pass < groups.length; pass++) {
      var movedAny = false;
      for (var i = 0; i < groups.length; i++) {
        for (var j = i + 1; j < groups.length; j++) {
          var ga = groups[i], gb = groups[j];
          var sa = ga.members || [], sb = gb.members || [];
          if (sa.some(function (m) { return sb.indexOf(m) !== -1; })) continue; // share a member — not disjoint
          var ba = box(ga), bb = box(gb);
          if (!ba || !bb) continue;
          var overlapX = Math.min(ba.x1, bb.x1) - Math.max(ba.x0, bb.x0);
          var overlapY = Math.min(ba.y1, bb.y1) - Math.max(ba.y0, bb.y0);
          if (overlapX <= 0 || overlapY <= 0) continue;
          movedAny = true;
          var aC = { x: (ba.x0 + ba.x1) / 2, y: (ba.y0 + ba.y1) / 2 };
          var bC = { x: (bb.x0 + bb.x1) / 2, y: (bb.y0 + bb.y1) / 2 };
          if (overlapX <= overlapY) {
            var dir = bC.x >= aC.x ? 1 : -1;
            var threshold = dir > 0 ? Math.max(ba.x0, bb.x0) : Math.min(ba.x1, bb.x1);
            var delta = overlapX + 8;
            Object.keys(positions).forEach(function (id) {
              var p = positions[id];
              if (dir > 0 ? p.x >= threshold : p.x <= threshold) p.x += dir * delta;
            });
          } else {
            var dirY = bC.y >= aC.y ? 1 : -1;
            var thresholdY = dirY > 0 ? Math.max(ba.y0, bb.y0) : Math.min(ba.y1, bb.y1);
            var deltaY = overlapY + 8;
            Object.keys(positions).forEach(function (id) {
              var p = positions[id];
              if (dirY > 0 ? p.y >= thresholdY : p.y <= thresholdY) p.y += dirY * deltaY;
            });
          }
        }
      }
      if (!movedAny) break;
    }
  }

  /* ── SVG helpers ── */
  var SVG_NS = "http://www.w3.org/2000/svg";
  function el(tag, attrs) {
    var e = document.createElementNS(SVG_NS, tag);
    if (attrs) for (var k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }
  function text(x, y, str, attrs) {
    var t = el("text", attrs);
    t.setAttribute("x", x);
    t.setAttribute("y", y);
    t.textContent = str;
    return t;
  }

  function curve(sx, sy, ex, ey) {
    var dy = ey - sy;
    return {
      d: "M" + sx.toFixed(1) + "," + sy.toFixed(1) +
        " C" + sx.toFixed(1) + "," + (sy + dy * 0.45).toFixed(1) +
        " " + ex.toFixed(1) + "," + (ey - dy * 0.45).toFixed(1) +
        " " + ex.toFixed(1) + "," + ey.toFixed(1),
    };
  }

  /* ── Diagram drawing ── */
  function styleFor(table, kind) {
    return (table && table[kind]) || (table && table._default) || {};
  }

  function nodeGroupsMap(groups) {
    var m = {};
    (groups || []).forEach(function (g) {
      (g.members || []).forEach(function (mem) {
        (m[mem] = m[mem] || []).push(g.id);
      });
    });
    return m;
  }

  function drawDiagram(svg, visible, styles, positions, edgeVia, idPrefix) {
    var nodes = visible.nodes, edges = visible.edges, groups = visible.groups || [];
    var groupsById = visible.groupsById || {};
    if (!Object.keys(positions).length) {
      svg.appendChild(text(200, 100, "No nodes", { "text-anchor": "middle", fill: "#87867F" }));
      return;
    }

    var W = 0, H = 0;
    Object.keys(positions).forEach(function (id) {
      var p = positions[id];
      W = Math.max(W, p.x + p.w);
      H = Math.max(H, p.y + p.h);
    });
    W += PAD; H += PAD;
    svg.setAttribute("viewBox", "0 0 " + Math.round(W) + " " + Math.round(H));

    var nodeGroups = nodeGroupsMap(groups);

    var defs = el("defs");
    svg.appendChild(defs);
    var colorsUsed = {};
    edges.forEach(function (e) { colorsUsed[styleFor(styles.edge, e.kind).color || "#C8C5BC"] = true; });
    colorsUsed[styles.edge._default.color] = true;
    Object.keys(colorsUsed).forEach(function (color) {
      var cid = idPrefix + color.replace("#", "");
      var marker = el("marker", { id: "arr-" + cid, markerWidth: 7, markerHeight: 7, refX: 6, refY: 3.5, orient: "auto" });
      marker.appendChild(el("path", { d: "M0,0 L0,7 L7,3.5 z", fill: color }));
      defs.appendChild(marker);
    });

    /* groups (bounding boxes, drawn first) — only currently-expanded groups
       reach here at all; a collapsed group is a node (see drawn placeholder
       below), not a box. Boxes nest: a group containing an expanded
       sub-group extends to cover that sub-group's own box, computed
       recursively from real positions up through the nesting. */
    var rawBoxCache = {};
    function computeRawBox(gid) {
      if (rawBoxCache.hasOwnProperty(gid)) return rawBoxCache[gid];
      var g = groupsById[gid];
      var x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, any = false;
      (g.members || []).forEach(function (m) {
        var b = null;
        if (positions[m]) {
          b = { x0: positions[m].x, y0: positions[m].y, x1: positions[m].x + positions[m].w, y1: positions[m].y + positions[m].h };
        } else if (groupsById[m]) {
          b = computeRawBox(m);
        }
        if (b) { any = true; x0 = Math.min(x0, b.x0); y0 = Math.min(y0, b.y0); x1 = Math.max(x1, b.x1); y1 = Math.max(y1, b.y1); }
      });
      var box = any ? { x0: x0, y0: y0, x1: x1, y1: y1 } : null;
      rawBoxCache[gid] = box;
      return box;
    }

    groups.forEach(function (g) {
      var raw = computeRawBox(g.id);
      if (!raw) return;
      var gx0 = raw.x0 - 16, gy0 = raw.y0 - 28, gx1 = raw.x1 + 16, gy1 = raw.y1 + 16;
      var gst = styleFor(styles.group, g.kind);
      var gg = el("g", { class: "sys-group", "data-gid": g.id });
      gg.appendChild(el("rect", {
        x: gx0.toFixed(1), y: gy0.toFixed(1), width: (gx1 - gx0).toFixed(1), height: (gy1 - gy0).toFixed(1),
        rx: 12, fill: gst.fill, stroke: gst.stroke, "stroke-width": 1, "stroke-dasharray": "5,3",
      }));
      var labelText = text(gx0 + 10, gy0 + 17, g.label || g.id, {
        "font-family": "ui-monospace,monospace", "font-size": 10, fill: gst.stroke, opacity: 0.9,
      });
      gg.appendChild(labelText);
      var collapseBtn = text(gx1 - 14, gy0 + 17, "✕", {
        "font-family": "ui-monospace,monospace", "font-size": 11, fill: gst.stroke,
        style: "cursor:pointer", "text-anchor": "middle", class: "sys-expand-btn",
      });
      collapseBtn.addEventListener("click", function (evt) {
        evt.stopPropagation();
        window.sysToggleGroup(svg.closest(".sys-arch-scope"), g.id, false);
      });
      gg.appendChild(collapseBtn);
      svg.appendChild(gg);
    });

    /* edges */
    edges.forEach(function (edge, edgeIdx) {
      var sp = positions[edge.from], dp = positions[edge.to];
      if (!sp || !dp || edge.from === edge.to) return;
      var sx = sp.x + sp.w / 2, sy = sp.y + sp.h;
      var ex = dp.x + dp.w / 2, ey = dp.y;
      var est = styleFor(styles.edge, edge.kind);
      var color = est.color || styles.edge._default.color;
      var dashed = !!est.dashed || !!edge.async;
      var cid = idPrefix + color.replace("#", "");
      var g = el("g", {
        class: "sys-edge", "data-kind": edge.kind || "",
        "data-from": idPrefix + edge.from, "data-to": idPrefix + edge.to,
        "data-src-groups": (nodeGroups[edge.from] || []).join(" "),
        "data-dst-groups": (nodeGroups[edge.to] || []).join(" "),
      });
      // Long edges (spanning more than one layer) route through reserved
      // via-lane points instead of one straight curve, so they never cut
      // through a real node sitting in an intermediate layer.
      var vias = (edgeVia[edgeIdx] || []).map(function (viaId) {
        var vp = positions[viaId];
        return { x: vp.x + vp.w / 2, y: vp.y + vp.h / 2 };
      });
      var points = [{ x: sx, y: sy }].concat(vias, [{ x: ex, y: ey }]);
      var d = "";
      for (var i = 0; i < points.length - 1; i++) {
        var seg = curve(points[i].x, points[i].y, points[i + 1].x, points[i + 1].y);
        d += i === 0 ? seg.d : seg.d.replace(/^M[^C]*/, " ");
      }
      var pathAttrs = { d: d, fill: "none", stroke: color, "stroke-width": 1.5, "marker-end": "url(#arr-" + cid + ")" };
      if (dashed) pathAttrs["stroke-dasharray"] = "6,4";
      g.appendChild(el("path", pathAttrs));
      if (edge.label) {
        // Label sits at the midpoint of the routed path, not the straight
        // src-to-dst line — for a via-routed edge that's the via point
        // itself, not wherever the line used to pass before being rerouted.
        var midIdx = (points.length - 1) / 2;
        var mx, my;
        if (Number.isInteger(midIdx)) {
          mx = points[midIdx].x; my = points[midIdx].y;
        } else {
          var i0 = Math.floor(midIdx), i1 = Math.ceil(midIdx);
          mx = (points[i0].x + points[i1].x) / 2;
          my = (points[i0].y + points[i1].y) / 2;
        }
        var lw = edge.label.length * 5.8 + 10;
        g.appendChild(el("rect", { x: (mx - lw / 2).toFixed(1), y: (my - 9).toFixed(1), width: lw.toFixed(1), height: 14, rx: 3, fill: "rgba(250,249,245,0.92)" }));
        g.appendChild(text(mx, my + 2, edge.label, { "text-anchor": "middle", "font-family": "ui-monospace,monospace", "font-size": 10, fill: color }));
      }
      svg.appendChild(g);
    });

    /* nodes — real leaf nodes, plus collapsed-group placeholders (which
       carry _isGroupPlaceholder and are styled from the group table) */
    nodes.forEach(function (node) {
      var p = positions[node.id];
      if (!p) return;
      var isPlaceholder = !!node._isGroupPlaceholder;
      var nst = isPlaceholder ? styleFor(styles.group, node._groupKind) : styleFor(styles.node, node.kind);
      var stroke = nst.stroke, fill = nst.fill;
      if (!isPlaceholder && node.status && styles.changeStatus[node.status]) {
        stroke = styles.changeStatus[node.status].stroke;
        fill = styles.changeStatus[node.status].fill;
      }
      var groupStr = (nodeGroups[node.id] || []).join(" ");
      var g = el("g", {
        class: "sys-node", "data-id": idPrefix + node.id, "data-kind": node.kind || "",
        "data-status": node.status || "", "data-groups": groupStr, style: "cursor:pointer",
      });
      if (node.status === "deleted") g.setAttribute("opacity", "0.5");
      g.appendChild(el("rect", { x: p.x.toFixed(1), y: p.y.toFixed(1), width: p.w, height: p.h, rx: 10, fill: fill, stroke: stroke, "stroke-width": 1.5, class: "sys-nr" }));
      g.appendChild(text(p.x + 11, p.y + p.h / 2 - 3, isPlaceholder ? "▣" : (nst.icon || "○"), { "dominant-baseline": "middle", "font-family": "ui-monospace,monospace", "font-size": 10, fill: stroke, opacity: 0.75 }));
      var maxChars = maxCharsFor(p.w);
      g.appendChild(text(p.x + 27, p.y + p.h / 2 - 6, truncate(node.label || node.id, maxChars), { "font-family": "ui-serif,Georgia,serif", "font-size": 13, "font-weight": 500, fill: "#141413" }));
      if (node.tech) {
        g.appendChild(text(p.x + 27, p.y + p.h / 2 + 10, truncate(node.tech, maxChars), { "font-family": "ui-monospace,monospace", "font-size": 10, fill: "#87867F" }));
      }
      if (isPlaceholder) {
        var expandBtn = text(p.x + p.w - 14, p.y + 15, "⤢", {
          "font-family": "ui-monospace,monospace", "font-size": 12, fill: stroke,
          style: "cursor:pointer", "text-anchor": "middle", class: "sys-expand-btn",
        });
        expandBtn.addEventListener("click", function (evt) {
          evt.stopPropagation();
          window.sysToggleGroup(svg.closest(".sys-arch-scope"), node.id, true);
        });
        g.appendChild(expandBtn);
      }
      g.addEventListener("click", function () { window.sysClick(g); });
      svg.appendChild(g);
    });
  }

  /* ── Sequence overlay (animate paths) ──
   * Steps reference real leaf node ids; `resolve` maps each endpoint to
   * whatever is actually drawn right now (the leaf itself, or the nearest
   * collapsed ancestor's placeholder), so Animate works regardless of which
   * groups happen to be expanded. */
  function drawOverlay(svg, sequences, positions, idPrefix, resolve) {
    (sequences || []).forEach(function (seq) {
      (seq.steps || []).forEach(function (step, i) {
        var fromId = resolve(step.from), toId = resolve(step.to);
        var sp = positions[fromId], dp = positions[toId];
        if (!sp || !dp) return;
        var gid = "ov-" + idPrefix + seq.id + "-" + i;
        var g = el("g", {
          class: "seq-step-ov", id: gid, "data-seq": seq.id, "data-step": i,
          "data-from": idPrefix + fromId, "data-to": idPrefix + toId, style: "opacity:0",
        });
        var pathD, dotX, dotY;
        if (fromId === toId) {
          var cx = sp.x + sp.w, cy = sp.y + sp.h / 2;
          pathD = "M" + cx.toFixed(1) + "," + (cy - 8).toFixed(1) +
            " Q" + (cx + 24).toFixed(1) + "," + (cy - 8).toFixed(1) + " " + (cx + 24).toFixed(1) + "," + cy.toFixed(1) +
            " Q" + (cx + 24).toFixed(1) + "," + (cy + 8).toFixed(1) + " " + cx.toFixed(1) + "," + (cy + 8).toFixed(1);
          dotX = cx; dotY = cy - 8;
        } else {
          var sx = sp.x + sp.w / 2, sy = sp.y + sp.h;
          var ex = dp.x + dp.w / 2, ey = dp.y;
          pathD = curve(sx, sy, ex, ey).d;
          dotX = sx; dotY = sy;
        }
        g.appendChild(el("path", { class: "seq-ov-path", d: pathD, fill: "none", stroke: "#D97757", "stroke-width": 2 }));
        g.appendChild(el("circle", { class: "seq-dot", cx: dotX.toFixed(1), cy: dotY.toFixed(1), r: 5, fill: "#D97757" }));
        svg.appendChild(g);
      });
    });
  }

  /* ── Expand/collapse: visible-graph computation ──
   * A node/group is visible iff every ancestor in its parent chain is
   * expanded. A group that is itself visible but not expanded is drawn as
   * a single placeholder node standing in for its whole subtree. Every
   * edge endpoint is resolved to its nearest visible ancestor — always
   * unambiguous, since each id has at most one parent (validated
   * server-side). */
  function buildParentMap(groups) {
    var parentOf = {};
    (groups || []).forEach(function (g) {
      (g.members || []).forEach(function (m) { parentOf[m] = g.id; });
    });
    return parentOf;
  }

  function isVisible(id, parentOf, expandedSet, memo) {
    if (memo.hasOwnProperty(id)) return memo[id];
    var p = parentOf[id];
    var result;
    if (p === undefined) result = true;
    else if (!expandedSet.has(p)) result = false;
    else result = isVisible(p, parentOf, expandedSet, memo);
    memo[id] = result;
    return result;
  }

  function drawnAncestorFor(leafId, parentOf, expandedSet, memo) {
    if (isVisible(leafId, parentOf, expandedSet, memo)) return leafId;
    var cur = parentOf[leafId];
    while (cur !== undefined) {
      if (isVisible(cur, parentOf, expandedSet, memo) && !expandedSet.has(cur)) return cur;
      cur = parentOf[cur];
    }
    return leafId; // shouldn't happen given the single-parent invariant
  }

  function getVisibleGraph(spec, expandedSet) {
    var groupsById = {};
    (spec.groups || []).forEach(function (g) { groupsById[g.id] = g; });
    var parentOf = buildParentMap(spec.groups);
    var memo = {};

    var nodes = (spec.nodes || []).filter(function (n) {
      return isVisible(n.id, parentOf, expandedSet, memo);
    });

    (spec.groups || []).forEach(function (g) {
      if (isVisible(g.id, parentOf, expandedSet, memo) && !expandedSet.has(g.id)) {
        var count = (g.members || []).length;
        nodes.push({
          id: g.id, label: g.label || g.id, kind: g.kind,
          tech: count + (count === 1 ? " member" : " members"),
          _isGroupPlaceholder: true, _groupKind: g.kind,
        });
      }
    });

    var visibleGroups = (spec.groups || []).filter(function (g) {
      return isVisible(g.id, parentOf, expandedSet, memo) && expandedSet.has(g.id);
    });

    var edges = [];
    (spec.edges || []).forEach(function (e) {
      var from = drawnAncestorFor(e.from, parentOf, expandedSet, memo);
      var to = drawnAncestorFor(e.to, parentOf, expandedSet, memo);
      if (from === to) return; // both endpoints collapsed into the same visible box
      edges.push(Object.assign({}, e, { from: from, to: to }));
    });

    function resolve(id) { return drawnAncestorFor(id, parentOf, expandedSet, memo); }

    return { nodes: nodes, edges: edges, groups: visibleGroups, groupsById: groupsById, resolve: resolve };
  }

  /* ── Public API ── */
  function renderDiagram(payload, mountEl, idPrefix) {
    mountEl.innerHTML = "";
    var svg = el("svg", { style: "display:block;width:100%;height:auto;max-height:680px", id: idPrefix + "sys-svg" });
    mountEl.appendChild(svg);

    if (!mountEl._archExpandedSet) mountEl._archExpandedSet = new Set();
    var visible = getVisibleGraph(payload.spec, mountEl._archExpandedSet);
    var layout = layoutGraph(visible.nodes, visible.edges, visible.groups);
    drawDiagram(svg, visible, payload.styles, layout.positions, layout.edgeVia, idPrefix);
    drawOverlay(svg, payload.spec.sequences, layout.positions, idPrefix, visible.resolve);

    mountEl._archPayload = payload;
    mountEl._archIdPrefix = idPrefix;
  }

  window.sysToggleGroup = function (scope, groupId, expand) {
    if (!scope) return;
    var mountEl = scope.querySelector(".sys-mount");
    if (!mountEl || !mountEl._archPayload) return;
    if (!mountEl._archExpandedSet) mountEl._archExpandedSet = new Set();
    if (expand) mountEl._archExpandedSet.add(groupId);
    else mountEl._archExpandedSet.delete(groupId);
    renderDiagram(mountEl._archPayload, mountEl, mountEl._archIdPrefix);
  };

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".sys-mount").forEach(function (mountEl) {
      var dataEl = document.getElementById(mountEl.getAttribute("data-source"));
      if (!dataEl) return;
      var payload = JSON.parse(dataEl.textContent);
      renderDiagram(payload, mountEl, mountEl.getAttribute("data-prefix") || "");
    });
  });
})();
