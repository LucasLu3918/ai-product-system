#!/usr/bin/env python3
"""Exercise Phase 3 evidence, ownership and optional Gate policy in small Git fixtures."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from jsonschema import validate as validate_json

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import implementation_enforcement as enforcement
import integration_gate
import openapi_contracts

TEMPLATE = yaml.safe_load((ROOT / "templates/implementation/IMPLEMENTATION_PROFILE.yaml").read_text(encoding="utf-8"))
REPORT_SCHEMA = json.loads((ROOT / "templates/implementation/IMPLEMENTATION_ENFORCEMENT_REPORT.schema.json").read_text(encoding="utf-8"))


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def save_profile(root: Path, profile: dict) -> None:
    (root / "IMPLEMENTATION_PROFILE.yaml").write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")


def new_repo(root: Path, *, quality: bool = False, generated: bool = False) -> tuple[dict, str, str]:
    (root / "src").mkdir()
    (root / "scripts").mkdir()
    (root / "references/languages/go").mkdir(parents=True)
    (root / "references/languages/go/PROFILE.yaml").write_bytes((ROOT / "references/languages/go/PROFILE.yaml").read_bytes())
    (root / "README.md").write_text("Project-native Go rules\n", encoding="utf-8")
    (root / "go.mod").write_text("module example.test/phase3\n\ngo 1.23\n", encoding="utf-8")
    (root / "src/api.go").write_text("package src\n", encoding="utf-8")
    profile = yaml.safe_load(yaml.safe_dump(TEMPLATE))
    profile["status"] = "READY"
    profile["contract"].update({"type": "none", "affects_change": False})
    profile["unresolved"] = []
    profile["enforcement"].update({"mode": "enforce", "scope_paths": ["src/**"],
                                    "language_profile": "references/languages/go/PROFILE.yaml"})
    profile["ownership"]["project_owned"] = [{"path": "src/api.go", "source": "repository", "reference": "README.md"}]
    if quality:
        (root / "scripts/check.py").write_text("print('project check PASS')\n", encoding="utf-8")
        profile["enforcement"]["commands"] = [{"id": "project-check", "argv": ["python3", "scripts/check.py"],
                                                 "source": "scripts/check.py", "timeout_seconds": 3,
                                                 "deterministic": True}]
        profile["quality"]["project_required"] = [{"id": "project-check", "command_id": "project-check",
                                                      "evidence_report": "evidence/project-check.json"}]
    if generated:
        (root / "src/client.go").write_text("package src // generated v1\n", encoding="utf-8")
        (root / "api.json").write_text('{"version":1}\n', encoding="utf-8")
        profile["ownership"]["generated"] = ["src/client.go"]
        profile["enforcement"]["generation_records"] = [{
            "path": "src/client.go", "tool": "fixture-generator", "version": "1",
            "output_sha256": enforcement.digest_file(root / "src/client.go"),
            "inputs": [{"path": "api.json", "sha256": enforcement.digest_file(root / "api.json")}],
        }]
    save_profile(root, profile)
    git(root, "init", "-q")
    git(root, "config", "user.email", "aips-test")
    git(root, "config", "user.name", "AIPS Test")
    git(root, "add", ".")
    git(root, "commit", "-qm", "base")
    base = git(root, "rev-parse", "HEAD")
    (root / "src/api.go").write_text("package src // candidate\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-qm", "candidate")
    return profile, base, git(root, "rev-parse", "HEAD")


with tempfile.TemporaryDirectory(prefix="aips-phase3-") as temporary:
    root = Path(temporary) / "repo"
    root.mkdir()
    profile, base, head = new_repo(root)
    path = root / "IMPLEMENTATION_PROFILE.yaml"
    first = enforcement.inspect_profile(path, root, base, head, mode="enforce")
    second = enforcement.inspect_profile(path, root, base, head, mode="enforce")
    assert first["status"] == "PASS", first
    assert first["fingerprint"] == second["fingerprint"], "same candidate must produce the same report"
    validate_json(first, REPORT_SCHEMA)
    stale = enforcement.inspect_profile(path, root, base, head, mode="enforce",
                                        expected_profile_sha256="sha256:" + "0" * 64)
    assert stale["status"] == "BLOCKED" and any(row["reason"] == "profile_fingerprint_mismatch" for row in stale["checks"])
    report_mode = {"implementation_enforcement": {"mode": "report", "profile_path": "IMPLEMENTATION_PROFILE.yaml",
                                                   "paths": ["src/**"]}}
    row, detail = integration_gate.implementation_enforcement_check(report_mode, ["src/api.go"], root, base, head)
    assert row["status"] == "PASS" and detail["status"] == "PASS", (row, detail)
    row, detail = integration_gate.implementation_enforcement_check(report_mode, ["docs/readme.md"], root, base, head)
    assert row["status"] == "SKIPPED" and detail is None
    enforce_mode = {"implementation_enforcement": {"mode": "enforce", "profile_path": "IMPLEMENTATION_PROFILE.yaml",
                                                    "paths": ["src/**"], "expected_profile_sha256": "sha256:" + "0" * 64}}
    row, detail = integration_gate.implementation_enforcement_check(enforce_mode, ["src/api.go"], root, base, head)
    assert row["status"] == "FAIL" and detail["status"] == "BLOCKED", (row, detail)
    try:
        enforcement.repo_file(root, "../outside")
        raise AssertionError("parent traversal accepted")
    except enforcement.EnforcementError:
        pass
    outside = Path(temporary) / "outside"
    outside.write_text("private", encoding="utf-8")
    (root / "escape").symlink_to(outside)
    try:
        enforcement.repo_file(root, "escape")
        raise AssertionError("symlink escape accepted")
    except enforcement.EnforcementError:
        pass
    profile["enforcement"]["scope_paths"] = ["unrelated/**"]
    save_profile(root, profile)
    git(root, "add", "IMPLEMENTATION_PROFILE.yaml")
    git(root, "commit", "-qm", "narrow profile scope")
    policy = {"implementation_enforcement": {"mode": "enforce", "profile_path": "IMPLEMENTATION_PROFILE.yaml",
                                            "paths": ["src/**"]}}
    row, detail = integration_gate.implementation_enforcement_check(policy, ["src/api.go"], root, base, "HEAD")
    assert row["status"] == "FAIL" and detail["status"] == "SKIPPED", "Gate must reject scope bypass"

with tempfile.TemporaryDirectory(prefix="aips-phase3-unknown-") as temporary:
    root = Path(temporary)
    profile, base, head = new_repo(root)
    profile["ownership"]["project_owned"] = []
    save_profile(root, profile)
    git(root, "add", ".")
    git(root, "commit", "-qm", "unknown ownership")
    result = enforcement.inspect_profile(root / "IMPLEMENTATION_PROFILE.yaml", root, base, "HEAD", mode="enforce")
    assert result["status"] == "BLOCKED" and any(row["reason"] == "ownership_unresolved" for row in result["checks"])

with tempfile.TemporaryDirectory(prefix="aips-phase3-generated-") as temporary:
    root = Path(temporary)
    profile, base, head = new_repo(root, generated=True)
    result = enforcement.inspect_profile(root / "IMPLEMENTATION_PROFILE.yaml", root, base, head, mode="enforce")
    assert result["status"] == "PASS", result
    (root / "src/client.go").write_text("package src // direct edit\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-qm", "edit generated output")
    result = enforcement.inspect_profile(root / "IMPLEMENTATION_PROFILE.yaml", root, base, "HEAD", mode="enforce")
    assert result["status"] == "BLOCKED" and any(row["reason"] == "generation_record_stale" for row in result["checks"])

with tempfile.TemporaryDirectory(prefix="aips-phase3-quality-") as temporary:
    root = Path(temporary)
    profile, base, head = new_repo(root, quality=True)
    path = root / "IMPLEMENTATION_PROFILE.yaml"
    result = enforcement.inspect_profile(path, root, base, head, mode="enforce")
    assert result["status"] == "UNVERIFIED", result
    command_report = enforcement.run_command(path, root, "project-check", 2)
    assert command_report["status"] == "PASS" and len(command_report["runs"]) == 2
    validate_json(command_report, REPORT_SCHEMA)
    (root / "evidence").mkdir()
    evidence = root / "evidence/project-check.json"
    evidence.write_text(json.dumps(command_report), encoding="utf-8")
    result = enforcement.inspect_profile(path, root, base, head, mode="enforce")
    assert result["status"] == "PASS", result
    command_report["status"] = "FAIL"
    evidence.write_text(json.dumps(command_report), encoding="utf-8")
    result = enforcement.inspect_profile(path, root, base, head, mode="enforce")
    assert result["status"] == "FAIL" and any(row["reason"] == "project_command_failed" for row in result["checks"])
    try:
        enforcement.run_command(path, root, "project-check", 1)
        raise AssertionError("single run accepted for deterministic command")
    except enforcement.EnforcementError:
        pass
    (root / "scripts/check.py").write_text("print('changed command')\n", encoding="utf-8")
    git(root, "add", "scripts/check.py")
    git(root, "commit", "-qm", "change project command")
    result = enforcement.inspect_profile(path, root, base, "HEAD", mode="enforce")
    assert result["status"] == "UNVERIFIED" and any(row["reason"] == "command_evidence_stale" for row in result["checks"])

with tempfile.TemporaryDirectory(prefix="aips-phase3-timeout-") as temporary:
    root = Path(temporary)
    profile, base, head = new_repo(root, quality=True)
    (root / "scripts/check.py").write_text("import time\ntime.sleep(2)\n", encoding="utf-8")
    profile["enforcement"]["commands"][0]["timeout_seconds"] = 1
    save_profile(root, profile)
    git(root, "add", ".")
    git(root, "commit", "-qm", "slow project check")
    report = enforcement.run_command(root / "IMPLEMENTATION_PROFILE.yaml", root, "project-check", 2)
    assert report["status"] == "UNVERIFIED" and report["runs"][0]["timed_out"] is True
    profile["enforcement"]["commands"][0]["argv"] = ["sh", "-c", "echo unsafe"]
    save_profile(root, profile)
    git(root, "add", "IMPLEMENTATION_PROFILE.yaml")
    git(root, "commit", "-qm", "inline shell command")
    try:
        enforcement.run_command(root / "IMPLEMENTATION_PROFILE.yaml", root, "project-check", 2)
        raise AssertionError("shell command accepted")
    except enforcement.EnforcementError:
        pass

with tempfile.TemporaryDirectory(prefix="aips-phase3-openapi-") as temporary:
    root = Path(temporary)
    profile, base, head = new_repo(root)
    spec = root / "api.yaml"
    spec.write_text("openapi: 3.0.0\ninfo: {title: Fixture, version: '1'}\npaths:\n  /ping:\n    get:\n      operationId: ping\n      responses:\n        '200': {description: ok}\n", encoding="utf-8")
    profile["contract"].update({"type": "openapi", "source": "api.yaml", "authority": "canonical", "affects_change": True,
                                 "resolution": "confirmed", "evidence": [{"source": "human", "reference": "README.md"}]})
    profile["contract"]["openapi"].update({"validation_status": "PASS", "validation_report": "evidence/openapi-validation.json",
                                             "spec_sha256": enforcement.digest_file(spec)})
    save_profile(root, profile)
    git(root, "add", "api.yaml", "IMPLEMENTATION_PROFILE.yaml")
    git(root, "commit", "-qm", "declare canonical spec")
    validation = openapi_contracts.validate_spec(spec, root)
    (root / "evidence").mkdir()
    (root / "evidence/openapi-validation.json").write_text(json.dumps(validation), encoding="utf-8")
    result = enforcement.inspect_profile(root / "IMPLEMENTATION_PROFILE.yaml", root, base, "HEAD", mode="enforce")
    assert result["status"] == "UNVERIFIED" and any(row["reason"] == "openapi_evidence_missing" for row in result["checks"])
    spec.write_text(spec.read_text(encoding="utf-8") + "# drift\n", encoding="utf-8")
    git(root, "add", "api.yaml")
    git(root, "commit", "-qm", "drift spec")
    result = enforcement.inspect_profile(root / "IMPLEMENTATION_PROFILE.yaml", root, base, "HEAD", mode="enforce")
    assert result["status"] == "BLOCKED" and any(row["reason"] == "openapi_evidence_stale" for row in result["checks"])

print("Implementation Phase 3 lifecycle PASS: exact candidate, ownership, generation, quality, OpenAPI, Gate scope and reproducibility.")
