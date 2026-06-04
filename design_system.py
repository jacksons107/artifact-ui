import html as _html

BASE_CSS = """
:root {
  --ivory: #FAF9F5;
  --slate: #141413;
  --clay: #D97757;
  --clay-d: #B85C3E;
  --oat: #E3DACC;
  --olive: #788C5D;
  --rust: #B04A3F;
  --white: #FFFFFF;

  --gray-100: #F0EEE6;
  --gray-300: #D1CFC5;
  --gray-500: #87867F;
  --gray-700: #3D3D3A;

  --serif: ui-serif, Georgia, serif;
  --sans: system-ui, -apple-system, sans-serif;
  --mono: ui-monospace, 'SF Mono', Menlo, monospace;

  --border: 1.5px solid var(--gray-300);
  --radius-sm: 8px;
  --radius-md: 12px;

  --shadow-sm: 0 1px 2px rgba(20,20,19,0.06);
  --shadow-md: 0 4px 14px rgba(20,20,19,0.08);
}

*, *::before, *::after { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--ivory);
  color: var(--slate);
  font-family: var(--sans);
  font-size: 15px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

.page {
  max-width: 920px;
  margin: 0 auto;
  padding: 48px 28px 96px;
}

.page-wide {
  max-width: 1180px;
  margin: 0 auto;
  padding: 48px 32px 64px;
}

/* ── Page header ── */
.page-header { margin-bottom: 40px; }
.eyebrow {
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--gray-500);
  margin-bottom: 6px;
}
.page-header h1 {
  font-family: var(--serif);
  font-weight: 500;
  font-size: 36px;
  letter-spacing: -0.01em;
  margin: 0 0 6px;
}
.page-header .description {
  color: var(--gray-500);
  font-size: 14px;
  margin: 0;
  max-width: 640px;
}

/* ── Section ── */
.section { margin-bottom: 48px; }
.section-header { display: flex; align-items: center; gap: 16px; margin-bottom: 18px; }
.section-header h2 {
  font-family: var(--serif);
  font-weight: 500;
  font-size: 22px;
  letter-spacing: -0.01em;
  margin: 0;
  white-space: nowrap;
}
.section-divider { flex: 1; height: 1px; background: var(--gray-300); }

/* ── Layouts ── */
.layout-stack { display: flex; flex-direction: column; gap: 16px; }
.layout-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
.layout-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.layout-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.layout-sidebar { display: grid; grid-template-columns: 1fr 300px; gap: 32px; align-items: start; }
.layout-sidebar .sidebar { position: sticky; top: 24px; }

@media (max-width: 920px) {
  .layout-grid-2, .layout-grid-3, .layout-grid-4, .layout-sidebar {
    grid-template-columns: 1fr;
  }
}

/* ── Badge ── */
.badge {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 9px;
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 500;
  border-radius: 999px;
}
.badge-neutral  { background: var(--gray-100); color: var(--gray-700); }
.badge-accent   { background: rgba(217,119,87,0.14); color: var(--clay); }
.badge-success  { background: rgba(120,140,93,0.16); color: var(--olive); }
.badge-warning  { background: rgba(184,156,110,0.20); color: #7A6A4F; }
.badge-danger   { background: rgba(176,74,63,0.14); color: var(--rust); }
.badge-outlined { background: transparent; color: var(--gray-700); border: var(--border); }

/* ── Avatar ── */
.avatar {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: var(--oat);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-700);
}
.avatar.bordered { border: 1.5px solid var(--gray-300); }
.avatar.o2 { background: #DCE4D2; }
.avatar.o3 { background: #ECD9CE; }
.avatar.o4 { background: var(--gray-100); }

/* ── Buttons ── */
.btn {
  display: inline-flex;
  align-items: center;
  height: 36px;
  padding: 0 16px;
  font-family: var(--sans);
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s;
  border: 1.5px solid transparent;
}
.btn-primary   { background: var(--clay); color: var(--white); border-color: var(--clay); }
.btn-primary:hover { background: var(--clay-d); border-color: var(--clay-d); }
.btn-secondary { background: var(--white); color: var(--slate); border-color: var(--gray-300); }
.btn-secondary:hover { background: var(--gray-100); }
.btn-ghost     { background: transparent; color: var(--gray-700); border-color: var(--gray-300); }
.btn-ghost:hover { background: var(--gray-100); }
.btn-danger    { background: var(--rust); color: var(--white); border-color: var(--rust); }
.btn-danger:hover { background: #9A3F3F; border-color: #9A3F3F; }

/* ── Chip (inline tag) ── */
.chip {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 8px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 999px;
  background: var(--gray-100);
  color: var(--gray-700);
}
.chip.olive { background: rgba(120,140,93,0.16); color: var(--olive); }
.chip.clay  { background: rgba(217,119,87,0.14); color: var(--clay); }
.chip.rust  { background: rgba(176,74,63,0.14); color: var(--rust); }

/* ── Card ── */
.card {
  border-radius: 12px;
  padding: 20px;
  transition: box-shadow 0.15s;
}
.card:hover { outline: 2px solid var(--clay); outline-offset: 2px; }
.card-head   { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.card-titles { min-width: 0; }
.card-title  { font-family: var(--serif); font-size: 17px; font-weight: 500; margin: 0 0 2px; line-height: 1.3; }
.card-sub    { font-size: 13px; color: var(--gray-500); margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-chips  { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 14px; }

.card.flat     { background: var(--white); }
.card.outlined { background: var(--white); border: var(--border); }
.card.elevated { background: var(--white); box-shadow: var(--shadow-md); }
.card.stripe   { background: var(--white); border: var(--border); position: relative; overflow: hidden; }
.card.stripe::before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 4px; background: var(--clay); }
.card.inset    { background: var(--oat); }
.card.horizontal { background: var(--white); border: var(--border); display: flex; align-items: center; gap: 14px; }
.card.horizontal .card-head  { margin: 0; flex: 1; min-width: 0; }
.card.horizontal .card-chips { margin: 0; }

/* ── Stat card ── */
.stat-card {
  background: var(--white);
  border: var(--border);
  border-radius: 12px;
  padding: 20px 22px 18px;
}
.stat-card.warn { border-left: 4px solid var(--clay); padding-left: 19px; }
.stat-num   { font-family: var(--serif); font-size: 44px; font-weight: 500; line-height: 1; margin-bottom: 8px; }
.stat-label { font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--gray-500); }
.stat-delta { font-family: var(--mono); font-size: 11px; margin-top: 6px; }
.stat-delta.up   { color: var(--olive); }
.stat-delta.flat { color: var(--gray-500); }
.stat-delta.down { color: var(--rust); }

/* ── Data table ── */
table.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: var(--white);
  border: var(--border);
  border-radius: 12px;
  overflow: hidden;
}
table.data-table thead th {
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--gray-500);
  background: var(--gray-100);
  padding: 12px 16px;
  border-bottom: 1px solid var(--gray-300);
}
table.data-table tbody td {
  padding: 13px 16px;
  border-bottom: 1px solid var(--gray-100);
  font-size: 14px;
  vertical-align: middle;
}
table.data-table tbody tr:last-child td { border-bottom: none; }
table.data-table tbody tr:hover { background: var(--ivory); }

.pr-link { font-family: var(--mono); font-size: 13px; color: var(--clay); text-decoration: none; border-bottom: 1px dotted transparent; }
.pr-link:hover { border-bottom-color: var(--clay); }
.risk { display: inline-flex; align-items: center; gap: 7px; font-size: 12px; color: var(--gray-500); }
.risk-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; display: inline-block; }
.risk-dot.low  { background: var(--olive); }
.risk-dot.med  { background: var(--clay); }
.risk-dot.high { background: var(--rust); }

/* ── Diff block ── */
.diff {
  background: var(--slate);
  font-family: var(--mono);
  font-size: 12.5px;
  line-height: 1.7;
  overflow-x: auto;
  border-radius: 8px;
}
.diff-row {
  display: grid;
  grid-template-columns: 48px 18px 1fr;
  align-items: baseline;
  padding: 0 14px 0 0;
  white-space: pre;
}
.diff-row .ln   { text-align: right; padding-right: 14px; color: var(--gray-500); user-select: none; }
.diff-row .mark { text-align: center; color: var(--gray-500); }
.diff-row .code { color: #E8E6DC; }
.diff-row.ctx .code { color: #B8B6AC; }
.diff-row.add { background: rgba(120,140,93,0.15); }
.diff-row.add .mark { color: var(--olive); }
.diff-row.del { background: rgba(176,74,63,0.15); }
.diff-row.del .mark { color: var(--rust); }
.diff-row.hunk { background: rgba(255,255,255,0.04); }
.diff-row.hunk .code { color: var(--gray-500); }

/* ── Review comments ── */
.comment-thread { display: flex; flex-direction: column; gap: 14px; padding: 18px 20px 20px; background: var(--gray-100); }
.bubble {
  position: relative;
  background: var(--white);
  border: 1.5px solid var(--gray-300);
  border-left-width: 4px;
  border-radius: 8px;
  padding: 12px 14px 12px 16px;
  max-width: 680px;
}
.bubble.blocking { border-left-color: var(--clay); }
.bubble.nit      { border-left-color: var(--gray-300); }
.bubble.suggest  { border-left-color: var(--olive); }
.bubble .anchor  { font-family: var(--mono); font-size: 11.5px; color: var(--gray-500); margin-bottom: 4px; }
.bubble .label   { font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; margin-right: 8px; }
.bubble.blocking .label { color: var(--clay); }
.bubble.nit .label      { color: var(--gray-500); }
.bubble.suggest .label  { color: var(--olive); }

/* ── Kanban board ── */
.kanban-board { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; align-items: start; }
@media (max-width: 920px) { .kanban-board { grid-template-columns: repeat(2, 1fr); } }

.kanban-col {
  background: var(--white);
  border: 1.5px solid var(--gray-300);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 200px;
}
.kanban-col.accent-clay  { border-top: 3px solid var(--clay); }
.kanban-col.accent-olive { border-top: 3px solid var(--olive); }
.kanban-col.accent-gray  { border-top: 3px solid var(--gray-500); }
.kanban-col.accent-light { border-top: 3px solid var(--gray-300); }
.kanban-col.dragover { outline: 2px dashed var(--clay); outline-offset: -6px; background: #FBF6F2; }

.kanban-col-head {
  position: sticky; top: 0; z-index: 1;
  background: var(--white);
  display: flex; align-items: baseline; gap: 8px;
  padding: 14px 14px 10px;
  border-bottom: 1.5px solid var(--gray-100);
}
.kanban-col-head h3 {
  font-family: var(--serif);
  font-weight: 500;
  font-size: 17px;
  margin: 0;
  letter-spacing: -0.01em;
}
.kanban-col-head .count {
  margin-left: auto;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--gray-500);
  background: var(--gray-100);
  border: 1.5px solid var(--gray-300);
  border-radius: 999px;
  padding: 1px 8px;
  min-width: 26px;
  text-align: center;
}
.kanban-col-body { padding: 10px 10px 6px; display: flex; flex-direction: column; gap: 8px; flex: 1; min-height: 60px; }

/* ── Ticket ── */
.ticket {
  background: var(--white);
  border: 1.5px solid var(--gray-300);
  border-radius: 8px;
  padding: 10px 11px 9px;
  cursor: grab;
  user-select: none;
  transition: border-color 120ms ease, box-shadow 120ms ease, opacity 120ms ease;
}
.ticket:hover  { border-color: var(--gray-500); box-shadow: var(--shadow-sm); }
.ticket:active { cursor: grabbing; }
.ticket.dragging { opacity: .4; }
.ticket.dim      { opacity: .25; }

.ticket-top { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }
.tid    { font-family: var(--mono); font-size: 11px; color: var(--gray-500); }
.ttitle { font-size: 13px; line-height: 1.35; color: var(--slate); margin-bottom: 7px; }
.ticket-bot { display: flex; align-items: center; gap: 6px; }

.tag { font-family: var(--mono); font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; border-radius: 999px; padding: 1px 7px 2px; border: 1px solid transparent; cursor: pointer; }
.tag:hover { filter: brightness(0.96); }
.tag-bug   { background: #F5E2D8; color: var(--clay-d); border-color: #E8C9BA; }
.tag-feat  { background: #E8EDE0; color: #5C6F44; border-color: #CFDAC0; }
.tag-chore, .tag-debt { background: var(--gray-100); color: var(--gray-700); border-color: var(--gray-300); }

.est {
  margin-left: auto;
  font-family: var(--mono);
  font-size: 10px;
  color: var(--gray-500);
  border: 1.5px solid var(--gray-300);
  border-radius: 4px;
  width: 18px; height: 18px;
  display: flex; align-items: center; justify-content: center;
}
.owner {
  font-family: var(--mono);
  font-size: 10px;
  width: 20px; height: 20px;
  border-radius: 50%;
  background: var(--oat);
  color: var(--gray-700);
  display: flex; align-items: center; justify-content: center;
}
.owner.o2 { background: #DCE4D2; }
.owner.o3 { background: #ECD9CE; }
.owner.o4 { background: var(--gray-100); }

/* ── Toolbar ── */
.toolbar {
  position: sticky; top: 0; z-index: 10;
  display: flex; flex-wrap: wrap; align-items: center; gap: 28px;
  padding: 16px 20px;
  margin-bottom: 28px;
  background: var(--white);
  border: var(--border);
  border-radius: 12px;
}
.control { display: flex; align-items: center; gap: 10px; }
.control-label { font-family: var(--mono); font-size: 12px; color: var(--gray-700); }
.control-value { font-family: var(--mono); font-size: 12px; color: var(--gray-500); min-width: 36px; }

input[type="range"] { appearance: none; width: 140px; height: 4px; background: var(--gray-300); border-radius: 2px; outline: none; }
input[type="range"]::-webkit-slider-thumb { appearance: none; width: 16px; height: 16px; background: var(--clay); border-radius: 50%; cursor: pointer; }
input[type="range"]::-moz-range-thumb { width: 16px; height: 16px; background: var(--clay); border: none; border-radius: 50%; cursor: pointer; }

.radio-group { display: inline-flex; border: var(--border); border-radius: 8px; overflow: hidden; }
.radio-group label { padding: 6px 12px; font-size: 13px; cursor: pointer; user-select: none; color: var(--gray-700); border-right: 1px solid var(--gray-300); }
.radio-group label:last-child { border-right: none; }
.radio-group input { display: none; }
.radio-group label:has(input:checked) { background: var(--gray-100); }

.check { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; cursor: pointer; user-select: none; }
.check input { appearance: none; width: 16px; height: 16px; border: 1.5px solid var(--gray-300); border-radius: 4px; margin: 0; cursor: pointer; position: relative; }
.check input:checked { background: var(--clay); border-color: var(--clay); }
.check input:checked::after { content: ""; position: absolute; left: 4px; top: 0; width: 4px; height: 9px; border: solid var(--white); border-width: 0 2px 2px 0; transform: rotate(45deg); }

/* ── Bullet list ── */
.bullet-list { list-style: none; margin: 0; padding: 0; }
.bullet-list li { position: relative; padding: 0 0 12px 24px; font-size: 15px; color: var(--gray-700); }
.bullet-list li::before { content: ""; position: absolute; left: 6px; top: 8px; width: 7px; height: 7px; border-radius: 2px; background: var(--clay); }
.bullet-list li strong { color: var(--slate); font-weight: 600; }

/* ── Inset panel ── */
.inset-panel { background: var(--oat); border-radius: 12px; padding: 20px 22px; }
.inset-item { display: flex; align-items: baseline; gap: 14px; padding: 8px 0; }
.inset-item + .inset-item { border-top: 1px solid rgba(20,20,19,0.08); }
.inset-tag  { font-family: var(--mono); font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--gray-700); background: var(--ivory); border-radius: 4px; padding: 3px 7px; flex-shrink: 0; }
.inset-body { font-size: 14px; color: var(--gray-700); }
.inset-note { color: var(--gray-500); font-size: 12px; }

/* ── Prose / body copy ── */
.prose p { margin: 0 0 14px; color: var(--gray-700); }
.prose ul { list-style: none; padding: 0; margin: 0; }
.prose li { position: relative; padding-left: 22px; margin-bottom: 10px; }
.prose li::before { content: ""; position: absolute; left: 4px; top: 9px; width: 6px; height: 6px; background: var(--gray-500); border-radius: 2px; }

/* flow_diagram */
.diagram-wrap { background: var(--white); border: var(--border); border-radius: 12px; padding: 24px; overflow: hidden; }
.diagram-caption { font-size: 12px; color: var(--gray-500); margin-top: 12px; font-family: var(--mono); }

/* ── Utility ── */
.divider { border: none; border-top: 1px solid var(--gray-300); margin: 0; }
.mono    { font-family: var(--mono); }
.serif   { font-family: var(--serif); }
.text-muted { color: var(--gray-500); }
.text-sm { font-size: 13px; }
.text-xs { font-size: 12px; }

/* ── Organisms ── */

/* chart-panel */
.chart-panel { background: var(--white); border: var(--border); border-radius: 12px; padding: 24px 28px 18px; }
.chart-panel svg { display: block; width: 100%; height: auto; }

/* file-card (PR review) */
.file-card { border: var(--border); border-radius: 12px; background: var(--white); margin-bottom: 16px; overflow: hidden; scroll-margin-top: 20px; }
.file-head { padding: 14px 20px; border-bottom: 1.5px solid var(--gray-100); display: flex; align-items: center; gap: 12px; }
.file-path { font-family: var(--mono); font-size: 13px; color: var(--slate); flex: 1; }
.file-delta { font-family: var(--mono); font-size: 12px; color: var(--gray-500); }
.risk-tag { font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; padding: 3px 8px; border-radius: 6px; font-weight: 600; }
.risk-tag.safe      { background: rgba(120,140,93,0.15); color: var(--olive); }
.risk-tag.medium    { background: var(--oat); color: #7A6A4F; }
.risk-tag.attention { background: rgba(217,119,87,0.15); color: var(--clay); }

/* event_timeline */
.event-timeline { display: flex; flex-direction: column; gap: 0; position: relative; }
.event-entry { display: grid; grid-template-columns: 72px 24px 1fr; gap: 0 12px; align-items: flex-start; padding: 0 0 20px; }
.event-time { font-family: var(--mono); font-size: 11px; color: var(--gray-500); padding-top: 3px; text-align: right; }
.event-dot-wrap { display: flex; flex-direction: column; align-items: center; gap: 0; }
.event-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }
.event-entry:not(:last-child) .event-dot-wrap::after { content: ""; display: block; width: 2px; flex: 1; background: var(--gray-300); margin-top: 4px; min-height: 16px; }
.event-body { font-size: 14px; color: var(--gray-700); padding-top: 2px; }

/* milestone_timeline */
.milestone-timeline { display: flex; flex-direction: column; gap: 0; }
.milestone { display: grid; grid-template-columns: 120px 28px 1fr; gap: 0 14px; padding: 0 0 24px; }
.milestone-date { font-family: var(--mono); font-size: 11px; color: var(--gray-500); text-align: right; padding-top: 3px; }
.milestone-track { display: flex; flex-direction: column; align-items: center; }
.milestone-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; margin-top: 2px; }
.milestone:not(:last-child) .milestone-track::after { content: ""; display: block; width: 2px; flex: 1; background: var(--gray-300); margin-top: 4px; min-height: 20px; }
.milestone-content h4 { font-family: var(--serif); font-size: 16px; font-weight: 500; margin: 0; }

/* shipped_item_list */
.shipped-list { display: flex; flex-direction: column; }
.shipped-item { display: flex; align-items: flex-start; gap: 14px; padding: 14px 0; border-bottom: 1px solid var(--gray-100); }
.shipped-item:last-child { border-bottom: none; }
.shipped-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 6px; }
.shipped-body { flex: 1; min-width: 0; }
.shipped-title { font-family: var(--serif); font-size: 15px; font-weight: 500; margin-bottom: 2px; }
.shipped-desc { font-size: 13px; color: var(--gray-500); }
.shipped-ref { font-family: var(--mono); font-size: 12px; color: var(--clay); white-space: nowrap; padding-top: 2px; }

/* callout */
.callout { border-radius: 12px; padding: 20px 24px; margin-bottom: 0; }
.callout.callout-dark { background: var(--slate); color: var(--ivory); }
.callout.callout-tinted { background: var(--oat); }
.callout-label { font-family: var(--mono); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
.callout.callout-dark .callout-label { color: var(--oat); }
.callout.callout-tinted .callout-label { color: var(--clay); }
.callout-content { font-size: 14px; line-height: 1.65; }
.callout.callout-dark .callout-content { color: rgba(250,249,245,0.85); }
.callout.callout-tinted .callout-content { color: var(--gray-700); }

/* action_checklist */
.action-list { display: flex; flex-direction: column; gap: 10px; }
.action-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; background: var(--white); border: var(--border); border-radius: 8px; }
.action-item.done { background: var(--gray-100); }
.action-check { width: 18px; height: 18px; border-radius: 4px; border: 1.5px solid var(--gray-300); display: flex; align-items: center; justify-content: center; font-size: 11px; flex-shrink: 0; }
.action-body { flex: 1; font-size: 13px; color: var(--gray-700); }
.action-due { font-family: var(--mono); font-size: 11px; color: var(--gray-500); white-space: nowrap; }

/* decision_card */
.decision-card { background: var(--white); border: 2px solid var(--clay); border-radius: 12px; padding: 24px; background: rgba(217,119,87,0.05); }
.decision-question { font-family: var(--serif); font-size: 22px; font-weight: 500; line-height: 1.3; margin-bottom: 8px; }

/* code_block */
.code-block-wrap { border: var(--border); border-radius: 10px; overflow: hidden; }
.code-block-head { padding: 9px 14px; background: var(--gray-100); border-bottom: 1px solid var(--gray-300); display: flex; align-items: center; justify-content: space-between; }
.code-block-body { margin: 0; padding: 16px 18px; background: var(--slate); color: #E8E6DC; font-family: var(--mono); font-size: 12.5px; line-height: 1.7; overflow-x: auto; }

/* drag_list */
.drag-list { list-style: none; margin: 0; padding: 0; }
.drag-item { display: flex; align-items: center; gap: 10px; padding: 9px 10px; margin: 2px 0; border-radius: 8px; cursor: grab; user-select: none; transition: background 120ms, opacity 120ms; }
.drag-item:hover { background: var(--gray-100); }
.drag-item.dragging { opacity: 0.35; cursor: grabbing; }
.drag-grip { display: grid; grid-template-columns: 3px 3px; gap: 3px; width: 10px; height: 16px; }
.drag-grip i { display: block; width: 3px; height: 3px; border-radius: 50%; background: var(--gray-300); }
.drag-item:hover .drag-grip i { background: var(--gray-700); }
.drag-label { flex: 1; font-size: 14px; color: var(--slate); }
.drag-count { font-family: var(--mono); font-size: 11px; color: var(--gray-500); background: var(--gray-100); border: 1.5px solid var(--gray-300); border-radius: 999px; padding: 1px 8px; }

/* step_list */
.step-list { display: flex; flex-direction: column; gap: 20px; }
.step { display: grid; grid-template-columns: 28px 1fr; gap: 14px; align-items: flex-start; }
.step-num { width: 28px; height: 28px; border-radius: 50%; background: var(--clay); color: var(--white); font-family: var(--mono); font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.step-title { font-weight: 500; font-size: 15px; color: var(--slate); padding-top: 4px; }

/* two_col_compare */
.two-col-compare { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 720px) { .two-col-compare { grid-template-columns: 1fr; } }
.compare-col-head { font-family: var(--mono); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--gray-500); margin-bottom: 12px; }
"""


def page_wrapper(title: str, body_html: str, extra_css: str = "", wide: bool = False) -> str:
    page_class = "page-wide" if wide else "page"
    css = BASE_CSS + extra_css
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_html.escape(title)}</title>
  <style>{css}</style>
</head>
<body>
  <div class="{page_class}">
    {body_html}
  </div>
</body>
</html>"""
