# ── Validation ────────────────────────────────────────────────────────────────
#
# Groups are collapsible nodes: `groups[].members` may list real node ids
# and/or other group ids (nesting), every id may have at most one parent
# group, and there is no separate `detail` block — a group's own members ARE
# what it expands to reveal. A group must have either 0 or 2+ members — a
# single-member group adds no value over referencing that member directly.
# `clone_of` lets one group's entire member subtree (nodes, nested groups,
# and the edges among/touching them) be reused under a new id-prefix instead
# of hand-duplicated.

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).parent / "spec_schema.json"
_SCHEMA = json.loads(SCHEMA_PATH.read_text())
_VALIDATOR = Draft202012Validator(_SCHEMA)


def _validate_schema(data: dict) -> None:
    """Shape-validates raw spec input against spec_schema.json (required fields,
    types, structural nesting) before any graph-relational checks run below —
    those checks assume well-shaped input and raise confusing secondary errors
    otherwise. Run pre-clone-resolution since 'clone_of' only exists pre-resolution."""
    errors = sorted(_VALIDATOR.iter_errors(data), key=lambda e: list(map(str, e.absolute_path)))
    if not errors:
        return
    e = errors[0]
    path = "".join(f"[{p!r}]" if isinstance(p, str) else f"[{p}]" for p in e.absolute_path)
    location = f"data{path}" if path else "data (top level)"
    raise ValueError(f"{location}: {e.message}")


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
    """Validates group shape, that every member is a known node or group id,
    and that every node/group has at most one parent group (required for
    collapse/expand to be unambiguous)."""
    group_ids = set()
    for i, group in enumerate(groups):
        if "id" not in group:
            raise ValueError(f"{context}groups[{i}] is missing required field 'id'.")
        if "label" not in group:
            raise ValueError(f"{context}groups[{i}] (id={group['id']!r}) is missing required field 'label'.")
        if group["id"] in group_ids:
            raise ValueError(f"{context}groups[{i}]: duplicate group id {group['id']!r}.")
        group_ids.add(group["id"])
        if len(group.get("members", [])) == 1:
            raise ValueError(
                f"{context}groups[{i}] (id={group['id']!r}): a group with exactly one member adds no "
                f"value over referencing that member directly — give it a second member or remove the group."
            )

    parent_of: dict = {}
    for i, group in enumerate(groups):
        gid = group["id"]
        for member in group.get("members", []):
            if member not in node_ids and member not in group_ids:
                raise ValueError(
                    f"{context}groups[{i}] (id={gid!r}): member {member!r} is not a known node id or group id."
                )
            if member == gid:
                raise ValueError(f"{context}groups[{i}] (id={gid!r}): a group cannot be a member of itself.")
            if member in parent_of and parent_of[member] != gid:
                raise ValueError(
                    f"{context}groups[{i}] (id={gid!r}): member {member!r} is already a member of group "
                    f"{parent_of[member]!r} — a node or group may belong to at most one parent group."
                )
            parent_of[member] = gid

    # Cycle check: a group can't (transitively) contain itself.
    children = {g["id"]: list(g.get("members", [])) for g in groups}
    for start in group_ids:
        stack, visiting = [start], set()
        while stack:
            cur = stack.pop()
            if cur == start and cur in visiting:
                raise ValueError(f"{context}groups: cycle detected — group {start!r} transitively contains itself.")
            if cur in visiting:
                continue
            visiting.add(cur)
            for m in children.get(cur, []):
                if m in group_ids:
                    if m == start:
                        raise ValueError(f"{context}groups: cycle detected — group {start!r} transitively contains itself.")
                    stack.append(m)


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


# ── clone_of resolution ────────────────────────────────────────────────────

def _subtree_ids(group_id: str, groups_by_id: dict) -> tuple:
    """BFS over group membership starting at group_id. Returns
    (group_ids_in_subtree_including_root, leaf_node_ids_in_subtree)."""
    sub_groups, leaf_ids = {group_id}, set()
    queue = [group_id]
    while queue:
        gid = queue.pop()
        g = groups_by_id[gid]
        for m in g.get("members", []):
            if m in groups_by_id:
                if m not in sub_groups:
                    sub_groups.add(m)
                    queue.append(m)
            else:
                leaf_ids.add(m)
    return sub_groups, leaf_ids


