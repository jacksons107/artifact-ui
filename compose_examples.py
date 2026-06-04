"""
21 compose payload examples — one per Anthropic example page, plus data_flow.
Each value is the full data dict for render_artifact(template='compose', data=...).
Call get_example(name) via MCP to retrieve any of these.
"""

EXAMPLES = {}

# ── 1. engineering_status ─────────────────────────────────────────────────────
EXAMPLES["engineering_status"] = {
    "title": "Engineering Status — Week 11",
    "header": {
        "eyebrow": "acme/app · main",
        "title": "Engineering Status — Week 11",
        "description": "Mar 10 – Mar 16, 2025",
        "pill": "auto-generated",
    },
    "sections": [
        {
            "layout": "grid", "cols": 4, "gap": 14,
            "items": [
                {"primitive": "stat_card", "number": 14, "label": "PRs merged", "delta": "+3 vs wk10", "delta_direction": "up"},
                {"primitive": "stat_card", "number": 6,  "label": "Deploys", "delta": "±0", "delta_direction": "flat"},
                {"primitive": "stat_card", "number": 1,  "label": "Incidents", "warning": True, "delta": "SEV-2 · 47m", "delta_direction": "flat"},
                {"primitive": "stat_card", "number": 3,  "label": "Flaky tests fixed", "delta": "suite now 99.1%", "delta_direction": "up"},
            ],
        },
        {
            "header": "Highlights", "layout": "stack",
            "items": [{"primitive": "bullet_list", "items": [
                {"strong": "Bulk task editing shipped to 100%.", "text": "Multi-select toolbar ramped to all workspaces by Thursday with no error-rate regression."},
                {"strong": "Sync API p95 down 38%.", "text": "Replacing per-task auth checks with a batch lookup cut the hot path from 410ms to 255ms."},
                {"strong": "One SEV-2 on Wednesday", "text": "— a config rollout pushed a bad connection-pool limit to sync workers. Mitigated in 47 minutes."},
            ]}],
        },
        {
            "header": "Shipped", "layout": "stack",
            "items": [{"primitive": "table", "columns": ["PR", "Title", "Author", "Risk"], "rows": [
                [{"type": "link", "text": "#4871"}, "Bulk edit toolbar: selection model + keyboard shortcuts", "Mira Okafor", {"type": "risk", "level": "med", "label": "Med"}],
                [{"type": "link", "text": "#4874"}, "Batch auth lookup for /v2/sync hot path", "Devon Park", {"type": "risk", "level": "med", "label": "Med"}],
                [{"type": "link", "text": "#4878"}, "Fix race in attachment uploader retry loop", "Sam Reyes", {"type": "risk", "level": "low", "label": "Low"}],
                [{"type": "link", "text": "#4879"}, "Migrate reminder scheduler to idempotent job keys", "Priya Anand", {"type": "risk", "level": "high", "label": "High"}],
                [{"type": "link", "text": "#4882"}, "Board view: collapse empty swimlanes by default", "Mira Okafor", {"type": "risk", "level": "low", "label": "Low"}],
            ]}],
        },
        {
            "header": "Velocity", "layout": "stack",
            "items": [{"primitive": "bar_chart", "y_max": 4,
                "bars": [
                    {"label": "Mon", "value": 2}, {"label": "Tue", "value": 3},
                    {"label": "Wed", "value": 1}, {"label": "Thu", "value": 4, "highlight": True},
                    {"label": "Fri", "value": 2}, {"label": "Sat", "value": 1}, {"label": "Sun", "value": 1},
                ],
                "caption": "PRs merged per day. Thursday spike is the bulk-edit feature train (4 PRs landed together).",
            }],
        },
        {
            "header": "Carryover", "layout": "stack",
            "items": [{"primitive": "inset_panel", "items": [
                {"tag": "In review", "text": "Workspace export to CSV — waiting on pagination review.", "note": "Sam Reyes"},
                {"tag": "Blocked",   "text": "SSO group mapping — blocked on staging IdP credentials from IT.", "note": "Priya Anand"},
                {"tag": "Slipped",   "text": "Mobile push reliability dashboard — deprioritized for incident follow-up.", "note": "Devon Park"},
            ]}],
        },
    ],
}

# ── 2. pr_review ──────────────────────────────────────────────────────────────
EXAMPLES["pr_review"] = {
    "title": "PR #247 — Review Summary",
    "header": {
        "eyebrow": "acme/app · feat/notification-engine → main",
        "title": "Add batched notification dispatcher",
        "pill": "In Review",
    },
    "sections": [
        {
            "layout": "grid", "cols": 4, "gap": 14,
            "items": [
                {"primitive": "stat_card", "number": "+312", "label": "Lines added", "delta": "5 files", "delta_direction": "flat"},
                {"primitive": "stat_card", "number": "−47",  "label": "Lines removed"},
                {"primitive": "stat_card", "number": 2, "label": "Blocking issues", "warning": True},
                {"primitive": "stat_card", "number": 3, "label": "Nit comments"},
            ],
        },
        {
            "header": "Summary", "layout": "stack",
            "items": [{"primitive": "prose", "text": "This PR moves notification delivery to a batched async dispatcher, reducing API latency on write paths. The queue is backed by Redis sorted sets with exponential backoff on failures."}],
        },
        {
            "header": "Files", "layout": "stack",
            "items": [
                {"primitive": "file_section", "path": "src/notifications/dispatcher.ts",
                 "additions": 180, "deletions": 0, "risk": "medium",
                 "hunks": [
                     {"type": "hunk", "code": "@@ -0,0 +1,12 @@"},
                     {"type": "add", "line": 1, "code": "import { Redis } from '../lib/redis';"},
                     {"type": "add", "line": 2, "code": "import { NotificationJob } from './types';"},
                     {"type": "add", "line": 3, "code": ""},
                     {"type": "add", "line": 4, "code": "export class NotificationDispatcher {"},
                     {"type": "add", "line": 5, "code": "  private queue: Redis;"},
                     {"type": "add", "line": 6, "code": "  constructor(private concurrency = 8) {}"},
                     {"type": "add", "line": 7, "code": "}"},
                 ],
                 "comments": [
                     {"severity": "blocking", "anchor": "line 6", "text": "Concurrency of 8 still risks saturating the shared Redis connection pool under load. Consider making this configurable per environment."},
                     {"severity": "nit", "anchor": "line 5", "text": "Type should be RedisClient, not Redis, to keep the abstraction boundary clean."},
                 ]},
                {"primitive": "file_section", "path": "src/notifications/sender.ts",
                 "additions": 12, "deletions": 47, "risk": "high",
                 "hunks": [
                     {"type": "hunk", "code": "@@ -23,8 +23,3 @@"},
                     {"type": "ctx", "line": 23, "code": "export async function send(n: Notification) {"},
                     {"type": "del", "line": 24, "code": "  await mailer.send(n.email, n.subject, n.body);"},
                     {"type": "del", "line": 25, "code": "  await sms.send(n.phone, n.body);"},
                     {"type": "add", "line": 24, "code": "  return dispatcher.enqueue(n);"},
                     {"type": "ctx", "line": 25, "code": "}"},
                 ],
                 "comments": [
                     {"severity": "blocking", "anchor": "line 24", "text": "No error handling if enqueue fails — the caller will silently swallow the error. Wrap in try/catch."},
                 ]},
            ],
        },
        {
            "header": "Next steps", "layout": "stack",
            "items": [{"primitive": "action_checklist", "items": [
                {"avatar": "DP", "description": "Add error handling to enqueue call in sender.ts"},
                {"avatar": "DP", "description": "Make concurrency configurable via env var"},
                {"avatar": "MO", "description": "Add integration test for queue backpressure"},
                {"avatar": "JT", "description": "Review Redis connection pool sizing in staging", "done": True},
            ]}],
        },
    ],
}

