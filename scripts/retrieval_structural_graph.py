from __future__ import annotations

import sqlite3
from typing import Any


def structural_relation_boosts(
    conn: sqlite3.Connection,
    symbol_map: dict[int, tuple[float, list[str]]],
    terms: list[str],
    fts_available: bool,
    *,
    max_bridges: int,
    max_identifiers_per_bridge: int,
    max_target_definitions: int,
    max_test_chunks: int,
    identifier_re: Any,
    is_test_path: Any,
    companion_test_key: Any,
) -> tuple[dict[int, tuple[float, list[str]]], dict[str, Any]]:
    """Build a bounded, index-backed exact-identifier two-hop relation graph.

    This remains a trial lane. It seeds only from exact query symbols, uses the
    lexical index (or a bounded LIKE fallback) to discover bridge chunks, then
    resolves identifiers in those bridges through the indexed symbol table.
    """
    seed_rows: list[sqlite3.Row] = []
    exact_terms = set(terms)
    for chunk_id, (boost, _) in symbol_map.items():
        if boost < 0.9:
            continue
        for row in conn.execute(
            "SELECT name, path, chunk_id FROM symbols WHERE chunk_id = ?",
            (chunk_id,),
        ).fetchall():
            if str(row["name"]).lower() in exact_terms:
                seed_rows.append(row)

    stats: dict[str, Any] = {
        "seed_symbols": 0,
        "bridge_chunks": 0,
        "target_definitions": 0,
        "test_chunks_scanned": 0,
        "truncated": False,
        "limits": {
            "bridges": max_bridges,
            "identifiers_per_bridge": max_identifiers_per_bridge,
            "target_definitions": max_target_definitions,
            "test_chunks": max_test_chunks,
        },
    }
    if not seed_rows:
        return {}, stats

    seed_names = {str(row["name"]) for row in seed_rows}
    seed_paths = {str(row["path"]) for row in seed_rows}
    stats["seed_symbols"] = len(seed_names)

    boosts: dict[int, tuple[float, list[str]]] = {}
    structural_paths: dict[str, str] = {}

    def add_boost(chunk_id: int, value: float, reason: str) -> None:
        old_value, old_reasons = boosts.get(chunk_id, (0.0, []))
        boosts[chunk_id] = (
            max(old_value, value),
            list(dict.fromkeys([*old_reasons, reason])),
        )

    bridges: dict[int, sqlite3.Row] = {}
    for seed_name in sorted(seed_names):
        remaining = max_bridges - len(bridges)
        if remaining <= 0:
            stats["truncated"] = True
            break

        rows: list[sqlite3.Row] = []
        if fts_available:
            try:
                rows = conn.execute(
                    """
                    SELECT c.id, c.path, c.text
                    FROM chunks_fts
                    JOIN chunks c ON c.id = chunks_fts.rowid
                    WHERE chunks_fts MATCH ?
                    LIMIT ?
                    """,
                    (f'"{seed_name}"', remaining + 1),
                ).fetchall()
            except sqlite3.OperationalError:
                rows = []

        if not rows:
            rows = conn.execute(
                "SELECT id, path, text FROM chunks WHERE instr(text, ?) > 0 LIMIT ?",
                (seed_name, remaining + 1),
            ).fetchall()

        for row in rows:
            if len(bridges) >= max_bridges:
                stats["truncated"] = True
                break
            source_path = str(row["path"])
            if source_path in seed_paths:
                continue
            tokens = set(identifier_re.findall(str(row["text"])))
            if seed_name not in tokens:
                continue
            bridges[int(row["id"])] = row

    stats["bridge_chunks"] = len(bridges)
    target_ids: set[int] = set()

    for bridge_id, chunk in sorted(bridges.items()):
        source_path = str(chunk["path"])
        tokens = sorted(set(identifier_re.findall(str(chunk["text"]))))
        if len(tokens) > max_identifiers_per_bridge:
            tokens = tokens[:max_identifiers_per_bridge]
            stats["truncated"] = True

        matched_seeds = sorted(seed_names & set(tokens))
        if not matched_seeds:
            continue

        add_boost(
            bridge_id,
            0.62,
            "structural_reference_to_seed:" + ",".join(matched_seeds),
        )
        structural_paths[source_path] = "bridge"

        if not tokens:
            continue
        placeholders = ",".join("?" for _ in tokens)
        target_rows = conn.execute(
            f"SELECT name, path, chunk_id FROM symbols "
            f"WHERE chunk_id IS NOT NULL AND name IN ({placeholders})",
            tuple(tokens),
        ).fetchall()

        by_name: dict[str, list[sqlite3.Row]] = {}
        for target in target_rows:
            by_name.setdefault(str(target["name"]), []).append(target)

        for token in tokens:
            targets = by_name.get(token) or []
            if not targets or len(targets) > 4:
                continue
            for target in targets:
                target_path = str(target["path"])
                target_chunk = target["chunk_id"]
                if target_chunk is None:
                    continue
                target_id = int(target_chunk)
                if target_path == source_path or target_path in seed_paths:
                    continue
                if target_id not in target_ids and len(target_ids) >= max_target_definitions:
                    stats["truncated"] = True
                    continue
                target_ids.add(target_id)
                add_boost(
                    target_id,
                    0.58,
                    f"structural_two_hop:{matched_seeds[0]}->{source_path}->{token}",
                )
                if not is_test_path(target_path):
                    structural_paths[target_path] = "target"

    stats["target_definitions"] = len(target_ids)

    companion_keys = {
        companion_test_key(path): path
        for path in structural_paths
        if not is_test_path(path) and companion_test_key(path)
    }
    if companion_keys:
        test_rows = conn.execute(
            "SELECT id, path FROM chunks WHERE kind = 'test' LIMIT ?",
            (max_test_chunks + 1,),
        ).fetchall()
        if len(test_rows) > max_test_chunks:
            stats["truncated"] = True
            test_rows = test_rows[:max_test_chunks]
        stats["test_chunks_scanned"] = len(test_rows)
        for chunk in test_rows:
            path = str(chunk["path"])
            key = companion_test_key(path)
            if key in companion_keys:
                add_boost(
                    int(chunk["id"]),
                    0.52,
                    f"structural_companion_test:{companion_keys[key]}",
                )

    return boosts, stats
