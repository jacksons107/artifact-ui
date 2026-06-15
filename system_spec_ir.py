"""DSL -> semantic IR compilation for system_spec.

The DSL (top-level JSON keys: nodes, edges, groups, data, actions, invariants,
initial_tokens) is authored by the LLM. compile_ir() expands it into a
Petri-net-like IR (places/transitions/arcs) plus failure-mode expansion and
normalized invariants, which is embedded as JSON into the rendered artifact
and consumed by the in-browser engine (system_spec_ir_js.py).
"""

from collections import defaultdict

# ── Failure-mode vocabulary ────────────────────────────────────────────────

FAILURE_MODE_TABLE = {
    "unavailable": {
        "kinds": {"db", "queue", "cache", "service", "http_service", "external"},
        "expand": "unavailable",
        "tags": lambda kind: ["availability", f"{kind}-failure"],
    },
    "timeout": {
        "kinds": {"db", "service", "http_service", "external"},
        "expand": "unavailable",
        "tags": lambda kind: ["availability", "latency", f"{kind}-failure"],
    },
    "stale_read": {
        "kinds": {"db", "cache"},
        "expand": "stale_variant",
        "tags": lambda kind: ["database-failure" if kind == "db" else "cache-failure", "stale_read"],
    },
    "message_drop": {
        "kinds": {"queue"},
        "expand": "drop",
        "tags": lambda kind: ["messaging-failure", "message_drop"],
    },
    "message_delay": {
        "kinds": {"queue"},
        "expand": "delay",
        "tags": lambda kind: ["messaging-failure", "latency", "message_delay"],
    },
}

INVARIANT_RULE_TYPES = {"precedes", "requires", "excludes", "eventually"}


# ── Validation ────────────────────────────────────────────────────────────

def _validate_nodes_edges(nodes: list, edges: list, context: str) -> set:
    node_ids = set()
    for i, node in enumerate(nodes):
        if "id" not in node:
            raise ValueError(f"{context}nodes[{i}] is missing required field 'id'.")
        if "label" not in node:
            raise ValueError(f"{context}nodes[{i}] (id={node['id']!r}) is missing required field 'label'.")
        if node["id"] in node_ids:
            raise ValueError(f"{context}nodes[{i}]: duplicate node id {node['id']!r}.")
        node_ids.add(node["id"])

    for i, node in enumerate(nodes):
        for mode in node.get("failure_modes", []):
            entry = FAILURE_MODE_TABLE.get(mode)
            if entry is None:
                raise ValueError(
                    f"{context}nodes[{i}] (id={node['id']!r}): unknown failure_mode {mode!r}. "
                    f"Known modes: {sorted(FAILURE_MODE_TABLE)}."
                )
            kind = node.get("kind", "")
            if kind not in entry["kinds"]:
                raise ValueError(
                    f"{context}nodes[{i}] (id={node['id']!r}): failure_mode {mode!r} does not apply to "
                    f"kind {kind!r}. Applies to: {sorted(entry['kinds'])}."
                )

    for i, edge in enumerate(edges):
        src = edge.get("from")
        dst = edge.get("to")
        if src is None:
            raise ValueError(f"{context}edges[{i}] is missing required field 'from'.")
        if dst is None:
            raise ValueError(f"{context}edges[{i}] is missing required field 'to'.")
        if src not in node_ids:
            raise ValueError(f"{context}edges[{i}]: 'from' references unknown node id {src!r}.")
        if dst not in node_ids:
            raise ValueError(f"{context}edges[{i}]: 'to' references unknown node id {dst!r}.")

    return node_ids


def _validate_data(data: list) -> set:
    data_ids = set()
    for i, d in enumerate(data):
        if "id" not in d:
            raise ValueError(f"data[{i}] is missing required field 'id'.")
        if "label" not in d:
            raise ValueError(f"data[{i}] (id={d['id']!r}) is missing required field 'label'.")
        if d["id"] in data_ids:
            raise ValueError(f"data[{i}]: duplicate data id {d['id']!r}.")
        data_ids.add(d["id"])
    return data_ids


