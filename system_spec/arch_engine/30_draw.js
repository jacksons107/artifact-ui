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
