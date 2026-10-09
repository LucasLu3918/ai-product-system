from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Any

import yaml

_IGNORED_DIRS = {".git", ".ai", ".venv", "venv", "node_modules", "vendor", "dist", "build", "__pycache__"}


def _python_sources(root: Path, max_files: int) -> tuple[list[Path], bool]:
    """Return a deterministic, bounded set of repository Python sources."""
    limit = max(1, min(max_files, 8000))
    found: list[Path] = []
    truncated = False
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(name for name in dirs if name not in _IGNORED_DIRS and not name.startswith("."))
        for name in sorted(files):
            path = Path(base) / name
            if path.suffix != ".py" or path.is_symlink():
                continue
            found.append(path)
            if len(found) > limit:
                truncated = True
                break
        if truncated:
            break
    return sorted(found[:limit]), truncated


def _module_path(root: Path, module: str, level: int, source: Path, module_paths: dict[str, str]) -> str | None:
    """Resolve only exact repository Python module paths; leave ambiguity unknown."""
    parts = module.split(".") if module else []
    if level:
        package = list(source.parent.parts)
        package = package[: max(0, len(package) - level + 1)]
        parts = package + parts
    name = ".".join(part for part in parts if part)
    return module_paths.get(name)


def generate_relation_candidates(
    root: Path,
    seed_paths: list[str],
    *,
    max_files: int = 8000,
    max_candidates: int = 300,
) -> dict[str, Any]:
    """Generate read-only, provenance-backed source relationship candidates.

    Results are a review aid only: this function never modifies the canonical
    Impact Graph and does not infer runtime behavior from dynamic dispatch.
    """
    root = root.resolve()
    seeds = sorted({str(Path(item).as_posix()).strip("./") for item in seed_paths if item})
    files, file_truncated = _python_sources(root, max(1, min(max_files, 8000)))
    module_paths: dict[str, str] = {}
    ambiguous_modules: set[str] = set()
    parsed: dict[str, ast.AST] = {}
    for path in files:
        relative = path.relative_to(root).as_posix()
        module = relative[:-3].replace("/", ".")
        module = module.removesuffix(".__init__")
        if module in module_paths or module in ambiguous_modules:
            module_paths.pop(module, None)
            ambiguous_modules.add(module)
        else:
            module_paths[module] = relative
        try:
            parsed[relative] = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError):
            continue

    candidates: dict[tuple[str, str, str, int], dict[str, Any]] = {}
    unresolved: list[dict[str, Any]] = []

    def add(source: str, target: str, relation: str, evidence_path: str, line: int, kind: str) -> None:
        key = (source, target, relation, line)
        candidates[key] = {
            "from": source,
            "to": target,
            "relation": relation,
            "resolution": "static_candidate",
            "review_status": "unreviewed",
            "provenance": {"path": evidence_path, "line": line, "kind": kind},
        }

    for relative, tree in parsed.items():
        is_test = relative.startswith("tests/") or "/tests/" in relative
        for node in ast.walk(tree):
            module: str | None = None
            level = 0
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = module_paths.get(alias.name)
                    if target:
                        add(relative, target, "test_imports" if is_test else "imports", relative, node.lineno, "python_import")
                continue
            if isinstance(node, ast.ImportFrom):
                module, level = node.module, node.level
                target = _module_path(root, module or "", level, Path(relative), module_paths)
                if target:
                    add(relative, target, "test_imports" if is_test else "imports", relative, node.lineno, "python_import")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"__import__", "eval", "exec"}:
                unresolved.append({"kind": "dynamic_python_relation", "path": relative, "line": node.lineno})
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"import_module", "getattr"}:
                unresolved.append({"kind": "dynamic_dispatch", "path": relative, "line": node.lineno})

    # Preserve explicit command-to-handler relationships when argparse dispatch
    # is represented by a literal command comparison in the same script.
    for relative, tree in parsed.items():
        if not relative.startswith("scripts/"):
            continue
        local_defs = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for node in ast.walk(tree):
            if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
                continue
            test = node.test
            if not (isinstance(test.left, ast.Attribute) and test.left.attr == "command" and isinstance(test.left.value, ast.Name) and test.left.value.id == "args"):
                continue
            command = next((part.value for part in test.comparators if isinstance(part, ast.Constant) and isinstance(part.value, str)), None)
            if not command:
                continue
            for nested in ast.walk(node):
                if isinstance(nested, ast.Call) and isinstance(nested.func, ast.Name) and nested.func.id in local_defs:
                    add(f"{relative}#command:{command}", f"{relative}#{nested.func.id}", "dispatches_to", relative, nested.lineno, "literal_cli_dispatch")

    placement_path = root / "config/documentation-placement.yaml"
    if placement_path.is_file():
        try:
            placement_text = placement_path.read_text(encoding="utf-8", errors="replace")
            placement = yaml.safe_load(placement_text) or {}
        except (OSError, yaml.YAMLError):
            placement = {}
            unresolved.append({"kind": "documentation_registry_unreadable", "path": "config/documentation-placement.yaml"})
        for rule in placement.get("placement_rules") or []:
            if not isinstance(rule, dict):
                continue
            docs = rule.get("placements") or {}
            for trigger in rule.get("triggers") or []:
                trigger = str(trigger)
                if trigger not in seeds:
                    continue
                for doc_path in docs:
                    doc_path = str(doc_path)
                    line = next((i for i, value in enumerate(placement_text.splitlines(), 1) if trigger in value), 1)
                    add(trigger, doc_path, "documented_by", "config/documentation-placement.yaml", line, "documentation_placement_registry")

    def endpoint_path(value: str) -> str:
        return value.split("#", 1)[0]

    selected = [
        item for item in candidates.values()
        if endpoint_path(item["from"]) in seeds or endpoint_path(item["to"]) in seeds
    ]
    selected.sort(key=lambda item: (item["from"], item["to"], item["relation"], item["provenance"]["path"], item["provenance"]["line"]))
    truncated = file_truncated or len(selected) > max_candidates
    selected = selected[: max(1, min(max_candidates, 300))]
    return {
        "status": "TRUNCATED" if truncated else "CANDIDATES_ONLY",
        "seed_paths": seeds,
        "scanned_python_files": len(files),
        "candidates": selected,
        "candidate_count": len(selected),
        "unresolved": sorted(
            (item for item in unresolved if item.get("path") in seeds),
            key=lambda item: (item.get("path", ""), int(item.get("line", 0)), item["kind"]),
        ),
        "global_coverage": {"api": "partial", "data": "partial", "events": "partial", "consumers": "unknown"},
        "canonical_graph_written": False,
    }


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