def _validate_actions(actions: list, node_ids: set, data_ids: set) -> set:
    action_ids = set()
    for i, a in enumerate(actions):
        if "id" not in a:
            raise ValueError(f"actions[{i}] is missing required field 'id'.")
        if "label" not in a:
            raise ValueError(f"actions[{i}] (id={a['id']!r}) is missing required field 'label'.")
        if a["id"] in action_ids:
            raise ValueError(f"actions[{i}]: duplicate action id {a['id']!r}.")
        action_ids.add(a["id"])

        node = a.get("node")
        if node is None:
            raise ValueError(f"actions[{i}] (id={a['id']!r}) is missing required field 'node'.")
        if node not in node_ids:
            raise ValueError(f"actions[{i}] (id={a['id']!r}): 'node' references unknown node id {node!r}.")

        for field in ("consumes", "produces"):
            for d in a.get(field, []):
                if d not in data_ids:
                    raise ValueError(
                        f"actions[{i}] (id={a['id']!r}): {field}[] references unknown data id {d!r}."
                    )

        for field in ("reads", "writes"):
            for n in a.get(field, []):
                if n not in node_ids:
                    raise ValueError(
                        f"actions[{i}] (id={a['id']!r}): {field}[] references unknown node id {n!r}."
                    )

    return action_ids


def _validate_invariants(invariants: list, action_ids: set, node_ids: set) -> None:
    for i, inv in enumerate(invariants):
        if "id" not in inv:
            raise ValueError(f"invariants[{i}] is missing required field 'id'.")
        if "label" not in inv:
            raise ValueError(f"invariants[{i}] (id={inv['id']!r}) is missing required field 'label'.")
        rule = inv.get("rule")
        if not rule or "type" not in rule:
            raise ValueError(f"invariants[{i}] (id={inv['id']!r}) is missing required field 'rule.type'.")
        if rule["type"] not in INVARIANT_RULE_TYPES:
            raise ValueError(
                f"invariants[{i}] (id={inv['id']!r}): unknown rule.type {rule['type']!r}. "
                f"Known types: {sorted(INVARIANT_RULE_TYPES)}."
            )
        for key in ("before", "after", "then"):
            ref = rule.get(key)
            if ref is None:
                continue
            if "action" in ref and ref["action"] not in action_ids:
                raise ValueError(
                    f"invariants[{i}] (id={inv['id']!r}): rule.{key}.action references unknown action id {ref['action']!r}."
                )
            if "node" in ref and ref["node"] not in node_ids:
                raise ValueError(
                    f"invariants[{i}] (id={inv['id']!r}): rule.{key}.node references unknown node id {ref['node']!r}."
                )


def validate_spec(data: dict) -> dict:
    title  = data.get("title", "Untitled System")
    nodes  = data.get("nodes", [])
    edges  = data.get("edges", [])
    groups = data.get("groups", [])
    spec_data = data.get("data", [])
    actions = data.get("actions", [])
    invariants = data.get("invariants", [])
    initial_tokens = data.get("initial_tokens", [])

    if not nodes:
        raise ValueError("system_spec requires at least one node in 'nodes'.")

    node_ids = _validate_nodes_edges(nodes, edges, "")

    for i, group in enumerate(groups):
        if "id" not in group:
            raise ValueError(f"groups[{i}] is missing required field 'id'.")
        if "label" not in group:
            raise ValueError(f"groups[{i}] (id={group['id']!r}) is missing required field 'label'.")
        for member in group.get("members", []):
            if member not in node_ids:
                raise ValueError(
                    f"groups[{i}] (id={group['id']!r}): member {member!r} is not a known node id."
                )

    data_ids = _validate_data(spec_data)
    action_ids = _validate_actions(actions, node_ids, data_ids)
    _validate_invariants(invariants, action_ids, node_ids)

    for i, tok in enumerate(initial_tokens):
        if tok not in data_ids:
            raise ValueError(f"initial_tokens[{i}] references unknown data id {tok!r}.")

    return {
        "title": title,
        "description": data.get("description", ""),
        "nodes": nodes,
        "edges": edges,
        "groups": groups,
        "data": spec_data,
        "actions": actions,
        "invariants": invariants,
        "initial_tokens": initial_tokens,
        "node_ids": node_ids,
        "data_ids": data_ids,
        "action_ids": action_ids,
    }