# ── 3. pr_writeup ─────────────────────────────────────────────────────────────
EXAMPLES["pr_writeup"] = {
    "title": "PR #312 — Move notification delivery onto a queue",
    "header": {
        "eyebrow": "acme/app · feat/notification-queue → main",
        "title": "Move notification delivery onto a queue",
        "pill": "Ready for Review",
    },
    "sections": [
        {
            "layout": "stack",
            "items": [{"primitive": "callout", "variant": "tinted", "label": "TL;DR",
                "content": "Replaces three synchronous mailer/SMS/push calls with a single async queue push. Delivery happens in background workers, cutting p95 on the write path by ~60ms."}],
        },
        {
            "header": "Before / After", "layout": "stack",
            "items": [{"primitive": "two_col_compare", "cols": [
                {"header": "Before", "items": [
                    {"primitive": "code_block", "language": "typescript", "code": "await mailer.send(n.email, n.subject, n.body);\nawait sms.send(n.phone, n.body);\nawait push.send(n.deviceToken, n.body);"},
                ]},
                {"header": "After", "items": [
                    {"primitive": "code_block", "language": "typescript", "code": "await deliveryQueue.push({ notification: n, enqueuedAt: Date.now() });"},
                ]},
            ]}],
        },
        {
            "header": "Files changed", "layout": "stack",
            "items": [{"primitive": "table", "columns": ["File", "Changes", "Risk"], "rows": [
                [{"type": "mono", "text": "src/notifications/delivery.ts"}, "+28 / −0",  {"type": "risk", "level": "med",  "label": "Med"}],
                [{"type": "mono", "text": "src/notifications/sender.ts"},   "+3 / −89",  {"type": "risk", "level": "high", "label": "High"}],
                [{"type": "mono", "text": "src/lib/queue.ts"},              "+216 / −0", {"type": "risk", "level": "low",  "label": "Low"}],
            ]}],
        },
        {
            "header": "Test plan", "layout": "stack",
            "items": [{"primitive": "action_checklist", "items": [
                {"avatar": "DP", "description": "Unit tests for queue retry / backoff logic", "done": True},
                {"avatar": "DP", "description": "Integration test: notification delivered after queue drain"},
                {"avatar": "QA", "description": "Load test: 1000 notifications/min sustained for 5 min"},
                {"avatar": "DP", "description": "Rollout: enable for 5% of workspaces via feature flag"},
            ]}],
        },
        {
            "header": "Rollout", "layout": "stack",
            "items": [{"primitive": "milestone_timeline", "milestones": [
                {"date": "Mar 20", "title": "Merge to main", "done": True},
                {"date": "Mar 21", "title": "Enable for 5% — monitor error rate + latency"},
                {"date": "Mar 24", "title": "Ramp to 50% if clean"},
                {"date": "Mar 27", "title": "Full rollout — remove flag"},
            ]}],
        },
    ],
}

# ── 4. incident_report ────────────────────────────────────────────────────────
EXAMPLES["incident_report"] = {
    "title": "INC-2025-0412 — Elevated 502s on task sync",
    "header": {
        "eyebrow": "SEV-2 · Resolved · Apr 12, 2025",
        "title": "INC-2025-0412 — Elevated 502s on task sync",
    },
    "sections": [
        {
            "layout": "grid", "cols": 4, "gap": 14,
            "items": [
                {"primitive": "stat_card", "number": "47m", "label": "Time to mitigate", "warning": True},
                {"primitive": "stat_card", "number": "2.1%", "label": "Error rate peak", "delta": "normal <0.1%", "delta_direction": "flat"},
                {"primitive": "stat_card", "number": "~340", "label": "Affected requests"},
                {"primitive": "stat_card", "number": "0",   "label": "Data loss"},
            ],
        },
        {
            "layout": "stack",
            "items": [{"primitive": "callout", "variant": "dark", "label": "TL;DR",
                "content": "A config change pushed a bad connection-pool limit (max: 2) to the sync worker fleet, causing 502s on all task-sync requests. Rolled back in 47 minutes. Root cause: staging CI does not validate worker config against production limits."}],
        },
        {
            "header": "Timeline", "layout": "stack",
            "items": [{"primitive": "event_timeline", "entries": [
                {"time": "14:02", "body": "Config change deployed to production (connection pool max → 2)", "state": "neutral"},
                {"time": "14:07", "body": "PagerDuty alert: api-sync p95 latency > 2s", "state": "impact"},
                {"time": "14:11", "body": "SEV-2 declared. Devon Park + Mira Okafor on call.", "state": "impact"},
                {"time": "14:19", "body": "Root cause identified: bad pool limit in worker config", "state": "neutral"},
                {"time": "14:23", "body": "Rollback initiated for config change", "state": "neutral"},
                {"time": "14:49", "body": "Error rate nominal. Incident mitigated.", "state": "mitigated"},
                {"time": "15:02", "body": "Postmortem scheduled for Apr 14.", "state": "neutral"},
            ]}],
        },
        {
            "header": "Root cause", "layout": "stack",
            "items": [
                {"primitive": "prose", "text": "The config template for sync workers uses a max_connections field that was inadvertently set to 2 in a parameterization PR. The CI check only validates config syntax, not value ranges."},
                {"primitive": "file_section", "path": "config/workers/sync.yaml",
                 "additions": 1, "deletions": 1, "risk": "high",
                 "hunks": [
                     {"type": "hunk", "code": "@@ -8,3 +8,3 @@"},
                     {"type": "ctx", "line": 8, "code": "pool:"},
                     {"type": "del", "line": 9, "code": "  max_connections: 40"},
                     {"type": "add", "line": 9, "code": "  max_connections: 2   # BUG: should be 40"},
                 ]},
            ],
        },
        {
            "header": "Action items", "layout": "stack",
            "items": [{"primitive": "action_checklist", "items": [
                {"avatar": "DP", "description": "Add CI check: validate worker config values against known safe ranges", "due": "Apr 18"},
                {"avatar": "MO", "description": "Add runbook: connection pool exhaustion symptoms + remediation", "due": "Apr 16"},
                {"avatar": "AK", "description": "Add alerting: pool utilization > 80% → PagerDuty", "due": "Apr 20"},
                {"avatar": "JT", "description": "Schedule game day: pool exhaustion scenario", "due": "May 1"},
                {"avatar": "DP", "description": "Update postmortem doc with final timeline", "done": True},
            ]}],
        },
    ],
}

# ── 5. impl_plan ──────────────────────────────────────────────────────────────
EXAMPLES["impl_plan"] = {
    "title": "Implementation Plan — Comment Threads on Task Cards",
    "header": {
        "eyebrow": "acme/app · Feature Design",
        "title": "Comment Threads on Task Cards",
        "description": "Spec for adding inline comment threads to task cards in board and list views.",
    },
    "sections": [
        {
            "layout": "grid", "cols": 4, "gap": 14,
            "items": [
                {"primitive": "stat_card", "number": 3, "label": "Slices"},
                {"primitive": "stat_card", "number": "~6w", "label": "Estimated scope"},
                {"primitive": "stat_card", "number": 2, "label": "Open questions", "warning": True},
                {"primitive": "stat_card", "number": 4, "label": "Reviewers"},
            ],
        },
        {
            "header": "Milestones", "layout": "stack",
            "items": [{"primitive": "milestone_timeline", "milestones": [
                {"date": "Week 1–2", "title": "Slice 1: Data model + API", "done": True,
                 "description": "Comment schema, REST endpoints, WebSocket events",
                 "tags": ["backend", "API"]},
                {"date": "Week 3–4", "title": "Slice 2: UI — task card thread",
                 "description": "Thread toggle, comment composer, reply threading",
                 "tags": ["frontend", "design"]},
                {"date": "Week 5", "title": "Slice 3: Notifications",
                 "description": "Email digest, in-app badge, @mention resolution",
                 "tags": ["backend", "notifications"]},
                {"date": "Week 6", "title": "Rollout + flag removal",
                 "description": "Ramp to 100%, remove feature flag, final QA",
                 "tags": ["infra"]},
            ]}],
        },
        {
            "header": "Risk table", "layout": "stack",
            "items": [{"primitive": "table", "columns": ["Risk", "Severity", "Mitigation"], "rows": [
                ["WebSocket state divergence under reconnect", {"type": "risk", "level": "high", "label": "High"}, "Idempotent event IDs + server-authoritative thread state"],
                ["@mention autocomplete latency", {"type": "risk", "level": "med",  "label": "Med"},  "Cache member index per workspace; invalidate on member change"],
                ["Mobile layout for deep threads", {"type": "risk", "level": "med",  "label": "Med"},  "Collapse threads >2 deep; expand on tap"],
                ["Notification volume spike at launch", {"type": "risk", "level": "low",  "label": "Low"},  "Digest mode enabled by default; per-user opt-out"],
            ]}],
        },
        {
            "header": "Open questions", "layout": "stack",
            "items": [
                {"primitive": "decision_card",
                 "question": "Should threads be visible on all views or only expanded cards?",
                 "context": "Showing inline on all cards adds visual noise. Showing only on expanded cards hides activity.",
                 "options": [{"label": "All views"}, {"label": "Expanded only", "suggested": True}, {"label": "Configurable per workspace"}]},
                {"primitive": "decision_card",
                 "question": "How do we handle @mentions across workspace guests?",
                 "context": "Guests have limited visibility. Mentioning a guest in a restricted task could leak context.",
                 "options": [{"label": "Block guest @mentions", "suggested": True}, {"label": "Warn + confirm"}, {"label": "Allow, no restriction"}]},
            ],
        },
        {
            "header": "Data flow", "layout": "stack",
            "items": [{"primitive": "flow_diagram",
                "direction": "LR",
                "node_width": 140,
                "node_height": 52,
                "h_gap": 36,
                "v_gap": 48,
                "nodes": [
                    {"id": "ui",  "label": "Task Card UI", "sublabel": "React",    "accent": "clay"},
                    {"id": "api", "label": "Comment API",  "sublabel": "Node.js"},
                    {"id": "pg",  "label": "PostgreSQL",   "sublabel": "persist"},
                    {"id": "ws",  "label": "WebSocket",    "sublabel": "broadcast", "accent": "olive"},
                    {"id": "notif", "label": "Notifier",   "sublabel": "async",     "accent": "gray"},
                ],
                "edges": [
                    {"from": "ui",  "to": "api",   "label": "POST"},
                    {"from": "api", "to": "pg",    "label": "write"},
                    {"from": "api", "to": "ws",    "label": "fan-out"},
                    {"from": "api", "to": "notif", "label": "queue", "style": "dashed"},
                ],
                "caption": "Left-to-right read path — dashed = async",
            }],
        },
        {
            "header": "Action items", "layout": "stack",
            "items": [{"primitive": "action_checklist", "items": [
                {"avatar": "PA", "description": "Finalize comment schema — decide on hard-delete vs soft-delete", "due": "Mar 20", "done": True},
                {"avatar": "MO", "description": "Design review: thread layout in list vs board view", "due": "Mar 22"},
                {"avatar": "DP", "description": "Spike: WebSocket reconnect strategy with idempotent events", "due": "Mar 25"},
                {"avatar": "JT", "description": "Confirm notification digest API contract with mobile team", "due": "Mar 27"},
            ]}],
        },
    ],
}

