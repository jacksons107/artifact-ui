# ── Sequence animation: diagram view, playback timeline, architecture ──────
# overlay/animate selector. One cohesive feature (sequence playback),
# spanning the Sequences tab's own diagrams and the Architecture tab's
# "Animate" overlay — both drive the same scrub/play timeline widget.

CSS = """
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
"""

JS = """
/* ── Sequence playback timeline ─────────────────── */
var _tlPlayIntervals = new WeakMap();

function _tlSteps(timeline) {
    var kind = timeline.getAttribute('data-target-kind');
    var seqId = timeline.getAttribute('data-seq');
    var list;
    if (kind === 'arch') {
        var scope = timeline.closest('.sys-arch-scope');
        list = scope ? scope.querySelectorAll('.seq-step-ov[data-seq="' + CSS.escape(seqId) + '"]') : [];
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
        var scope = timeline.closest('.sys-arch-scope');
        return scope ? scope.querySelector('.sys-node[data-id="' + CSS.escape(nodeId) + '"]') : null;
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
        ? (timeline.closest('.sys-arch-scope') ? timeline.closest('.sys-arch-scope').querySelectorAll('.sys-node') : [])
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
        ? (timeline.closest('.sys-arch-scope') ? timeline.closest('.sys-arch-scope').querySelectorAll('.sys-node') : [])
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
function _archApplyScopeFade(scope, seqId) {
    var touched = new Set();
    if (seqId) {
        scope.querySelectorAll('.seq-step-ov[data-seq="' + CSS.escape(seqId) + '"]').forEach(function(g) {
            var f = g.getAttribute('data-from'), t = g.getAttribute('data-to');
            if (f) touched.add(f);
            if (t) touched.add(t);
        });
    }
    scope.querySelectorAll('.sys-node').forEach(function(n) {
        var nid = n.getAttribute('data-id');
        n.classList.toggle('seq-unrelated', !!seqId && !touched.has(nid));
    });
    scope.querySelectorAll('.sys-edge').forEach(function(e) {
        var f = e.getAttribute('data-from'), t = e.getAttribute('data-to');
        var related = touched.has(f) && touched.has(t);
        e.classList.toggle('seq-unrelated', !!seqId && !related);
    });
}

function sysArchSeqChange(sel) {
    var scope = sel.closest('.sys-arch-scope');
    if (!scope) return;
    var val = sel.value;
    scope.querySelectorAll('.sys-atl-block').forEach(function(b) {
        var match = val !== '' && b.getAttribute('data-seq') === val;
        b.style.display = match ? '' : 'none';
        if (!match) {
            var tl = b.querySelector('.sys-timeline');
            if (tl) _tlReset(tl);
        }
    });
    _archApplyScopeFade(scope, val);
}

/* ── Jump to a sequence from a node's detail panel ── */
function sysPlaySeqFromNode(btn) {
    var scope = btn.closest('.sys-arch-scope');
    if (!scope) return;
    var seqId = btn.getAttribute('data-seq');
    var stepIdx = parseInt(btn.getAttribute('data-step'), 10);

    var sel = scope.querySelector('.sys-arch-animate .sys-seq-sel');
    if (sel && sel.value !== seqId) {
        sel.value = seqId;
        sysArchSeqChange(sel);
    }

    var block = scope.querySelector('.sys-atl-block[data-seq="' + CSS.escape(seqId) + '"]');
    var timeline = block ? block.querySelector('.sys-timeline') : null;
    if (timeline) {
        _tlStopPlay(timeline);
        _tlGoToStep(timeline, stepIdx, false);
        timeline.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

/* ── Sequence selector ─────────────────────────── */
function sysSeqChange(sel) {
    var val = sel.value;
    document.querySelectorAll('.sys-seq-panel').forEach(function(p) {
        p.style.display = (p.id === 'seqp-' + val) ? '' : 'none';
    });
}
"""
