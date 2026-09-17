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
sys.path.insert(0, str(ROOT / "scripts"))
from governance_guard import fingerprint  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(args: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, env=env, capture_output=True, text=True)


def json_run(args: list[str], env: dict[str, str]) -> dict:
    result = run(args, env=env)
    require(result.returncode == 0, f"command failed: {args}: {result.stdout} {result.stderr}")
    return json.loads(result.stdout)


def git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, capture_output=True, text=True)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        project = base / "project"
        config = base / "config"
        home = base / "home"
        project.mkdir()
        home.mkdir()
        (project / ".ai").mkdir()
        (project / "docs").mkdir()
        (project / "main.py").write_text("print('ok')\n", encoding="utf-8")
        target = project / "docs" / "PROJECT_RULES.md"
        original_target = "# Project Rules\n\nExisting rule.\n"
        promoted_target = "# Project Rules\n\nExisting rule.\n\n## Architecture invariant\n\nDomain dependencies point inward.\n"
        target.write_text(original_target, encoding="utf-8")

        git(project, "init", "-q")
        git(project, "branch", "-m", "main")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Evidence")
        git(project, "add", "main.py", "docs/PROJECT_RULES.md")
        git(project, "commit", "-qm", "baseline")

        env = dict(os.environ)
        env["HOME"] = str(home)
        env["XDG_CONFIG_HOME"] = str(config)

        boot = json_run([
            sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json",
        ], env)
        store = Path(boot["store"])
        intel_path = store / "PROJECT_INTELLIGENCE.yaml"
        intel = load_yaml(intel_path)
        topic_rel = "topics/architecture-invariant.md"
        topic_path = store / topic_rel
        topic_path.parent.mkdir(parents=True, exist_ok=True)
        topic_path.write_text("Domain dependencies point inward.\n", encoding="utf-8")
        intel.setdefault("topics", {})["architecture-invariant"] = {
            "path": topic_rel,
            "type": "INTERPRETATION",
            "confidence": "high",
            "evidence": ["src-repeat-confirmation-1", "src-repeat-confirmation-2"],
            "watch": ["src/**"],
        }
        write_yaml(intel_path, intel)

        proposed = json_run([
            sys.executable, str(PI), "promotion-propose",
            "--project", str(project),
            "--topic", "architecture-invariant",
            "--target", "docs/PROJECT_RULES.md",
            "--text", promoted_target,
            "--format", "json",
        ], env)
        proposal_path = Path(proposed["proposal"])
        proposal = load_yaml(proposal_path)
        require(proposal.get("status") == "PROPOSED", "promotion must begin as PROPOSED")
        require(proposal.get("fingerprint") == proposed.get("fingerprint"), "proposal fingerprint mismatch")
        require(target.read_text(encoding="utf-8") == original_target, "proposal must not mutate authoritative source")
        require(topic_path.exists(), "proposal must not remove derived topic")

        no_approval = run([
            sys.executable, str(PI), "promotion-apply",
            "--project", str(project), "--proposal", str(proposal_path), "--format", "json",
        ], env=env)
        require(no_approval.returncode != 0, "promotion without approval must fail")
        require(target.read_text(encoding="utf-8") == original_target, "failed approval must not mutate target")
        require(topic_path.exists(), "failed approval must preserve derived topic")

        binding = proposal["binding"]
        expected_scope = {
            "branch": binding["branch"],
            "candidate_commit": binding["candidate_commit"],
            "files": [binding["target"]],
            "boundaries": [f"project-intelligence:{binding['topic']}"],
            "operations": ["project_intelligence_promotion"],
            "proposal_fingerprint": proposal["fingerprint"],
            "topic": binding["topic"],
            "target": binding["target"],
        }
        approval = {
            "version": 1,
            "approval": {
                "id": "APR-PI-054",
                "type": "PROJECT_INTELLIGENCE_PROMOTION",
                "status": "APPROVED",
                "approved_by": "fixture-user",
                "approved_at": "2026-09-17T00:00:00+00:00",
            },
            "proposal": {"fingerprint": proposal["fingerprint"]},
            "scope": {**expected_scope, "fingerprint": fingerprint(expected_scope)},
            "evidence": {"validation": ["repeated confirmation"], "unresolved": []},
            "metadata": {"created_at": "2026-09-17T00:00:00+00:00", "updated_at": "2026-09-17T00:00:00+00:00"},
        }
        approval_path = store / "promotions" / "APPROVAL.yaml"
        write_yaml(approval_path, approval)

        target.write_text("# Project Rules\n\nConcurrent user edit.\n", encoding="utf-8")
        drifted = run([
            sys.executable, str(PI), "promotion-apply",
            "--project", str(project), "--proposal", str(proposal_path),
            "--approval", str(approval_path), "--format", "json",
        ], env=env)
        require(drifted.returncode != 0, "target drift must block promotion")
        require("Concurrent user edit" in target.read_text(encoding="utf-8"), "target drift must be preserved")
        require(topic_path.exists(), "target drift must preserve derived topic")

        target.write_text(original_target, encoding="utf-8")
        applied = json_run([
            sys.executable, str(PI), "promotion-apply",
            "--project", str(project), "--proposal", str(proposal_path),
            "--approval", str(approval_path), "--format", "json",
        ], env)
        require(applied.get("status") == "PROMOTED", "approved promotion did not complete")
        require(target.read_text(encoding="utf-8") == promoted_target, "authoritative target content mismatch")

        registry = load_yaml(store / "SOURCE_REGISTRY.yaml")
        registered = [s for s in (registry.get("sources") or []) if s.get("path") == "docs/PROJECT_RULES.md"]
        require(len(registered) == 1, "authoritative target must be registered exactly once")
        require(registered[0].get("authority") == "official_document", "promoted docs target authority mismatch")
        require(registered[0].get("content_duplicated") is False, "authoritative source must remain pointer-over-copy")

        promoted_intel = load_yaml(intel_path)
        promoted_topic = (promoted_intel.get("topics") or {}).get("architecture-invariant") or {}
        require(promoted_topic.get("type") == "AUTHORITATIVE_POINTER", "derived topic must become authoritative pointer")
        require(promoted_topic.get("authoritative_source") == "docs/PROJECT_RULES.md", "pointer target mismatch")
        require(promoted_topic.get("content_duplicated") is False, "promoted PI topic must not duplicate authoritative content")
        require(not topic_path.exists(), "duplicate derived topic content must be removed")

        final_proposal = load_yaml(proposal_path)
        require(final_proposal.get("status") == "PROMOTED", "proposal must record PROMOTED state")
        require("content" not in final_proposal, "promoted proposal must not retain duplicate authoritative content")
        require(final_proposal.get("authoritative_source") == "docs/PROJECT_RULES.md", "proposal pointer missing")

    print("project_intelligence_promotion_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
