#!/usr/bin/env python3
"""Exercise OpenAPI validation, non-network references, and contract evidence binding."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import openapi_contracts as contracts


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


valid = ROOT / "tests/fixtures/openapi_phase2_valid.yaml"
invalid = ROOT / "tests/fixtures/openapi_phase2_invalid.yaml"
network_ref = ROOT / "tests/fixtures/openapi_phase2_network_ref.yaml"
result = contracts.validate_spec(valid, ROOT)
require(result["status"] == "PASS" and result["openapi_version"] == "3.1.0", "valid OpenAPI fixture must validate")
local_ref = ROOT / "tests/fixtures/openapi_phase2_local_ref.yaml"
local_target = ROOT / "tests/fixtures/openapi_phase2_local_target.yaml"
local_target.write_text("responses:\n  ok:\n    description: Local response\n", encoding="utf-8")
local_ref.write_text(
    "openapi: 3.1.0\ninfo:\n  title: Local ref fixture\n  version: '1'\npaths:\n  /x:\n    get:\n      operationId: getX\n      responses:\n        '200':\n          $ref: openapi_phase2_local_target.yaml#/responses/ok\n",
    encoding="utf-8",
)
try:
    require(contracts.validate_spec(local_ref, ROOT)["status"] == "PASS", "repository-local references should resolve")
finally:
    local_ref.unlink(missing_ok=True)
    local_target.unlink(missing_ok=True)
valid_doc = contracts.load_yaml(valid)
for version in ("3.0.3", "3.2.0"):
    alternate = ROOT / "tests/fixtures" / f"openapi_phase2_{version.replace('.', '_')}.yaml"
    alternate_doc = dict(valid_doc)
    alternate_doc["openapi"] = version
    alternate.write_text(__import__("yaml").safe_dump(alternate_doc, sort_keys=False), encoding="utf-8")
    try:
        require(contracts.validate_spec(alternate, ROOT)["openapi_version"] == version, f"OpenAPI {version} should validate")
    finally:
        alternate.unlink(missing_ok=True)
try:
    contracts.validate_spec(invalid, ROOT)
except contracts.ContractError:
    pass
else:
    raise AssertionError("invalid OpenAPI fixture must fail validation")
try:
    contracts.validate_spec(network_ref, ROOT)
except contracts.ContractError as exc:
    require("network" in str(exc), "network reference rejection must be explicit")
else:
    raise AssertionError("network references must be rejected without fetching")

with tempfile.TemporaryDirectory(prefix="aips-openapi-ref-", dir=ROOT) as temp_name:
    link = ROOT / "tests/fixtures/openapi_phase2_escape.yaml"
    link.write_text("openapi: 3.1.0\ninfo:\n  title: Ref boundary\n  version: 1\npaths:\n  /x:\n    get:\n      responses:\n        '200':\n          $ref: ../../../../etc/passwd\n", encoding="utf-8")
    try:
        try:
            contracts.validate_spec(link, ROOT)
        except contracts.ContractError as exc:
            require("escapes" in str(exc), "path traversal rejection must be explicit")
        else:
            raise AssertionError("path traversal references must be rejected")
    finally:
        link.unlink(missing_ok=True)

with tempfile.TemporaryDirectory(prefix="aips-openapi-outside-") as temp_name:
    outside = Path(temp_name) / "outside.yaml"
    outside.write_text("safe: true\n", encoding="utf-8")
    link = ROOT / "tests/fixtures/openapi_phase2_external_link.yaml"
    link.symlink_to(outside)
    ref_doc = ROOT / "tests/fixtures/openapi_phase2_symlink_ref.yaml"
    ref_doc.write_text("openapi: 3.1.0\ninfo:\n  title: Ref boundary\n  version: 1\npaths:\n  /x:\n    get:\n      responses:\n        '200':\n          $ref: openapi_phase2_external_link.yaml#/value\n", encoding="utf-8")
    try:
        try:
            contracts.validate_spec(ref_doc, ROOT)
        except contracts.ContractError as exc:
            require("escapes" in str(exc), "symlink escape rejection must be explicit")
        else:
            raise AssertionError("symlink references outside the root must be rejected")
    finally:
        ref_doc.unlink(missing_ok=True)
        link.unlink(missing_ok=True)

cli = [sys.executable, str(ROOT / "scripts/openapi_contracts.py"), "compare", str(valid), str(valid),
       "--baseline-authority", "canonical", "--repo-root", str(ROOT)]
comparison = subprocess.run(cli, cwd=ROOT, check=False, capture_output=True, text=True, timeout=30)
require(comparison.returncode == 0 and json.loads(comparison.stdout)["status"] == "NO_CHANGE",
        "canonical baseline CLI comparison should return NO_CHANGE")
blocked = subprocess.run(cli[:-4] + ["--baseline-authority", "descriptive", "--repo-root", str(ROOT)],
                         cwd=ROOT, check=False, capture_output=True, text=True, timeout=30)
require(blocked.returncode == 2 and json.loads(blocked.stdout)["status"] == "BLOCKED",
        "non-canonical baseline must be blocked")

with tempfile.TemporaryDirectory(prefix="aips-openapi-evidence-", dir=ROOT) as temp_name:
    report = Path(temp_name) / "junit.xml"
    evidence = Path(temp_name) / "evidence.json"
    script = "import os,pathlib; pathlib.Path(os.environ['AIPS_JUNIT_XML']).write_text('<testsuite tests=\"1\"><testcase classname=\"api.listWidgets\" name=\"returns_widgets\"/></testsuite>', encoding='utf-8')"
    command = [sys.executable, "-c", script]
    args = type("Args", (), {
        "repo_root": ROOT,
        "spec": valid,
        "command": json.dumps(command),
        "junit": report,
        "timeout": 10,
        "output": evidence,
    })()
    require(contracts._run(args) == 0, "successful JUnit test command should produce PASS evidence")
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    require(payload["status"] == "PASS", "evidence status must be PASS")
    require(payload["repository_revision"] == contracts.git_revision(ROOT), "evidence must bind current Git revision")
    require(payload["junit"]["sha256"].startswith("sha256:"), "JUnit digest must be bound")
    require(payload["operation_coverage"]["covered"] == ["listWidgets"], "operation coverage must be explicit")
    require(payload["raw_output_persisted"] is False, "raw command output must not be persisted")
    freshness = contracts.verify_evidence(evidence, ROOT)
    require(freshness["status"] == "PASS", "fresh test evidence must verify")
    report.write_text("<testsuite tests='1'><testcase name='modified'/></testsuite>", encoding="utf-8")
    stale = contracts.verify_evidence(evidence, ROOT)
    require(stale["status"] == "STALE" and any("junit:content_digest_changed" in reason for reason in stale["stale_reasons"]),
            "changed JUnit must invalidate evidence")

with tempfile.TemporaryDirectory(prefix="aips-openapi-stale-evidence-", dir=ROOT) as temp_name:
    project = Path(temp_name) / "product"
    project.mkdir()
    (project / "api").mkdir()
    (project / "evidence").mkdir()
    spec = project / "api/openapi.yaml"
    spec.write_bytes(valid.read_bytes())
    (project / "README.md").write_text("fixture\n", encoding="utf-8")

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=project, check=True, capture_output=True, text=True)

    git("init", "-q")
    git("config", "user.email", "aips-test")
    git("config", "user.name", "AIPS Test")
    git("add", ".")
    git("commit", "-qm", "evidence baseline")
    junit_path = project / "evidence/contract-tests.xml"
    evidence_path = project / "evidence/openapi-evidence.json"
    script = "import os,pathlib; pathlib.Path(os.environ['AIPS_JUNIT_XML']).write_text('<testsuite tests=\"1\"><testcase classname=\"api.listWidgets\" name=\"returns_widgets\"/></testsuite>', encoding='utf-8')"
    args = type("Args", (), {
        "repo_root": project,
        "spec": spec,
        "command": json.dumps([sys.executable, "-c", script]),
        "junit": junit_path,
        "timeout": 10,
        "output": evidence_path,
    })()
    require(contracts._run(args) == 0, "isolated candidate should produce current evidence")
    require(contracts.verify_evidence(evidence_path, project)["status"] == "PASS",
            "evidence must pass on its exact fixture revision")

    original_spec = spec.read_bytes()
    spec.write_bytes(original_spec + b"\n# changed contract fixture\n")
    stale_spec = contracts.verify_evidence(evidence_path, project)
    require(stale_spec["status"] == "STALE" and "spec:content_digest_changed" in stale_spec["stale_reasons"],
            "changed OpenAPI content must invalidate evidence")
    spec.write_bytes(original_spec)

    (project / "README.md").write_text("new candidate revision\n", encoding="utf-8")
    git("add", "README.md")
    git("commit", "-qm", "advance candidate")
    stale_revision = contracts.verify_evidence(evidence_path, project)
    require(stale_revision["status"] == "STALE" and "repository_revision_changed" in stale_revision["stale_reasons"],
            "a new candidate revision must invalidate otherwise unchanged evidence")
    junit_path.unlink()
    require(contracts._run(args) == 0, "evidence must be regenerable after candidate changes")
    recovered = contracts.verify_evidence(evidence_path, project)
    require(recovered["status"] == "PASS", "fresh evidence must restore PASS on the current revision")

duplicate = ROOT / "tests/fixtures/openapi_phase2_duplicate_key.yaml"
duplicate.write_text("openapi: 3.1.0\ninfo:\n  title: First\n  title: Second\n", encoding="utf-8")
try:
    try:
        contracts.load_yaml(duplicate)
    except contracts.ContractError as exc:
        require("duplicate YAML key" in str(exc), "duplicate keys must be diagnosed")
    else:
        raise AssertionError("duplicate YAML keys must be rejected")
finally:
    duplicate.unlink(missing_ok=True)

print("OpenAPI lifecycle PASS: validity, offline ref policy, operation coverage, exact revision and JUnit digest binding.")
