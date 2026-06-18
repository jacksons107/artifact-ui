from collections import defaultdict, deque

from .styles import NODE_W, NODE_H, H_GAP, V_GAP, PAD

# ── Layout ────────────────────────────────────────────────────────────────────

def layout_graph(nodes: list, edges: list, groups: list) -> dict:
    """
    Assign (x, y, w, h) to each node using longest-path layering (Kahn's).
    Nodes in the same group are placed adjacent within their layer.
    Returns {node_id: {x, y, w, h}}.
    """
    node_ids = [n["id"] for n in nodes]

    # Group membership: node_id -> group_id (first group wins)
    node_group: dict[str, str] = {}
    for g in groups:
        for member in g.get("members", []):
            if member not in node_group:
                node_group[member] = g["id"]

    # Build adjacency
    in_deg = {nid: 0 for nid in node_ids}
    succs  = {nid: [] for nid in node_ids}
    for edge in edges:
        src, dst = edge["from"], edge["to"]
        if src != dst:
            succs[src].append(dst)
            in_deg[dst] += 1

    # Longest-path layer assignment
    layer: dict[str, int] = {}
    queue: deque = deque()
    for nid in node_ids:
        if in_deg[nid] == 0:
            layer[nid] = 0
            queue.append(nid)

    while queue:
        nid = queue.popleft()
        for succ in succs[nid]:
            new_l = layer[nid] + 1
            layer[succ] = max(layer.get(succ, 0), new_l)
            in_deg[succ] -= 1
            if in_deg[succ] == 0:
                queue.append(succ)

    # Nodes in cycles were never enqueued — place at max_layer + 1
    max_l = max(layer.values()) if layer else 0
    for nid in node_ids:
        if nid not in layer:
            max_l += 1
            layer[nid] = max_l

    # Group by layer, sort within each layer by (group_id, node_id) for co-location
    layers_map: dict[int, list] = defaultdict(list)
    for nid in node_ids:
        layers_map[layer[nid]].append(nid)
    for l in layers_map:
        layers_map[l].sort(key=lambda nid: (node_group.get(nid, "\xff"), nid))

    # Find the widest layer to center narrower layers
    max_layer_w = max(
        len(ns) * NODE_W + max(0, len(ns) - 1) * H_GAP
        for ns in layers_map.values()
    )

    positions: dict[str, dict] = {}
    for l_idx in sorted(layers_map):
        ns = layers_map[l_idx]
        layer_w = len(ns) * NODE_W + max(0, len(ns) - 1) * H_GAP
        start_x = PAD + (max_layer_w - layer_w) / 2
        y = PAD + l_idx * (NODE_H + V_GAP)
        for i, nid in enumerate(ns):
            x = start_x + i * (NODE_W + H_GAP)
            positions[nid] = {"x": x, "y": y, "w": NODE_W, "h": NODE_H}

    return positions
