"""Generate and verify deterministic Runtime Context invariant coverage."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/runtime-invariants.yaml"


def build_matrix(config: dict[str, Any]) -> list[dict[str, str]]:
    dimensions = config.get("dimensions")
    if not isinstance(dimensions, dict) or not dimensions:
        raise ValueError("runtime invariant dimensions must be a non-empty mapping")
    names = sorted(dimensions)
    if any(not isinstance(dimensions[name], list) or not dimensions[name] for name in names):
        raise ValueError("every runtime invariant dimension must have values")
    rows = [dict(zip(names, values, strict=True)) for values in itertools.product(*(dimensions[name] for name in names))]
    if len(rows) > config.get("policy", {}).get("maximum_cases", 128):
        raise ValueError("runtime invariant matrix exceeds maximum_cases")
    if len({tuple(row[name] for name in names) for row in rows}) != len(rows):
        raise ValueError("runtime invariant matrix contains duplicate cases")
    for high_risk in config.get("high_risk_combinations", []):
        if high_risk not in rows:
            raise ValueError(f"high-risk combination is outside the matrix: {high_risk}")
    return rows


def pair_coverage(rows: list[dict[str, str]]) -> set[tuple[str, str, str, str]]:
    if not rows:
        return set()
    dimensions = sorted(rows[0])
    coverage: set[tuple[str, str, str, str]] = set()
    for row in rows:
        for left, right in itertools.combinations(dimensions, 2):
            coverage.add((left, row[left], right, row[right]))
    return coverage


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify bounds, uniqueness, and full pair coverage")
    parser.add_argument("--json", action="store_true", help="Print case matrix as JSON")
    args = parser.parse_args()
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    rows = build_matrix(config)
    dimensions = config["dimensions"]
    expected_pairs = sum(len(dimensions[left]) * len(dimensions[right]) for left, right in itertools.combinations(sorted(dimensions), 2))
    coverage = pair_coverage(rows)
    if len(coverage) != expected_pairs:
        raise SystemExit(f"runtime matrix pair coverage incomplete: {len(coverage)}/{expected_pairs}")
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if args.json:
        print(json.dumps({"version": 1, "case_count": len(rows), "pair_count": len(coverage), "sha256": digest, "cases": rows}, indent=2, sort_keys=True))
    else:
        print(f"runtime invariant matrix: PASS cases={len(rows)} pairs={len(coverage)} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
