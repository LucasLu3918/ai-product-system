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
PI = ROOT / "scripts" / "project_intelligence.py"
CLI = ROOT / "bin" / "aips"


def run(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, env=env, capture_output=True, text=True)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, capture_output=True, text=True)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        project = base / "project"
        home = base / "home"
        config = base / "config"
        project.mkdir()
        home.mkdir()
        (project / "AGENTS.md").write_text("# Rules\nPreserve domain boundaries.\n", encoding="utf-8")
        (project / "main.py").write_text("print('fixture')\n", encoding="utf-8")
        git(project, "init", "-q")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Test")
        git(project, "add", "AGENTS.md", "main.py")
        git(project, "commit", "-qm", "initial")

        env = dict(os.environ)
        env["HOME"] = str(home)
        env["XDG_CONFIG_HOME"] = str(config)

        first = run([sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"], env)
        require(first.returncode == 0, f"initial bootstrap failed: {first.stdout} {first.stderr}")
        store = Path(json.loads(first.stdout)["store"])
        overrides_path = store / "PROJECT_OVERRIDES.yaml"
        overrides = load_yaml(overrides_path)
        approved = {
            "id": "architecture.domain_boundary",
            "value": "isolated-domain",
            "approved_by": "project-owner",
            "evidence": ["AGENTS.md"],
        }
        overrides["approved_inferences"] = [approved]
        overrides["additional_rules"] = [{"id": "testing.minimum", "value": "characterization-first"}]
        overrides_path.write_text(yaml.safe_dump(overrides, sort_keys=False), encoding="utf-8")

        (project / "docs").mkdir()
        (project / "docs" / "architecture.md").write_text("New scan evidence for fixture.\n", encoding="utf-8")
        git(project, "add", "docs/architecture.md")
        git(project, "commit", "-qm", "new discovery evidence")

        second = run([sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"], env)
        require(second.returncode == 0, f"refresh bootstrap failed: {second.stdout} {second.stderr}")
        after_refresh = load_yaml(overrides_path)
        require(after_refresh.get("approved_inferences") == [approved], "refresh must preserve approved inference")
        require((after_refresh.get("additional_rules") or [])[0].get("value") == "characterization-first", "refresh must preserve additional rule")

        discovery_path = store / "DISCOVERY.yaml"
        discovery = load_yaml(discovery_path)
        discovery["inferences"] = [{
            "id": "architecture.domain_boundary",
            "value": "shared-domain",
            "type": "INTERPRETATION",
            "confidence": "high",
            "evidence": ["docs/architecture.md"],
        }]
        discovery_path.write_text(yaml.safe_dump(discovery, sort_keys=False), encoding="utf-8")

        reconcile = run([sys.executable, str(PI), "reconcile-overrides", "--project", str(project), "--format", "json"], env)
        require(reconcile.returncode == 0, f"reconcile failed: {reconcile.stdout} {reconcile.stderr}")
        result = json.loads(reconcile.stdout)
        require(result.get("active_conflicts") == 1, "contradictory discovery must create one active conflict")

        reconciled = load_yaml(overrides_path)
        require(reconciled.get("approved_inferences") == [approved], "reconciliation must not overwrite approved inference")
        conflicts = reconciled.get("conflicts") or []
        require(len(conflicts) == 1, "conflict must persist in PROJECT_OVERRIDES")
        conflict = conflicts[0]
        require(conflict.get("type") == "override_discovery_contradiction", "wrong conflict type")
        require(conflict.get("approved_value") == "isolated-domain", "approved value must remain visible")
        require(conflict.get("discovered_value") == "shared-domain", "discovered contradiction must remain visible")
        require(conflict.get("evidence") == ["docs/architecture.md"], "conflict evidence must be retained")

        again = run(["bash", str(CLI), "intelligence", "reconcile-overrides", "--project", str(project), "--format", "json"], env)
        require(again.returncode == 0, f"CLI idempotent reconciliation failed: {again.stdout} {again.stderr}")
        again_doc = json.loads(again.stdout)
        require(again_doc.get("new_conflicts") == 0, "second reconciliation must report zero new conflicts")
        require(len(load_yaml(overrides_path).get("conflicts") or []) == 1, "reconciliation must not duplicate same conflict")

        context = run([
            sys.executable, str(PI), "context", "--project", str(project), "--runtime", "codex",
            "--prompt", "modify API handler", "--format", "json", "--explain",
        ], env)
        require(context.returncode == 0, f"context failed: {context.stdout} {context.stderr}")
        context_doc = json.loads(context.stdout)
        surfaced = (context_doc.get("context") or {}).get("authority_conflicts") or []
        require(len(surfaced) == 1, "active authority conflict must surface in turn context")
        fail_reasons = (context_doc.get("fail_policy") or {}).get("reasons") or []
        require("unresolved_authority_conflict" in fail_reasons, "mutation must fail closed on unresolved authority conflict")

    print("project_override_reconciliation_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
