"""Regression evidence for Plan27 extensions; fixtures never claim real inference."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import struct
import sys
import tempfile
import zlib
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import agent_eval
import character_artifacts
import character_asset_validation
import creative_execution
import creative_quality_benchmark
import creative_trace
import opencode_native_guard
import opencode_skill_projection
import opencode_trace
import project_diagnostics
import project_intelligence
import project_intelligence_discovery
import project_intelligence_impact_graph
import retrieval_intelligence
import retrieval_query_terms
from performance_evidence import observed_distribution
from validation_observation import summarize_timings


def main() -> int:
    for facade, implementation, names in (
        (project_intelligence, project_intelligence_discovery, ("sha", "file_hash", "safe_walk", "discover_sources", "inventory", "seed_impact_graph")),
        (retrieval_intelligence, retrieval_query_terms, ("query_terms", "semantic_alias_expansion", "fts_expression")),
        (creative_execution, creative_trace, ("trace_path", "read_trace", "record_trace")),
        (character_artifacts, character_asset_validation, ("ArtifactError", "inspect_asset", "_validate_svg_bytes", "sha256_file")),
    ):
        for name in names:
            assert getattr(facade, name) is getattr(implementation, name), name
    assert project_intelligence.sha("台灣") == hashlib.sha256("台灣".encode()).hexdigest()
    assert retrieval_intelligence.query_terms("Graph GRAPH 圖像 x _API") == ["graph", "圖像", "_api"]
    assert retrieval_intelligence.fts_expression(['a"b', "中文", "!"]) == '"ab" OR "中文"'
    assert retrieval_intelligence.extract_symbols("fixture.py", "execute()\ndef execute():\n    execute()\n") == [("execute", "function", 2)]
    assert observed_distribution([]) == {"status": "UNKNOWN", "sample_count": 0, "invalid_count": 0, "p50": None, "p95": None}
    assert observed_distribution([1, 2, 3, True, float("nan"), float("inf"), -1])["p95"] == 3
    assert observed_distribution([1, 2, 3, True, float("nan"), float("inf"), -1])["invalid_count"] == 4
    records = [{"pull_request": 1, "head_sha": "a" * 40, "change_class": "core", "timestamp": "2026-10-10T00:00:00Z",
                "evidence_complete": True, "full_validation_run": True, "measurements": {"repository_duration_ms": 100}}]
    records.append({**records[0], "timestamp": "2026-10-10T00:01:00Z", "measurements": {"repository_duration_ms": 120}})
    records.append({**records[0], "pull_request": 2, "evidence_complete": False})
    stats = summarize_timings(records)
    assert stats["candidate_count"] == 1 and stats["by_change_class"]["core"]["p50"] == 120
    assert stats["selective_execution_authorized"] is False
    assert summarize_timings([])["status"] == "UNKNOWN"
    assert opencode_native_guard.tool_effect_boundary("mcp_custom_write")["enforcement"] == "UNSUPPORTED"
    assert opencode_native_guard.tool_effect_boundary("shell")["effect"] == "unknown"
    assert opencode_native_guard.evaluate_write(tool="mcp_custom_write", resources=[], root=".", manifest={})["decision"] == "UNSUPPORTED"

    with tempfile.TemporaryDirectory(prefix="aips-plan27-") as temporary:
        root = Path(temporary)
        project = root / "project"
        project.mkdir()
        (project / "scripts").mkdir()
        (project / "scripts/a.py").write_text("import b\n")
        (project / "scripts/b.py").write_text("from c import work\n")
        (project / "scripts/c.py").write_text("def work(): return 1\n")
        (project / "scripts/facade.py").write_text("import c as _c\nwork = _c.work\n")
        assert retrieval_intelligence._local_import_target(project, "scripts/facade.py", "work") == ("local", "work", "scripts/c.py")
        (project / "scripts/caller.py").write_text("import facade as f\ndef caller(): return f.work()\n")
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("CREATE TABLE symbols(name TEXT, path TEXT, line INTEGER)")
        connection.execute("INSERT INTO symbols VALUES ('work', 'scripts/c.py', 1)")
        targets, error, external = retrieval_intelligence._resolve_call_target(project, connection, "scripts/caller.py", "work")
        assert len(targets) == 1 and targets[0]["path"] == "scripts/c.py" and error is None and external is False
        connection.close()
        one = project_intelligence_impact_graph.generate_relation_candidates(project, ["scripts/a.py"])
        three = project_intelligence_impact_graph.generate_relation_candidates(project, ["scripts/a.py"], max_depth=3)
        assert len(one["candidates"]) == 1 and len(three["candidates"]) == 3
        assert all(row["confidence"] == "candidate" and row["review_status"] == "unreviewed" for row in three["candidates"])
        assert three["canonical_graph_written"] is False
        for seed in ("../outside.py", "/outside.py"):
            try:
                project_intelligence_impact_graph.generate_relation_candidates(project, [seed])
            except ValueError:
                pass
            else:
                raise AssertionError("escaping seed accepted")
        missing = project_diagnostics._intelligence_check({"exists": False}, None, project)
        plan = project_diagnostics.recovery_plan([missing])
        assert plan["execution_authorized"] is False
        assert [step["action"] for step in plan["steps"]] == ["bootstrap", "complete_required_topics", "finalize", "verify"]
        assert plan["steps"][2]["depends_on"] == [plan["steps"][1]["id"]]
        assert plan["steps"][0]["authorization"] == "APPROVED_TASK_SCOPE_REQUIRED"
        assert not (project / ".ai").exists()

        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(root / "config"), "XDG_STATE_HOME": str(root / "state")}):
            assert opencode_skill_projection.native_acceptance("2.0.24")["status"] == "UNVERIFIED"
            report = {"schema_version": 1, "version": "2.0.24", "platform": sys.platform,
                      "plugin_sha256": hashlib.sha256((ROOT / "harness/adapters/opencode/plugin.ts").read_bytes()).hexdigest(),
                      "acceptance_sha256": hashlib.sha256((ROOT / "tests/evidence/opencode_native_acceptance.py").read_bytes()).hexdigest(),
                      "runtime_source_sha256": opencode_skill_projection.native_source_digest(),
                      "checks": {"context_delivery": "VERIFIED", "permission_hook_execution": "VERIFIED", "creative_prepare": "VERIFIED_NATIVE_HOST",
                                 "admission_revocation": "VERIFIED_NATIVE_HOST", "l3_external_actions": "UNVERIFIED", "session_cancel": "UNVERIFIED", "instruction_model_delivery": "UNVERIFIED"}}
            path = opencode_skill_projection.state_root() / "native-acceptance.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(report))
            assert opencode_skill_projection.native_acceptance("2.0.24")["status"] == "RECORDED"
            assert opencode_skill_projection.native_acceptance("2.0.25")["reason_code"] == "acceptance_stale"
            report["checks"]["permission_hook_execution"] = "FAIL"
            path.write_text(json.dumps(report))
            assert opencode_skill_projection.native_acceptance("2.0.24")["status"] == "FAILED"
            report["checks"]["permission_hook_execution"] = "invented"
            path.write_text(json.dumps(report))
            assert opencode_skill_projection.native_acceptance("2.0.24")["reason_code"] == "acceptance_invalid"
            creative_execution.record_trace({"at": "2026-10-10T00:00:00Z", "provider": "comfyui_local", "operation": "generate",
                                             "status": "COMPLETE", "reason_code": "fixture", "attempts": 1, "elapsed_ms": 12})
            summary = creative_trace.read_trace()["observed_metrics"]
            assert summary["complete"] == 1 and summary["human_visual_quality"] == "UNVERIFIED"
            creative_execution.record_trace({"prompt": "must not persist"})
            assert "must not persist" not in creative_trace.trace_path().read_text()
        digest_root = root / "digest-source"
        for relative in ("harness/adapters/opencode/plugin.ts", "harness/adapters/opencode/AGENTS.md", "harness/BOOTSTRAP.md", "SYSTEM_CORE.md", "VERSION"):
            file = digest_root / relative; file.parent.mkdir(parents=True, exist_ok=True); file.write_text("fixture")
        (digest_root / "config").mkdir()
        outside = root / "outside.yaml"; outside.write_text("must not read outside source")
        (digest_root / "config/escape.yaml").symlink_to(outside)
        with patch.object(opencode_skill_projection, "ROOT", digest_root):
            try:
                opencode_skill_projection.native_source_digest()
            except ValueError:
                pass
            else:
                raise AssertionError("source binding followed an escaping symlink")
        trace = root / "context.jsonl"
        trace.write_text(json.dumps({"runtime": "opencode", "event": "context", "status": "delivered", "context_bytes": 100, "context_command_ms": 12}) + "\n")
        metrics = opencode_trace.read_events(trace, 20)["observed_metrics"]
        assert metrics["context_bytes"]["p50"] == 100 and metrics["model_usage_status"] == "UNKNOWN"
        quality = creative_quality_benchmark.summarize_trials(project, {"version": 1, "trials": []})
        assert quality["status"] == "UNKNOWN"
        assert all(row["status"] == "UNVERIFIED" for row in quality["visual_dimensions"].values())
        invalid = creative_quality_benchmark.summarize_trials(project, {"version": 1, "trials": [{"source": "fixture"}, {"source": "observed_host", "provider": "external"}]})
        assert invalid["artifact_bound_samples"] == 0 and invalid["invalid_or_unobserved"] == 2
        provider = {"base_url": "http://127.0.0.1:8188", "workflow": {"1": {"inputs": {}}, "2": {"inputs": {}},
                    "3": {"inputs": {}}, "4": {"inputs": {}}}, "prompt_id": "1", "latent_node_id": "2",
                    "sampler_node_id": "3", "save_nodes": ["4"]}
        calls = []
        def timeout_request(url: str, **kwargs) -> bytes:
            calls.append((url, kwargs.get("data")))
            if url.endswith("/prompt"):
                return b'{"prompt_id":"owned-job"}'
            assert url.endswith("/queue") and json.loads(kwargs["data"]) == {"delete": ["owned-job"]}
            return b'{}'
        with patch.object(creative_execution, "local_request", side_effect=timeout_request), patch.object(creative_execution.time, "monotonic", side_effect=[0, 2]):
            try:
                creative_execution.comfy_execute({"prompt": "fixture", "operation": "generate"}, provider, root / "never.png", 1)
            except creative_execution.Blocked as exc:
                assert exc.reason_code == "comfy_job_recovery_required"
            else:
                raise AssertionError("accepted job timeout permitted resubmission")
        assert len(calls) == 2 and not (root / "never.png").exists()
        calls.clear()
        def polling_request(url: str, **kwargs) -> bytes:
            if "/history/" in url:
                raise creative_execution.TransientProviderError("fixture polling failure")
            return timeout_request(url, **kwargs)
        with patch.object(creative_execution, "local_request", side_effect=polling_request), patch.object(creative_execution.time, "monotonic", return_value=0):
            try:
                creative_execution.comfy_execute({"prompt": "fixture", "operation": "generate"}, provider, root / "never.png", 1)
            except creative_execution.Blocked as exc:
                assert exc.reason_code == "comfy_job_recovery_required"
            else:
                raise AssertionError("accepted polling failure permitted resubmission")
        assert len([url for url, _ in calls if url.endswith("/prompt")]) == 1
        assert not any(url.endswith("/interrupt") for url, _ in calls)
        output = project / "fixture.png"
        def chunk(kind: bytes, data: bytes) -> bytes:
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        output.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 64, 64, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress((b"\0" + b"\0\xff\0" * 64) * 64)) + chunk(b"IEND", b""))
        trial = {"source": "observed_host", "provider": "comfyui_local", "model_revision": "fixture-only",
                 "device": "fixture-only", "output": "fixture.png", "sha256": "sha256:" + hashlib.sha256(output.read_bytes()).hexdigest(),
                 "elapsed_ms": 12, "visual_review": {"reviewer_type": "human", "reviewer": "fixture",
                 "dimensions": {"composition": "REVISE"}}, "user_acceptance": "NOT_RECORDED"}
        checked = creative_quality_benchmark.summarize_trials(project, {"version": 1, "trials": [trial]})
        assert checked["artifact_bound_samples"] == 1 and checked["elapsed_ms"]["p50"] == 12
        assert checked["visual_dimensions"]["composition"]["revise"] == 1
        assert checked["runtime_attestation"] == "UNVERIFIED" and checked["user_acceptance_status"] == "NOT_RECORDED"
        assert checked["visual_dimensions"]["character_identity"]["status"] == "UNVERIFIED"
        trial["sha256"] = "sha256:" + "0" * 64
        assert creative_quality_benchmark.summarize_trials(project, {"version": 1, "trials": [trial]})["artifact_bound_samples"] == 0

        cases = root / "cases"; cases.mkdir()
        results = root / "results"; results.mkdir()
        report = agent_eval.analyze(cases, results)
        assert report["observed_task_outcomes"]["status"] == "UNKNOWN"
        assert report["observed_task_outcomes"]["completed"] is None
        case = {"version": 1, "id": "fixture-task", "scenario_id": "002", "input": {"prompt": "fixture only"},
                "system_dependencies": ["scripts/agent_eval.py"], "rubric": {}}
        (cases / "fixture.yaml").write_text(yaml.safe_dump(case))
        result = {"version": 1, "case_id": case["id"], "scenario_id": "002", "case_fingerprint": agent_eval.fingerprint(case),
                  "execution": {"provider": "fixture", "model": "fixture", "runtime": "fixture", "executed_at": "2026-10-10T00:00:00Z",
                                "system_fingerprint": agent_eval.system_fingerprint(case),
                                "task_observation": {"source": "observed_host", "task_completed": False, "human_corrections": 2, "false_positives": 1}},
                  "response": {}}
        (results / "fixture.yaml").write_text(yaml.safe_dump(result))
        outcome = agent_eval.analyze(cases, results)["observed_task_outcomes"]
        assert outcome["status"] == "RECORDED" and outcome["completed"] == 0 and outcome["human_corrections"] == 2
        result["case_fingerprint"] = "sha256:" + "0" * 64
        (results / "fixture.yaml").write_text(yaml.safe_dump(result))
        assert agent_eval.analyze(cases, results)["observed_task_outcomes"]["status"] == "UNKNOWN"

    tasks = yaml.safe_load((ROOT / "templates/conformance/AGENT_TASK_BENCHMARK.yaml").read_text())
    assert {task["domain"] for task in tasks["tasks"]} == {"coding", "creative", "planning", "security"}
    for task in tasks["tasks"]:
        assert (ROOT / task["case"]).is_file()
    print("PLAN27 LIFECYCLE PASS: compatibility, bounded impact, recovery, native freshness, privacy and evidence distinctions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
