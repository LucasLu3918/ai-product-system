#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import evolution_analysis as evolution_facade
import evolution_preanalysis as evolution_impl
import project_intelligence as project_facade
import project_intelligence_impact_graph as project_impl
import project_intelligence_temporal as project_temporal_impl
import publish_post_merge as publish_post_merge_impl
import publish_preflight as publish_facade
import repository_health as health_facade
import repository_health_conformance as health_impl
import retrieval_intelligence as retrieval_facade
import retrieval_storage as retrieval_storage_impl
import retrieval_structural_graph as retrieval_impl


def main() -> int:
    assert project_facade.traverse_architecture_impact_graph is project_impl.traverse_architecture_impact_graph
    assert project_facade.temporal_query is project_temporal_impl.temporal_query
    assert publish_facade.PreflightError is publish_post_merge_impl.PreflightError
    assert callable(publish_facade.post_merge)
    assert callable(publish_facade.sync_installed)
    assert health_facade.run_scenario_conformance is health_impl.run_scenario_conformance
    assert retrieval_facade.structural_relation_boosts is retrieval_impl.structural_relation_boosts
    for name in ("open_db", "open_read_db", "metadata_get", "metadata_set"):
        assert getattr(retrieval_facade, name) is getattr(retrieval_storage_impl, name), name
    for name in (
        "PREANALYSIS_START",
        "PREANALYSIS_END",
        "canonical_digest",
        "evidence_digest",
        "utc_now",
        "_normalized_rule_text",
        "_title_tokens",
        "validate_local_preanalysis_config",
        "_near_duplicate_membership",
        "_build_review_queue",
        "build_local_preanalysis",
        "validate_local_preanalysis",
        "preanalysis_markdown",
        "extract_preanalysis",
    ):
        assert getattr(evolution_facade, name) is getattr(evolution_impl, name), name
    for function in (
        project_facade.traverse_architecture_impact_graph,
        project_facade.temporal_query,
        publish_facade.post_merge,
        publish_facade.sync_installed,
        health_facade.run_scenario_conformance,
        retrieval_facade.structural_relation_boosts,
        retrieval_facade.open_db,
        retrieval_facade.open_read_db,
        retrieval_facade.metadata_get,
        retrieval_facade.metadata_set,
    ):
        assert callable(function)
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        result = project_facade.temporal_query(base / "no-git-repository", base / "store", "current", None, None, None, None)
        assert result["mode"] == "CURRENT"
        assert result["availability"] == "GIT_HEAD_UNAVAILABLE"
        assert result["assertions"] == []
        assert result["canonical"] == str(base / "store" / "TEMPORAL_ASSERTIONS.yaml")
        assert result["digest"].startswith("sha256:") and len(result["digest"]) == 71
    print("INTERNAL MODULE EXTRACTION FACADE LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
