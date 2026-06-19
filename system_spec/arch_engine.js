/* ── Architecture diagram engine ──────────────────────────────────────────
 * Client-side port of layout.py + svg_architecture.py + seq_overlay.py.
 * This is the ONLY place node/edge/group positions are computed for the
 * Architecture tab and every Code Detail module — both the first paint and
 * every later expand/collapse call the same renderDiagram(), so there is
 * never a second layout implementation to keep in sync.
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

  /* ── Layout: Kahn's longest-path layering, variable node width ── */
  function layoutGraph(nodes, edges, groups) {
    edges = edges || [];
    var nodeIds = nodes.map(function (n) { return n.id; });
    var nodeIdSet = {}; nodeIds.forEach(function (id) { nodeIdSet[id] = true; });
    var nodeGroup = {};
    (groups || []).forEach(function (g) {
      (g.members || []).forEach(function (m) { if (!(m in nodeGroup)) nodeGroup[m] = g.id; });
    });

    var inDeg = {}, succs = {};
    nodeIds.forEach(function (id) { inDeg[id] = 0; succs[id] = []; });
    edges.forEach(function (e) {
      if (e.from !== e.to && nodeIdSet[e.from] && nodeIdSet[e.to]) {
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
    nodeIds.forEach(function (id) { if (layer[id] === undefined) { maxL++; layer[id] = maxL; } });

    // Expanded-group floor correction: a freshly-spliced-in detail node with
    // no incoming edge of its own (e.g. it's only ever called FROM a sibling
    // inside the same group) would otherwise get seeded as a global root at
    // layer 0 by Kahn's above, regardless of where its group actually sits —
    // visually stranding it (and the group's bounding box) at the top of the
    // whole diagram. Pull such "stray" members up to their group's floor —
    // the lowest layer among siblings that DO have a real incoming edge —
    // then re-propagate forward so anything depending on the pulled-up node
    // stays consistent.
    var expandedGroups = (groups || []).filter(function (g) { return g._collapseTarget; });
    if (expandedGroups.length) {
      expandedGroups.forEach(function (g) {
        var members = g.members || [];
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
        edges.forEach(function (e) {
          if (e.from === e.to || !nodeIdSet[e.from] || !nodeIdSet[e.to]) return;
          if (layer[e.to] < layer[e.from] + 1) { layer[e.to] = layer[e.from] + 1; changed = true; }
        });
        if (!changed) break;
      }
    }
    function inDeg0Orig(id) {
      // Recompute original in-degree (the loop above mutates inDeg) — cheap enough at this scale.
      var n = 0;
      edges.forEach(function (e) { if (e.to === id && e.from !== id && nodeIdSet[e.from]) n++; });
      return n === 0;
    }

    var layersMap = {};
    nodeIds.forEach(function (id) { (layersMap[layer[id]] = layersMap[layer[id]] || []).push(id); });
    Object.keys(layersMap).forEach(function (l) {
      layersMap[l].sort(function (a, b) {
        var ga = nodeGroup[a] || "￿", gb = nodeGroup[b] || "￿";
        if (ga !== gb) return ga < gb ? -1 : 1;
        return a < b ? -1 : a > b ? 1 : 0;
      });
    });

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
        layersMap[l].push(viaId);
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
    return { positions: positions, edgeVia: edgeVia };
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

  function drawDiagram(svg, spec, styles, positions, edgeVia, idPrefix, expandable) {
    var nodes = spec.nodes, edges = spec.edges, groups = spec.groups || [];
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

    /* groups (bounding boxes, drawn first) — an expandable group's box only
       appears once it's actually expanded (the synthetic _collapseTarget
       group); the collapsed single node never gets a box hugging it. */
    groups.forEach(function (g) {
      var isExpandableSource = !!(g.detail && g.detail.nodes && g.detail.nodes.length) && !g._collapseTarget;
      if (isExpandableSource) return;
      var members = (g.members || []).filter(function (m) { return positions[m]; });
      if (!members.length) return;
      var gx0 = Math.min.apply(null, members.map(function (m) { return positions[m].x; })) - 16;
      var gy0 = Math.min.apply(null, members.map(function (m) { return positions[m].y; })) - 28;
      var gx1 = Math.max.apply(null, members.map(function (m) { return positions[m].x + positions[m].w; })) + 16;
      var gy1 = Math.max.apply(null, members.map(function (m) { return positions[m].y + positions[m].h; })) + 16;
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
      if (g._collapseTarget) {
        var collapseBtn = text(gx1 - 14, gy0 + 17, "✕", {
          "font-family": "ui-monospace,monospace", "font-size": 11, fill: gst.stroke,
          style: "cursor:pointer", "text-anchor": "middle", class: "sys-expand-btn",
        });
        collapseBtn.addEventListener("click", function (evt) {
          evt.stopPropagation();
          window.sysCollapseGroup(svg.closest(".sys-arch-scope"));
        });
        gg.appendChild(collapseBtn);
      }
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

    /* nodes */
    nodes.forEach(function (node) {
      var p = positions[node.id];
      if (!p) return;
      var nst = styleFor(styles.node, node.kind);
      var stroke = nst.stroke, fill = nst.fill;
      if (node.status && styles.changeStatus[node.status]) {
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
      g.appendChild(text(p.x + 11, p.y + p.h / 2 - 3, nst.icon || "○", { "dominant-baseline": "middle", "font-family": "ui-monospace,monospace", "font-size": 10, fill: stroke, opacity: 0.75 }));
      var maxChars = maxCharsFor(p.w);
      g.appendChild(text(p.x + 27, p.y + p.h / 2 - 6, truncate(node.label || node.id, maxChars), { "font-family": "ui-serif,Georgia,serif", "font-size": 13, "font-weight": 500, fill: "#141413" }));
      if (node.tech) {
        g.appendChild(text(p.x + 27, p.y + p.h / 2 + 10, truncate(node.tech, maxChars), { "font-family": "ui-monospace,monospace", "font-size": 10, fill: "#87867F" }));
      }
      if (expandable[node.id]) {
        var expandBtn = text(p.x + p.w - 14, p.y + 15, "⤢", {
          "font-family": "ui-monospace,monospace", "font-size": 12, fill: stroke,
          style: "cursor:pointer", "text-anchor": "middle", class: "sys-expand-btn",
        });
        expandBtn.addEventListener("click", function (evt) {
          evt.stopPropagation();
          window.sysExpandGroup(svg.closest(".sys-arch-scope"), expandable[node.id]);
        });
        g.appendChild(expandBtn);
      }
      g.addEventListener("click", function () { window.sysClick(g); });
      svg.appendChild(g);
    });
  }

  /* ── Sequence overlay (animate paths) — only drawn while not expanded ── */
  function drawOverlay(svg, sequences, positions, idPrefix) {
    (sequences || []).forEach(function (seq) {
      (seq.steps || []).forEach(function (step, i) {
        var sp = positions[step.from], dp = positions[step.to];
        if (!sp || !dp) return;
        var gid = "ov-" + idPrefix + seq.id + "-" + i;
        var g = el("g", {
          class: "seq-step-ov", id: gid, "data-seq": seq.id, "data-step": i,
          "data-from": idPrefix + step.from, "data-to": idPrefix + step.to, style: "opacity:0",
        });
        var pathD, dotX, dotY;
        if (step.from === step.to) {
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

  /* ── Expand/collapse data transforms ── */
  function findExpandableGroups(spec) {
    var map = {}; // member node id -> group id
    (spec.groups || []).forEach(function (g) {
      if (g.detail && g.detail.nodes && g.detail.nodes.length) {
        (g.members || []).forEach(function (m) { map[m] = g.id; });
      }
    });
    return map;
  }

  function buildExpandedSpec(spec, groupId) {
    var group = spec.groups.filter(function (g) { return g.id === groupId; })[0];
    var members = group.members || [];
    var detail = group.detail;
    var boundary = detail.boundary || {};

    var nodes = spec.nodes.filter(function (n) { return members.indexOf(n.id) === -1; }).concat(detail.nodes);

    // For each top-level edge touching an expanded member, redirect that endpoint to the
    // exact internal node named in detail.boundary[neighborId]. Edges fully inside or fully
    // outside the expanded group pass through unchanged.
    var edges = spec.edges.map(function (e) {
      var fromIsMember = members.indexOf(e.from) !== -1;
      var toIsMember = members.indexOf(e.to) !== -1;
      if (fromIsMember && !toIsMember) return Object.assign({}, e, { from: boundary[e.to] });
      if (toIsMember && !fromIsMember) return Object.assign({}, e, { to: boundary[e.from] });
      return e;
    }).concat(detail.edges || []);

    var groups = spec.groups.filter(function (g) { return g.id !== groupId; }).concat([{
      id: "_expanded_" + groupId, label: group.label, kind: group.kind,
      members: detail.nodes.map(function (n) { return n.id; }), _collapseTarget: true,
    }]).concat(detail.groups || []);

    return { nodes: nodes, edges: edges, groups: groups, sequences: spec.sequences };
  }

  /* ── Public API ── */
  function renderDiagram(payload, mountEl, idPrefix) {
    mountEl.innerHTML = "";
    var svg = el("svg", { style: "display:block;width:100%;height:auto;max-height:680px", id: idPrefix + "sys-svg" });
    mountEl.appendChild(svg);

    var spec = mountEl._archExpanded ? mountEl._archExpandedSpec : payload.spec;
    var expandable = mountEl._archExpanded ? {} : findExpandableGroups(payload.spec);
    var layout = layoutGraph(spec.nodes, spec.edges, spec.groups);
    drawDiagram(svg, spec, payload.styles, layout.positions, layout.edgeVia, idPrefix, expandable);
    if (!mountEl._archExpanded) drawOverlay(svg, payload.spec.sequences, layout.positions, idPrefix);

    mountEl._archPayload = payload;
    mountEl._archIdPrefix = idPrefix;
  }

  window.sysExpandGroup = function (scope, groupId) {
    if (!scope) return;
    var mountEl = scope.querySelector(".sys-mount");
    if (!mountEl || !mountEl._archPayload) return;
    mountEl._archExpandedSpec = buildExpandedSpec(mountEl._archPayload.spec, groupId);
    mountEl._archExpanded = true;
    renderDiagram(mountEl._archPayload, mountEl, mountEl._archIdPrefix);
  };

  window.sysCollapseGroup = function (scope) {
    if (!scope) return;
    var mountEl = scope.querySelector(".sys-mount");
    if (!mountEl || !mountEl._archPayload) return;
    mountEl._archExpanded = false;
    mountEl._archExpandedSpec = null;
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
