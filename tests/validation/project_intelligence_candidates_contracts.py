from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from project_intelligence import impact_candidates
from project_intelligence_impact_graph import generate_relation_candidates


def main() -> int:
    errors: list[str] = []
    root = Path(__file__).resolve().parents[2]
    result = impact_candidates(root, ["scripts/project_intelligence_impact_graph.py"], max_files=1, max_candidates=1)
    if result.get("canonical_graph_written") is not False:
        errors.append("candidate generation must not write the canonical Impact Graph")
    if result.get("global_coverage") != {"api": "partial", "data": "partial", "events": "partial", "consumers": "unknown"}:
        errors.append("global coverage must remain partial/unknown")
    if not isinstance(result.get("candidates"), list) or not isinstance(result.get("unresolved"), list):
        errors.append("candidate and unresolved outputs must remain explicit lists")
    if impact_candidates.__name__ != "impact_candidates" or generate_relation_candidates.__name__ != "generate_relation_candidates":
        errors.append("public facade and implementation entry points must remain available")
    if result.get("status") not in {"CANDIDATES_ONLY", "TRUNCATED"}:
        errors.append("candidate command must report a non-canonical candidate status")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: Project Intelligence relation candidate contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