# ── 6. platform_status ────────────────────────────────────────────────────────
EXAMPLES["platform_status"] = {
    "title": "Platform Eng — Week of Mar 10",
    "wide": False,
    "header": {
        "eyebrow": "Platform Engineering",
        "title": "Week of Mar 10",
    },
    "sections": [
        {
            "header": "Shipped", "layout": "stack",
            "items": [{"primitive": "shipped_item_list", "items": [
                {"title": "Service mesh rollout complete", "description": "All 14 internal services now route through Envoy sidecar. mTLS enforced end-to-end.", "reference": "#4820", "color": "var(--olive)"},
                {"title": "Build cache hit rate 94%", "description": "Switched to remote Bazel cache with content-addressable storage. CI median time down 4m.", "reference": "#4831", "color": "var(--olive)"},
                {"title": "Secrets rotation automation", "description": "AWS Secrets Manager rotation now triggers automatic redeploy for affected services.", "reference": "#4839", "color": "var(--clay)"},
            ]}],
        },
        {
            "header": "In progress", "layout": "stack",
            "items": [{"primitive": "table", "columns": ["Initiative", "Owner", "Status", "ETA"], "rows": [
                ["K8s upgrade to 1.29", "Devon Park", {"type": "badge", "tone": "warning", "text": "In progress"}, "Mar 21"],
                ["OIDC SSO for internal tools", "Priya Anand", {"type": "badge", "tone": "warning", "text": "In progress"}, "Mar 28"],
                ["Log aggregation migration", "Jules Tan", {"type": "badge", "tone": "neutral", "text": "Blocked"}, "TBD"],
            ]}],
        },
        {
            "header": "Velocity (PRs merged)", "layout": "stack",
            "items": [{"primitive": "bar_chart", "y_max": 6,
                "bars": [
                    {"label": "Mon", "value": 3}, {"label": "Tue", "value": 5, "highlight": True},
                    {"label": "Wed", "value": 4}, {"label": "Thu", "value": 4},
                    {"label": "Fri", "value": 6, "highlight": True}, {"label": "Sat", "value": 1}, {"label": "Sun", "value": 0},
                ], "caption": "23 PRs total this week, up from 17 last week."
            }],
        },
        {
            "header": "Decision needed", "layout": "stack",
            "items": [{"primitive": "decision_card",
                "question": "Adopt Argo CD for GitOps or extend current Helm-based pipeline?",
                "context": "Argo CD gives us reconciliation loops and drift detection. Helm pipeline is simpler but requires manual sync verification. Decision needed before K8s 1.29 upgrade.",
                "options": [{"label": "Adopt Argo CD", "suggested": True}, {"label": "Extend Helm pipeline"}, {"label": "Defer 6 weeks"}]
            }],
        },
    ],
}

# ── 7. kanban_triage ─────────────────────────────────────────────────────────
EXAMPLES["kanban_triage"] = {
    "title": "Cycle 14 Triage",
    "wide": True,
    "header": {
        "eyebrow": "acme / editor / triage",
        "title": "Cycle 14 triage",
        "description": "Drag tickets between columns to adjust priority. Estimates: S = 1pt, M = 3pt, L = 5pt.",
    },
    "sections": [{
        "layout": "stack",
        "items": [{"primitive": "kanban_board", "columns": [
            {"title": "Now", "accent": "clay", "id": "now", "tickets": [
                {"id": "BIR-241", "title": "Fix sync conflict toast when two edits land within 100ms", "tag": "bug",  "estimate": "M", "owner_initials": "AK"},
                {"id": "BIR-247", "title": "Keyboard shortcut for bulk-assign owner", "tag": "feat", "estimate": "S", "owner_initials": "MO", "owner_class": "o2"},
                {"id": "BIR-253", "title": "Section collapse state not persisted on reload", "tag": "bug",  "estimate": "S", "owner_initials": "AK"},
            ]},
            {"title": "Next", "accent": "olive", "id": "next", "tickets": [
                {"id": "BIR-229", "title": "Export board view to CSV", "tag": "feat", "estimate": "M", "owner_initials": "SR", "owner_class": "o3"},
                {"id": "BIR-234", "title": "Due-date picker: support recurring dates", "tag": "feat", "estimate": "L", "owner_initials": "PA"},
                {"id": "BIR-238", "title": "Reduce attachment thumbnail load time", "tag": "chore", "estimate": "S", "owner_initials": "JT", "owner_class": "o4"},
            ]},
            {"title": "Later", "accent": "gray", "id": "later", "tickets": [
                {"id": "BIR-201", "title": "Gantt chart view for milestone tracking", "tag": "feat", "estimate": "L", "owner_initials": "MO", "owner_class": "o2"},
                {"id": "BIR-214", "title": "SSO group → workspace role sync", "tag": "feat", "estimate": "L", "owner_initials": "PA"},
            ]},
            {"title": "Cut", "accent": "light", "id": "cut", "tickets": [
                {"id": "BIR-188", "title": "Email digest: per-section unsubscribe", "tag": "feat", "estimate": "M"},
                {"id": "BIR-196", "title": "Legacy import from Asana XML", "tag": "chore", "estimate": "L"},
            ]},
        ]}],
    }],
}

