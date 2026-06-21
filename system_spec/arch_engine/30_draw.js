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

/* Control points [p0,c1,c2,p3] for the vertical S-curve curve() draws —
 * factored out so label placement (15_label_layout.js, via
 * sampleEdgeSegment below) can sample the exact same curve it renders,
 * instead of approximating it with a straight line between anchors. */
function cubicControlPoints(sx, sy, ex, ey) {
  var dy = ey - sy;
  return [{ x: sx, y: sy }, { x: sx, y: sy + dy * 0.45 }, { x: ex, y: ey - dy * 0.45 }, { x: ex, y: ey }];
}

/* Same idea as cubicControlPoints(), but for side-anchored (back/same-row)
 * edges: the anchors sit on the right edge of each box, so the natural
 * bulge is horizontal (always outward to the right) rather than vertical —
 * a vertical-offset S-curve here would cut back across whatever sits
 * between the two boxes instead of looping around it. */
function cubicControlPointsSide(sx, sy, ex, ey) {
  var bulge = Math.max(40, Math.abs(ey - sy) * 0.3);
  return [{ x: sx, y: sy }, { x: sx + bulge, y: sy }, { x: ex + bulge, y: ey }, { x: ex, y: ey }];
}

function cubicPathD(pts) {
  return "M" + pts[0].x.toFixed(1) + "," + pts[0].y.toFixed(1) +
    " C" + pts[1].x.toFixed(1) + "," + pts[1].y.toFixed(1) +
    " " + pts[2].x.toFixed(1) + "," + pts[2].y.toFixed(1) +
    " " + pts[3].x.toFixed(1) + "," + pts[3].y.toFixed(1);
}

function curve(sx, sy, ex, ey) {
  return { d: cubicPathD(cubicControlPoints(sx, sy, ex, ey)) };
}

function curveSide(sx, sy, ex, ey) {
  return { d: cubicPathD(cubicControlPointsSide(sx, sy, ex, ey)) };
}

/* Samples a cubic bezier (Bernstein form) into `steps+1` points — used to
 * approximate an edge's actual rendered curve as a polyline, for label
 * placement's "does this box sit on top of some OTHER edge" check. */
function sampleCubic(pts, steps) {
  var out = [];
  for (var i = 0; i <= steps; i++) {
    var t = i / steps, mt = 1 - t;
    var a = mt * mt * mt, b = 3 * mt * mt * t, c = 3 * mt * t * t, d = t * t * t;
    out.push({
      x: a * pts[0].x + b * pts[1].x + c * pts[2].x + d * pts[3].x,
      y: a * pts[0].y + b * pts[1].y + c * pts[2].y + d * pts[3].y,
    });
  }
  return out;
}

/* Samples one consecutive point-pair's rendered curve segment — `back`
 * picks the same straight-vs-side control points drawDiagram's draw loop
 * uses, so the sampled polyline matches exactly what gets drawn. */
function sampleEdgeSegment(p0, p1, back, steps) {
  var pts = back
    ? cubicControlPointsSide(p0.x, p0.y, p1.x, p1.y)
    : cubicControlPoints(p0.x, p0.y, p1.x, p1.y);
  return sampleCubic(pts, steps || 12);
}

/* ── Diagram drawing ── */
function styleFor(table, kind) {
  return (table && table[kind]) || (table && table._default) || {};
}

