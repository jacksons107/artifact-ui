# ── Page assembly: embedded CSS / JS ──────────────────────────────────────────

_CSS = """
/* ── Tabs ─────────────────────────────────────── */
.sys-tabs { display: flex; gap: 0; border-bottom: 1.5px solid var(--gray-300); margin-bottom: 20px; }
.sys-tab { font-family: var(--mono); font-size: 12px; background: none; border: none;
           padding: 7px 16px; cursor: pointer; color: var(--gray-500);
           border-bottom: 2px solid transparent; margin-bottom: -1.5px; transition: color 0.1s; }
.sys-tab:hover { color: var(--slate); }
.sys-tab.active { color: var(--slate); border-bottom-color: var(--clay); font-weight: 500; }

/* ── Architecture view ────────────────────────── */
.sys-wrap { display: flex; gap: 20px; align-items: flex-start; }
.sys-main { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; gap: 12px; }
.sys-diagram { background: var(--white); border: var(--border); border-radius: 12px; padding: 20px; overflow-x: auto; }
.sys-sidebar { flex: 0 0 260px; display: flex; flex-direction: column; gap: 12px; }

/* ── Filter bar (architecture) ────────────────── */
.sys-arch-filters { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }

/* ── Filter chips (shared) ────────────────────── */
.sys-fl { font-family: var(--mono); font-size: 10px; color: var(--gray-500); }
.sys-fc { font-family: var(--mono); font-size: 11px; border: 1.5px solid currentColor;
          background: none; border-radius: 100px; padding: 2px 10px;
          cursor: pointer; opacity: 0.3; transition: opacity 0.1s; }
.sys-fc.active { opacity: 1; background: rgba(0,0,0,0.03); }

/* ── Detail panel ─────────────────────────────── */
.sys-panel { background: var(--white); border: var(--border); border-radius: 12px; padding: 18px; }
.sys-ph { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.sys-plabel { font-family: var(--serif); font-size: 15px; font-weight: 600; flex: 1; }
.sys-kbadge { font-family: var(--mono); font-size: 10px; border: 1px solid; border-radius: 4px; padding: 2px 6px; }
.sys-pdesc { font-size: 13px; color: var(--gray-700); margin: 0 0 10px; line-height: 1.5; }
.sys-meta { display: grid; grid-template-columns: auto 1fr; gap: 3px 12px; font-size: 12px; margin: 0 0 10px; }
.sys-meta dt { color: var(--gray-500); font-family: var(--mono); }
.sys-meta dd { color: var(--slate); margin: 0; }
.sys-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px; }
.sys-tag { font-family: var(--mono); font-size: 10px; background: var(--gray-100); color: var(--gray-700); border-radius: 4px; padding: 2px 7px; }
.sys-edges { border-top: 1px solid var(--gray-100); padding-top: 10px; }
.sys-eg-label { font-family: var(--mono); font-size: 10px; color: var(--gray-500); margin: 6px 0 3px; }
.sys-er { font-size: 12px; color: var(--gray-700); display: flex; gap: 8px; align-items: baseline; padding: 2px 0; }
.sys-ek { font-family: var(--mono); font-size: 10px; color: var(--gray-500); }
.sys-er-link { color: var(--clay); cursor: pointer; text-decoration: none; }
.sys-er-link:hover { text-decoration: underline; }

/* ── Node interaction ─────────────────────────── */
.sys-nr { transition: filter 0.12s; }
.sys-node:hover .sys-nr { filter: brightness(0.94); }
.sys-node.active .sys-nr { stroke-width: 2.5px !important; filter: brightness(0.91); }
.sys-node.filtered-out,
.sys-edge.filtered-out,
.sys-group.filtered-out,
.sys-node.seq-unrelated,
.sys-edge.seq-unrelated { opacity: 0.12; pointer-events: none; }

/* ── Hint / placeholder ───────────────────────── */
.sys-hint { color: var(--gray-500); font-size: 12px; text-align: center; padding: 32px 16px;
            font-family: var(--mono); background: var(--white); border: var(--border);
            border-radius: 12px; border-style: dashed; }

/* ── Legend ───────────────────────────────────── */
.sys-legend { background: var(--white); border: var(--border); border-radius: 12px; padding: 14px 18px; }
.sys-leg-group { margin-bottom: 10px; }
.sys-leg-group:last-child { margin-bottom: 0; }
.sys-leg-title { font-family: var(--mono); font-size: 10px; color: var(--gray-500); margin-bottom: 5px; }
.sys-leg-row { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--gray-700); padding: 2px 0; }
.sys-leg-row span:first-child { width: 16px; text-align: center; font-size: 12px; }
.sys-leg-line { display: inline-block; width: 20px; border-top: 2px solid; height: 0; }

/* ── Component list ───────────────────────────── */
.sys-clist { display: flex; flex-direction: column; gap: 14px; }
.sys-filters { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.sys-tbl-wrap { overflow-x: auto; background: var(--white); border: var(--border); border-radius: 12px; }
.sys-ctable { width: 100%; border-collapse: collapse; font-size: 13px; }
.sys-ctable th { font-family: var(--mono); font-size: 10px; color: var(--gray-500); text-align: left;
                 padding: 10px 14px; border-bottom: 1.5px solid var(--gray-300); white-space: nowrap; }
.sys-ctable td { padding: 9px 14px; border-bottom: 1px solid var(--gray-100); vertical-align: top; }
.sys-ctable tbody tr:last-child td { border-bottom: none; }
.sys-cr:hover td { background: var(--gray-100); }
.sys-mono { font-family: var(--mono); font-size: 12px; color: var(--gray-700); }
.sys-dc { font-size: 12px; color: var(--gray-500); max-width: 280px; }

/* ── Layer diagram view ───────────────────────── */
.sys-layer-wrap { background: var(--white); border: var(--border); border-radius: 12px; padding: 20px; overflow-x: auto; }

/* ── Sequence diagram view ────────────────────── */
.sys-seq-wrap { display: flex; flex-direction: column; gap: 14px; }
.sys-seq-controls { display: flex; align-items: center; gap: 10px; }
.sys-seq-sel { font-family: var(--mono); font-size: 12px; border: var(--border); border-radius: 6px;
               padding: 5px 12px; background: var(--white); color: var(--slate); cursor: pointer;
               appearance: none; -webkit-appearance: none; }
.sys-seq-panel { background: var(--white); border: var(--border); border-radius: 12px; padding: 20px; overflow-x: auto; }
.sys-seq-panel-flat { background: none; border: none; padding: 0; }
.sys-seq-step:hover .sys-seq-line { filter: brightness(0.85); }
.sys-seq-step.active .sys-seq-line { stroke-width: 2.5px !important; }

/* ── Code detail view ──────────────────────────── */
.sys-cd-wrap { display: flex; flex-direction: column; gap: 14px; }
.sys-cd-controls { display: flex; align-items: center; gap: 10px; }
.sys-cd-sel { font-family: var(--mono); font-size: 12px; border: var(--border); border-radius: 6px;
              padding: 5px 12px; background: var(--white); color: var(--slate); cursor: pointer;
              appearance: none; -webkit-appearance: none; }
.sys-cd-panel { display: flex; flex-direction: column; gap: 12px; }

/* ── Dependency matrix ────────────────────────── */
.sys-matrix-wrap { overflow-x: auto; background: var(--white); border: var(--border); border-radius: 12px; }
.sys-mtx { border-collapse: collapse; font-size: 12px; white-space: nowrap; }
.sys-mh0 { min-width: 160px; }
.sys-mth { padding: 0; vertical-align: bottom; border-left: 1px solid var(--gray-100); }
.sys-mth-inner { writing-mode: vertical-rl; transform: rotate(180deg); padding: 12px 8px 8px;
                  font-family: var(--mono); font-size: 11px; display: flex; align-items: center;
                  gap: 4px; color: var(--gray-700); }
.sys-mrh { padding: 8px 14px; font-family: var(--mono); font-size: 12px; white-space: nowrap;
           border-right: 1.5px solid var(--gray-300); color: var(--gray-700); border-bottom: 1px solid var(--gray-100); }
.sys-mc  { padding: 7px 10px; text-align: center; border-left: 1px solid var(--gray-100);
           border-bottom: 1px solid var(--gray-100); font-family: var(--mono); font-size: 10px; min-width: 64px; }
.sys-mc-hit { font-weight: 500; }
.sys-mtx thead tr { border-bottom: 1.5px solid var(--gray-300); }
.sys-mtx thead th { border-bottom: 1.5px solid var(--gray-300); }

/* ── Description ──────────────────────────────── */
.sys-desc { font-size: 14px; color: var(--gray-700); margin: 0 0 20px; line-height: 1.6; }

/* ── Filter bar separator ─────────────────────── */
.sys-fl-sep { display: inline-block; width: 1px; height: 16px; background: var(--gray-300); margin: 0 6px; vertical-align: middle; }

/* ── Code snippet in detail panel ─────────────── */
.sys-sig { margin: 10px 0 6px; padding: 6px 10px; background: var(--gray-100); border-left: 3px solid var(--clay); border-radius: 0 4px 4px 0; }
.sys-sig code { font-family: var(--mono); font-size: 12px; color: var(--slate); }
.sys-snippet { margin: 6px 0 0; }
.sys-snippet pre { margin: 0; padding: 10px 12px; background: var(--ivory); border: var(--border); border-radius: 8px; overflow-x: auto; max-height: 320px; font-size: 0.78rem; line-height: 1.5; }
.sys-snippet pre code { font-family: var(--mono); }

/* ── Sequence playback timeline ────────────────── */
.sys-timeline { display: flex; flex-direction: column; gap: 8px; background: var(--white);
                border: var(--border); border-radius: 12px; padding: 14px 16px; }
.sys-tl-controls { display: flex; align-items: center; gap: 10px; }
.sys-tl-play { font-family: var(--mono); font-size: 13px; border: 1.5px solid var(--clay); color: var(--clay);
               background: none; border-radius: 100px; width: 28px; height: 28px; cursor: pointer; flex: 0 0 auto; }
.sys-tl-play:hover { background: rgba(217,119,87,0.08); }
.sys-tl-label { font-family: var(--mono); font-size: 11px; color: var(--gray-700); }
.sys-tl-track { position: relative; height: 20px; cursor: pointer; }
.sys-tl-track::before { content: ''; position: absolute; top: 50%; left: 0; right: 0; height: 3px;
                         background: var(--gray-300); border-radius: 2px; transform: translateY(-50%); }
.sys-tl-fill { position: absolute; top: 50%; left: 0; height: 3px; background: var(--clay);
               border-radius: 2px; transform: translateY(-50%); pointer-events: none; }
.sys-tl-tick { position: absolute; top: 50%; width: 8px; height: 8px; border-radius: 100%;
               background: var(--white); border: 1.5px solid var(--gray-300); transform: translate(-50%, -50%);
               cursor: pointer; z-index: 1; }
.sys-tl-tick:hover { border-color: var(--clay); }
.sys-tl-thumb { position: absolute; top: 50%; width: 14px; height: 14px; border-radius: 100%;
                background: var(--clay); border: 2px solid var(--white); box-shadow: 0 1px 3px rgba(0,0,0,0.25);
                transform: translate(-50%, -50%); cursor: grab; z-index: 2; }
.sys-now-playing { border-top: 1px solid var(--gray-100); padding-top: 10px; }
.sys-now-playing-label { font-family: var(--mono); font-size: 11px; color: var(--gray-700); margin-bottom: 4px; }

/* ── Sequence playback states ─────────────────── */
.seq-step-ov { transition: opacity 0.25s; }
.seq-step-ov .seq-ov-path { opacity: 0.9; }
.seq-step-ov.seq-visited .seq-ov-path { opacity: 0.35; }
.seq-dot { opacity: 0; filter: drop-shadow(0 0 3px rgba(217,119,87,0.8)); transition: opacity 0.15s; }
.sys-node.seq-active .sys-nr { stroke-width: 2.5px !important; filter: drop-shadow(0 0 4px rgba(217,119,87,0.65)); }
.sys-node.seq-visited .sys-nr { fill: rgba(217,119,87,0.07) !important; }
.sys-seq-participant.seq-active .sys-seq-pbox { stroke-width: 2.5px !important; filter: drop-shadow(0 0 4px rgba(217,119,87,0.65)); }
.sys-seq-participant.seq-visited .sys-seq-pbox { fill: rgba(217,119,87,0.07) !important; }
.sys-seq-step.seq-visited .sys-seq-line { opacity: 0.35; }
.sys-seq-step.seq-active .sys-seq-line { stroke-width: 2.5px; filter: drop-shadow(0 0 3px rgba(217,119,87,0.7)); }

/* ── Architecture animate control row ─────────── */
.sys-arch-animate { display: flex; flex-direction: column; gap: 10px; margin-bottom: 14px; }

/* ── Appears-in-sequences (node detail panel) ─── */
.sys-seq-refs { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }

/* ── Changes tab ──────────────────────────────── */
.sys-changes { display: flex; flex-direction: column; gap: 24px; }
.sys-chg-section { background: var(--white); border: var(--border); border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.sys-chg-header { font-family: var(--mono); font-size: 12px; font-weight: 600; padding: 4px 0 4px 10px; border-left: 3px solid; letter-spacing: 0.04em; text-transform: uppercase; }
.sys-chg-node { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.sys-chg-label { font-family: var(--serif); font-size: 14px; }
.sys-chg-fp { font-family: var(--mono); font-size: 11px; color: var(--gray-500); }
.sys-chg-pre { margin: 4px 0 0; padding: 10px 12px; background: var(--ivory); border: var(--border); border-radius: 8px; overflow-x: auto; max-height: 360px; font-size: 0.78rem; line-height: 1.5; }
.sys-chg-pre code { font-family: var(--mono); }
.sys-chg-diff { display: flex; gap: 12px; flex-wrap: wrap; }
.sys-chg-side { flex: 1 1 340px; display: flex; flex-direction: column; gap: 4px; }
.sys-chg-side-label { font-family: var(--mono); font-size: 10px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; }
"""