# ── 8. design_system_ref ──────────────────────────────────────────────────────
EXAMPLES["design_system_ref"] = {
    "title": "Design System Reference",
    "header": {"eyebrow": "Acme Design System", "title": "Design System Reference",
                "description": "Color tokens, typography scale, spacing, and core components."},
    "sections": [
        {
            "header": "Color palette", "layout": "grid", "cols": 4,
            "items": [
                {"primitive": "card", "variant": "outlined", "content": "<div style='width:100%;height:48px;border-radius:8px;background:var(--ivory);margin-bottom:8px'></div><div style='font-family:var(--mono);font-size:12px'>--ivory<br><span style='color:var(--gray-500)'>#FAF9F5</span></div>"},
                {"primitive": "card", "variant": "outlined", "content": "<div style='width:100%;height:48px;border-radius:8px;background:var(--slate);margin-bottom:8px'></div><div style='font-family:var(--mono);font-size:12px'>--slate<br><span style='color:var(--gray-500)'>#141413</span></div>"},
                {"primitive": "card", "variant": "outlined", "content": "<div style='width:100%;height:48px;border-radius:8px;background:var(--clay);margin-bottom:8px'></div><div style='font-family:var(--mono);font-size:12px'>--clay<br><span style='color:var(--gray-500)'>#D97757</span></div>"},
                {"primitive": "card", "variant": "outlined", "content": "<div style='width:100%;height:48px;border-radius:8px;background:var(--oat);margin-bottom:8px'></div><div style='font-family:var(--mono);font-size:12px'>--oat<br><span style='color:var(--gray-500)'>#E3DACC</span></div>"},
                {"primitive": "card", "variant": "outlined", "content": "<div style='width:100%;height:48px;border-radius:8px;background:var(--olive);margin-bottom:8px'></div><div style='font-family:var(--mono);font-size:12px'>--olive<br><span style='color:var(--gray-500)'>#788C5D</span></div>"},
                {"primitive": "card", "variant": "outlined", "content": "<div style='width:100%;height:48px;border-radius:8px;background:var(--rust);margin-bottom:8px'></div><div style='font-family:var(--mono);font-size:12px'>--rust<br><span style='color:var(--gray-500)'>#B04A3F</span></div>"},
                {"primitive": "card", "variant": "outlined", "content": "<div style='width:100%;height:48px;border-radius:8px;background:var(--gray-300);margin-bottom:8px'></div><div style='font-family:var(--mono);font-size:12px'>--gray-300<br><span style='color:var(--gray-500)'>#D1CFC5</span></div>"},
                {"primitive": "card", "variant": "outlined", "content": "<div style='width:100%;height:48px;border-radius:8px;background:var(--gray-500);margin-bottom:8px'></div><div style='font-family:var(--mono);font-size:12px'>--gray-500<br><span style='color:var(--gray-500)'>#87867F</span></div>"},
            ],
        },
        {
            "header": "Typography", "layout": "stack",
            "items": [{"primitive": "card", "variant": "outlined", "content":
                "<div style='display:flex;flex-direction:column;gap:16px'>"
                "<div><div style='font-family:var(--serif);font-size:36px;font-weight:500'>Display / H1 — Serif 36px</div></div>"
                "<div><div style='font-family:var(--serif);font-size:24px;font-weight:500'>H2 — Serif 24px</div></div>"
                "<div><div style='font-family:var(--sans);font-size:16px'>Body — Sans 16px · Regular weight · 1.6 line height</div></div>"
                "<div><div style='font-family:var(--mono);font-size:12px;text-transform:uppercase;letter-spacing:0.08em;color:var(--gray-500)'>Eyebrow · Mono 12px Uppercase</div></div>"
                "<div><div style='font-family:var(--mono);font-size:13px;color:var(--gray-700)'>Code · Mono 13px</div></div>"
                "</div>"
            }],
        },
        {
            "header": "Badges", "layout": "stack",
            "items": [{"primitive": "card", "variant": "outlined", "content":
                "<div style='display:flex;gap:8px;flex-wrap:wrap'>"
                "<span class='badge badge-neutral'>neutral</span>"
                "<span class='badge badge-accent'>accent</span>"
                "<span class='badge badge-success'>success</span>"
                "<span class='badge badge-warning'>warning</span>"
                "<span class='badge badge-danger'>danger</span>"
                "<span class='badge badge-outlined'>outlined</span>"
                "</div>"
            }],
        },
        {
            "header": "Buttons", "layout": "stack",
            "items": [{"primitive": "card", "variant": "outlined", "content":
                "<div style='display:flex;gap:10px;flex-wrap:wrap'>"
                "<button class='btn btn-primary'>Primary</button>"
                "<button class='btn btn-secondary'>Secondary</button>"
                "<button class='btn btn-ghost'>Ghost</button>"
                "<button class='btn btn-danger'>Danger</button>"
                "</div>"
            }],
        },
        {
            "header": "Card variants", "layout": "grid", "cols": 3,
            "items": [
                {"primitive": "card", "variant": "flat",       "title": "Flat",       "subtitle": "No border, no shadow", "tags": ["flat"]},
                {"primitive": "card", "variant": "outlined",   "title": "Outlined",   "subtitle": "Border, no shadow",   "tags": ["outlined"]},
                {"primitive": "card", "variant": "elevated",   "title": "Elevated",   "subtitle": "Shadow, no border",   "tags": ["elevated"]},
                {"primitive": "card", "variant": "stripe",     "title": "Stripe",     "subtitle": "Border + accent top", "tags": ["stripe"]},
                {"primitive": "card", "variant": "inset",      "title": "Inset",      "subtitle": "Tinted background",   "tags": ["inset"]},
                {"primitive": "card", "variant": "horizontal", "title": "Horizontal", "subtitle": "Row layout",          "tags": ["horizontal"]},
            ],
        },
    ],
}

# ── 9. card_matrix ────────────────────────────────────────────────────────────
EXAMPLES["card_matrix"] = {
    "title": "Card Variant Matrix",
    "header": {"eyebrow": "Component explorer", "title": "Card variant matrix",
                "description": "Six structural treatments of the Card component."},
    "sections": [
        {
            "layout": "grid", "cols": 3, "gap": 28,
            "items": [
                {"primitive": "v_stack", "gap": 8, "items": [
                    {"primitive": "badge", "text": "A · Flat", "tone": "neutral"},
                    {"primitive": "card", "variant": "flat", "title": "Weekly planning", "subtitle": "12 tasks · due Friday", "initials": "WP", "tags": ["Q2", "Roadmap"], "actions": [{"text": "Open", "variant": "ghost"}]},
                ]},
                {"primitive": "v_stack", "gap": 8, "items": [
                    {"primitive": "badge", "text": "B · Outlined", "tone": "neutral"},
                    {"primitive": "card", "variant": "outlined", "title": "Weekly planning", "subtitle": "12 tasks · due Friday", "initials": "WP", "tags": ["Q2", "Roadmap"], "actions": [{"text": "Open", "variant": "ghost"}]},
                ]},
                {"primitive": "v_stack", "gap": 8, "items": [
                    {"primitive": "badge", "text": "C · Elevated", "tone": "neutral"},
                    {"primitive": "card", "variant": "elevated", "title": "Weekly planning", "subtitle": "12 tasks · due Friday", "initials": "WP", "tags": ["Q2", "Roadmap"], "actions": [{"text": "Open", "variant": "ghost"}]},
                ]},
                {"primitive": "v_stack", "gap": 8, "items": [
                    {"primitive": "badge", "text": "D · Stripe", "tone": "neutral"},
                    {"primitive": "card", "variant": "stripe", "title": "Weekly planning", "subtitle": "12 tasks · due Friday", "initials": "WP", "tags": ["Q2", "Roadmap"], "actions": [{"text": "Open", "variant": "ghost"}]},
                ]},
                {"primitive": "v_stack", "gap": 8, "items": [
                    {"primitive": "badge", "text": "E · Inset", "tone": "neutral"},
                    {"primitive": "card", "variant": "inset", "title": "Weekly planning", "subtitle": "12 tasks · due Friday", "initials": "WP", "tags": ["Q2", "Roadmap"], "actions": [{"text": "Open", "variant": "ghost"}]},
                ]},
                {"primitive": "v_stack", "gap": 8, "items": [
                    {"primitive": "badge", "text": "F · Horizontal", "tone": "neutral"},
                    {"primitive": "card", "variant": "horizontal", "title": "Weekly planning", "subtitle": "12 tasks · due Friday", "initials": "WP", "tags": ["Q2"], "actions": [{"text": "Open", "variant": "ghost"}]},
                ]},
            ],
        },
    ],
}

# ── 10. deploy_pipeline ───────────────────────────────────────────────────────
EXAMPLES["deploy_pipeline"] = {
    "title": "Deploy Pipeline — Annotated Flowchart",
    "header": {"eyebrow": "acme/app · CI/CD", "title": "Deploy pipeline",
                "description": "End-to-end flow from pull request to production. Click any stage for details."},
    "sections": [
        {
            "layout": "stack",
            "items": [{"primitive": "callout", "variant": "tinted", "label": "How to read this",
                "content": "Each stage must pass before the next begins. Gates (◆) are manual approval steps. Click a node to see what runs there."}],
        },
        {
            "layout": "stack",
            "items": [{"html":
                "<div style='display:flex;flex-direction:column;gap:0;align-items:center'>"
                + "".join([
                    f"<div style='background:var(--white);border:var(--border);border-radius:10px;padding:14px 28px;min-width:280px;text-align:center;margin:0'>"
                    f"<div style='font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--gray-500);margin-bottom:4px'>{stage[1]}</div>"
                    f"<div style='font-family:var(--serif);font-size:16px;font-weight:500'>{stage[0]}</div>"
                    f"</div>"
                    + (f"<div style='width:2px;height:24px;background:var(--gray-300)'></div>" if i < 5 else "")
                    for i, stage in enumerate([
                        ("PR Created", "trigger"),
                        ("CI — lint + typecheck + tests", "automated"),
                        ("Security scan + SAST", "automated"),
                        ("Preview deploy (Vercel)", "automated"),
                        ("Manual approval", "gate ◆"),
                        ("Production deploy", "automated"),
                    ])
                ])
                + "</div>"
            }],
        },
        {
            "header": "Stage details", "layout": "stack",
            "items": [{"primitive": "step_list", "steps": [
                {"title": "CI — lint + typecheck + tests", "body": "Runs ESLint, TypeScript compiler, and Jest test suite. Must pass with 0 failures.", "code": "npm run lint && tsc --noEmit && jest --ci"},
                {"title": "Security scan", "body": "Semgrep SAST scan + npm audit for known CVEs. Blocks on HIGH or CRITICAL findings."},
                {"title": "Preview deploy", "body": "Vercel preview deployment created automatically. Link posted to PR as a check."},
                {"title": "Manual approval", "body": "At least one senior engineer must approve the PR. Bot checks for review + green CI before allowing merge."},
                {"title": "Production deploy", "body": "Triggered on merge to main. Zero-downtime rolling deploy via Kubernetes. Smoke test runs against prod for 5 minutes post-deploy."},
            ]}],
        },
    ],
}