def _id_map_for_clone(source_id: str, new_id: str, ids: set) -> dict:
    id_map = {}
    prefix = source_id + "_"
    for old_id in ids:
        if old_id == source_id:
            id_map[old_id] = new_id
        elif old_id.startswith(prefix):
            id_map[old_id] = new_id + "_" + old_id[len(prefix):]
        else:
            raise ValueError(
                f"clone_of: id {old_id!r} inside group {source_id!r}'s subtree doesn't start with "
                f"{prefix!r} — every node/group nested under a clonable group must be prefixed with the "
                f"group's own id (e.g. {source_id}_worker) so clone_of can derive the cloned ids mechanically."
            )
    return id_map


def _resolve_clones(nodes: list, edges: list, groups: list) -> tuple:
    groups_by_id = {g["id"]: g for g in groups if "id" in g}
    clone_groups = [g for g in groups if g.get("clone_of")]
    if not clone_groups:
        return nodes, edges, groups

    for g in clone_groups:
        source_id = g["clone_of"]
        if source_id not in groups_by_id:
            raise ValueError(f"groups (id={g['id']!r}): clone_of references unknown group id {source_id!r}.")
        if groups_by_id[source_id].get("clone_of"):
            raise ValueError(
                f"groups (id={g['id']!r}): clone_of source {source_id!r} is itself a clone — chained clone_of "
                f"is not allowed, clone the original group instead."
            )

    node_by_id = {n["id"]: n for n in nodes}
    new_nodes, new_edges, new_groups = [], [], []

    for g in clone_groups:
        source_id, new_id = g["clone_of"], g["id"]
        sub_group_ids, leaf_ids = _subtree_ids(source_id, groups_by_id)
        id_map = _id_map_for_clone(source_id, new_id, sub_group_ids | leaf_ids)

        for nid in leaf_ids:
            clone = copy.deepcopy(node_by_id[nid])
            clone["id"] = id_map[nid]
            new_nodes.append(clone)

        for gid in sub_group_ids:
            src_group = groups_by_id[gid]
            clone = copy.deepcopy(src_group)
            clone["id"] = id_map[gid]
            clone["members"] = [id_map[m] for m in src_group.get("members", [])]
            clone.pop("clone_of", None)
            if gid == source_id:
                # The clone's own label/kind (as authored on `g`) win; everything else is inherited.
                clone["label"] = g.get("label", clone.get("label"))
                if g.get("kind"):
                    clone["kind"] = g["kind"]
            new_groups.append(clone)

        for e in edges:
            from_in, to_in = e.get("from") in leaf_ids, e.get("to") in leaf_ids
            if not from_in and not to_in:
                continue
            ce = copy.deepcopy(e)
            if from_in:
                ce["from"] = id_map[e["from"]]
            if to_in:
                ce["to"] = id_map[e["to"]]
            new_edges.append(ce)

    clone_ids = {g["id"] for g in clone_groups}
    remaining_groups = [g for g in groups if g["id"] not in clone_ids]
    return nodes + new_nodes, edges + new_edges, remaining_groups + new_groups


def parse_spec(data: dict) -> dict:
    _validate_schema(data)

    title  = data.get("title", "Untitled System")
    nodes  = data.get("nodes", [])
    edges  = data.get("edges", [])
    groups = data.get("groups", [])
    seqs   = data.get("sequences", [])

    if not nodes:
        raise ValueError("system_spec requires at least one node in 'nodes'.")

    nodes, edges, groups = _resolve_clones(nodes, edges, groups)

    node_ids = _validate_nodes_edges(nodes, edges, "")
    _validate_groups(groups, node_ids, "")
    _validate_sequences(seqs, node_ids, "")

    return {
        "title":       title,
        "description": data.get("description", ""),
        "nodes":       nodes,
        "edges":       edges,
        "groups":      groups,
        "sequences":   seqs,
        "node_ids":    node_ids,
    }
