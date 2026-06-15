"""Embedded vanilla-JS engine for the semantic IR.

Provides in-browser simulation, bounded reachability/trace enumeration, trace
ranking, invariant checking, a small EAV/tag query matcher, derived
sequence/dataflow diagram rendering, and trace animation. No dependencies —
operates purely on the IR JSON embedded by system_spec.py as
<script id="sys-ir" type="application/json">.
"""

IR_JS = """
/* ── Core: load IR ──────────────────────────────────────────────────── */
var SysIR = (function () {

function load() {
    var el = document.getElementById('sys-ir');
    if (!el) return null;
    return JSON.parse(el.textContent);
}

function enabled(t, marking, fired) {
    if (t.in.length === 0) return !fired.has(t.id);
    for (var i = 0; i < t.in.length; i++) {
        if (!marking.has(t.in[i])) return false;
    }
    return true;
}

function fire(t, marking) {
    var m = new Set(marking);
    t.in.forEach(function (p) { m.delete(p); });
    t.out.forEach(function (p) { m.add(p); });
    return m;
}

/* Single deterministic "happy path" trace using only non-synthetic transitions. */
function simulate(ir, maxSteps) {
    maxSteps = maxSteps || 50;
    var marking = new Set(ir.net.initial_marking);
    var fired = new Set();
    var trace = [];
    var seenMarkings = new Set();
    for (var step = 0; step < maxSteps; step++) {
        var sig = Array.from(marking).sort().join(',') + '|' + trace.length;
        if (seenMarkings.has(sig)) break;
        seenMarkings.add(sig);
        var candidates = ir.net.transitions.filter(function (t) {
            return !t.synthetic && enabled(t, marking, fired);
        });
        if (candidates.length === 0) break;
        var t = candidates[0];
        marking = fire(t, marking);
        fired.add(t.id);
        trace.push(t.id);
    }
    return trace;
}

/* Bounded BFS/DFS enumeration of traces, allowing at most one synthetic
   (failure) transition per trace to avoid combinatorial blowup. */
function enumerateTraces(ir, opts) {
    opts = opts || {};
    var maxTraces = opts.maxTraces || 25;
    var maxDepth = opts.maxDepth || 12;
    var maxStates = opts.maxStates || 2000;

    var results = [];
    var statesVisited = 0;

    var stack = [{
        marking: new Set(ir.net.initial_marking),
        fired: new Set(),
        trace: [],
        usedSynthetic: false
    }];

    while (stack.length > 0 && results.length < maxTraces && statesVisited < maxStates) {
        var state = stack.pop();
        statesVisited++;

        var candidates = ir.net.transitions.filter(function (t) {
            if (t.synthetic && state.usedSynthetic) return false;
            return enabled(t, state.marking, state.fired);
        });

        if (candidates.length === 0 || state.trace.length >= maxDepth) {
            if (state.trace.length > 0) results.push(state.trace.slice());
            continue;
        }

        for (var i = 0; i < candidates.length; i++) {
            var t = candidates[i];
            var newMarking = fire(t, state.marking);
            var newFired = new Set(state.fired);
            newFired.add(t.id);
            stack.push({
                marking: newMarking,
                fired: newFired,
                trace: state.trace.concat([t.id]),
                usedSynthetic: state.usedSynthetic || t.synthetic
            });
        }
    }
    return results;
}

/* ── Trace ranking ──────────────────────────────────────────────────── */
function traceTags(ir, trace) {
    var tags = new Set();
    var byId = {};
    ir.net.transitions.forEach(function (t) { byId[t.id] = t; });
    trace.forEach(function (tid) {
        (byId[tid].tags || []).forEach(function (tag) { tags.add(tag); });
    });
    return tags;
}

function traceHasFailure(ir, trace) {
    var byId = {};
    ir.net.transitions.forEach(function (t) { byId[t.id] = t; });
    return trace.some(function (tid) { return byId[tid].synthetic; });
}

function rankTraces(ir, traces) {
    var annotated = traces.map(function (trace) {
        var byId = {};
        ir.net.transitions.forEach(function (t) { byId[t.id] = t; });
        var failureCount = trace.filter(function (tid) { return byId[tid].synthetic; }).length;
        return {
            trace: trace,
            length: trace.length,
            failureCount: failureCount,
            tags: Array.from(traceTags(ir, trace))
        };
    });
    annotated.sort(function (a, b) {
        if (a.failureCount !== b.failureCount) return b.failureCount - a.failureCount;
        return a.length - b.length;
    });
    return annotated;
}

/* ── Invariant checking ────────────────────────────────────────────────
   precedes:   violation if any 'after' transition fires before any 'before' transition has fired
   requires:   violation if any 'after' transition fires but no 'before' transition ever fires
   excludes:   violation if both 'before' and 'after' transitions appear in the same trace
   eventually: violation if 'after' fires but no 'then' transition fires afterwards          */
function checkInvariant(ir, inv, traces) {
    var rule = inv.rule;
    var beforeSet = new Set(rule.before || []);
    var afterSet = new Set(rule.after || []);
    var thenSet = new Set(rule.then || []);

    for (var ti = 0; ti < traces.length; ti++) {
        var trace = traces[ti];
        if (rule.type === 'precedes' || rule.type === 'requires') {
            var seenBefore = false;
            for (var i = 0; i < trace.length; i++) {
                if (beforeSet.has(trace[i])) seenBefore = true;
                if (afterSet.has(trace[i]) && !seenBefore) {
                    return { holds: false, counterexample: trace, violationIndex: i };
                }
            }
        } else if (rule.type === 'excludes') {
            var hasBefore = trace.some(function (t) { return beforeSet.has(t); });
            var hasAfter = trace.some(function (t) { return afterSet.has(t); });
            if (hasBefore && hasAfter) {
                return { holds: false, counterexample: trace, violationIndex: null };
            }
        } else if (rule.type === 'eventually') {
            for (var j = 0; j < trace.length; j++) {
                if (afterSet.has(trace[j])) {
                    var satisfied = trace.slice(j + 1).some(function (t) { return thenSet.has(t); });
                    if (!satisfied) {
                        return { holds: false, counterexample: trace, violationIndex: j };
                    }
                }
            }
        }
    }
    return { holds: true, counterexample: null, violationIndex: null };
}

/* ── EAV / tag query matcher ───────────────────────────────────────────
   verbs:
     produced_by(placeId)  - backward walk of transitions that produce placeId
     involving(nodeId)     - transitions running on nodeId + traces touching them
     tagged(tag)           - transitions carrying tag + traces touching them      */
function queryProducedBy(ir, placeId, depth) {
    depth = depth || 0;
    if (depth > 6) return [];
    var producers = ir.net.transitions.filter(function (t) { return t.out.indexOf(placeId) !== -1; });
    var result = [];
    producers.forEach(function (t) {
        var upstream = [];
        t.in.forEach(function (p) { upstream = upstream.concat(queryProducedBy(ir, p, depth + 1)); });
        result.push({ transition: t.id, label: t.label, node: t.node, upstream: upstream });
    });
    return result;
}

function queryInvolving(ir, nodeId, traces) {
    var tids = (ir.meta.node_to_transitions || {})[nodeId] || [];
    var tidSet = new Set(tids);
    var matchingTraces = traces.filter(function (trace) {
        return trace.some(function (t) { return tidSet.has(t); });
    });
    return { transitions: tids, traces: matchingTraces };
}

function queryTagged(ir, tag, traces) {
    var tids = (ir.tags_index[tag] || {}).transitions || [];
    var tidSet = new Set(tids);
    var matchingTraces = traces.filter(function (trace) {
        return trace.some(function (t) { return tidSet.has(t); });
    });
    return { transitions: tids, traces: matchingTraces };
}

return {
    load: load,
    simulate: simulate,
    enumerateTraces: enumerateTraces,
    rankTraces: rankTraces,
    traceHasFailure: traceHasFailure,
    checkInvariant: checkInvariant,
    queryProducedBy: queryProducedBy,
    queryInvolving: queryInvolving,
    queryTagged: queryTagged
};
})();

/* ── Rendering helpers ─────────────────────────────────────────────────── */

function sysIRLabel(ir, id) {
    if (ir.data_objects[id]) return ir.data_objects[id].label || id;
    var t = ir.net.transitions.find(function (x) { return x.id === id; });
    if (t) return t.label || id;
    var n = ir.structural.nodes.find(function (x) { return x.id === id; });
    if (n) return n.label || id;
    return id;
}

function sysIRNodeLabel(ir, nodeId) {
    var n = ir.structural.nodes.find(function (x) { return x.id === nodeId; });
    return n ? (n.label || nodeId) : nodeId;
}

/* Render a derived sequence diagram for a trace: one column per node touched. */
function sysRenderSequenceSVG(ir, trace) {
    var byId = {};
    ir.net.transitions.forEach(function (t) { byId[t.id] = t; });

    var participants = [];
    var seen = {};
    trace.forEach(function (tid) {
        var node = byId[tid].node;
        if (!seen[node]) { seen[node] = true; participants.push(node); }
    });
    if (participants.length === 0) return '<p class="sys-hint">Empty trace.</p>';

    var COL_W = 150, COL_GAP = 50, HEADER_H = 46, STEP_H = 56, TOP = 16, SIDE = 36;
    var n = participants.length;
    var W = 2 * SIDE + n * COL_W + Math.max(0, n - 1) * COL_GAP;
    var H = TOP + HEADER_H + trace.length * STEP_H + 24;
    var colX = {};
    participants.forEach(function (nid, i) { colX[nid] = SIDE + i * (COL_W + COL_GAP) + COL_W / 2; });

    var lifelineTop = TOP + HEADER_H;
    var lifelineBot = H - 12;

    var parts = ['<svg viewBox="0 0 ' + W + ' ' + H + '" style="display:block;width:100%;height:auto;max-height:680px">'];
    participants.forEach(function (nid) {
        var cx = colX[nid];
        var x = cx - COL_W / 2;
        parts.push('<rect x="' + x + '" y="' + TOP + '" width="' + COL_W + '" height="' + HEADER_H + '" rx="8" fill="#FFFFFF" stroke="#D1CFC5" stroke-width="1.5"/>');
        parts.push('<text x="' + cx + '" y="' + (TOP + HEADER_H / 2) + '" text-anchor="middle" dominant-baseline="middle" font-family="ui-serif,Georgia,serif" font-size="12" font-weight="500" fill="#141413">' + sysIRNodeLabel(ir, nid) + '</text>');
        parts.push('<line x1="' + cx + '" y1="' + lifelineTop + '" x2="' + cx + '" y2="' + lifelineBot + '" stroke="#D1CFC5" stroke-width="1" stroke-dasharray="4,4"/>');
    });

    trace.forEach(function (tid, i) {
        var t = byId[tid];
        var cx = colX[t.node];
        var y = lifelineTop + (i + 0.5) * STEP_H;
        var color = t.synthetic ? '#B04A3F' : '#D97757';
        parts.push('<circle cx="' + cx + '" cy="' + y + '" r="5" fill="' + color + '"/>');
        parts.push('<text x="' + (cx + 12) + '" y="' + (y + 4) + '" font-family="ui-monospace,monospace" font-size="11" fill="' + color + '">' + t.label + '</text>');
        parts.push('<text x="' + (SIDE - 8) + '" y="' + (y + 4) + '" text-anchor="end" font-family="ui-monospace,monospace" font-size="9" fill="#D1CFC5">' + (i + 1) + '</text>');
    });

    parts.push('</svg>');
    return parts.join('\\n');
}

/* Render a dataflow DAG: data places -> transitions -> data places. */
function sysRenderDataflowSVG(ir) {
    var places = ir.net.places.filter(function (p) { return !p.synthetic; });
    var transitions = ir.net.transitions.filter(function (t) { return !t.synthetic; });
    if (places.length === 0) return '<p class="sys-hint">No data objects defined.</p>';

    // Layer by BFS depth from initial marking
    var depth = {};
    ir.net.initial_marking.forEach(function (p) { depth[p] = 0; });
    var changed = true, guard = 0;
    while (changed && guard < 50) {
        changed = false; guard++;
        transitions.forEach(function (t) {
            var maxIn = -1;
            t.in.forEach(function (p) { if (depth[p] !== undefined) maxIn = Math.max(maxIn, depth[p]); });
            if (maxIn === -1) return;
            var td = maxIn + 1;
            if (depth[t.id] === undefined || td > depth[t.id]) { depth[t.id] = td; changed = true; }
            t.out.forEach(function (p) {
                var pd = td + 1;
                if (depth[p] === undefined || pd > depth[p]) { depth[p] = pd; changed = true; }
            });
        });
    }

    var maxDepth = 0;
    Object.keys(depth).forEach(function (k) { maxDepth = Math.max(maxDepth, depth[k]); });

    var byDepth = {};
    places.concat(transitions).forEach(function (item) {
        var d = depth[item.id] !== undefined ? depth[item.id] : maxDepth + 1;
        (byDepth[d] = byDepth[d] || []).push(item);
    });

    var COL_W = 170, ROW_H = 64, PAD = 30;
    var maxRow = 0;
    Object.keys(byDepth).forEach(function (k) { maxRow = Math.max(maxRow, byDepth[k].length); });
    var W = PAD * 2 + (maxDepth + 1) * COL_W;
    var H = PAD * 2 + maxRow * ROW_H;

    var pos = {};
    Object.keys(byDepth).sort(function (a, b) { return a - b; }).forEach(function (d) {
        var items = byDepth[d];
        items.forEach(function (item, i) {
            pos[item.id] = { x: PAD + d * COL_W, y: PAD + i * ROW_H, isPlace: !!item.data_object || places.indexOf(item) !== -1 };
        });
    });

    var parts = ['<svg viewBox="0 0 ' + W + ' ' + H + '" style="display:block;width:100%;height:auto;max-height:680px">'];
    parts.push('<defs><marker id="dfarr" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L0,7 L7,3.5 z" fill="#C8C5BC"/></marker></defs>');

    // Arcs
    ir.net.arcs.forEach(function (arc) {
        if (arc.dir !== 'out') return;
        var from = pos[arc.transition], to = pos[arc.place];
        if (!from || !to) return;
        parts.push('<line x1="' + (from.x + 130) + '" y1="' + (from.y + 16) + '" x2="' + to.x + '" y2="' + (to.y + 16) + '" stroke="#C8C5BC" stroke-width="1.3" marker-end="url(#dfarr)"/>');
    });
    ir.net.arcs.forEach(function (arc) {
        if (arc.dir !== 'in') return;
        var from = pos[arc.place], to = pos[arc.transition];
        if (!from || !to) return;
        parts.push('<line x1="' + (from.x + 130) + '" y1="' + (from.y + 16) + '" x2="' + to.x + '" y2="' + (to.y + 16) + '" stroke="#C8C5BC" stroke-width="1.3" marker-end="url(#dfarr)"/>');
    });

    // Nodes
    places.forEach(function (p) {
        var xy = pos[p.id]; if (!xy) return;
        parts.push('<rect x="' + xy.x + '" y="' + xy.y + '" width="130" height="32" rx="16" fill="rgba(120,140,93,0.07)" stroke="#788C5D" stroke-width="1.5"/>');
        parts.push('<text x="' + (xy.x + 65) + '" y="' + (xy.y + 16) + '" text-anchor="middle" dominant-baseline="middle" font-family="ui-serif,Georgia,serif" font-size="11" fill="#141413">' + (p.label || p.id) + '</text>');
    });
    transitions.forEach(function (t) {
        var xy = pos[t.id]; if (!xy) return;
        parts.push('<rect x="' + xy.x + '" y="' + xy.y + '" width="130" height="32" rx="6" fill="rgba(217,119,87,0.07)" stroke="#D97757" stroke-width="1.5"/>');
        parts.push('<text x="' + (xy.x + 65) + '" y="' + (xy.y + 16) + '" text-anchor="middle" dominant-baseline="middle" font-family="ui-monospace,monospace" font-size="10" fill="#141413">' + t.label + '</text>');
    });

    parts.push('</svg>');
    return parts.join('\\n');
}

/* ── Animation: step through a trace, highlighting architecture nodes ─── */
var _sysAnimTimer = null;
function sysAnimateTrace(ir, trace) {
    if (_sysAnimTimer) { clearInterval(_sysAnimTimer); _sysAnimTimer = null; }
    document.querySelectorAll('.sys-node').forEach(function (n) { n.classList.remove('sys-anim-active'); });
    var byId = {};
    ir.net.transitions.forEach(function (t) { byId[t.id] = t; });
    var i = 0;
    var info = document.getElementById('sys-anim-info');
    function step() {
        document.querySelectorAll('.sys-node').forEach(function (n) { n.classList.remove('sys-anim-active'); });
        if (i >= trace.length) { clearInterval(_sysAnimTimer); _sysAnimTimer = null; return; }
        var t = byId[trace[i]];
        var el = document.querySelector('.sys-node[data-id="' + t.node + '"]');
        if (el) el.classList.add('sys-anim-active');
        if (info) info.textContent = (i + 1) + '/' + trace.length + ': ' + t.label;
        i++;
    }
    step();
    _sysAnimTimer = setInterval(step, 900);
}

/* ── Tab initialization ────────────────────────────────────────────────── */
function sysIRInit() {
    var ir = SysIR.load();
    if (!ir) return;
    window._sysIR = ir;

    var happyPath = SysIR.simulate(ir);
    var allTraces = SysIR.enumerateTraces(ir, {});
    if (allTraces.length === 0 && happyPath.length > 0) allTraces = [happyPath];
    window._sysTraces = allTraces;

    // Dataflow tab
    var dfEl = document.getElementById('sys-dataflow-svg');
    if (dfEl) dfEl.innerHTML = sysRenderDataflowSVG(ir);

    // Sequences tab (derived traces)
    var seqSel = document.getElementById('sys-seq-select');
    var seqSvg = document.getElementById('sys-seq-svg');
    if (seqSel && seqSvg) {
        var ranked = SysIR.rankTraces(ir, allTraces.length ? allTraces : [happyPath]);
        ranked.forEach(function (r, i) {
            var opt = document.createElement('option');
            opt.value = i;
            opt.textContent = (i === 0 ? 'Happy path' : 'Scenario ' + (i + 1)) +
                (r.failureCount ? ' (' + r.failureCount + ' failure)' : '') +
                ' — ' + r.length + ' steps';
            seqSel.appendChild(opt);
        });
        window._sysRanked = ranked;
        seqSvg.innerHTML = ranked.length ? sysRenderSequenceSVG(ir, ranked[0].trace) : '<p class="sys-hint">No derivable traces.</p>';
        seqSel.onchange = function () {
            var r = ranked[parseInt(seqSel.value, 10)];
            seqSvg.innerHTML = sysRenderSequenceSVG(ir, r.trace);
            sysAnimateTrace(ir, r.trace);
        };
    }

    // Scenarios tab
    var scList = document.getElementById('sys-scenarios-list');
    if (scList) {
        var ranked2 = window._sysRanked || SysIR.rankTraces(ir, allTraces);
        scList.innerHTML = '';
        ranked2.forEach(function (r, i) {
            var div = document.createElement('div');
            div.className = 'sys-scenario-row';
            var kind = r.failureCount > 0 ? 'Failure path' : 'Happy path';
            div.innerHTML = '<strong>' + kind + '</strong> — ' + r.length + ' steps' +
                (r.tags.length ? ' <span class="sys-tags-inline">' + r.tags.map(function (t) { return '<span class="sys-tag">' + t + '</span>'; }).join('') + '</span>' : '') +
                '<div class="sys-scenario-trace">' + r.trace.map(function (tid) { return sysIRLabel(ir, tid); }).join(' → ') + '</div>';
            div.onclick = function () { sysAnimateTrace(ir, r.trace); };
            scList.appendChild(div);
        });
        if (ranked2.length === 0) scList.innerHTML = '<p class="sys-hint">No derivable scenarios.</p>';
    }

    // Invariants tab
    var invList = document.getElementById('sys-invariants-list');
    if (invList) {
        invList.innerHTML = '';
        (ir.invariants || []).forEach(function (inv) {
            var result = SysIR.checkInvariant(ir, inv, allTraces);
            var div = document.createElement('div');
            div.className = 'sys-invariant-row ' + (result.holds ? 'sys-inv-pass' : 'sys-inv-fail');
            var html = '<div class="sys-inv-header"><span class="sys-inv-status">' + (result.holds ? 'HOLDS' : 'VIOLATED') + '</span>' +
                '<strong>' + inv.label + '</strong>' +
                '<span class="sys-kbadge">' + inv.severity + '</span></div>';
            if (!result.holds) {
                html += '<div class="sys-scenario-trace">' + result.counterexample.map(function (tid) { return sysIRLabel(ir, tid); }).join(' → ') + '</div>';
                html += '<button class="sys-fc active sys-inv-animate">Animate counterexample</button>';
            }
            div.innerHTML = html;
            if (!result.holds) {
                div.querySelector('.sys-inv-animate').onclick = function () { sysAnimateTrace(ir, result.counterexample); };
            }
            invList.appendChild(div);
        });
        if (!(ir.invariants || []).length) invList.innerHTML = '<p class="sys-hint">No invariants declared.</p>';
    }

    // Query tab
    var qInput = document.getElementById('sys-query-input');
    var qResults = document.getElementById('sys-query-results');
    var qButtons = document.getElementById('sys-query-buttons');
    if (qInput && qResults) {
        function runQuery() {
            var q = qInput.value.trim();
            qResults.innerHTML = '';
            if (!q) return;
            var m;
            if ((m = q.match(/^how is (.+) created\\??$/i)) || (m = q.match(/^produced[_ ]by[: ]+(.+)$/i))) {
                var target = m[1].trim();
                var place = ir.net.places.find(function (p) { return p.id === target || p.label === target; });
                if (!place) { qResults.innerHTML = '<p class="sys-hint">Unknown data object: ' + target + '</p>'; return; }
                var producers = SysIR.queryProducedBy(ir, place.id);
                qResults.innerHTML = producers.length ?
                    producers.map(function (p) { return '<div class="sys-scenario-row"><strong>' + p.label + '</strong> on ' + sysIRNodeLabel(ir, p.node) + '</div>'; }).join('') :
                    '<p class="sys-hint">No transitions produce ' + target + '.</p>';
                return;
            }
            if ((m = q.match(/^(?:show )?(?:paths|traces) involving (.+)$/i))) {
                var nodeId = m[1].trim();
                var node = ir.structural.nodes.find(function (n) { return n.id === nodeId || n.label === nodeId; });
                var res = SysIR.queryInvolving(ir, node ? node.id : nodeId, allTraces);
                renderTraceResults(res);
                return;
            }
            if ((m = q.match(/^(?:show )?(?:paths|traces) (?:with|tagged) (.+)$/i))) {
                var tag = m[1].trim();
                var res2 = SysIR.queryTagged(ir, tag, allTraces);
                renderTraceResults(res2);
                return;
            }
            qResults.innerHTML = '<p class="sys-hint">Try: "how is Session created", "paths involving session_cache", "traces with database-failure"</p>';
        }
        function renderTraceResults(res) {
            if (!res.traces.length) { qResults.innerHTML = '<p class="sys-hint">No matching traces.</p>'; return; }
            qResults.innerHTML = res.traces.map(function (trace) {
                return '<div class="sys-scenario-row sys-scenario-clickable"><div class="sys-scenario-trace">' + trace.map(function (tid) { return sysIRLabel(ir, tid); }).join(' → ') + '</div></div>';
            }).join('');
            Array.from(qResults.children).forEach(function (el, i) {
                el.onclick = function () { sysAnimateTrace(ir, res.traces[i]); };
            });
        }
        qInput.addEventListener('keydown', function (e) { if (e.key === 'Enter') runQuery(); });
        if (qButtons) {
            qButtons.querySelectorAll('button').forEach(function (b) {
                b.onclick = function () { qInput.value = b.getAttribute('data-q'); runQuery(); };
            });
        }
    }
}

document.addEventListener('DOMContentLoaded', sysIRInit);
"""
