"""Run the Phase 5 reference product through the real Phase 2/3/4 chain."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import implementation_enforcement as enforcement
import openapi_contracts
import openapi_generator_adapter as generator

SOURCE = ROOT / "examples/openapi-client-pilot"


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, text=True, capture_output=True).stdout.strip()


with tempfile.TemporaryDirectory(prefix="aips-openapi-client-pilot-") as temporary:
    project = Path(temporary) / "product"
    shutil.copytree(SOURCE, project, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (project / "tools/generate_client.py").chmod(0o755)
    git(project, "init", "-q")
    git(project, "config", "user.email", "aips-test")
    git(project, "config", "user.name", "AIPS Test")
    git(project, "add", ".")
    git(project, "commit", "-qm", "reference product baseline")
    base = git(project, "rev-parse", "HEAD")
    evidence = project / "evidence"
    evidence.mkdir()
    spec = project / "api/openapi.json"
    validation = openapi_contracts.validate_spec(spec, project)
    (evidence / "openapi-validation.json").write_text(json.dumps(validation), encoding="utf-8")

    preview = generator.inspect_adapter(project, "IMPLEMENTATION_PROFILE.yaml", "pilot-python")
    assert preview["status"] == "READY" and not (project / "client/generated").exists()
    generated = generator.inspect_adapter(project, "IMPLEMENTATION_PROFILE.yaml", "pilot-python", execute=True)
    assert generated["status"] == "PASS" and generated["determinism_verified"] is True, generated
    (evidence / "generator.json").write_text(json.dumps(generated), encoding="utf-8")
    client = project / "client/generated/client.py"
    assert client.is_file() and generated["outputs"][0]["path"] == "client/generated/client.py"

    # Changed generated sources and Profile are the exact candidate under inspection.
    git(project, "add", "client/generated/client.py", "IMPLEMENTATION_PROFILE.yaml")
    git(project, "commit", "-qm", "generate Widgets client")
    head = git(project, "rev-parse", "HEAD")
    validation = openapi_contracts.validate_spec(spec, project)
    (evidence / "openapi-validation.json").write_text(json.dumps(validation), encoding="utf-8")
    direct = subprocess.run([sys.executable, "verify.py"], cwd=project, check=False,
                            capture_output=True, text=True)
    assert direct.returncode == 0, (direct.stdout, direct.stderr)
    command = [sys.executable, str(ROOT / "scripts/openapi_contracts.py"), "run-contract-tests",
               "api/openapi.json", "--repo-root", str(project), "--command",
               json.dumps([sys.executable, "verify.py"]), "--junit", "evidence/pilot-junit.xml",
               "--output", str(evidence / "openapi-conformance.json")]
    contract_run = subprocess.run(command, cwd=project, check=False, capture_output=True, text=True)
    assert contract_run.returncode == 0, (contract_run.stdout, contract_run.stderr)
    command_report = enforcement.run_command(project / "IMPLEMENTATION_PROFILE.yaml", project,
                                             "pilot-integration", 2)
    assert command_report["status"] == "PASS", command_report
    (evidence / "pilot-command.json").write_text(json.dumps(command_report), encoding="utf-8")

    report = enforcement.inspect_profile(project / "IMPLEMENTATION_PROFILE.yaml", project, base, head,
                                         mode="enforce")
    assert report["status"] == "PASS", report
    assert any(row["id"] == "generator-report-pilot-python" and row["status"] == "PASS"
               for row in report["checks"])

    # A re-fingerprinted stale report still cannot bless unchanged outputs.
    report_path = evidence / "generator.json"
    original = report_path.read_bytes()
    tampered = json.loads(original)
    tampered["candidate_revision"] = "0" * 40
    payload = dict(tampered)
    payload.pop("fingerprint")
    tampered["fingerprint"] = enforcement.canonical_digest(payload)
    report_path.write_text(json.dumps(tampered), encoding="utf-8")
    stale = enforcement.inspect_profile(project / "IMPLEMENTATION_PROFILE.yaml", project, base, head,
                                        mode="enforce")
    assert stale["status"] == "BLOCKED" and any(row["reason"] == "generator_report_missing_or_stale"
                                                  for row in stale["checks"])
    report_path.write_bytes(original)
    report_path.unlink()
    missing = enforcement.inspect_profile(project / "IMPLEMENTATION_PROFILE.yaml", project, base, head,
                                          mode="enforce")
    assert missing["status"] == "BLOCKED" and any(row["id"] == "generator-report-pilot-python"
                                                  and row["status"] == "BLOCKED" for row in missing["checks"])
    report_path.write_bytes(original)

    # Existing generated files are protected from direct edits before replacement.
    old = client.read_bytes()
    client.write_text("# direct edit\n", encoding="utf-8")
    try:
        generator.inspect_adapter(project, "IMPLEMENTATION_PROFILE.yaml", "pilot-python", execute=True)
        raise AssertionError("edited generated client was replaced")
    except generator.AdapterError:
        pass
    client.write_bytes(old)

print("OpenAPI client reference pilot PASS")