# ── 11. consistent_hashing ────────────────────────────────────────────────────
EXAMPLES["consistent_hashing"] = {
    "title": "Consistent Hashing — An Interactive Explainer",
    "header": {"eyebrow": "Distributed Systems", "title": "Consistent hashing",
                "description": "How data is distributed across nodes without full reshuffling when topology changes."},
    "sections": [
        {
            "layout": "stack",
            "items": [{"primitive": "prose",
                "text": "In a naive hash ring, adding or removing a node requires remapping most keys. Consistent hashing limits remapping to K/N keys on average (K = keys, N = nodes), making it ideal for distributed caches and databases."}],
        },
        {
            "layout": "sidebar",
            "main": [{"html":
                # 5-node ring SVG — precomputed positions (cos/sin of 2π*i/5)
                # Angles: 0°=right, 72°, 144°, 216°, 288° → cx/cy rounded to int
                "<div style='background:var(--white);border:var(--border);border-radius:12px;padding:24px;text-align:center'>"
                "<svg viewBox='0 0 320 320' style='width:100%;max-width:320px'>"
                "<circle cx='160' cy='160' r='120' fill='none' stroke='var(--gray-300)' stroke-width='2'/>"
                "<circle cx='280' cy='160' r='14' fill='var(--clay)' stroke='var(--white)' stroke-width='2'/>"
                "<text x='305' y='164' text-anchor='middle' font-family='system-ui' font-size='11' fill='var(--gray-700)'>N1</text>"
                "<circle cx='197' cy='46' r='14' fill='var(--clay)' stroke='var(--white)' stroke-width='2'/>"
                "<text x='212' y='22' text-anchor='middle' font-family='system-ui' font-size='11' fill='var(--gray-700)'>N2</text>"
                "<circle cx='90' cy='87' r='14' fill='var(--clay)' stroke='var(--white)' stroke-width='2'/>"
                "<text x='70' y='68' text-anchor='middle' font-family='system-ui' font-size='11' fill='var(--gray-700)'>N3</text>"
                "<circle cx='90' cy='233' r='14' fill='var(--clay)' stroke='var(--white)' stroke-width='2'/>"
                "<text x='70' y='257' text-anchor='middle' font-family='system-ui' font-size='11' fill='var(--gray-700)'>N4</text>"
                "<circle cx='197' cy='274' r='14' fill='var(--clay)' stroke='var(--white)' stroke-width='2'/>"
                "<text x='212' y='298' text-anchor='middle' font-family='system-ui' font-size='11' fill='var(--gray-700)'>N5</text>"
                "</svg>"
                "<p style='font-size:12px;color:var(--gray-500);margin-top:8px'>5-node ring — keys route to the next clockwise node</p>"
                "</div>"
            }],
            "sidebar": [{"primitive": "v_stack", "gap": 16, "items": [
                {"primitive": "stat_card", "number": "1/N", "label": "Keys remapped on node add"},
                {"primitive": "stat_card", "number": "1/N", "label": "Keys remapped on node remove"},
                {"primitive": "prose", "items": ["Virtual nodes (vnodes) improve load balance by placing each server at multiple ring positions.", "Replication: replicate to the next R clockwise neighbors.", "Used in: Cassandra, DynamoDB, Chord DHT."]},
            ]}],
        },
        {
            "header": "Comparison", "layout": "stack",
            "items": [{"primitive": "table", "columns": ["Strategy", "Keys remapped on change", "Load balance", "Use case"], "rows": [
                ["Naive modulo hash", "~100%", "Even", "Single-server caches"],
                ["Consistent hashing", "~1/N", "Uneven without vnodes", "Distributed caches"],
                ["Consistent + vnodes", "~1/N", "Very even", "Production databases"],
            ]}],
        },
    ],
}

# ── 12. rate_limiting ─────────────────────────────────────────────────────────
EXAMPLES["rate_limiting"] = {
    "title": "How rate limiting works in acme_api",
    "header": {"eyebrow": "acme_api · Documentation", "title": "How rate limiting works",
                "description": "Token-bucket algorithm applied per API key. Limits reset on a rolling 60-second window."},
    "sections": [
        {
            "layout": "stack",
            "items": [{"primitive": "callout", "variant": "tinted", "label": "Quick summary",
                "content": "Each API key gets a bucket of tokens. Every request costs 1 token. Tokens refill at a fixed rate. When the bucket is empty, requests return 429 Too Many Requests."}],
        },
        {
            "header": "How it works", "layout": "stack",
            "items": [{"primitive": "step_list", "steps": [
                {"title": "Request arrives", "body": "API gateway extracts the API key from the Authorization header."},
                {"title": "Bucket lookup", "body": "Redis lookup for the key's current token count and last refill timestamp.", "code": "GET ratelimit:{api_key}"},
                {"title": "Refill tokens", "body": "Tokens added since last request: elapsed_seconds × rate. Capped at burst_limit."},
                {"title": "Consume token", "body": "If count ≥ 1: decrement, allow request. If count < 1: return 429 with Retry-After header."},
                {"title": "Write back", "body": "Atomic SETEX writes updated count + timestamp with TTL = window_size.", "code": "SETEX ratelimit:{api_key} 60 {new_count}:{timestamp}"},
            ]}],
        },
        {
            "header": "Configuration", "layout": "stack",
            "items": [{"primitive": "code_block", "tabs": [
                {"label": "YAML", "code": "rate_limiting:\n  default_rate: 100        # tokens/minute\n  burst_limit: 150         # max bucket size\n  window_seconds: 60\n  storage: redis\n  key_prefix: ratelimit", "active": True},
                {"label": "Per-route", "code": "routes:\n  /v2/sync:\n    rate: 20\n    burst: 30\n  /v1/export:\n    rate: 5\n    burst: 5"},
            ]}],
        },
        {
            "header": "Response headers", "layout": "stack",
            "items": [{"primitive": "table", "columns": ["Header", "Value", "Meaning"], "rows": [
                [{"type": "mono", "text": "X-RateLimit-Limit"},     "100",   "Tokens per window"],
                [{"type": "mono", "text": "X-RateLimit-Remaining"}, "42",    "Tokens left in current window"],
                [{"type": "mono", "text": "X-RateLimit-Reset"},     "1712345678", "Unix timestamp when bucket refills"],
                [{"type": "mono", "text": "Retry-After"},           "14",    "Seconds to wait (429 responses only)"],
            ]}],
        },
        {
            "layout": "stack",
            "items": [{"primitive": "callout", "variant": "tinted", "label": "Gotchas",
                "content": "Clock skew between API gateway instances can cause brief over-allowance. Use Redis Lua scripts for atomic check-and-decrement to prevent race conditions under high concurrency."}],
        },
    ],
}

# ── 13. auth_flow ─────────────────────────────────────────────────────────────
EXAMPLES["auth_flow"] = {
    "title": "How authentication flows through acme_web",
    "header": {"eyebrow": "acme_web · Architecture", "title": "Authentication flow",
                "description": "From login form submission to session cookie — what happens at each layer."},
    "sections": [
        {
            "layout": "stack",
            "items": [{"html":
                "<div style='background:var(--white);border:var(--border);border-radius:12px;padding:24px;overflow-x:auto'>"
                "<div style='display:flex;align-items:center;gap:0;min-width:600px'>"
                + "".join([
                    f"<div style='background:var(--{"oat" if i%2==0 else "gray-100"});border:var(--border);border-radius:8px;padding:12px 16px;text-align:center;flex:1'>"
                    f"<div style='font-family:var(--mono);font-size:10px;color:var(--gray-500);margin-bottom:4px'>{actor[1]}</div>"
                    f"<div style='font-size:13px;font-weight:500'>{actor[0]}</div></div>"
                    + (f"<div style='font-size:18px;color:var(--gray-300);padding:0 8px'>→</div>" if i < 3 else "")
                    for i, actor in enumerate([("Browser", "client"), ("Next.js Edge", "middleware"), ("Auth Service", "backend"), ("Redis", "session store")])
                ])
                + "</div></div>"
            }],
        },
        {
            "header": "Step-by-step", "layout": "stack",
            "items": [{"primitive": "step_list", "steps": [
                {"title": "User submits login form", "body": "Browser POSTs credentials to /api/auth/login.", "code": "POST /api/auth/login\nContent-Type: application/json\n{\"email\": \"...\", \"password\": \"...\"}"},
                {"title": "Edge middleware validates CSRF token", "body": "Next.js middleware checks the X-CSRF-Token header against the session cookie before forwarding."},
                {"title": "Auth service verifies credentials", "body": "Bcrypt comparison against stored hash. Returns JWT on success.", "code": "jwt.sign({ sub: user.id, role: user.role }, SECRET, { expiresIn: '15m' })"},
                {"title": "Session created in Redis", "body": "Refresh token stored in Redis with 7-day TTL. Short-lived JWT returned to client.", "code": "SET session:{userId} {refreshToken} EX 604800"},
                {"title": "Cookie set on response", "body": "HttpOnly + Secure + SameSite=Strict cookie set. No token exposed to JavaScript.", "code": "Set-Cookie: session=...; HttpOnly; Secure; SameSite=Strict"},
            ]}],
        },
        {
            "header": "Key files", "layout": "stack",
            "items": [{"primitive": "table", "columns": ["File", "Purpose"], "rows": [
                [{"type": "mono", "text": "middleware.ts"},                    "CSRF check + auth redirect for protected routes"],
                [{"type": "mono", "text": "app/api/auth/login/route.ts"},     "Credential validation + JWT issuance"],
                [{"type": "mono", "text": "lib/auth/session.ts"},             "Redis session CRUD"],
                [{"type": "mono", "text": "lib/auth/jwt.ts"},                 "JWT sign/verify helpers"],
                [{"type": "mono", "text": "app/api/auth/refresh/route.ts"},   "Refresh token rotation endpoint"],
            ]}],
        },
    ],
}

