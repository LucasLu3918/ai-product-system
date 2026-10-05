from __future__ import annotations

from typing import Any


def traverse_architecture_impact_graph(
    graph: dict[str, Any],
    seeds: list[dict[str, Any]],
    explicit_seed_ids: list[str],
    directions: list[str],
    max_depth: int,
    max_nodes: int,
    max_edges: int,
    changed_paths: list[str],
) -> dict[str, Any]:
    """Traverse reviewed architecture relations in the declared edge direction."""
    graph_nodes = graph.get("nodes") if isinstance(graph.get("nodes"), dict) else {}
    edges = graph.get("edges") if isinstance(graph.get("edges"), list) else []
    requested: set[str] = set(explicit_seed_ids)
    for seed in seeds:
        name = str(seed.get("symbol") or seed.get("name") or "")
        path = str(seed.get("path") or "")
        for node_id, node in graph_nodes.items():
            if str(node_id) == name or str((node or {}).get("symbol") or "") == name:
                requested.add(str(node_id))
            if path and path in {str((node or {}).get("path") or ""), str((node or {}).get("source") or "")}:
                requested.add(str(node_id))
    matched = sorted(node_id for node_id in requested if node_id in graph_nodes)
    result: dict[str, Any] = {
        "status": "INCOMPLETE",
        "seed_ids": matched,
        "requested_seed_ids": sorted(requested),
        "directions": directions,
        "coverage": graph.get("coverage") or {},
        "coverage_scope_ids": [],
        "visited_nodes": 0,
        "visited_edges": 0,
        "reached_depth": {direction: 0 for direction in directions},
        "truncated": False,
        "nodes": [],
        "paths": [],
        "evidence": [],
        "unresolved": [],
        "resolution": {"exact": [], "unresolved": []},
    }
    if not matched:
        result["status"] = "BOUNDED_WITH_UNKNOWNS"
        result["unresolved"].append({"kind": "architecture_seed_unmapped", "seeds": sorted(requested)})
        result["resolution"]["unresolved"].append("architecture_seed_unmapped")
        return result

    relevant_coverage_keys = set()
    if "consumers" in directions:
        relevant_coverage_keys.update({"api", "data", "events", "consumers"})
    coverage = graph.get("coverage") or {}
    scopes = graph.get("coverage_scopes") or []
    matched_set = set(matched)
    selected_scopes = []
    for scope in scopes:
        if not isinstance(scope, dict):
            continue
        seed_values = scope.get("seed_ids")
        if not isinstance(seed_values, list) or not seed_values or any(not isinstance(item, str) or not item for item in seed_values):
            continue
        scope_seeds = set(seed_values)
        if matched_set and matched_set.issubset(scope_seeds):
            selected_scopes.append(scope)
    # A reviewed, explicitly bounded scope can establish coverage for its own
    # seeds without making a broader repository-wide coverage claim.
    usable_scopes = [
        scope for scope in selected_scopes
        if isinstance(scope.get("id"), str) and scope.get("id")
        and isinstance(scope.get("evidence"), list) and scope.get("evidence")
        and all(isinstance(item, str) and item for item in scope["evidence"])
        and isinstance(scope.get("coverage"), dict)
    ]
    if usable_scopes:
        coverage = {
            key: "complete" if all(
                str((scope.get("coverage") or {}).get(key) or "unknown").lower()
                in {"complete", "covered", "full", "ready"}
                for scope in usable_scopes
            ) else "unknown"
            for key in relevant_coverage_keys
        }
        result["coverage_scope_ids"] = sorted(str(scope["id"]) for scope in usable_scopes)
    unknown_coverage = sorted(
        key for key in relevant_coverage_keys
        if str(coverage.get(key) or "unknown").lower() not in {"complete", "covered", "full", "ready"}
    )
    if unknown_coverage:
        result["unresolved"].append({"kind": "architecture_graph_coverage", "dimensions": unknown_coverage})
        result["resolution"]["unresolved"].extend(unknown_coverage)

    visited: dict[str, dict[str, Any]] = {}
    frontier: list[tuple[str, int, list[str]]] = []
    changed = set(changed_paths)
    for node_id in matched:
        visited[node_id] = {"symbol": node_id, "path": (graph_nodes[node_id] or {}).get("path") or (graph_nodes[node_id] or {}).get("source"), "line": None, "depth": 0, "kind": "seed", "layer": "architecture"}
        frontier.append((node_id, 0, [node_id]))

    while frontier:
        node_id, depth, chain = frontier.pop(0)
        if depth >= max_depth:
            if any(
                ((edge.get("to") == node_id) if direction == "callers" else (edge.get("from") == node_id))
                and ((edge.get("from") if direction == "callers" else edge.get("to")) not in visited)
                for edge in edges for direction in directions
            ):
                result["truncated"] = True
            continue
        for direction in directions:
            for edge in edges:
                if not isinstance(edge, dict):
                    continue
                if direction == "callers" and edge.get("to") == node_id:
                    next_id = str(edge.get("from") or "")
                elif direction == "consumers" and edge.get("from") == node_id:
                    next_id = str(edge.get("to") or "")
                else:
                    continue
                if next_id not in graph_nodes or not next_id:
                    result["unresolved"].append({"kind": "architecture_edge_target_missing", "edge": edge.get("id"), "node": next_id})
                    result["resolution"]["unresolved"].append(next_id)
                    continue
                if len(result["paths"]) >= max_edges or len(visited) >= max_nodes:
                    result["truncated"] = True
                    continue
                node_data = graph_nodes[next_id] or {}
                node = {
                    "symbol": next_id,
                    "path": node_data.get("path") or node_data.get("source"),
                    "line": None,
                    "depth": depth + 1,
                    "kind": "architecture",
                    "layer": "architecture",
                    "impact_status": "affected_and_changed" if str(node_data.get("path") or node_data.get("source") or "") in changed else "affected_but_unchanged",
                    "disposition": "pending_review",
                }
                edge_evidence = {
                    "from": edge.get("from"),
                    "to": edge.get("to"),
                    "relation": edge.get("relation"),
                    "direction": direction,
                    "resolution": "exact",
                    "provenance": edge.get("provenance"),
                    "id": edge.get("id"),
                }
                result["paths"].append(edge_evidence)
                result["evidence"].append({"kind": "impact_graph_edge", "id": edge.get("id"), "from": edge.get("from"), "to": edge.get("to"), "relation": edge.get("relation")})
                result["resolution"]["exact"].append(edge.get("id") or f"{edge.get('from')}->{edge.get('to')}")
                if next_id not in visited:
                    if next_id in chain:
                        continue
                    visited[next_id] = node
                    frontier.append((next_id, depth + 1, [*chain, next_id]))
                result["reached_depth"][direction] = max(result["reached_depth"][direction], depth + 1)
    result["nodes"] = sorted(visited.values(), key=lambda node: (int(node["depth"]), str(node["symbol"])))
    result["visited_nodes"] = len(visited)
    result["visited_edges"] = len(result["paths"])
    result["status"] = "TRUNCATED" if result["truncated"] else ("BOUNDED_WITH_UNKNOWNS" if result["unresolved"] else "COMPLETE")
    return result
