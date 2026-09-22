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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, env=env, capture_output=True, text=True)


def json_run(args: list[str], env: dict[str, str]) -> dict:
    result = run(args, env)
    require(result.returncode == 0, f"command failed: {args}: {result.stdout} {result.stderr}")
    return json.loads(result.stdout)


def git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, capture_output=True, text=True)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        home = base / "home"
        config = base / "config"
        project = base / "project"
        home.mkdir()
        project.mkdir()
        (project / ".ai").mkdir()
        (project / "src").mkdir()
        (project / "src" / "api.py").write_text("def error_response():\n    return {'error': 'stable'}\n", encoding="utf-8")
        (project / "README.md").write_text("# Promotion fixture\n", encoding="utf-8")
        git(project, "init", "-q")
        git(project, "branch", "-m", "main")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Evidence")
        git(project, "add", "-A")
        git(project, "commit", "-qm", "baseline")

        env = dict(os.environ)
        env["HOME"] = str(home)
        env["XDG_CONFIG_HOME"] = str(config)
        boot = json_run([sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"], env)
        store = Path(boot["store"])
        intel_path = store / "PROJECT_INTELLIGENCE.yaml"
        overrides_path = store / "PROJECT_OVERRIDES.yaml"
        registry_path = store / "SOURCE_REGISTRY.yaml"

        topic_rel = "topics/api-error-contract.md"
        topic_path = store / topic_rel
        topic_path.parent.mkdir(parents=True, exist_ok=True)
        derived_content = "# API Error Contract\n\nAll public API errors use the stable envelope `{error: string}`.\n"
        topic_path.write_text(derived_content, encoding="utf-8")
        intel = load_yaml(intel_path)
        intel.setdefault("topics", {})["api-error-contract"] = {
            "path": topic_rel,
            "type": "OBSERVED_CONVENTION",
            "confidence": "high",
            "evidence": ["src/api.py", "review:api-contract-1", "review:api-contract-2"],
            "watch": ["src/api.py"],
            "promotion": {"confirmations": ["review:api-contract-1", "review:api-contract-2"]},
        }
        intel_path.write_text(yaml.safe_dump(intel, sort_keys=False), encoding="utf-8")

        target = "docs/API_ERROR_RULE.md"
        plan = json_run([
            sys.executable, str(PI), "promotion-plan", "--project", str(project),
            "--topic", "api-error-contract", "--format", "json",
        ], env)
        require(plan.get("status") == "RECOMMENDED", "repeated confirmed invariant must be recommended for promotion")
        require(plan.get("approval_required") is True, "promotion recommendation must require approval")
        require(plan.get("mutation_performed") is False, "promotion plan must remain non-mutating")
        require(not (project / target).exists(), "promotion plan must not create authoritative source")
        require(topic_path.exists(), "promotion plan must preserve derived content")

        denied = run([
            sys.executable, str(PI), "promotion-apply", "--project", str(project),
            "--topic", "api-error-contract", "--target", target,
            "--approval-id", "PROMOTE-API-001", "--format", "json",
        ], env)
        require(denied.returncode != 0, "promotion without approval must fail")
        require("Matching APPROVED promotion approval" in denied.stderr, "missing approval failure must be explicit")
        require(not (project / target).exists(), "failed promotion must not mutate authoritative project files")
        require(topic_path.exists(), "failed promotion must preserve derived content")

        overrides = load_yaml(overrides_path)
        overrides["promotion_approvals"] = [{
            "id": "PROMOTE-API-001",
            "topic": "api-error-contract",
            "target": target,
            "status": "APPROVED",
            "approved_by": "fixture-human",
            "approved_at": "2026-09-17T00:00:00Z",
        }]
        overrides_path.write_text(yaml.safe_dump(overrides, sort_keys=False), encoding="utf-8")

        applied = json_run([
            sys.executable, str(PI), "promotion-apply", "--project", str(project),
            "--topic", "api-error-contract", "--target", target,
            "--approval-id", "PROMOTE-API-001", "--format", "json",
        ], env)
        require(applied.get("status") == "PROMOTED", "approved promotion must succeed")
        require(applied.get("content_duplicated") is False, "promotion must report pointer-over-copy deduplication")
        authoritative = project / target
        require(authoritative.read_text(encoding="utf-8") == derived_content, "authoritative source must receive approved derived rule content")
        require(not topic_path.exists(), "duplicate derived content must be removed after promotion")

        registry = load_yaml(registry_path)
        promoted_sources = [item for item in registry.get("sources") or [] if item.get("path") == target]
        require(len(promoted_sources) == 1, "promoted authoritative source must be registered exactly once")
        source = promoted_sources[0]
        require(source.get("authority") == "official_document", "docs promotion must register official_document authority")
        require(source.get("content_duplicated") is False, "SOURCE_REGISTRY must retain pointer-over-copy deduplication")
        require(source.get("promoted_from") == "api-error-contract", "promotion provenance must be registered")

        intel = load_yaml(intel_path)
        topic = (intel.get("topics") or {}).get("api-error-contract") or {}
        require("path" not in topic, "promoted topic must not keep a duplicate derived content path")
        pointer = topic.get("authoritative_pointer") or {}
        require(pointer.get("path") == target, "promoted topic must become authoritative pointer")
        require(topic.get("content_duplicated") is False, "promoted PI topic must explicitly remain non-duplicated")
        require((topic.get("promotion") or {}).get("status") == "PROMOTED", "promotion status must be durable")

        overrides = load_yaml(overrides_path)
        approval = (overrides.get("promotion_approvals") or [])[0]
        require(approval.get("status") == "APPLIED", "approval record must transition to APPLIED")
        require(approval.get("source_id") == source.get("id"), "approval record must link authoritative source")

        ctx = json_run([
            sys.executable, str(PI), "context", "--project", str(project),
            "--runtime", "claude-code", "--prompt", "Explain the API error contract.", "--format", "json",
        ], env)
        require(str(authoritative.resolve()) in ((ctx.get("context") or {}).get("project_native") or []), "promoted source must enter authoritative project context")

    print("project_intelligence_promotion_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
