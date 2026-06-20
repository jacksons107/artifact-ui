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
