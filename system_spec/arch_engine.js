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
 */
(function () {
  "use strict";

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

  /* ── Sugiyama-style layered layout, applied per-level ──
   * Four phases, run independently for whatever flat sibling list is
   * passed in: (1) cycle removal via DFS back-edge detection, so the graph
   * fed to ranking is always a DAG regardless of real feedback edges
   * (retries, callbacks, reroutes — common in real architectures); (2) rank
   * assignment via Kahn's longest-path on that acyclic subgraph; (3)
   * crossing reduction via iterative median/barycenter sweeps; (4)
   * coordinate assignment (per-layer centering, with per-row height to
   * accommodate a child that's itself a large expanded-group box). */

  // Phase 1: classic DFS back-edge detection (white/gray/black coloring,
  // iterative to avoid recursion-depth limits). An edge to a node currently
  // on the DFS stack (gray) closes a cycle — flag it by index. Removing
  // these edges from the graph used for ranking is guaranteed to yield a
  // DAG, so every node gets a real, finite rank with no "stray" fallback.
  //
  // Which edge in a cycle gets flagged as "the" back edge depends on DFS
  // root order — starting from a node that's itself mid-cycle (rather than
  // a true source) can flag the wrong edge (e.g. the legitimate forward
  // edge instead of the actual feedback edge), which then makes the
  // upstream node rank AFTER its own downstream dependent. Since which
  // nodes are mid-cycle vs true sources is exactly what raw in-degree
  // tells you, visit roots in ascending raw-in-degree order (ties keep
  // original order) so genuine sources are always explored first.
  function findBackEdgeSet(nodeIds, edges, nodeIdSet) {
    var adj = {};
    nodeIds.forEach(function (id) { adj[id] = []; });
    var rawInDeg = {};
    nodeIds.forEach(function (id) { rawInDeg[id] = 0; });
    edges.forEach(function (e, i) {
      if (e.from !== e.to && nodeIdSet[e.from] && nodeIdSet[e.to]) {
        adj[e.from].push({ to: e.to, idx: i });
        rawInDeg[e.to]++;
      }
    });
    var rootOrder = nodeIds.slice().sort(function (a, b) { return rawInDeg[a] - rawInDeg[b]; });

    var color = {}; // undefined=white, 1=gray, 2=black
    var backEdges = {};
    rootOrder.forEach(function (start) {
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

  // Phase 3: median/barycenter crossing reduction. Alternates top-down
  // (order each layer using the already-fixed layer above as reference)
  // and bottom-up (using the layer below) sweeps.
  function orderLayersByBarycenter(layersMap, layerKeys, predsOf, succsOf) {
    layerKeys.forEach(function (l) {
      layersMap[l].sort(function (a, b) { return a < b ? -1 : a > b ? 1 : 0; });
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
      var ids = layersMap[l].slice();
      var bcOf = {};
      ids.forEach(function (id) { bcOf[id] = barycenter(id, neighborsOf(id)); });
      ids.sort(function (a, b) {
        var ba = bcOf[a], bb = bcOf[b];
        if (ba === null && bb === null) return a < b ? -1 : a > b ? 1 : 0;
        if (ba === null) return 1;
        if (bb === null) return -1;
        return ba - bb || (a < b ? -1 : a > b ? 1 : 0);
      });
      layersMap[l] = ids;
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

  // The full per-level layout: takes a flat sibling list, a size-lookup
  // (so an expanded child can be sized as a large opaque box instead of a
  // normal node), and the edges that are "local" to this level (both
  // endpoints are members of this same sibling list). Returns positions
  // (top-left, in this level's own coordinate frame starting near (0,0)),
  // per-edge via-lane points for multi-layer edges, and the level's own
  // total width/height — which is exactly what the PARENT level needs to
  // size this whole level as a single box, if it's itself nested.
  function layoutFlat(memberIds, sizeOf, edges) {
    edges = edges || [];
    var nodeIdSet = {};
    memberIds.forEach(function (id) { nodeIdSet[id] = true; });

    var backEdges = findBackEdgeSet(memberIds, edges, nodeIdSet);

    var inDeg = {}, succs = {};
    memberIds.forEach(function (id) { inDeg[id] = 0; succs[id] = []; });
    edges.forEach(function (e, i) {
      if (e.from !== e.to && nodeIdSet[e.from] && nodeIdSet[e.to] && !backEdges[i]) {
        succs[e.from].push(e.to);
        inDeg[e.to]++;
      }
    });

    var layer = {};
    var queue = [];
    memberIds.forEach(function (id) { if (inDeg[id] === 0) { layer[id] = 0; queue.push(id); } });
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
    memberIds.forEach(function (id) { if (layer[id] !== undefined) maxL = Math.max(maxL, layer[id]); });
    // Defensive only — removing DFS back edges always yields a DAG, so
    // every node should already have a rank from the BFS above.
    memberIds.forEach(function (id) { if (layer[id] === undefined) { maxL++; layer[id] = maxL; } });

    var layersMap = {};
    memberIds.forEach(function (id) { (layersMap[layer[id]] = layersMap[layer[id]] || []).push(id); });

    var predsOf = {}, succsOf = {};
    memberIds.forEach(function (id) { predsOf[id] = []; succsOf[id] = []; });
    edges.forEach(function (e) {
      if (e.from === e.to || !nodeIdSet[e.from] || !nodeIdSet[e.to]) return;
      succsOf[e.from].push(e.to);
      predsOf[e.to].push(e.from);
    });
    var rankLayerKeys = Object.keys(layersMap).map(Number).sort(function (a, b) { return a - b; });
    orderLayersByBarycenter(layersMap, rankLayerKeys, predsOf, succsOf);

    // Reserve a via-lane in every intermediate layer for edges that skip
    // more than one layer, so the edge has somewhere of its own to pass
    // through instead of cutting across a real node sitting between its
    // endpoints. Keyed by LOCAL edge index — the caller (buildLevel, for
    // the hierarchical case) remaps this to a globally-unique id and to
    // the original (pre-resolution) edge index.
    var edgeVia = {};
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

    var widths = {}, heights = {};
    memberIds.forEach(function (id) { var sz = sizeOf(id); widths[id] = sz.w; heights[id] = sz.h; });
    Object.keys(edgeVia).forEach(function (i) {
      edgeVia[i].forEach(function (v) { widths[v] = 24; heights[v] = NODE_H; });
    });

    var layerKeys = Object.keys(layersMap).map(Number).sort(function (a, b) { return a - b; });
    var maxLayerW = 0;
    layerKeys.forEach(function (l) {
      var ns = layersMap[l];
      var w = ns.reduce(function (s, idd) { return s + widths[idd]; }, 0) + Math.max(0, ns.length - 1) * H_GAP;
      maxLayerW = Math.max(maxLayerW, w);
    });

    var positions = {};
    var y = PAD;
    layerKeys.forEach(function (l) {
      var ns = layersMap[l];
      var rowH = Math.max.apply(null, ns.map(function (idd) { return heights[idd] || NODE_H; }));
      var layerW = ns.reduce(function (s, idd) { return s + widths[idd]; }, 0) + Math.max(0, ns.length - 1) * H_GAP;
      var x = PAD + (maxLayerW - layerW) / 2;
      ns.forEach(function (idd) {
        var h = heights[idd] || NODE_H;
        positions[idd] = { x: x, y: y + (rowH - h) / 2, w: widths[idd], h: h };
        x += widths[idd] + H_GAP;
      });
      y += rowH + V_GAP;
    });

    var W = 0, H = 0;
    Object.keys(positions).forEach(function (idd) {
      var p = positions[idd];
      W = Math.max(W, p.x + p.w);
      H = Math.max(H, p.y + p.h);
    });
    W += PAD; H += PAD;

    return { positions: positions, edgeVia: edgeVia, w: W, h: H };
  }

  /* ── Hierarchical layout: recurse into each expanded group ──
   * Bottom-up: an expanded group's own members are laid out completely
   * independently (as if they were the whole diagram), and the resulting
   * {w,h} becomes that group's box size one level up. Top-down (via the
   * return-value chain, not a second pass): each level translates its
   * children's already-computed local positions into its own coordinate
   * frame as soon as it knows where it placed each child's box. */
  function layoutHierarchy(spec, expandedSet, resolvedEdges) {
    var groupsById = {};
    (spec.groups || []).forEach(function (g) { groupsById[g.id] = g; });
    var nodeById = {};
    (spec.nodes || []).forEach(function (n) { nodeById[n.id] = n; });
    var parentOf = buildParentMap(spec.groups);

    function membersOf(containerId) {
      if (containerId === null) {
        var ids = [];
        (spec.nodes || []).forEach(function (n) { if (parentOf[n.id] === undefined) ids.push(n.id); });
        (spec.groups || []).forEach(function (g) { if (parentOf[g.id] === undefined) ids.push(g.id); });
        return ids;
      }
      return (groupsById[containerId].members || []);
    }

    // Walk up from `id` until hitting the direct child of `containerId` —
    // i.e. which of THIS level's siblings `id` lives under (or is itself).
    // Returns null if `id` isn't under containerId at all.
    function ancestorAtLevel(id, containerId) {
      var cur = id;
      while (true) {
        var p = parentOf[cur];
        if (containerId === null ? p === undefined : p === containerId) return cur;
        if (p === undefined) return null;
        cur = p;
      }
    }

    var viaCounter = 0;
    var edgeViaByOrigIdx = {};

    function buildLevel(containerId) {
      var members = membersOf(containerId);
      var childSize = {};
      var childInner = {};

      members.forEach(function (id) {
        var g = groupsById[id];
        if (g) {
          if (expandedSet.has(id)) {
            var inner = buildLevel(id); // recurse first — bottom-up sizing
            childInner[id] = inner;
            childSize[id] = { w: inner.w + 2 * GROUP_PAD_X, h: inner.h + GROUP_PAD_TOP + GROUP_PAD_BOTTOM };
          } else {
            var count = (g.members || []).length;
            childSize[id] = { w: estWidth({ label: g.label || id, tech: count + (count === 1 ? " member" : " members") }), h: NODE_H };
          }
        } else {
          var n = nodeById[id];
          childSize[id] = { w: estWidth(n), h: NODE_H };
        }
      });

      // Local edges: any (already-resolved) edge whose two endpoints
      // resolve to two DIFFERENT direct children of this container. An
      // edge fully inside one child (e.g. internal to a nested expanded
      // group) is skipped here — it's already handled one level down.
      var localEdges = [];
      resolvedEdges.forEach(function (e, idx) {
        var a = ancestorAtLevel(e.from, containerId);
        var b = ancestorAtLevel(e.to, containerId);
        if (a !== null && b !== null && a !== b) localEdges.push({ from: a, to: b, _origIdx: idx });
      });

      var flat = layoutFlat(members, function (id) { return childSize[id]; }, localEdges);

      // Give this level's via-lane dummies globally-unique ids (so they
      // never collide with another level's), and record, per ORIGINAL
      // (pre-resolution-index) edge, which via ids it ended up with.
      var renamed = {};
      Object.keys(flat.positions).forEach(function (key) {
        if (key.indexOf("__via_") === 0) renamed[key] = "__via_g" + (viaCounter++);
      });
      localEdges.forEach(function (le, k) {
        var vias = flat.edgeVia[k];
        if (vias) edgeViaByOrigIdx[le._origIdx] = vias.map(function (v) { return renamed[v]; });
      });

      var positions = {};
      Object.keys(flat.positions).forEach(function (key) {
        positions[renamed[key] || key] = flat.positions[key];
      });

      var groupBoxesLocal = {};
      members.forEach(function (id) {
        if (!childInner[id]) return; // leaf or collapsed placeholder — nothing further to place
        var origin = positions[id]; // top-left + size this level assigned to the box
        delete positions[id]; // an expanded group is drawn as a box, not as a node
        groupBoxesLocal[id] = { x0: origin.x, y0: origin.y, x1: origin.x + origin.w, y1: origin.y + origin.h };
        var inner = childInner[id];
        var offX = origin.x + GROUP_PAD_X, offY = origin.y + GROUP_PAD_TOP;
        Object.keys(inner.positions).forEach(function (iid) {
          var ip = inner.positions[iid];
          positions[iid] = { x: offX + ip.x, y: offY + ip.y, w: ip.w, h: ip.h };
        });
        Object.keys(inner.groupBoxesLocal).forEach(function (gid) {
          var b = inner.groupBoxesLocal[gid];
          groupBoxesLocal[gid] = { x0: offX + b.x0, y0: offY + b.y0, x1: offX + b.x1, y1: offY + b.y1 };
        });
      });

      return { positions: positions, w: flat.w, h: flat.h, groupBoxesLocal: groupBoxesLocal };
    }

    var top = buildLevel(null);
    return { positions: top.positions, groupBoxes: top.groupBoxesLocal, edgeVia: edgeViaByOrigIdx, w: top.w, h: top.h };
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

  function drawDiagram(svg, visible, styles, layout, idPrefix) {
    var nodes = visible.nodes, edges = visible.edges, groupsById = visible.groupsById || {};
    var positions = layout.positions, groupBoxes = layout.groupBoxes, edgeVia = layout.edgeVia;
    if (!Object.keys(positions).length && !Object.keys(groupBoxes).length) {
      svg.appendChild(text(200, 100, "No nodes", { "text-anchor": "middle", fill: "#87867F" }));
      return;
    }

    svg.setAttribute("viewBox", "0 0 " + Math.round(layout.w) + " " + Math.round(layout.h));

    function directGroupOf(id) { return visible.parentOf[id] !== undefined ? [visible.parentOf[id]] : []; }

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

    /* groups (bounding boxes, drawn first) — sizes/positions come directly
       from the hierarchical layout, which already reserved exactly this
       much space for the group one level up; no further computation
       needed here, and nothing else can ever end up inside one. */
    Object.keys(groupBoxes).forEach(function (gid) {
      var b = groupBoxes[gid];
      var g = groupsById[gid];
      var gst = styleFor(styles.group, g && g.kind);
      var gg = el("g", { class: "sys-group", "data-gid": gid });
      gg.appendChild(el("rect", {
        x: b.x0.toFixed(1), y: b.y0.toFixed(1), width: (b.x1 - b.x0).toFixed(1), height: (b.y1 - b.y0).toFixed(1),
        rx: 12, fill: gst.fill, stroke: gst.stroke, "stroke-width": 1, "stroke-dasharray": "5,3",
      }));
      gg.appendChild(text(b.x0 + 10, b.y0 + 17, (g && g.label) || gid, {
        "font-family": "ui-monospace,monospace", "font-size": 10, fill: gst.stroke, opacity: 0.9,
      }));
      var collapseBtn = text(b.x1 - 14, b.y0 + 17, "✕", {
        "font-family": "ui-monospace,monospace", "font-size": 11, fill: gst.stroke,
        style: "cursor:pointer", "text-anchor": "middle", class: "sys-expand-btn",
      });
      collapseBtn.addEventListener("click", function (evt) {
        evt.stopPropagation();
        window.sysToggleGroup(svg.closest(".sys-arch-scope"), gid, false);
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
        "data-src-groups": directGroupOf(edge.from).join(" "),
        "data-dst-groups": directGroupOf(edge.to).join(" "),
      });
      // Long edges (spanning more than one layer, at whichever level they
      // were attributed to) route through reserved via-lane points
      // instead of one straight curve, so they never cut through a real
      // node sitting in an intermediate layer.
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
      var groupStr = directGroupOf(node.id).join(" ");
      var g = el("g", {
        class: "sys-node", "data-id": idPrefix + node.id, "data-kind": node.kind || "",
        "data-status": node.status || "", "data-groups": groupStr, style: "cursor:pointer",
        // A collapsed group's placeholder carries the GROUP's own kind
        // (e.g. "layer"), not a real node kind — the kind-filter bar only
        // ever lists real node kinds, so without this marker the filter
        // logic would treat the placeholder as matching no kind filter at
        // all and hide it unconditionally. data-group-id (raw, unprefixed
        // — matches the group filter buttons' data-ag) lets the filter
        // logic apply the GROUP filter to it instead.
        "data-is-group": isPlaceholder ? "1" : "",
        "data-group-id": isPlaceholder ? node.id : "",
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

    var edges = [];
    (spec.edges || []).forEach(function (e) {
      var from = drawnAncestorFor(e.from, parentOf, expandedSet, memo);
      var to = drawnAncestorFor(e.to, parentOf, expandedSet, memo);
      if (from === to) return; // both endpoints collapsed into the same visible box
      edges.push(Object.assign({}, e, { from: from, to: to }));
    });

    function resolve(id) { return drawnAncestorFor(id, parentOf, expandedSet, memo); }

    return { nodes: nodes, edges: edges, groupsById: groupsById, parentOf: parentOf, resolve: resolve };
  }

  /* ── Public API ── */
  function renderDiagram(payload, mountEl, idPrefix) {
    mountEl.innerHTML = "";
    var svg = el("svg", { style: "display:block;width:100%;height:auto;max-height:680px", id: idPrefix + "sys-svg" });
    mountEl.appendChild(svg);

    if (!mountEl._archExpandedSet) mountEl._archExpandedSet = new Set();
    var visible = getVisibleGraph(payload.spec, mountEl._archExpandedSet);
    var layout = layoutHierarchy(payload.spec, mountEl._archExpandedSet, visible.edges);
    drawDiagram(svg, visible, payload.styles, layout, idPrefix);
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
