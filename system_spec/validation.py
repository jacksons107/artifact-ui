# ── Validation ────────────────────────────────────────────────────────────────

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


def _validate_groups(groups: list, node_ids: set, context: str) -> None:
    for i, group in enumerate(groups):
        if "id" not in group:
            raise ValueError(f"{context}groups[{i}] is missing required field 'id'.")
        if "label" not in group:
            raise ValueError(f"{context}groups[{i}] (id={group['id']!r}) is missing required field 'label'.")
        for member in group.get("members", []):
            if member not in node_ids:
                raise ValueError(
                    f"{context}groups[{i}] (id={group['id']!r}): member {member!r} is not a known node id."
                )


def _validate_sequences(seqs: list, node_ids: set, context: str) -> None:
    for i, seq in enumerate(seqs):
        if "id" not in seq:
            raise ValueError(f"{context}sequences[{i}] is missing required field 'id'.")
        if "label" not in seq:
            raise ValueError(f"{context}sequences[{i}] (id={seq['id']!r}) is missing required field 'label'.")
        for j, step in enumerate(seq.get("steps", [])):
            for field in ("from", "to"):
                val = step.get(field)
                if val and val not in node_ids:
                    raise ValueError(
                        f"{context}sequences[{i}].steps[{j}]: {field!r} references unknown node id {val!r}."
                    )


def _validate_boundary(group: dict, edges: list, detail_node_ids: set, ctx: str) -> None:
    """Every external node with a top-level edge touching this group's members must have
    an explicit detail.boundary[external_id] -> internal_node_id mapping. No fallback —
    expand-in-place needs to know exactly which inner node receives each outside edge."""
    members = set(group.get("members", []))
    neighbors = set()
    for edge in edges:
        src, dst = edge.get("from"), edge.get("to")
        if src in members and dst not in members:
            neighbors.add(dst)
        if dst in members and src not in members:
            neighbors.add(src)
    if not neighbors:
        return

    boundary = group.get("detail", {}).get("boundary", {})
    if not isinstance(boundary, dict):
        raise ValueError(f"{ctx}boundary must be an object mapping external node ids to this detail's own node ids.")

    missing = sorted(n for n in neighbors if n not in boundary)
    if missing:
        raise ValueError(
            f"{ctx}boundary is missing a mapping for external neighbor(s) {missing!r}. "
            f"Every node with a top-level edge touching this group's members must have "
            f"boundary[{missing[0]!r}] = <id of the detail node that should receive that edge>."
        )

    for ext_id, internal_id in boundary.items():
        if internal_id not in detail_node_ids:
            raise ValueError(
                f"{ctx}boundary[{ext_id!r}] = {internal_id!r} is not a known id among this detail's own nodes."
            )


def parse_spec(data: dict) -> dict:
    title  = data.get("title", "Untitled System")
    nodes  = data.get("nodes", [])
    edges  = data.get("edges", [])
    groups = data.get("groups", [])
    seqs   = data.get("sequences", [])

    if not nodes:
        raise ValueError("system_spec requires at least one node in 'nodes'.")

    node_ids = _validate_nodes_edges(nodes, edges, "")
    _validate_groups(groups, node_ids, "")
    _validate_sequences(seqs, node_ids, "")

    for i, group in enumerate(groups):
        detail = group.get("detail")
        if not detail:
            continue
        ctx = f"groups[{i}] (id={group['id']!r}).detail."
        detail_node_ids = _validate_nodes_edges(
            detail.get("nodes", []), detail.get("edges", []), ctx
        )
        _validate_groups(detail.get("groups", []), detail_node_ids, ctx)
        _validate_sequences(detail.get("sequences", []), detail_node_ids, ctx)
        _validate_boundary(group, edges, detail_node_ids, ctx)

    return {
        "title":       title,
        "description": data.get("description", ""),
        "nodes":       nodes,
        "edges":       edges,
        "groups":      groups,
        "sequences":   seqs,
        "node_ids":    node_ids,
    }