function drawDiagram(svg, visible, styles, layout, idPrefix, routingMode) {
  routingMode = routingMode || "curve";
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

  /* edges — points/bends/polylines computed for every edge first, so both
     grid-mode routing (which needs every edge's points at once to keep two
     unrelated edges from bending at the same height, see
     routeEdgesOrthogonally) and label placement (which needs every OTHER
     edge's actual rendered path, see chooseLabelAnchor) have full
     knowledge of the whole diagram before anything is drawn. */
  var pointsByEdge = {};
  var backByEdge = {};
  var aggregated = aggregateEdges(edges);
  var drawEdges = aggregated.drawEdges, viaIndexOf = aggregated.viaIndexOf;
  var anchorOffsets = routingMode === "grid"
    ? computeOrthogonalAnchorOffsets(drawEdges)
    : computeEdgeAnchorOffsets(drawEdges);
  drawEdges.forEach(function (edge, edgeIdx) {
    var sp = positions[edge.from], dp = positions[edge.to];
    if (!sp || !dp || edge.from === edge.to) return;
    var off = anchorOffsets[edgeIdx];
    var back = edgeGoesBackward(sp, dp);
    backByEdge[edgeIdx] = back;
    var sx, sy, ex, ey;
    if (back) {
      sx = sp.x + sp.w; sy = sp.y + sp.h * off.fromFrac;
      ex = dp.x + dp.w; ey = dp.y + dp.h * off.toFrac;
    } else {
      sx = sp.x + sp.w * off.fromFrac; sy = sp.y + sp.h;
      ex = dp.x + dp.w * off.toFrac; ey = dp.y;
    }
    var vias = (edgeVia[viaIndexOf[edgeIdx]] || []).map(function (viaId) {
      var vp = positions[viaId];
      return { x: vp.x + vp.w / 2, y: vp.y + vp.h / 2 };
    });
    pointsByEdge[edgeIdx] = [{ x: sx, y: sy }].concat(vias, [{ x: ex, y: ey }]);
  });

  // Grid-mode routing needs every edge's points at once (not just its own)
  // so two unrelated edges crossing the same inter-layer gap can be kept
  // from bending at the same height — see routeEdgesOrthogonally. Computed
  // before label placement below so grid-mode labels can use the real bend
  // geometry too, not just the curve-mode anchor/via approximation.
  var gridBendsByEdge = {};
  if (routingMode === "grid") {
    var gridEdgeIdxs = [], gridPointsList = [], gridObstaclesList = [];
    Object.keys(pointsByEdge).forEach(function (edgeIdxStr) {
      var edgeIdx = Number(edgeIdxStr);
      var edge = drawEdges[edgeIdx];
      var viaIds = edgeVia[viaIndexOf[edgeIdx]] || [];
      gridEdgeIdxs.push(edgeIdx);
      gridPointsList.push(pointsByEdge[edgeIdx]);
      gridObstaclesList.push(obstaclesFor(positions, [edge.from, edge.to].concat(viaIds)));
    });
    var routed = routeEdgesOrthogonally(gridPointsList, gridObstaclesList);
    gridEdgeIdxs.forEach(function (edgeIdx, k) { gridBendsByEdge[edgeIdx] = routed[k]; });
  }

  // The actual rendered path of every edge, as a polyline — grid mode's
  // bends already are one; curve mode's is approximated by sampling the
  // same cubic bezier curve()/curveSide() draw, segment by segment (each
  // consecutive pair in pointsByEdge is its own curve, so samples are
  // concatenated, dropping the duplicate point at each join). Used only for
  // label placement's "would this box sit on some OTHER edge" check below
  // — the actual stroke is still drawn straight from pointsByEdge/
  // gridBendsByEdge in the draw loop further down.
  var polylineByEdge = {};
  Object.keys(pointsByEdge).forEach(function (edgeIdxStr) {
    var edgeIdx = Number(edgeIdxStr);
    if (routingMode === "grid") {
      polylineByEdge[edgeIdx] = gridBendsByEdge[edgeIdx] || pointsByEdge[edgeIdx];
      return;
    }
    var points = pointsByEdge[edgeIdx];
    var back = backByEdge[edgeIdx];
    var poly = [points[0]];
    for (var i = 0; i < points.length - 1; i++) {
      var sampled = sampleEdgeSegment(points[i], points[i + 1], back, 12);
      for (var k = 1; k < sampled.length; k++) poly.push(sampled[k]);
    }
    polylineByEdge[edgeIdx] = poly;
  });

  var labelCandidates = [];
  drawEdges.forEach(function (edge, edgeIdx) {
    if (!edge.label || !pointsByEdge[edgeIdx]) return;
    var lw = edge.label.length * 5.8 + 10;
    var anchor = chooseLabelAnchor(edgeIdx, polylineByEdge, lw, 14);
    if (!anchor) {
      // Degenerate (e.g. zero-length) path — fall back to the plain
      // anchor/via midpoint, same formula used before this change existed.
      var points = pointsByEdge[edgeIdx];
      var midIdx = (points.length - 1) / 2;
      var mx, my;
      if (Number.isInteger(midIdx)) {
        mx = points[midIdx].x; my = points[midIdx].y;
      } else {
        var i0 = Math.floor(midIdx), i1 = Math.ceil(midIdx);
        mx = (points[i0].x + points[i1].x) / 2;
        my = (points[i0].y + points[i1].y) / 2;
      }
      anchor = { x: mx - lw / 2, y: my - 9 };
    }
    labelCandidates.push({ key: edgeIdx, x: anchor.x, y: anchor.y, w: lw, h: 14 });
  });
  var labelBoxes = computeEdgeLabelBoxes(labelCandidates);

  drawEdges.forEach(function (edge, edgeIdx) {
    var points = pointsByEdge[edgeIdx];
    if (!points) return;
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
    var d;
    if (routingMode === "grid") {
      d = orthogonalPathD(gridBendsByEdge[edgeIdx]);
    } else {
      d = "";
      var curveFn = backByEdge[edgeIdx] ? curveSide : curve;
      for (var i = 0; i < points.length - 1; i++) {
        var seg = curveFn(points[i].x, points[i].y, points[i + 1].x, points[i + 1].y);
        d += i === 0 ? seg.d : seg.d.replace(/^M[^C]*/, " ");
      }
    }
    if (edge._aggregate) {
      // Wider, invisible twin of the real path purely as a larger click
      // target — the visible stroke is too thin to reliably click.
      g.appendChild(el("path", { d: d, fill: "none", stroke: "transparent", "stroke-width": 10 }));
    }
    var pathAttrs = {
      d: d, fill: "none", stroke: color, "stroke-width": edge._aggregate ? 2.5 : 1.5,
      "marker-end": "url(#arr-" + cid + ")",
    };
    if (dashed) pathAttrs["stroke-dasharray"] = "6,4";
    g.appendChild(el("path", pathAttrs));
    var box = labelBoxes[edgeIdx];
    if (edge.label && box) {
      g.appendChild(el("rect", { x: box.x.toFixed(1), y: box.y.toFixed(1), width: box.w.toFixed(1), height: box.h, rx: 3, fill: "rgba(250,249,245,0.92)" }));
      g.appendChild(text(box.x + box.w / 2, box.y + 11, edge.label, { "text-anchor": "middle", "font-family": "ui-monospace,monospace", "font-size": 10, fill: color }));
    }
    if (edge._aggregate) {
      g.setAttribute("data-members", JSON.stringify(edge._members.map(function (m) {
        return { kind: m.kind, label: m.label || "", from: m._origFrom, to: m._origTo };
      })));
      g.style.cursor = "pointer";
      g.addEventListener("click", function (evt) {
        evt.stopPropagation();
        window.sysEdgeAggregateClick(g);
      });
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
function drawOverlay(svg, sequences, positions, idPrefix, resolve, routingMode) {
  routingMode = routingMode || "curve";
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
        var back = edgeGoesBackward(sp, dp);
        var sx, sy, ex, ey;
        if (back) {
          sx = sp.x + sp.w; sy = sp.y + sp.h / 2;
          ex = dp.x + dp.w; ey = dp.y + dp.h / 2;
        } else {
          sx = sp.x + sp.w / 2; sy = sp.y + sp.h;
          ex = dp.x + dp.w / 2; ey = dp.y;
        }
        if (routingMode === "grid") {
          var obstacles = obstaclesFor(positions, [fromId, toId]);
          pathD = orthogonalPathD(orthogonalSegments([{ x: sx, y: sy }, { x: ex, y: ey }], obstacles));
        } else {
          pathD = (back ? curveSide : curve)(sx, sy, ex, ey).d;
        }
        dotX = sx; dotY = sy;
      }
      g.appendChild(el("path", { class: "seq-ov-path", d: pathD, fill: "none", stroke: "#D97757", "stroke-width": 2 }));
      g.appendChild(el("circle", { class: "seq-dot", cx: dotX.toFixed(1), cy: dotY.toFixed(1), r: 5, fill: "#D97757" }));
      svg.appendChild(g);
    });
  });
}
