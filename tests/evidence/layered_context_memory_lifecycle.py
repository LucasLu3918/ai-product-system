#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path
import sys
import subprocess
import json
import hashlib
import math
import sqlite3
from unittest.mock import patch

import yaml


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import retrieval_intelligence as RI
SPEC = importlib.util.spec_from_file_location("project_intelligence", ROOT / "scripts/project_intelligence.py")
PI = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(PI)


def require(test: bool, message: str) -> None:
    if not test:
        raise AssertionError(message)


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory) / "repo"
    root.mkdir()
    (root / "AGENTS.md").write_text("# authoritative source\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "AIPS Evidence"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "aips-evidence.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "AGENTS.md"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "baseline"], check=True)
    store = root.parent / "aips-test-intelligence"
    store.mkdir()
    PI.intelligence_store = lambda _root, create=False: (store, "EPHEMERAL", "test-project")
    (store / "PROJECT_INTELLIGENCE.yaml").write_text(
        "schema: {version: 3}\nstate: {readiness: READY, freshness: CURRENT}\n"
        "architecture: {summary: 'Deterministic system overview'}\ntopics: {}\n", encoding="utf-8")
    (store / "SOURCE_REGISTRY.yaml").write_text("sources:\n  - path: AGENTS.md\n", encoding="utf-8")
    (store / "PROJECT_OVERRIDES.yaml").write_text("overrides: []\n", encoding="utf-8")
    (store / "topics").mkdir()
    (store / "topics/architecture.md").write_text("# architecture\n", encoding="utf-8")
    (store / "topics/testing.md").write_text("# testing\n", encoding="utf-8")
    initial_head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    (store / "TEMPORAL_ASSERTIONS.yaml").write_text(
        yaml.safe_dump({"schema": {"version": 1}, "assertions": [
            {"id": f"assertion-{index}", "subject": "component" * 25, "predicate": "uses" * 25,
             "object": "value" * 25, "quality": "high", "source": "docs/source.md",
             "validity": {"from_revision": initial_head, "to_revision_exclusive": None}}
            for index in range(40)
        ]}), encoding="utf-8")
    intel = PI.load_yaml(store / "PROJECT_INTELLIGENCE.yaml", {})
    intel["topics"] = {
        "architecture": {"path": "topics/architecture.md"},
        "testing": {"path": "topics/testing.md"},
    }

    layers = PI.layered_context(root, store, intel, {"status": "CURRENT", "estimated_tokens": 5000}, [], {"status": "CURRENT", "affected_topics": []})
    require(layers["core"]["canonical"] is False and layers["core"]["derived"] is True,
            "L1 capsule must remain a derived view")
    require(layers["core"]["source_pointers"] == ["AGENTS.md"], "capsule must preserve source pointers")
    require(layers["recall"]["hard_budget_tokens"] == 6000, "Recall hard budget mismatch")
    require(layers["telemetry"]["total_estimated_tokens"] <= layers["telemetry"]["hard_budget_tokens"], "assembled Core + Recall must honor the hard budget")
    require(layers["recall"]["truncated"] is True, "oversized temporal Recall must report truncation")
    require(layers["archive"]["on_demand_only"] is True, "archive must load on demand")

    stale_unknown = PI.layered_context(root, store, intel, {"status": "UNAVAILABLE", "estimated_tokens": 0}, [], {
        "status": "STALE", "affected_topics": ["testing"], "reasons": ["watched_committed_path_changed:tests/example.py"]
    })
    require(stale_unknown["core"]["freshness"] == "STALE", "capsule freshness must use the current scan")
    require(stale_unknown["task_freshness"]["status"] == "STALE" and not stale_unknown["task_freshness"]["irrelevance_proven"],
            "no selected topic cannot prove an unrelated stale store irrelevant")
    unrelated = PI.layered_context(root, store, intel, {"status": "CURRENT", "estimated_tokens": 0},
                                   [str(store / "topics/architecture.md")], {
        "status": "STALE", "affected_topics": ["testing"], "reasons": ["watched_committed_path_changed:tests/example.py"]
    })
    require(unrelated["task_freshness"]["status"] == "CURRENT" and unrelated["task_freshness"]["irrelevance_proven"],
            "mapped unrelated changes may be skipped with explicit proof")
    source_change = PI.layered_context(root, store, intel, {"status": "CURRENT", "estimated_tokens": 0},
                                       [str(store / "topics/architecture.md")], {
        "status": "STALE", "affected_topics": ["source-registry"], "reasons": ["source_changed:AGENTS.md"]
    })
    require(source_change["task_freshness"]["status"] == "STALE", "source-registry changes must never be skipped as unrelated")
    unknown_change = PI.layered_context(root, store, intel, {"status": "CURRENT", "estimated_tokens": 0},
                                        [str(store / "topics/architecture.md")], {
        "status": "STALE", "affected_topics": ["unknown"], "reasons": ["revision_diff_unavailable"]
    })
    require(unknown_change["task_freshness"]["status"] == "STALE", "unmapped changes must fail closed")
    unknown_scan = PI.layered_context(root, store, intel, {"status": "CURRENT", "estimated_tokens": 0},
                                      [str(store / "topics/architecture.md")], {
        "status": "UNKNOWN", "affected_topics": ["unknown"], "reasons": ["revision_diff_unavailable"]
    })
    require(unknown_scan["task_freshness"]["status"] == "UNKNOWN" and not unknown_scan["task_freshness"]["irrelevance_proven"],
            "unknown freshness must never assert irrelevance proof")

    fake_secret = "api_key=" + "Ab1x" + "Cd2y" + "Ef3z" + "Gh4w" + "Ij5v" + "Kl6u"
    intel["architecture"] = {"summary": "contact " + "person" + "@" + "example" + ".invalid " + fake_secret}
    (store / "TEMPORAL_ASSERTIONS.yaml").write_text(yaml.safe_dump({"schema": {"version": 1}, "assertions": [
        {"id": "private-assertion", "subject": "person" + "@" + "example" + ".invalid", "predicate": "uses", "object": fake_secret, "quality": "high",
         "validity": {"from_revision": initial_head, "to_revision_exclusive": None}}
    ]}), encoding="utf-8")
    sanitized = PI.layered_context(root, store, intel, {"status": "CURRENT", "estimated_tokens": 0}, [], {"status": "CURRENT", "affected_topics": []})
    emitted = json.dumps(sanitized, ensure_ascii=False)
    require("[REDACTED]" in emitted and "person" + "@" + "example" + ".invalid" not in emitted and fake_secret.split("=", 1)[1] not in emitted,
            "derived core and temporal text must pass through the Runtime Content Safety Boundary")
    audit = PI.context_audit(root)
    require(audit["read_only"] and not audit["canonical_facts_modified"], "audit must be read-only")

    impact = PI.impact_init(root, "change overview", "test-change")
    impact_doc = PI.load_yaml(Path(impact["path"]), {})
    require(impact_doc["status"] == "DRAFT", "impact-init must start DRAFT")
    require(impact_doc["scope_review"]["status"] == "PENDING", "scope review must start pending")
    require(impact_doc["reconciliation"]["status"] == "PENDING", "reconciliation must start pending")
    bad_ready = {**impact_doc, "status": "READY", "unknowns": []}
    require(not PI.validate_impact_document(bad_ready)["valid"], "READY without reconciliation must fail closed")
    approved = {
        **impact_doc, "status": "IMPLEMENTATION_APPROVED", "unknowns": [],
        "scope_review": {"status": "APPROVED", "approval_reference": "user-authorization", "approved_at": "2026-09-24T00:00:00Z"},
    }
    require(PI.validate_impact_document(approved)["valid"], "approved bounded scope should permit implementation")
    (root / "change.txt").write_text("scoped implementation\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "change.txt"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "implement scoped change"], check=True)
    base = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD^"], check=True, capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    diff = subprocess.run(["git", "-C", str(root), "diff", "--binary", "--no-ext-diff", base, head, "--"], check=True, capture_output=True).stdout
    paths = subprocess.run(["git", "-C", str(root), "diff", "--name-only", "-z", base, head, "--"], check=True, capture_output=True).stdout
    actual_paths = sorted(path.decode() for path in paths.split(b"\0") if path)
    reconciled = {
        **approved, "status": "READY",
        "change": {**approved["change"], "target_paths": actual_paths},
        "reconciliation": {"status": "RECONCILED", "base_revision": base, "head_revision": head,
                           "diff_digest": "sha256:" + hashlib.sha256(diff).hexdigest(), "changed_files": actual_paths,
                           "impact_graph_reviewed": True, "evidence": ["temporary Git diff and Impact Graph reviewed"]},
    }
    require(PI.validate_impact_document(reconciled, root)["valid"], "real clean Git reconciliation should permit READY: " + repr(PI.validate_impact_document(reconciled, root)["errors"]))
    require(not PI.validate_impact_document(reconciled)["valid"], "READY without project Git state must fail closed")
    bad_digest = {**reconciled, "reconciliation": {**reconciled["reconciliation"], "diff_digest": "sha256:" + "0" * 64}}
    require(not PI.validate_impact_document(bad_digest, root)["valid"], "forged diff digest must fail")
    bad_file_set = {**reconciled, "reconciliation": {**reconciled["reconciliation"], "changed_files": ["AGENTS.md"]}}
    require(not PI.validate_impact_document(bad_file_set, root)["valid"], "misreported changed-file set must fail")
    bad_scope = {**reconciled, "change": {**reconciled["change"], "target_paths": ["AGENTS.md"]}}
    require(not PI.validate_impact_document(bad_scope, root)["valid"], "changes outside the declared path scope must fail")
    bad_head = {**reconciled, "reconciliation": {**reconciled["reconciliation"], "head_revision": base}}
    require(not PI.validate_impact_document(bad_head, root)["valid"], "head not equal to checkout must fail")
    impact_path = store / "CHANGE_IMPACT.yaml"
    impact_path.write_text(yaml.safe_dump(reconciled, sort_keys=False), encoding="utf-8")
    cli = subprocess.run([sys.executable, str(ROOT / "scripts/project_intelligence.py"), "impact-validate",
                          "--project", str(root), "--path", str(impact_path), "--format", "json"],
                         capture_output=True, text=True)
    require(cli.returncode == 0 and json.loads(cli.stdout)["valid"], "impact-validate CLI must perform Git-bound READY validation: " + repr((cli.returncode, cli.stdout, cli.stderr)))
    public_cli = subprocess.run([str(ROOT / "bin/aips"), "intelligence", "impact-validate", "--help"],
                                capture_output=True, text=True)
    require(public_cli.returncode == 0 and "--project" in public_cli.stdout and "--path" in public_cli.stdout,
            "documented aips impact-validate command must be routable from the installed CLI")
    require(PI.retrieval_failure_code(PermissionError("Operation not permitted")) == "RETRIEVAL_CACHE_ACCESS_DENIED",
            "cache permission failures need a stable diagnostic code")
    with patch.object(RI, "index_status", return_value={"status": "CURRENT"}), patch.object(
        RI, "open_db", side_effect=sqlite3.OperationalError("unable to open database file")
    ):
        query_diagnostic = RI.query_repository(root, store, "cache diagnostic", refresh=False)
    require(query_diagnostic["status"] == "INDEX_UNAVAILABLE" and query_diagnostic["reason_code"] == "SQLITE_OPEN_FAILED" and query_diagnostic["remediation"],
            "direct retrieval query must return an actionable SQLite open failure")
    with patch.object(RI, "open_db", side_effect=PermissionError("Operation not permitted")):
        index_diagnostic = RI.index_repository(root, store)
    require(index_diagnostic["status"] == "INDEX_UNAVAILABLE" and index_diagnostic["reason_code"] == "RETRIEVAL_CACHE_ACCESS_DENIED",
            "direct index rebuild must report cache access errors instead of a traceback")
    with patch.object(PI, "retrieval_index_status", return_value={"status": "CURRENT"}), patch.object(
        PI, "retrieval_query_repository", side_effect=PermissionError("cache path denied")
    ):
        unavailable = PI.context_manifest(root, "codex", "update the project module")
    retrieval = unavailable["context"]["retrieval"]
    require(retrieval["status"] == "UNAVAILABLE" and retrieval["reason_code"] == "RETRIEVAL_CACHE_ACCESS_DENIED" and retrieval.get("remediation"),
            "context manifest must return actionable privacy-safe cache diagnostics")
    require(str(root / "AGENTS.md") in unavailable["context"]["project_native"],
            "cache failure must retain canonical source-pointer fallback")
    private_email = "person" + "@" + "example" + ".invalid"
    fake_secret = "api_key=" + "Ab1x" + "Cd2y" + "Ef3z" + "Gh4w" + "Ij5v" + "Kl6u"
    with patch.object(PI, "retrieval_index_status", return_value={"status": "CURRENT"}), patch.object(
        PI, "retrieval_query_repository", return_value={"status": "READY", "estimated_tokens": 20,
            "results": [{"type": "code", "path": "src/example.py", "snippet": "contact " + private_email + " " + fake_secret}]}
    ):
        sanitized_retrieval = PI.context_manifest(root, "codex", "summarize project code")["context"]["retrieval"]
    serialized_retrieval = json.dumps(sanitized_retrieval, ensure_ascii=False)
    require(private_email not in serialized_retrieval and fake_secret.split("=", 1)[1] not in serialized_retrieval,
            "retrieval snippets must use the same Runtime Content Safety Boundary")

    hook_spec = importlib.util.spec_from_file_location("turn_context_hook", ROOT / "scripts/turn_context_hook.py")
    hook = importlib.util.module_from_spec(hook_spec)
    assert hook_spec and hook_spec.loader
    hook_spec.loader.exec_module(hook)
    hook_telemetry = {"total_estimated_tokens": 9000, "hard_budget_tokens": 800}
    hook_data = {
        "project": {"root": "/project/" + "x" * 500, "mode": "EPHEMERAL", "intelligence_store": "/cache/store"},
        "task": {"mutation_likely": True}, "requirements": {"targeted_refresh": ["modules"]},
        "intelligence": {"readiness": "READY", "freshness": "STALE"},
        "context": {"layers": {
            "core": {"canonical": False, "source_digest": "sha256:test", "summary": "architecture " * 1200},
            "recall": {"temporal_assertions": [], "truncated": False},
            "telemetry": hook_telemetry,
            "task_freshness": {"status": "STALE"},
        }, "project_native": ["/project/docs/" + "p" * 200 for _ in range(12)], "intelligence_topics": ["/cache/topics/" + "t" * 200 for _ in range(12)],
                   "retrieval": {"status": "UNAVAILABLE", "reason_code": "SQLITE_OPEN_FAILED", "remediation": "Rebuild the cache", "results": []}},
        "fail_policy": {"mode": "closed"},
    }
    compact = hook.compact_context(hook_data)
    require(math.ceil(len(compact) / 4) <= 800 and hook_telemetry["rendered_truncated"],
            "the actual compact hook output must stay under its hard budget and report truncation")
    require("readiness=READY freshness=STALE" in compact and "retrieval_status=UNAVAILABLE" in compact and "retrieval_error=SQLITE_OPEN_FAILED" in compact,
            "budget trimming must retain mandatory status and fallback signals")

print("layered_context_memory_lifecycle=PASS")