_JS = """
/* ── Tab switching ─────────────────────────────── */
function sysTab(el) {
    document.querySelectorAll('.sys-tab').forEach(function(t) { t.classList.remove('active'); });
    document.querySelectorAll('.sys-view').forEach(function(v) { v.style.display = 'none'; });
    el.classList.add('active');
    var view = document.getElementById('view-' + el.getAttribute('data-view'));
    if (view) view.style.display = 'block';
}

/* ── Node click (architecture detail panel) ─────── */
var _active = null;
function _selectNode(el) {
    var nid = el.getAttribute('data-id');
    var panel = document.getElementById('panel-' + nid);
    var wrap = el.closest('.sys-wrap');
    var hint = wrap ? wrap.querySelector('.sys-hint') : null;

    if (_active) _active.classList.remove('active');
    if (wrap) wrap.querySelectorAll('.sys-panel').forEach(function(p) { p.style.display = 'none'; });

    el.classList.add('active');
    _active = el;
    if (hint) hint.style.display = 'none';
    if (panel) panel.style.display = 'block';
}
function sysClick(el) {
    if (_active === el) {
        el.classList.remove('active');
        _active = null;
        var wrap = el.closest('.sys-wrap');
        var hint = wrap ? wrap.querySelector('.sys-hint') : null;
        if (wrap) wrap.querySelectorAll('.sys-panel').forEach(function(p) { p.style.display = 'none'; });
        if (hint) hint.style.display = 'block';
        return;
    }
    _selectNode(el);
}

/* ── Jump to a referenced node from a detail-panel link ─ */
function sysGoTo(linkEl) {
    var targetId = linkEl.getAttribute('data-target');
    var wrap = linkEl.closest('.sys-wrap');
    if (!wrap) return;
    var targetNode = wrap.querySelector('.sys-node[data-id="' + CSS.escape(targetId) + '"]');
    if (targetNode) {
        _selectNode(targetNode);
        targetNode.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

/* ── Sequence step example panels ──────────────── */
var _activeStep = null;
function sysSeqStepClick(el) {
    var targetId = el.getAttribute('data-target');
    var panel = document.getElementById(targetId);
    var wrap = el.closest('.sys-wrap');
    var hint = wrap ? wrap.querySelector('.sys-hint') : null;

    if (_activeStep === el) {
        el.classList.remove('active');
        _activeStep = null;
        if (panel) panel.style.display = 'none';
        if (hint) hint.style.display = 'block';
        return;
    }

    if (_activeStep) {
        _activeStep.classList.remove('active');
        var prevWrap = _activeStep.closest('.sys-wrap');
        if (prevWrap) prevWrap.querySelectorAll('.sys-panel').forEach(function(p) { p.style.display = 'none'; });
    }
    if (wrap) wrap.querySelectorAll('.sys-panel').forEach(function(p) { p.style.display = 'none'; });

    el.classList.add('active');
    _activeStep = el;
    if (hint) hint.style.display = 'none';
    if (panel) panel.style.display = 'block';
}

/* ── Sequence playback timeline ─────────────────── */
var _tlPlayIntervals = new WeakMap();

function _tlSteps(timeline) {
    var kind = timeline.getAttribute('data-target-kind');
    var seqId = timeline.getAttribute('data-seq');
    var list;
    if (kind === 'arch') {
        list = document.querySelectorAll('.seq-step-ov[data-seq="' + CSS.escape(seqId) + '"]');
    } else {
        var wrap = timeline.closest('.sys-wrap');
        list = wrap ? wrap.querySelectorAll('.sys-seq-step') : [];
    }
    return Array.prototype.slice.call(list).sort(function(a, b) {
        return (+a.getAttribute('data-step')) - (+b.getAttribute('data-step'));
    });
}

function _tlNodeFor(timeline, nodeId) {
    if (!nodeId) return null;
    var kind = timeline.getAttribute('data-target-kind');
    if (kind === 'arch') {
        return document.querySelector('#view-arch .sys-node[data-id="' + CSS.escape(nodeId) + '"]');
    }
    var wrap = timeline.closest('.sys-wrap');
    return wrap ? wrap.querySelector('.sys-seq-participant[data-id="' + CSS.escape(nodeId) + '"]') : null;
}

function _tlAnimateDot(stepEl) {
    var path = stepEl.querySelector('.seq-ov-path, .sys-seq-line');
    var dot = stepEl.querySelector('.seq-dot');
    if (!path || !dot || !path.getTotalLength) return;
    var len = path.getTotalLength();
    var start = performance.now();
    var dur = 550;
    function frame(now) {
        var t = Math.min(1, (now - start) / dur);
        var pt = path.getPointAtLength(t * len);
        dot.setAttribute('cx', pt.x.toFixed(1));
        dot.setAttribute('cy', pt.y.toFixed(1));
        dot.style.opacity = '1';
        if (t < 1) {
            requestAnimationFrame(frame);
        } else {
            setTimeout(function() { dot.style.opacity = '0'; }, 250);
        }
    }
    requestAnimationFrame(frame);
}

function _tlRenderNowPlaying(timeline, tick) {
    var card = timeline.querySelector('.sys-now-playing');
    if (!card) return;
    var label  = tick.dataset.label || '';
    var single = tick.dataset.example || '';
    var before = tick.dataset.exampleBefore || '';
    var after  = tick.dataset.exampleAfter || '';
    var lang   = (tick.dataset.exampleLang || 'plaintext').replace(/[^a-zA-Z0-9_-]/g, '') || 'plaintext';
    var idx    = parseInt(tick.getAttribute('data-step'), 10);

    var skeleton = '<div class="sys-now-playing-label"></div>';
    if (single) {
        skeleton += '<div class="sys-snippet"><pre><code class="language-' + lang + '"></code></pre></div>';
    } else if (before && after) {
        skeleton += '<div class="sys-chg-diff">'
            + '<div class="sys-chg-side"><div class="sys-chg-side-label" style="color:#B04A3F">Before</div>'
            + '<pre class="sys-chg-pre"><code class="language-' + lang + '"></code></pre></div>'
            + '<div class="sys-chg-side"><div class="sys-chg-side-label" style="color:#4A7C59">After</div>'
            + '<pre class="sys-chg-pre"><code class="language-' + lang + '"></code></pre></div>'
            + '</div>';
    } else if (after) {
        skeleton += '<pre class="sys-chg-pre"><code class="language-' + lang + '"></code></pre>';
    } else if (before) {
        skeleton += '<pre class="sys-chg-pre"><code class="language-' + lang + '"></code></pre>';
    }
    card.innerHTML = skeleton;

    var labelEl = card.querySelector('.sys-now-playing-label');
    if (labelEl) labelEl.textContent = 'Step ' + (idx + 1) + (label ? ': ' + label : '');

    var texts = single ? [single] : (before && after) ? [before, after] : after ? [after] : before ? [before] : [];
    var codeEls = card.querySelectorAll('pre code');
    codeEls.forEach(function(el, i) {
        el.textContent = texts[i] || '';
        if (window.hljs) hljs.highlightElement(el);
    });
}

function _tlGoToStep(timeline, newIdx, animate) {
    var kind  = timeline.getAttribute('data-target-kind');
    var ticks = timeline.querySelectorAll('.sys-tl-tick');
    var n     = ticks.length;
    if (n === 0) return;
    newIdx = Math.max(0, Math.min(n - 1, newIdx));
    var prevIdx = parseInt(timeline.getAttribute('data-current') || '-1', 10);
    timeline.setAttribute('data-current', String(newIdx));

    var pct   = n === 1 ? 0 : (newIdx / (n - 1)) * 100;
    var thumb = timeline.querySelector('.sys-tl-thumb');
    var fill  = timeline.querySelector('.sys-tl-fill');
    if (thumb) thumb.style.left = pct + '%';
    if (fill)  fill.style.width = pct + '%';

    var tick  = ticks[newIdx];
    var label = timeline.querySelector('.sys-tl-label');
    if (label) label.textContent = 'Step ' + (newIdx + 1) + '/' + n + (tick.dataset.label ? ': ' + tick.dataset.label : '');
    _tlRenderNowPlaying(timeline, tick);

    var steps = _tlSteps(timeline);
    steps.forEach(function(stepEl, idx) {
        stepEl.classList.remove('seq-active', 'seq-visited');
        if (idx < newIdx) stepEl.classList.add('seq-visited');
        if (idx === newIdx) stepEl.classList.add('seq-active');
        if (kind === 'arch') stepEl.style.opacity = (idx <= newIdx) ? '1' : '0';
    });

    var scopeNodes = kind === 'arch'
        ? document.querySelectorAll('#view-arch .sys-node')
        : (timeline.closest('.sys-wrap') ? timeline.closest('.sys-wrap').querySelectorAll('.sys-seq-participant') : []);
    scopeNodes.forEach(function(n) { n.classList.remove('seq-visited', 'seq-active'); });
    steps.forEach(function(stepEl, idx) {
        if (idx > newIdx) return;
        var to = _tlNodeFor(timeline, stepEl.getAttribute('data-to'));
        var from = _tlNodeFor(timeline, stepEl.getAttribute('data-from'));
        if (to) to.classList.add('seq-visited');
        if (from) from.classList.add('seq-visited');
    });
    var curStep = steps[newIdx];
    if (curStep) {
        var curTo = _tlNodeFor(timeline, curStep.getAttribute('data-to'));
        if (curTo) { curTo.classList.remove('seq-visited'); curTo.classList.add('seq-active'); }
    }

    if (animate && prevIdx === newIdx - 1 && curStep) {
        _tlAnimateDot(curStep);
    }
}

function _tlStopPlay(timeline) {
    var existing = _tlPlayIntervals.get(timeline);
    if (existing) {
        clearInterval(existing);
        _tlPlayIntervals.delete(timeline);
        var btn = timeline.querySelector('.sys-tl-play');
        if (btn) btn.textContent = '▶';
    }
}

function _tlReset(timeline) {
    _tlStopPlay(timeline);
    var kind = timeline.getAttribute('data-target-kind');
    timeline.removeAttribute('data-current');
    var thumb = timeline.querySelector('.sys-tl-thumb');
    var fill  = timeline.querySelector('.sys-tl-fill');
    if (thumb) thumb.style.left = '0%';
    if (fill)  fill.style.width = '0%';
    var n     = timeline.querySelectorAll('.sys-tl-tick').length;
    var label = timeline.querySelector('.sys-tl-label');
    if (label) label.textContent = 'Step 0/' + n;
    var card = timeline.querySelector('.sys-now-playing');
    if (card) card.innerHTML = '<div class="sys-now-playing-label">Select a step to preview it here</div>';
    var steps = _tlSteps(timeline);
    steps.forEach(function(s) {
        s.classList.remove('seq-active', 'seq-visited');
        if (kind === 'arch') s.style.opacity = '0';
    });
    var scopeNodes = kind === 'arch'
        ? document.querySelectorAll('#view-arch .sys-node')
        : (timeline.closest('.sys-wrap') ? timeline.closest('.sys-wrap').querySelectorAll('.sys-seq-participant') : []);
    scopeNodes.forEach(function(n) { n.classList.remove('seq-visited', 'seq-active'); });
}

function sysTlPlayToggle(btn) {
    var timeline = btn.closest('.sys-timeline');
    if (!timeline) return;
    var n = timeline.querySelectorAll('.sys-tl-tick').length;
    if (n === 0) return;

    if (_tlPlayIntervals.get(timeline)) {
        _tlStopPlay(timeline);
        return;
    }
    btn.textContent = '⏸';
    var cur = parseInt(timeline.getAttribute('data-current') || '-1', 10);
    if (cur < 0) _tlGoToStep(timeline, 0, true);
    var interval = setInterval(function() {
        var c = parseInt(timeline.getAttribute('data-current') || '-1', 10);
        var next = c + 1;
        if (next >= n) {
            _tlStopPlay(timeline);
            return;
        }
        _tlGoToStep(timeline, next, true);
    }, 1200);
    _tlPlayIntervals.set(timeline, interval);
}

function sysTlSeekClick(evt, tick) {
    evt.stopPropagation();
    var timeline = tick.closest('.sys-timeline');
    if (!timeline) return;
    _tlStopPlay(timeline);
    _tlGoToStep(timeline, parseInt(tick.getAttribute('data-step'), 10), false);
}

function sysTlTrackClick(evt, track) {
    var timeline = track.closest('.sys-timeline');
    if (!timeline) return;
    _tlStopPlay(timeline);
    var n = timeline.querySelectorAll('.sys-tl-tick').length;
    if (n === 0) return;
    var rect = track.getBoundingClientRect();
    var pct = Math.max(0, Math.min(1, (evt.clientX - rect.left) / rect.width));
    _tlGoToStep(timeline, Math.round(pct * (n - 1)), false);
}

function sysTlThumbDown(evt, thumb) {
    evt.preventDefault();
    var timeline = thumb.closest('.sys-timeline');
    if (!timeline) return;
    _tlStopPlay(timeline);
    var track = timeline.querySelector('.sys-tl-track');
    var n = timeline.querySelectorAll('.sys-tl-tick').length;
    if (!track || n === 0) return;

    function onMove(e) {
        var rect = track.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var pct = Math.max(0, Math.min(1, x / rect.width));
        _tlGoToStep(timeline, Math.round(pct * (n - 1)), false);
    }
    function onUp() {
        document.removeEventListener('pointermove', onMove);
        document.removeEventListener('pointerup', onUp);
    }
    document.addEventListener('pointermove', onMove);
    document.addEventListener('pointerup', onUp);
    onMove(evt);
}

/* ── Architecture-tab sequence animator selector ── */
function _archApplyScopeFade(seqId) {
    var touched = new Set();
    if (seqId) {
        document.querySelectorAll('.seq-step-ov[data-seq="' + CSS.escape(seqId) + '"]').forEach(function(g) {
            var f = g.getAttribute('data-from'), t = g.getAttribute('data-to');
            if (f) touched.add(f);
            if (t) touched.add(t);
        });
    }
    document.querySelectorAll('#view-arch .sys-node').forEach(function(n) {
        var nid = n.getAttribute('data-id');
        n.classList.toggle('seq-unrelated', !!seqId && !touched.has(nid));
    });
    document.querySelectorAll('#view-arch .sys-edge').forEach(function(e) {
        var f = e.getAttribute('data-from'), t = e.getAttribute('data-to');
        var related = touched.has(f) && touched.has(t);
        e.classList.toggle('seq-unrelated', !!seqId && !related);
    });
}

function sysArchSeqChange(sel) {
    var val = sel.value;
    document.querySelectorAll('.sys-atl-block').forEach(function(b) {
        var match = val !== '' && b.getAttribute('data-seq') === val;
        b.style.display = match ? '' : 'none';
        if (!match) {
            var tl = b.querySelector('.sys-timeline');
            if (tl) _tlReset(tl);
        }
    });
    _archApplyScopeFade(val);
}

/* ── Jump to a sequence from a node's detail panel ── */
function sysPlaySeqFromNode(btn) {
    var seqId = btn.getAttribute('data-seq');
    var stepIdx = parseInt(btn.getAttribute('data-step'), 10);

    var tabBtn = document.querySelector('.sys-tab[data-view="arch"]');
    if (tabBtn) sysTab(tabBtn);

    var sel = document.querySelector('.sys-arch-animate .sys-seq-sel');
    if (sel && sel.value !== seqId) {
        sel.value = seqId;
        sysArchSeqChange(sel);
    }

    var block = document.querySelector('.sys-atl-block[data-seq="' + CSS.escape(seqId) + '"]');
    var timeline = block ? block.querySelector('.sys-timeline') : null;
    if (timeline) {
        _tlStopPlay(timeline);
        _tlGoToStep(timeline, stepIdx, false);
        timeline.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

/* ── Architecture kind + status filters ─────────── */
function sysAKind(btn) {
    btn.classList.toggle('active');
    _applyArchFilter();
}
function sysAStatus(btn) {
    btn.classList.toggle('active');
    _applyArchFilter();
}
function sysAEKind(btn) {
    btn.classList.toggle('active');
    _applyArchFilter();
}
function sysAGroup(btn) {
    btn.classList.toggle('active');
    _applyArchFilter();
}
function _applyArchFilter() {
    var kinds = new Set();
    document.querySelectorAll('.sys-fc[data-ak].active').forEach(function(b) { kinds.add(b.getAttribute('data-ak')); });
    var statuses = new Set();
    document.querySelectorAll('.sys-fc[data-as].active').forEach(function(b) { statuses.add(b.getAttribute('data-as')); });
    var ekinds = new Set();
    document.querySelectorAll('.sys-fc[data-aek].active').forEach(function(b) { ekinds.add(b.getAttribute('data-aek')); });
    var agroups = new Set();
    document.querySelectorAll('.sys-fc[data-ag].active').forEach(function(b) { agroups.add(b.getAttribute('data-ag')); });
    var hasKindFilter   = document.querySelectorAll('.sys-fc[data-ak]').length > 0;
    var hasStatusFilter = document.querySelectorAll('.sys-fc[data-as]').length > 0;
    var hasEKindFilter  = document.querySelectorAll('.sys-fc[data-aek]').length > 0;
    var hasGroupFilter  = document.querySelectorAll('.sys-fc[data-ag]').length > 0;

    // Groups not currently active — if none are active, every group counts as inactive
    // (so deselecting all group toggles fades all groups, rather than showing everything).
    var inactiveGroups = new Set();
    if (hasGroupFilter) {
        document.querySelectorAll('.sys-fc[data-ag]').forEach(function(b) {
            var gid = b.getAttribute('data-ag');
            if (!agroups.has(gid)) inactiveGroups.add(gid);
        });
    }
    function _inInactiveGroup(groupsAttr) {
        if (inactiveGroups.size === 0 || !groupsAttr) return false;
        return groupsAttr.split(' ').some(function(gid) { return gid && inactiveGroups.has(gid); });
    }

    var hiddenNodes = new Set();
    document.querySelectorAll('.sys-node').forEach(function(n) {
        var k = n.getAttribute('data-kind');
        var s = n.getAttribute('data-status') || '';
        var kOk = !hasKindFilter   || (kinds.size > 0 && kinds.has(k));
        var sOk = !hasStatusFilter || !s || (statuses.size > 0 && statuses.has(s));
        var groupFaded = _inInactiveGroup(n.getAttribute('data-groups'));
        var hidden = !(kOk && sOk) || groupFaded;
        n.classList.toggle('filtered-out', hidden);
        if (hidden) hiddenNodes.add(n.getAttribute('data-id'));
    });
    document.querySelectorAll('.sys-edge').forEach(function(e) {
        var k = e.getAttribute('data-kind');
        var eOk = !hasEKindFilter || (ekinds.size > 0 && ekinds.has(k));
        var groupFaded = _inInactiveGroup(e.getAttribute('data-src-groups')) ||
                          _inInactiveGroup(e.getAttribute('data-dst-groups'));
        var endpointHidden = hiddenNodes.has(e.getAttribute('data-from')) || hiddenNodes.has(e.getAttribute('data-to'));
        e.classList.toggle('filtered-out', !eOk || groupFaded || endpointHidden);
    });
    document.querySelectorAll('.sys-group').forEach(function(g) {
        var gid = g.getAttribute('data-gid');
        var gOk = !hasGroupFilter || (agroups.size > 0 && agroups.has(gid));
        g.classList.toggle('filtered-out', !gOk);
    });
}

/* ── Sequence selector ─────────────────────────── */
function sysSeqChange(sel) {
    var val = sel.value;
    document.querySelectorAll('.sys-seq-panel').forEach(function(p) {
        p.style.display = (p.id === 'seqp-' + val) ? '' : 'none';
    });
}

/* ── Code detail selector ──────────────────────── */
function sysCodeDetailChange(sel) {
    var val = sel.value;
    document.querySelectorAll('.sys-cd-panel').forEach(function(p) {
        p.style.display = (p.id === 'cdp-' + val) ? '' : 'none';
    });
}

/* ── Component list filters ────────────────────── */
function sysFKind(btn) {
    btn.classList.toggle('active');
    _applyListFilter();
}
function sysFStatus(btn) {
    btn.classList.toggle('active');
    _applyListFilter();
}
function _applyListFilter() {
    var kinds = new Set();
    document.querySelectorAll('.sys-fc[data-fk].active').forEach(function(b) { kinds.add(b.getAttribute('data-fk')); });
    var statuses = new Set();
    document.querySelectorAll('.sys-fc[data-fs].active').forEach(function(b) { statuses.add(b.getAttribute('data-fs')); });
    var hasKindFilter = document.querySelectorAll('.sys-fc[data-fk]').length > 0;
    var hasStatusFilter = document.querySelectorAll('.sys-fc[data-fs]').length > 0;
    document.querySelectorAll('.sys-cr').forEach(function(row) {
        var k = row.getAttribute('data-rkind');
        var s = row.getAttribute('data-rstatus');
        var kOk = !hasKindFilter || kinds.size === 0 || kinds.has(k);
        var sOk = !hasStatusFilter || statuses.size === 0 || !s || statuses.has(s);
        row.style.display = (kOk && sOk) ? '' : 'none';
    });
}
"""
