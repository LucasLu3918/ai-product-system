#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/project_intelligence.py"
CLI = ROOT / "bin/aips"


def run(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, env=env)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        project = base / "project"
        project.mkdir()
        (project / ".ai").mkdir()
        (project / "AGENTS.md").write_text("# Project instructions\nPreserve approved architecture decisions.\n", encoding="utf-8")
        (project / "main.py").write_text("print('ok')\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        subprocess.run(["git", "config", "user.email", "aips@example.invalid"], cwd=project, check=True)
        subprocess.run(["git", "config", "user.name", "AIPS Test"], cwd=project, check=True)
        subprocess.run(["git", "add", "AGENTS.md", "main.py"], cwd=project, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=project, check=True)

        env = dict(os.environ)
        env["HOME"] = str(base / "home")
        env["XDG_CONFIG_HOME"] = str(base / "config")
        (base / "home").mkdir()

        boot = run([sys.executable, str(SCRIPT), "bootstrap", "--project", str(project), "--format", "json"], env)
        check(boot.returncode == 0, f"bootstrap failed: {boot.stdout} {boot.stderr}")

        store = project / ".ai" / "intelligence"
        overrides_path = store / "PROJECT_OVERRIDES.yaml"
        intel_path = store / "PROJECT_INTELLIGENCE.yaml"
        overrides = {
            "version": 2,
            "approved_inferences": [{
                "id": "INF-ORDERS",
                "subject": "architecture.orders.persistence",
                "scope": "project",
                "value": "repository",
                "reason": "confirmed",
            }],
            "additional_rules": [{
                "id": "RULE-PAYMENTS",
                "subject": "architecture.payments.layering",
                "scope": "project",
                "value": "application-before-infrastructure",
                "reason": "project policy",
            }],
            "exceptions": [{
                "id": "EX-LEGACY",
                "subject": "architecture.legacy-payment.layering",
                "scope": "legacy/payment",
                "value": "direct-access-allowed",
                "reason": "migration exception",
            }],
            "excluded_inferences": [{
                "id": "EXCLUDE-FRAMEWORK",
                "subject": "architecture.framework",
                "scope": "project",
                "value": "active-record",
                "reason": "explicitly rejected",
            }],
            "conflicts": [{
                "id": "manual-existing",
                "status": "OPEN",
                "kind": "MANUAL_REVIEW",
                "subject": "manual.subject",
            }],
        }
        overrides_path.write_text(yaml.safe_dump(overrides, sort_keys=False), encoding="utf-8")
        protected_keys = ("approved_inferences", "additional_rules", "exceptions", "excluded_inferences")
        protected_before = {key: overrides[key] for key in protected_keys}

        candidates = base / "discoveries.yaml"
        candidates.write_text(yaml.safe_dump({
            "version": 1,
            "discoveries": [
                {"id": "D-ORDERS", "subject": "architecture.orders.persistence", "scope": "project", "value": "repository", "type": "FACT", "evidence": ["main.py"]},
                {"id": "D-PAYMENTS", "subject": "architecture.payments.layering", "scope": "project", "value": "handler-direct-db", "type": "OBSERVED_CONVENTION", "confidence": "high", "evidence": ["main.py"]},
                {"id": "D-LEGACY", "subject": "architecture.legacy-payment.layering", "scope": "legacy/payment/handler", "value": "strict-clean-architecture", "type": "INTERPRETATION", "confidence": "medium", "evidence": ["main.py"]},
                {"id": "D-FRAMEWORK", "subject": "architecture.framework", "scope": "project", "value": "active-record", "type": "OBSERVED_CONVENTION", "confidence": "medium", "evidence": ["main.py"]},
                {"id": "D-NEW", "subject": "architecture.new-derived-fact", "scope": "project", "value": {"enabled": True}, "type": "FACT", "evidence": ["main.py"]},
            ],
        }, sort_keys=False), encoding="utf-8")

        first = run(["bash", str(CLI), "intelligence", "reconcile", "--project", str(project), "--discoveries", str(candidates), "--format", "json"], env)
        check(first.returncode == 0, f"reconcile failed: {first.stdout} {first.stderr}")
        first_doc = json.loads(first.stdout)
        check(first_doc["status"] == "CONFLICT", "contradictory discovery must report CONFLICT")
        check(first_doc["conflicts"] == 3, "expected three override conflicts")
        check(first_doc["aligned"] == 1, "expected one aligned approved inference")
        check(first_doc["accepted"] == 1, "expected one unmatched derived candidate")

        after = load_yaml(overrides_path)
        for key in protected_keys:
            check(after[key] == protected_before[key], f"{key} was overwritten during reconciliation")
        managed = [c for c in after["conflicts"] if c.get("managed_by") == "aips_project_intelligence_reconcile"]
        check(len(managed) == 3, "managed conflicts were not persisted")
        check(any(c.get("id") == "manual-existing" for c in after["conflicts"]), "manual conflict must be preserved")
        serialized_managed = yaml.safe_dump(managed, sort_keys=False)
        check("handler-direct-db" not in serialized_managed, "raw discovered values must not be duplicated into conflict records")
        check("strict-clean-architecture" not in serialized_managed, "raw discovered values must not be duplicated into conflict records")

        intel = load_yaml(intel_path)
        intel_managed = [c for c in intel.get("conflicts", []) if c.get("managed_by") == "aips_project_intelligence_reconcile"]
        check([c["id"] for c in intel_managed] == [c["id"] for c in managed], "Project Intelligence conflict view must match overrides")

        review = store / "reviews" / "PROJECT_INTELLIGENCE_REVIEW.html"
        check("architecture.payments.layering" in review.read_text(encoding="utf-8"), "review must surface reconciliation conflict subjects")

        second = run([sys.executable, str(SCRIPT), "reconcile", "--project", str(project), "--discoveries", str(candidates), "--format", "json"], env)
        check(second.returncode == 0, f"idempotent reconcile failed: {second.stdout} {second.stderr}")
        second_doc = json.loads(second.stdout)
        check(second_doc["conflict_ids"] == first_doc["conflict_ids"], "conflict IDs must be deterministic")
        second_overrides = load_yaml(overrides_path)
        check(len([c for c in second_overrides["conflicts"] if c.get("managed_by") == "aips_project_intelligence_reconcile"]) == 3, "reconciliation must not duplicate managed conflicts")

        candidates.write_text(yaml.safe_dump({
            "version": 1,
            "discoveries": [
                {"id": "D-ORDERS", "subject": "architecture.orders.persistence", "scope": "project", "value": "repository", "type": "FACT", "evidence": ["main.py"]},
                {"id": "D-PAYMENTS", "subject": "architecture.payments.layering", "scope": "project", "value": "application-before-infrastructure", "type": "OBSERVED_CONVENTION", "confidence": "high", "evidence": ["main.py"]},
                {"id": "D-LEGACY", "subject": "architecture.legacy-payment.layering", "scope": "legacy/payment/handler", "value": "direct-access-allowed", "type": "INTERPRETATION", "confidence": "medium", "evidence": ["main.py"]},
                {"id": "D-NEW", "subject": "architecture.new-derived-fact", "scope": "project", "value": {"enabled": True}, "type": "FACT", "evidence": ["main.py"]},
            ],
        }, sort_keys=False), encoding="utf-8")
        resolved = run([sys.executable, str(SCRIPT), "reconcile", "--project", str(project), "--discoveries", str(candidates), "--format", "json"], env)
        check(resolved.returncode == 0, f"resolved reconcile failed: {resolved.stdout} {resolved.stderr}")
        resolved_doc = json.loads(resolved.stdout)
        check(resolved_doc["status"] == "ALIGNED", "resolved candidate set must clear managed conflicts")
        final_overrides = load_yaml(overrides_path)
        for key in protected_keys:
            check(final_overrides[key] == protected_before[key], f"{key} changed after conflict resolution")
        check([c for c in final_overrides["conflicts"] if c.get("managed_by") == "aips_project_intelligence_reconcile"] == [], "stale managed conflicts should clear when evidence aligns")
        check(any(c.get("id") == "manual-existing" for c in final_overrides["conflicts"]), "manual conflict must survive managed conflict cleanup")

    print("project override reconciliation lifecycle: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
