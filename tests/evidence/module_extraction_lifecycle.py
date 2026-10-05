#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import project_intelligence as project_facade  # noqa: E402
import project_intelligence_impact_graph as project_impl  # noqa: E402
import repository_health as health_facade  # noqa: E402
import repository_health_conformance as health_impl  # noqa: E402
import retrieval_intelligence as retrieval_facade  # noqa: E402
import retrieval_structural_graph as retrieval_impl  # noqa: E402


def main() -> int:
    assert project_facade.traverse_architecture_impact_graph is project_impl.traverse_architecture_impact_graph
    assert health_facade.run_scenario_conformance is health_impl.run_scenario_conformance
    assert retrieval_facade.structural_relation_boosts is retrieval_impl.structural_relation_boosts
    for function in (
        project_facade.traverse_architecture_impact_graph,
        health_facade.run_scenario_conformance,
        retrieval_facade.structural_relation_boosts,
    ):
        assert callable(function)
    print("INTERNAL MODULE EXTRACTION FACADE LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
