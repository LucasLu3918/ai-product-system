#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path
import sys
import subprocess


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("project_intelligence", ROOT / "scripts/project_intelligence.py")
PI = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(PI)


def require(test: bool, message: str) -> None:
    if not test:
        raise AssertionError(message)


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "AGENTS.md").write_text("# authoritative source\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "AIPS Evidence"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "aips-evidence.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "AGENTS.md"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "baseline"], check=True)
    store = root / ".aips-test-intelligence"
    store.mkdir()
    PI.intelligence_store = lambda _root, create=False: (store, "EPHEMERAL", "test-project")
    (store / "PROJECT_INTELLIGENCE.yaml").write_text(
        "schema: {version: 3}\nstate: {readiness: READY, freshness: CURRENT}\n"
        "architecture: {summary: 'Deterministic system overview'}\ntopics: {}\n", encoding="utf-8")
    (store / "SOURCE_REGISTRY.yaml").write_text("sources:\n  - path: AGENTS.md\n", encoding="utf-8")
    (store / "PROJECT_OVERRIDES.yaml").write_text("overrides: []\n", encoding="utf-8")
    (store / "TEMPORAL_ASSERTIONS.yaml").write_text("schema: {version: 1}\nassertions: []\n", encoding="utf-8")

    layers = PI.layered_context(root, store, PI.load_yaml(store / "PROJECT_INTELLIGENCE.yaml", {}), {"status": "CURRENT", "estimated_tokens": 4}, [], {"status": "CURRENT", "affected_topics": []})
    require(layers["core"]["canonical"] is False and layers["core"]["derived"] is True,
            "L1 capsule must remain a derived view")
    require(layers["core"]["source_pointers"] == ["AGENTS.md"], "capsule must preserve source pointers")
    require(layers["recall"]["hard_budget_tokens"] == 6000, "Recall hard budget mismatch")
    require(layers["archive"]["on_demand_only"] is True, "archive must load on demand")
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
    reconciled = {
        **approved, "status": "READY",
        "reconciliation": {"status": "RECONCILED", "base_revision": "base", "head_revision": "head", "diff_digest": "sha256:diff", "impact_graph_reviewed": True, "evidence": ["diff-reviewed"]},
    }
    require(PI.validate_impact_document(reconciled)["valid"], "complete post-diff reconciliation should permit READY")

print("layered_context_memory_lifecycle=PASS")