# ── 14. support_tuner ─────────────────────────────────────────────────────────
EXAMPLES["support_tuner"] = {
    "title": "Support Reply Prompt Tuner",
    "header": {"eyebrow": "Internal tools", "title": "Support reply prompt tuner",
                "description": "Edit the system prompt template and preview it rendered against live sample tickets."},
    "sections": [
        {
            "layout": "stack",
            "items": [{"html": """
<style>
.tuner-wrap { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
@media (max-width: 720px) { .tuner-wrap { grid-template-columns: 1fr; } }
.tuner-editor { background: var(--white); border: var(--border); border-radius: 12px; overflow: hidden; }
.tuner-head { padding: 12px 16px; background: var(--gray-100); border-bottom: 1px solid var(--gray-300); font-family: var(--mono); font-size: 11px; color: var(--gray-500); display: flex; justify-content: space-between; }
.tuner-body { padding: 16px; min-height: 200px; font-family: var(--mono); font-size: 13px; line-height: 1.7; color: var(--gray-700); outline: none; white-space: pre-wrap; }
.slot { background: rgba(217,119,87,.15); color: var(--clay); border-radius: 3px; padding: 0 2px; font-weight: 600; }
.preview-card { background: var(--white); border: var(--border); border-radius: 10px; padding: 14px; margin-bottom: 10px; font-size: 13px; line-height: 1.7; color: var(--gray-700); }
.preview-label { font-family: var(--mono); font-size: 10px; text-transform: uppercase; letter-spacing: .06em; color: var(--gray-500); margin-bottom: 6px; }
</style>
<div class="tuner-wrap">
  <div class="tuner-editor">
    <div class="tuner-head"><span>Template</span><span id="char-count">0 chars</span></div>
    <div class="tuner-body" id="editor" contenteditable="true" spellcheck="false">You are a support agent for Acme.

A customer named {{customer_name}} on the {{plan_tier}} plan has opened a ticket:

Subject: {{ticket_subject}}
Body: {{ticket_body}}

Reply in a {{tone}} tone. Be concise and helpful.</div>
  </div>
  <div>
    <div class="preview-label">Live preview</div>
    <div id="previews"></div>
  </div>
</div>
<script>
var SAMPLES = [
  {label:'Free user',   data:{customer_name:'Priya N.',  plan_tier:'Free',  ticket_subject:'Can\'t export CSV',   ticket_body:'I need to export my tasks but the button is greyed out.', tone:'friendly'}},
  {label:'Team user',   data:{customer_name:'Marcus D.', plan_tier:'Team',  ticket_subject:'SSO not working',     ticket_body:'Our SAML SSO stopped working after the update.', tone:'technical'}},
  {label:'Pro user',    data:{customer_name:'Elena S.',  plan_tier:'Pro',   ticket_subject:'API rate limit help', ticket_body:'We keep hitting 429s on the sync endpoint.', tone:'professional'}},
];
var editor=document.getElementById('editor');
var previews=document.getElementById('previews');
var charCount=document.getElementById('char-count');
function getText(){return editor.innerText||'';}
function fill(tmpl,data){return tmpl.replace(/\\{\\{([^}]+)\\}\\}/g,function(_,k){return data[k.trim()]||'{{'+k.trim()+'}}'});}
function render(){
  var tmpl=getText();
  charCount.textContent=tmpl.length+' chars';
  previews.innerHTML=SAMPLES.map(function(s){
    return '<div class="preview-card"><div class="preview-label">'+s.label+'</div>'+fill(tmpl,s.data).replace(/\\n/g,'<br>')+'</div>';
  }).join('');
}
editor.addEventListener('input',render);
render();
</script>
"""}],
        },
    ],
}

# ── 15. debounced_search ──────────────────────────────────────────────────────
EXAMPLES["debounced_search"] = {
    "title": "Debounced Search — Three Approaches",
    "header": {"eyebrow": "Frontend patterns", "title": "Debounced search — three approaches",
                "description": "Comparing setTimeout reset, leading-edge, and requestAnimationFrame strategies."},
    "sections": [
        {
            "layout": "grid", "cols": 3, "gap": 24,
            "items": [
                {"primitive": "v_stack", "gap": 12, "items": [
                    {"primitive": "card", "variant": "outlined", "content": "<div style='font-family:var(--serif);font-size:16px;font-weight:500;margin-bottom:6px'>setTimeout reset</div><p style='font-size:13px;color:var(--gray-700)'>Cancel and restart a timer on every keystroke. Fires once, 300ms after the user stops typing.</p>"},
                    {"primitive": "code_block", "language": "js", "code": "let timer;\nfunction onInput(e) {\n  clearTimeout(timer);\n  timer = setTimeout(() => {\n    search(e.target.value);\n  }, 300);\n}"},
                    {"primitive": "inset_panel", "items": [
                        {"tag": "Pro", "text": "Simple to understand and implement"},
                        {"tag": "Con", "text": "No feedback during typing — feels unresponsive"},
                    ]},
                ]},
                {"primitive": "v_stack", "gap": 12, "items": [
                    {"primitive": "card", "variant": "stripe", "content": "<div style='font-family:var(--serif);font-size:16px;font-weight:500;margin-bottom:6px'>Leading edge ✦ recommended</div><p style='font-size:13px;color:var(--gray-700)'>Fire immediately on first keystroke, then ignore subsequent calls for 300ms.</p>"},
                    {"primitive": "code_block", "language": "js", "code": "let lastFire = 0;\nfunction onInput(e) {\n  const now = Date.now();\n  if (now - lastFire > 300) {\n    lastFire = now;\n    search(e.target.value);\n  }\n}"},
                    {"primitive": "inset_panel", "items": [
                        {"tag": "Pro", "text": "Instant feedback on first character"},
                        {"tag": "Con", "text": "May miss the final value if user types fast"},
                    ]},
                ]},
                {"primitive": "v_stack", "gap": 12, "items": [
                    {"primitive": "card", "variant": "outlined", "content": "<div style='font-family:var(--serif);font-size:16px;font-weight:500;margin-bottom:6px'>rAF throttle</div><p style='font-size:13px;color:var(--gray-700)'>Schedule search via requestAnimationFrame — fires at most once per frame (~16ms).</p>"},
                    {"primitive": "code_block", "language": "js", "code": "let rafId;\nfunction onInput(e) {\n  cancelAnimationFrame(rafId);\n  rafId = requestAnimationFrame(() => {\n    search(e.target.value);\n  });\n}"},
                    {"primitive": "inset_panel", "items": [
                        {"tag": "Pro", "text": "Synced to display refresh — no visual lag"},
                        {"tag": "Con", "text": "Too fast for network calls — combine with setTimeout"},
                    ]},
                ]},
            ],
        },
        {
            "layout": "stack",
            "items": [{"primitive": "callout", "variant": "tinted", "label": "Recommendation",
                "content": "Use leading-edge debounce for search inputs. Pair with an abort controller to cancel in-flight requests when a new one starts."}],
        },
    ],
}

# ── 16. sidebar_reorder ───────────────────────────────────────────────────────
EXAMPLES["sidebar_reorder"] = {
    "title": "Sidebar Drag-to-Reorder",
    "header": {"eyebrow": "UI prototype", "title": "Sidebar drag-to-reorder",
                "description": "Drag sidebar sections to reorder them. Changes save automatically."},
    "sections": [
        {
            "layout": "sidebar",
            "main": [{"primitive": "v_stack", "gap": 24, "items": [
                {"primitive": "drag_list", "title": "Sidebar sections", "items": [
                    {"label": "Inbox",      "count": 14},
                    {"label": "My tasks",   "count": 6},
                    {"label": "Projects",   "count": 3},
                    {"label": "Goals",      "count": 2},
                    {"label": "Portfolios", "count": 1},
                    {"label": "Reporting"},
                    {"label": "Team",       "count": 5},
                    {"label": "Archive"},
                ]},
            ]}],
            "sidebar": [{"primitive": "v_stack", "gap": 16, "items": [
                {"primitive": "callout", "variant": "tinted", "label": "How to use",
                    "content": "Grab the ⠿ grip handle and drag any section to a new position. The order persists to your user preferences."},
                {"primitive": "prose", "items": [
                    "Drag handle activates on hover",
                    "Drop indicator shows target position",
                    "Keyboard: Tab to focus, Space to grab, arrow keys to move",
                ]},
            ]}],
        },
    ],
}

