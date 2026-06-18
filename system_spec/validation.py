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


def parse_spec(data: dict) -> dict:
    title  = data.get("title", "Untitled System")
    nodes  = data.get("nodes", [])
    edges  = data.get("edges", [])
    groups = data.get("groups", [])
    seqs   = data.get("sequences", [])

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
        detail = group.get("detail")
        if detail:
            _validate_nodes_edges(
                detail.get("nodes", []), detail.get("edges", []),
                f"groups[{i}] (id={group['id']!r}).detail."
            )

    for i, seq in enumerate(seqs):
        if "id" not in seq:
            raise ValueError(f"sequences[{i}] is missing required field 'id'.")
        if "label" not in seq:
            raise ValueError(f"sequences[{i}] (id={seq['id']!r}) is missing required field 'label'.")
        for j, step in enumerate(seq.get("steps", [])):
            for field in ("from", "to"):
                val = step.get(field)
                if val and val not in node_ids:
                    raise ValueError(
                        f"sequences[{i}].steps[{j}]: {field!r} references unknown node id {val!r}."
                    )

    return {
        "title":       title,
        "description": data.get("description", ""),
        "nodes":       nodes,
        "edges":       edges,
        "groups":      groups,
        "sequences":   seqs,
        "node_ids":    node_ids,
    }
