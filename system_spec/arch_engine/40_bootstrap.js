/* ── Public API ── */
function renderDiagram(payload, mountEl, idPrefix) {
  mountEl.innerHTML = "";
  var svg = el("svg", { style: "display:block;width:100%;height:auto;max-height:680px", id: idPrefix + "sys-svg" });
  mountEl.appendChild(svg);

  if (!mountEl._archExpandedSet) mountEl._archExpandedSet = new Set();
  var routingMode = mountEl._archEdgeStyle || "curve";
  var visible = getVisibleGraph(payload.spec, mountEl._archExpandedSet);
  var layout = layoutHierarchy(payload.spec, mountEl._archExpandedSet, visible.edges);
  drawDiagram(svg, visible, payload.styles, layout, idPrefix, routingMode);
  drawOverlay(svg, payload.spec.sequences, layout.positions, idPrefix, visible.resolve, routingMode);

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

window.sysEdgeStyleChange = function (selectEl) {
  var scope = selectEl.closest(".sys-arch-scope");
  if (!scope) return;
  var mountEl = scope.querySelector(".sys-mount");
  if (!mountEl || !mountEl._archPayload) return;
  mountEl._archEdgeStyle = selectEl.value;
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