# ── 17. task_animation ────────────────────────────────────────────────────────
EXAMPLES["task_animation"] = {
    "title": "Task Completed Micro-interaction",
    "header": {"eyebrow": "Motion design", "title": "Task completed micro-interaction",
                "description": "Click a task to complete it and see three easing approaches."},
    "sections": [
        {
            "layout": "grid", "cols": 3, "gap": 24,
            "items": [
                {"primitive": "v_stack", "gap": 8, "items": [
                    {"primitive": "badge", "text": "Spring", "tone": "accent"},
                    {"html": "<div style='background:var(--white);border:var(--border);border-radius:12px;padding:20px;cursor:pointer' onclick='this.classList.toggle(\"done\")'><div style='display:flex;align-items:center;gap:10px'><div style='width:20px;height:20px;border-radius:50%;border:2px solid var(--gray-300);display:flex;align-items:center;justify-content:center;transition:all .4s cubic-bezier(.175,.885,.32,1.275);flex-shrink:0' class='circle'><svg width='10' height='10' style='opacity:0;transition:opacity .2s .15s'><path d='M1.5 5L4 7.5 8.5 2' stroke='white' stroke-width='1.8' fill='none' stroke-linecap='round'/></svg></div><span style='font-size:14px;transition:all .3s;color:var(--slate)'>Complete quarterly review</span></div></div><style>.done .circle{background:var(--clay);border-color:var(--clay)}.done .circle svg{opacity:1}.done span{text-decoration:line-through;color:var(--gray-500)}</style>"},
                ]},
                {"primitive": "v_stack", "gap": 8, "items": [
                    {"primitive": "badge", "text": "Ease-out", "tone": "neutral"},
                    {"html": "<div style='background:var(--white);border:var(--border);border-radius:12px;padding:20px;cursor:pointer' onclick='this.classList.toggle(\"done2\")'><div style='display:flex;align-items:center;gap:10px'><div style='width:20px;height:20px;border-radius:50%;border:2px solid var(--gray-300);display:flex;align-items:center;justify-content:center;transition:all .35s ease-out;flex-shrink:0' class='circle2'><svg width='10' height='10' style='opacity:0;transition:opacity .2s .1s'><path d='M1.5 5L4 7.5 8.5 2' stroke='white' stroke-width='1.8' fill='none' stroke-linecap='round'/></svg></div><span style='font-size:14px;transition:all .25s ease-out;color:var(--slate)'>Complete quarterly review</span></div></div><style>.done2 .circle2{background:var(--olive);border-color:var(--olive)}.done2 .circle2 svg{opacity:1}.done2 span{text-decoration:line-through;color:var(--gray-500)}</style>"},
                ]},
                {"primitive": "v_stack", "gap": 8, "items": [
                    {"primitive": "badge", "text": "Linear", "tone": "neutral"},
                    {"html": "<div style='background:var(--white);border:var(--border);border-radius:12px;padding:20px;cursor:pointer' onclick='this.classList.toggle(\"done3\")'><div style='display:flex;align-items:center;gap:10px'><div style='width:20px;height:20px;border-radius:50%;border:2px solid var(--gray-300);display:flex;align-items:center;justify-content:center;transition:all .3s linear;flex-shrink:0' class='circle3'><svg width='10' height='10' style='opacity:0;transition:opacity .15s linear'><path d='M1.5 5L4 7.5 8.5 2' stroke='white' stroke-width='1.8' fill='none' stroke-linecap='round'/></svg></div><span style='font-size:14px;transition:all .3s linear;color:var(--slate)'>Complete quarterly review</span></div></div><style>.done3 .circle3{background:var(--slate);border-color:var(--slate)}.done3 .circle3 svg{opacity:1}.done3 span{text-decoration:line-through;color:var(--gray-500)}</style>"},
                ]},
            ],
        },
        {
            "layout": "stack",
            "items": [{"primitive": "callout", "variant": "tinted", "label": "Easing guide",
                "content": "Spring (cubic-bezier .175/.885/.32/1.275) has a satisfying overshoot. Ease-out feels natural for completion states. Linear feels mechanical — avoid for emotional interactions."}],
        },
    ],
}

# ── 18. feature_flags ─────────────────────────────────────────────────────────
EXAMPLES["feature_flags"] = {
    "title": "Feature Flags — flags.production.json",
    "header": {"eyebrow": "acme/app · Production config", "title": "flags.production.json",
                "description": "Active feature flags. Changes here deploy within 30 seconds via config push."},
    "sections": [
        {
            "layout": "stack",
            "items": [{"primitive": "callout", "variant": "tinted", "label": "Warning",
                "content": "Editing flags directly affects production. Prefer the admin UI for gradual rollouts. This view is read-only — use the CLI to make changes."}],
        },
        {
            "header": "Active flags", "layout": "stack",
            "items": [{"primitive": "table", "columns": ["Flag", "Value", "Rollout", "Owner", "Since"], "rows": [
                [{"type": "mono", "text": "bulk_edit_toolbar"}, {"type": "badge", "tone": "success", "text": "enabled"}, "100%", "Mira Okafor", "Mar 14"],
                [{"type": "mono", "text": "notification_queue"}, {"type": "badge", "tone": "warning", "text": "partial"}, "25%",  "Devon Park",  "Mar 20"],
                [{"type": "mono", "text": "new_billing_ui"},    {"type": "badge", "tone": "warning", "text": "partial"}, "5%",   "Noor Halabi", "Mar 22"],
                [{"type": "mono", "text": "csv_export_v2"},     {"type": "badge", "tone": "success", "text": "enabled"}, "100%", "Sam Reyes",   "Feb 28"],
                [{"type": "mono", "text": "sso_group_sync"},    {"type": "badge", "tone": "neutral", "text": "disabled"}, "0%",  "Priya Anand", "—"],
            ]}],
        },
        {
            "header": "Config", "layout": "stack",
            "items": [{"primitive": "code_block", "filename": "flags.production.json", "code":
                '{\n  "bulk_edit_toolbar": { "enabled": true, "rollout": 1.0 },\n'
                '  "notification_queue": { "enabled": true, "rollout": 0.25 },\n'
                '  "new_billing_ui":    { "enabled": true, "rollout": 0.05 },\n'
                '  "csv_export_v2":     { "enabled": true, "rollout": 1.0 },\n'
                '  "sso_group_sync":    { "enabled": false, "rollout": 0.0 }\n}'
            }],
        },
    ],
}