# ── Compilation ──────────────────────────────────────────────────────────

def _resolve_ref(ref: dict, transitions: list, tags_index: dict, meta: dict) -> list:
    """Resolve an invariant rule reference to a sorted list of transition ids."""
    if "action" in ref:
        return [ref["action"]] if any(t["id"] == ref["action"] for t in transitions) else []
    if "tag" in ref:
        return sorted(tags_index.get(ref["tag"], {}).get("transitions", []))
    if "node" in ref:
        edge_kind = ref.get("edge_kind")
        if edge_kind:
            ids = [t["id"] for t in transitions if ref["node"] in t.get(edge_kind, [])]
        else:
            ids = meta["node_to_transitions"].get(ref["node"], [])
        return sorted(ids)
    return []


def compile_ir(spec: dict) -> dict:
    nodes = spec["nodes"]
    actions = spec["actions"]
    spec_data = spec["data"]

    node_by_id = {n["id"]: n for n in nodes}

    # ── Places: one per data object ────────────────────────────────────
    data_objects = {d["id"]: d for d in spec_data}
    places = [
        {"id": d["id"], "label": d.get("label", d["id"]), "data_object": d["id"], "synthetic": False}
        for d in spec_data
    ]
    place_ids = {p["id"] for p in places}

    # ── Base transitions from actions ──────────────────────────────────
    transitions = []
    for a in actions:
        transitions.append({
            "id": a["id"],
            "label": a.get("label", a["id"]),
            "node": a["node"],
            "in": list(a.get("consumes", [])),
            "out": list(a.get("produces", [])),
            "reads": list(a.get("reads", [])),
            "writes": list(a.get("writes", [])),
            "tags": list(a.get("tags", [])),
            "synthetic": False,
            "origin": None,
        })

    arcs = []
    for t in transitions:
        for p in t["in"]:
            arcs.append({"place": p, "transition": t["id"], "dir": "in"})
        for p in t["out"]:
            arcs.append({"place": p, "transition": t["id"], "dir": "out"})

    # ── Failure-mode expansion ───────────────────────────────────────────
    synthetic_error_places: dict[str, str] = {}  # node_id -> error place id

    def _error_place(node_id: str) -> str:
        if node_id not in synthetic_error_places:
            pid = f"{node_id}__error"
            synthetic_error_places[node_id] = pid
            places.append({
                "id": pid,
                "label": f"{node_by_id[node_id].get('label', node_id)} Error",
                "data_object": None,
                "synthetic": True,
            })
            place_ids.add(pid)
        return synthetic_error_places[node_id]

    for node in nodes:
        node_id = node["id"]
        kind = node.get("kind", "")
        local = [t for t in transitions if t["node"] == node_id and not t["synthetic"]]

        for mode in node.get("failure_modes", []):
            entry = FAILURE_MODE_TABLE[mode]
            tags = entry["tags"](kind) + [mode]
            expand = entry["expand"]

            if expand == "unavailable":
                in_places = sorted({p for t in local for p in t["in"]})
                out_place = _error_place(node_id)
                tid = f"{node_id}__{mode}"
                transitions.append({
                    "id": tid,
                    "label": f"{node.get('label', node_id)}: {mode}",
                    "node": node_id,
                    "in": in_places,
                    "out": [out_place],
                    "reads": [],
                    "writes": [],
                    "tags": tags,
                    "synthetic": True,
                    "origin": {"expanded_from": [t["id"] for t in local], "failure_mode": mode},
                })
                for p in in_places:
                    arcs.append({"place": p, "transition": tid, "dir": "in"})
                arcs.append({"place": out_place, "transition": tid, "dir": "out"})

            elif expand == "stale_variant":
                for t in transitions:
                    if t["synthetic"]:
                        continue
                    if node_id not in t.get("reads", []):
                        continue
                    tid = f"{t['id']}__stale_{node_id}"
                    transitions.append({
                        "id": tid,
                        "label": f"{t['label']} (stale {node.get('label', node_id)})",
                        "node": node_id,
                        "in": list(t["in"]),
                        "out": list(t["out"]),
                        "reads": list(t.get("reads", [])),
                        "writes": [],
                        "tags": list(t.get("tags", [])) + tags,
                        "synthetic": True,
                        "origin": {"expanded_from": [t["id"]], "failure_mode": mode},
                    })
                    for p in t["in"]:
                        arcs.append({"place": p, "transition": tid, "dir": "in"})
                    for p in t["out"]:
                        arcs.append({"place": p, "transition": tid, "dir": "out"})

            elif expand == "drop":
                producers = [
                    t for t in transitions
                    if not t["synthetic"] and (node_id in t.get("writes", []) or t["node"] == node_id)
                ]
                for t in producers:
                    tid = f"{t['id']}__drop"
                    transitions.append({
                        "id": tid,
                        "label": f"{t['label']} (dropped by {node.get('label', node_id)})",
                        "node": node_id,
                        "in": list(t["in"]),
                        "out": [],
                        "reads": [],
                        "writes": [],
                        "tags": tags,
                        "synthetic": True,
                        "origin": {"expanded_from": [t["id"]], "failure_mode": mode},
                    })
                    for p in t["in"]:
                        arcs.append({"place": p, "transition": tid, "dir": "in"})

            elif expand == "delay":
                producers = [
                    t for t in transitions
                    if not t["synthetic"] and (node_id in t.get("writes", []) or t["node"] == node_id)
                ]
                for t in producers:
                    tid = f"{t['id']}__delay"
                    transitions.append({
                        "id": tid,
                        "label": f"{t['label']} (delayed by {node.get('label', node_id)})",
                        "node": node_id,
                        "in": list(t["in"]),
                        "out": list(t["out"]),
                        "reads": list(t.get("reads", [])),
                        "writes": list(t.get("writes", [])),
                        "tags": list(t.get("tags", [])) + tags,
                        "synthetic": True,
                        "origin": {"expanded_from": [t["id"]], "failure_mode": mode},
                        "delay": True,
                    })
                    for p in t["in"]:
                        arcs.append({"place": p, "transition": tid, "dir": "in"})
                    for p in t["out"]:
                        arcs.append({"place": p, "transition": tid, "dir": "out"})

    # ── Indexes ──────────────────────────────────────────────────────────
    tags_index: dict = defaultdict(lambda: {"transitions": []})
    node_to_transitions: dict = defaultdict(list)
    transition_to_node: dict = {}
    for t in transitions:
        transition_to_node[t["id"]] = t["node"]
        node_to_transitions[t["node"]].append(t["id"])
        for tag in t["tags"]:
            tags_index[tag]["transitions"].append(t["id"])

    meta = {
        "node_to_transitions": dict(node_to_transitions),
        "transition_to_node": transition_to_node,
    }
    tags_index = {k: v for k, v in tags_index.items()}

    # ── Initial marking ─────────────────────────────────────────────────
    if spec.get("initial_tokens"):
        initial_marking = list(spec["initial_tokens"])
    else:
        consumed = {p for t in transitions for p in t["in"]}
        initial_marking = [p["id"] for p in places if p["id"] not in consumed and not p["synthetic"]]

    # ── Invariants ───────────────────────────────────────────────────────
    compiled_invariants = []
    for inv in spec["invariants"]:
        rule = inv["rule"]
        norm_rule = {"type": rule["type"]}
        for key in ("before", "after", "then"):
            if key in rule:
                norm_rule[key] = _resolve_ref(rule[key], transitions, tags_index, meta)
        compiled_invariants.append({
            "id": inv["id"],
            "label": inv["label"],
            "severity": inv.get("severity", "medium"),
            "rule": norm_rule,
        })

    return {
        "structural": {
            "nodes": spec["nodes"],
            "edges": spec["edges"],
            "groups": spec["groups"],
        },
        "data_objects": data_objects,
        "net": {
            "places": places,
            "transitions": transitions,
            "arcs": arcs,
            "initial_marking": initial_marking,
        },
        "invariants": compiled_invariants,
        "tags_index": tags_index,
        "meta": meta,
    }


def has_behavioral(data: dict) -> bool:
    return bool(data.get("actions") or data.get("data") or data.get("invariants"))
