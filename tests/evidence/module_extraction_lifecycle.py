#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import creative_errors as creative_errors_impl
import creative_execution as creative_facade
import creative_prompt_compiler as creative_impl
import evolution_analysis as evolution_facade
import evolution_preanalysis as evolution_impl
import project_intelligence as project_facade
import project_intelligence_context as project_context_impl
import project_intelligence_impact_graph as project_impl
import project_intelligence_promotion as project_promotion_impl
import project_intelligence_storage as project_storage_impl
import project_intelligence_temporal as project_temporal_impl
import publish_post_merge as publish_post_merge_impl
import publish_preflight as publish_facade
import repository_health as health_facade
import repository_health_conformance as health_impl
import retrieval_intelligence as retrieval_facade
import retrieval_storage as retrieval_storage_impl
import retrieval_structural_graph as retrieval_impl


def main() -> int:
    assert creative_facade.compile_creative_prompt is creative_impl.compile_creative_prompt
    assert creative_facade.model_recommendation is creative_impl.model_recommendation
    assert creative_facade.Blocked is creative_errors_impl.Blocked
    try:
        creative_facade.compile_creative_prompt({}, {})
    except creative_errors_impl.Blocked as exc:
        assert exc.reason_code == "compiled_prompt_invalid"
    else:
        raise AssertionError("invalid prompt did not preserve the shared Blocked exception")
    for name in ("atomic_text", "atomic_yaml", "writer_lock"):
        assert getattr(project_facade, name) is getattr(project_storage_impl, name), name
    assert project_facade.traverse_architecture_impact_graph is project_impl.traverse_architecture_impact_graph
    assert project_facade.temporal_query is project_temporal_impl.temporal_query
    assert project_facade.compact_context_manifest is project_context_impl.compact_context_manifest
    assert project_facade.SOURCE_NAMES is project_context_impl.SOURCE_NAMES
    assert project_facade._promotion_candidate is project_promotion_impl.promotion_candidate
    assert publish_facade.PreflightError is publish_post_merge_impl.PreflightError
    assert callable(publish_facade.post_merge)
    assert callable(publish_facade.sync_installed)
    assert health_facade.run_scenario_conformance is health_impl.run_scenario_conformance
    assert project_facade.atomic_text is project_storage_impl.atomic_text
    assert project_facade.atomic_yaml is project_storage_impl.atomic_yaml
    assert project_facade.writer_lock is project_storage_impl.writer_lock
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
        project_facade.compact_context_manifest,
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
        storage = base / "storage"
        text_path = storage / "atomic.txt"
        project_facade.atomic_text(text_path, "atomic evidence\n")
        assert text_path.read_text(encoding="utf-8") == "atomic evidence\n"
        yaml_path = storage / "atomic.yaml"
        project_facade.atomic_yaml(yaml_path, {"status": "PASS"})
        assert yaml.safe_load(yaml_path.read_text(encoding="utf-8")) == {"status": "PASS"}
        with project_facade.writer_lock(storage):
            assert (storage / ".writer.lock").is_file()
            try:
                with project_facade.writer_lock(storage):
                    raise AssertionError("nested writer lock unexpectedly succeeded")
            except RuntimeError as exc:
                assert "writer lock is active" in str(exc)
        assert not (storage / ".writer.lock").exists()
        derived = base / "store" / "topics" / "architecture.md"
        derived.parent.mkdir(parents=True)
        derived.write_text("architecture evidence", encoding="utf-8")
        candidate, candidate_path = project_facade._promotion_candidate(
            base / "store",
            {"topics": {"architecture": {
                "path": "topics/architecture.md",
                "type": "FACT",
                "evidence": [{"source": "tests"}],
                "promotion": {"confirmations": ["reviewer-one", "reviewer-two"]},
            }}},
            "architecture",
        )
        assert candidate_path == derived and candidate["status"] == "RECOMMENDED"
        assert candidate["approval_required"] is True and candidate["mutation_performed"] is False
        assert project_facade._promotion_target(base, "docs/rules.md").is_relative_to(base.resolve())
        try:
            project_facade._promotion_target(base, "../outside.md")
        except RuntimeError:
            pass
        else:
            raise AssertionError("promotion target must remain confined to the project")
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