# ── 19. background_jobs ───────────────────────────────────────────────────────
EXAMPLES["background_jobs"] = {
    "title": "Background Jobs — Header Illustrations",
    "header": {"eyebrow": "acme/app · Design assets", "title": "Background jobs — header illustrations",
                "description": "Three SVG illustrations for the background jobs feature page headers."},
    "sections": [
        {
            "layout": "grid", "cols": 3, "gap": 24,
            "items": [
                {"primitive": "card", "variant": "outlined", "content":
                    "<div style='background:var(--oat);border-radius:8px;padding:24px;margin-bottom:12px;display:flex;align-items:center;justify-content:center;height:120px'>"
                    "<svg viewBox='0 0 80 80' style='width:60px;height:60px'>"
                    "<rect x='10' y='30' width='16' height='40' rx='3' fill='var(--clay)' opacity='.7'/>"
                    "<rect x='32' y='20' width='16' height='50' rx='3' fill='var(--clay)'/>"
                    "<rect x='54' y='40' width='16' height='30' rx='3' fill='var(--clay)' opacity='.5'/>"
                    "</svg></div>"
                    "<div style='font-family:var(--serif);font-size:15px;font-weight:500;margin-bottom:4px'>Job queue</div>"
                    "<div style='font-size:12px;color:var(--gray-500)'>Work items waiting to be processed</div>"},
                {"primitive": "card", "variant": "outlined", "content":
                    "<div style='background:var(--oat);border-radius:8px;padding:24px;margin-bottom:12px;display:flex;align-items:center;justify-content:center;height:120px'>"
                    "<svg viewBox='0 0 80 80' style='width:60px;height:60px'>"
                    "<circle cx='40' cy='40' r='28' fill='none' stroke='var(--clay)' stroke-width='4'/>"
                    "<path d='M40 20 L40 40 L55 55' stroke='var(--clay)' stroke-width='4' fill='none' stroke-linecap='round'/>"
                    "</svg></div>"
                    "<div style='font-family:var(--serif);font-size:15px;font-weight:500;margin-bottom:4px'>Retry timeline</div>"
                    "<div style='font-size:12px;color:var(--gray-500)'>Exponential backoff between retries</div>"},
                {"primitive": "card", "variant": "outlined", "content":
                    "<div style='background:var(--oat);border-radius:8px;padding:24px;margin-bottom:12px;display:flex;align-items:center;justify-content:center;height:120px'>"
                    "<svg viewBox='0 0 80 80' style='width:60px;height:60px'>"
                    "<circle cx='40' cy='20' r='8' fill='var(--clay)'/>"
                    "<line x1='40' y1='28' x2='20' y2='52' stroke='var(--clay)' stroke-width='3'/>"
                    "<line x1='40' y1='28' x2='40' y2='52' stroke='var(--clay)' stroke-width='3'/>"
                    "<line x1='40' y1='28' x2='60' y2='52' stroke='var(--clay)' stroke-width='3'/>"
                    "<circle cx='20' cy='58' r='6' fill='var(--oat)' stroke='var(--clay)' stroke-width='2'/>"
                    "<circle cx='40' cy='58' r='6' fill='var(--oat)' stroke='var(--clay)' stroke-width='2'/>"
                    "<circle cx='60' cy='58' r='6' fill='var(--oat)' stroke='var(--clay)' stroke-width='2'/>"
                    "</svg></div>"
                    "<div style='font-family:var(--serif);font-size:15px;font-weight:500;margin-bottom:4px'>Fan-out</div>"
                    "<div style='font-size:12px;color:var(--gray-500)'>One job spawns many parallel workers</div>"},
            ],
        },
        {
            "header": "Color palette used", "layout": "stack",
            "items": [{"primitive": "card", "variant": "outlined", "content":
                "<div style='display:flex;gap:16px;flex-wrap:wrap'>"
                + "".join([
                    f"<div style='display:flex;align-items:center;gap:8px'>"
                    f"<div style='width:20px;height:20px;border-radius:4px;background:{c[1]}'></div>"
                    f"<span style='font-family:var(--mono);font-size:12px;color:var(--gray-700)'>{c[0]}</span>"
                    f"</div>"
                    for c in [("--clay", "var(--clay)"), ("--oat", "var(--oat)"), ("--olive", "var(--olive)"), ("--rust", "var(--rust)")]
                ])
                + "</div>"
            }],
        },
    ],
}

# ── 20. empty_states ──────────────────────────────────────────────────────────
EXAMPLES["empty_states"] = {
    "title": "Empty States — Four Visual Directions",
    "header": {"eyebrow": "Design exploration", "title": "Empty states — four visual directions",
                "description": "Four distinct approaches for the tasks-list empty state."},
    "sections": [
        {
            "layout": "grid", "cols": 2, "gap": 32,
            "items": [
                {"primitive": "card", "variant": "outlined", "content":
                    "<div style='text-align:center;padding:32px 16px'>"
                    "<div style='font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--gray-500);margin-bottom:16px'>A · Minimal</div>"
                    "<div style='width:48px;height:48px;border-radius:50%;background:var(--gray-100);margin:0 auto 16px;display:flex;align-items:center;justify-content:center'>"
                    "<svg width='20' height='20' viewBox='0 0 20 20'><path d='M3 5h14M3 10h14M3 15h8' stroke='var(--gray-300)' stroke-width='1.5' stroke-linecap='round'/></svg></div>"
                    "<div style='font-family:var(--serif);font-size:18px;font-weight:500;margin-bottom:6px'>No tasks yet</div>"
                    "<p style='font-size:13px;color:var(--gray-500);margin:0 0 16px'>Add a task to get started.</p>"
                    "<button class='btn btn-primary' style='height:32px;font-size:13px;padding:0 14px'>New task</button></div>"},
                {"primitive": "card", "variant": "outlined", "content":
                    "<div style='text-align:center;padding:32px 16px'>"
                    "<div style='font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--gray-500);margin-bottom:16px'>B · Illustrated</div>"
                    "<div style='width:80px;height:60px;margin:0 auto 16px;position:relative'>"
                    "<div style='width:60px;height:48px;background:var(--oat);border-radius:6px;position:absolute;top:6px;left:10px'></div>"
                    "<div style='width:60px;height:48px;background:var(--white);border:var(--border);border-radius:6px;position:absolute;top:0;left:0'>"
                    "<div style='margin:8px;height:4px;border-radius:2px;background:var(--gray-300)'></div>"
                    "<div style='margin:8px;margin-top:4px;height:4px;border-radius:2px;background:var(--gray-300);width:60%'></div>"
                    "</div></div>"
                    "<div style='font-family:var(--serif);font-size:18px;font-weight:500;margin-bottom:6px'>All clear</div>"
                    "<p style='font-size:13px;color:var(--gray-500);margin:0 0 16px'>Your task list is empty. Enjoy the moment.</p>"
                    "<button class='btn btn-secondary' style='height:32px;font-size:13px;padding:0 14px'>Create task</button></div>"},
                {"primitive": "card", "variant": "inset", "content":
                    "<div style='text-align:center;padding:32px 16px'>"
                    "<div style='font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--gray-500);margin-bottom:16px'>C · Playful</div>"
                    "<div style='font-size:48px;margin-bottom:8px'>🌱</div>"
                    "<div style='font-family:var(--serif);font-size:18px;font-weight:500;margin-bottom:6px'>Room to grow</div>"
                    "<p style='font-size:13px;color:var(--gray-500);margin:0 0 16px'>Plant your first task and watch your list bloom.</p>"
                    "<button class='btn btn-primary' style='height:32px;font-size:13px;padding:0 14px'>Add first task</button></div>"},
                {"primitive": "card", "variant": "outlined", "content":
                    "<div style='padding:24px'>"
                    "<div style='font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--gray-500);margin-bottom:16px'>D · Instructional</div>"
                    "<div style='font-family:var(--serif);font-size:18px;font-weight:500;margin-bottom:16px'>Get started with tasks</div>"
                    + "".join([
                        f"<div style='display:flex;gap:12px;margin-bottom:12px'>"
                        f"<div style='width:22px;height:22px;border-radius:50%;background:var(--clay);color:white;font-family:var(--mono);font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0'>{n}</div>"
                        f"<div style='font-size:13px;color:var(--gray-700);padding-top:3px'>{t}</div></div>"
                        for n, t in [("1", "Press N or click New task"), ("2", "Set a due date and owner"), ("3", "Add to a project or goal")]
                    ])
                    + "<button class='btn btn-ghost' style='height:32px;font-size:13px;padding:0 14px;margin-top:4px'>Create task →</button></div>"},
            ],
        },
    ],
}

# ── 21. data_flow ─────────────────────────────────────────────────────────────
EXAMPLES["data_flow"] = {
    "title": "Comment Thread Data Flow",
    "header": {
        "eyebrow": "acme/app · Architecture",
        "title": "Comment thread data flow",
        "description": "How a comment travels from the task card UI to storage, real-time clients, and notifications.",
    },
    "sections": [
        {
            "layout": "stack",
            "items": [{"primitive": "flow_diagram",
                "direction": "TB",
                "node_width": 160,
                "node_height": 58,
                "h_gap": 40,
                "v_gap": 60,
                "nodes": [
                    {"id": "ui",    "label": "Task Card UI",   "sublabel": "React",         "accent": "clay"},
                    {"id": "api",   "label": "Comment API",    "sublabel": "Node.js / REST"},
                    {"id": "ws",    "label": "WebSocket",      "sublabel": "broadcast",      "accent": "olive"},
                    {"id": "pg",    "label": "PostgreSQL",     "sublabel": "persist"},
                    {"id": "redis", "label": "Redis",          "sublabel": "thread cache"},
                    {"id": "email", "label": "Email Service",  "sublabel": "notify",         "accent": "gray"},
                ],
                "edges": [
                    {"from": "ui",  "to": "api",   "label": "create / fetch"},
                    {"from": "api", "to": "ws",    "label": "broadcast"},
                    {"from": "api", "to": "pg",    "label": "persist"},
                    {"from": "api", "to": "redis", "label": "cache thread"},
                    {"from": "api", "to": "email", "label": "@mention notify", "style": "dashed"},
                ],
                "caption": "Solid = synchronous · Dashed = async / background worker",
            }],
        },
        {
            "header": "Component responsibilities", "layout": "stack",
            "items": [{"primitive": "table", "columns": ["Component", "Technology", "Responsibility"], "rows": [
                ["Task Card UI",  "React",        "Renders thread, sends create/fetch calls, opens WebSocket"],
                ["Comment API",  "Node.js",      "Validates, persists, fans out to WS + email worker"],
                ["WebSocket",    "Socket.io",    "Pushes new comments to all connected clients in the workspace"],
                ["PostgreSQL",   "pg 15",        "Source of truth — comments, threads, mentions"],
                ["Redis",        "Redis 7",      "Caches recent thread state to avoid DB round-trips on open"],
                ["Email Service","Sendgrid",     "Delivers @mention digest emails, async via job queue"],
            ]}],
        },
    ],
}
