#!/usr/bin/env python3
"""Exercise explicit OpenAPI generator preview, apply, ownership and rollback boundaries."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from jsonschema import validate as validate_json

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import implementation_profile_validate as profile_validator
import openapi_generator_adapter as adapter

TEMPLATE = yaml.safe_load((ROOT / "templates/implementation/IMPLEMENTATION_PROFILE.yaml").read_text(encoding="utf-8"))
SCHEMA = json.loads((ROOT / "templates/implementation/GENERATOR_ADAPTER_REPORT.schema.json").read_text(encoding="utf-8"))


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True).stdout.strip()


def make_repo(root: Path, *, mode: str = "safe", timeout: int = 5) -> Path:
    for directory in ("api", "evidence", "tools", "config", "src/generated"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    spec = root / "api/openapi.yaml"
    spec.write_text("openapi: 3.1.0\ninfo:\n  title: Fixture\n  version: '1'\npaths: {}\n", encoding="utf-8")
    (root / "config/generator.yaml").write_text("package: fixture\n", encoding="utf-8")
    executable = root / "tools/fake_generator.py"
    executable.write_text(
        "#!/usr/bin/env python3\n"
        "import argparse, pathlib, sys, time\n"
        "p=argparse.ArgumentParser(); p.add_argument('--version', action='store_true'); p.add_argument('--spec'); p.add_argument('--config'); p.add_argument('--output'); p.add_argument('--mode', default='safe'); a=p.parse_args()\n"
        "if a.version: print('fixture-generator 1.0'); raise SystemExit(0)\n"
        "if a.mode == 'sleep': time.sleep(10)\n"
        "out=pathlib.Path(a.output); out.mkdir(exist_ok=True)\n"
        "if a.mode == 'symlink': (out/'client.go').symlink_to('/etc/passwd')\n"
        "elif a.mode == 'unexpected': (out/'unexpected.txt').write_text('unexpected')\n"
        "else: (out/'client.go').write_text('package client\\n')\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    profile = yaml.safe_load(yaml.safe_dump(TEMPLATE))
    profile["status"] = "READY"
    profile["contract"].update({"source": "api/openapi.yaml", "authority": "canonical", "resolution": "confirmed",
                                "evidence": [{"source": "human", "reference": "fixture"}]})
    profile["contract"]["openapi"].update({"validation_status": "PASS", "validation_report": "evidence/openapi-validation.json",
                                              "spec_sha256": "sha256:" + __import__("hashlib").sha256(spec.read_bytes()).hexdigest()})
    profile["unresolved"] = []
    profile["generation"].update({"enabled": True, "policy": "boundary_only", "adapters": [{
        "id": "fixture", "type": "openapi_client_cli", "spec_path": "api/openapi.yaml",
        "executable": "tools/fake_generator.py", "executable_sha256": adapter.digest_file(executable),
        "version": "fixture-generator 1.0", "version_args": ["--version"],
        "argv": ["--spec", "{spec}", "--config", "{input:config/generator.yaml}", "--output", "{output}", "--mode", mode],
        "tool_inputs": ["config/generator.yaml"], "output_dir": "src/generated/client",
        "output_patterns": ["*.go"], "deterministic": True, "timeout_seconds": timeout,
        "max_files": 10, "max_bytes": 10000,
    }]})
    profile_path = root / "IMPLEMENTATION_PROFILE.yaml"
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")
    git(root, "init", "-q")
    git(root, "config", "user.email", "aips-test")
    git(root, "config", "user.name", "AIPS Test")
    git(root, "add", ".")
    git(root, "commit", "-qm", "fixture base")
    report = {"schema_version": 1, "status": "PASS", "kind": "openapi_validation", "openapi_version": "3.1.0",
              "spec": {"path": "api/openapi.yaml", "sha256": "sha256:" + __import__("hashlib").sha256(spec.read_bytes()).hexdigest()},
              "repository_revision": git(root, "rev-parse", "HEAD"), "validator": "openapi-spec-validator==0.9.0",
              "network_references": "DENIED"}
    (root / "evidence/openapi-validation.json").write_text(json.dumps(report), encoding="utf-8")
    result = profile_validator.validate_profile(profile)
    assert result["structural_status"] == "PASS" and result["implementation_status"] == "READY", result
    return profile_path


with tempfile.TemporaryDirectory(prefix="aips-phase4-generator-") as temporary:
    root = Path(temporary) / "repo"
    root.mkdir()
    profile_path = make_repo(root)
    preview = adapter.inspect_adapter(root, "IMPLEMENTATION_PROFILE.yaml", "fixture")
    validate_json(preview, SCHEMA)
    assert preview["status"] == "READY" and not preview["applied"] and not (root / "src/generated/client").exists()

    result = adapter.inspect_adapter(root, "IMPLEMENTATION_PROFILE.yaml", "fixture", execute=True)
    validate_json(result, SCHEMA)
    assert result["status"] == "PASS" and result["applied"] and result["determinism_verified"] is True
    generated = root / "src/generated/client/client.go"
    assert generated.read_text(encoding="utf-8") == "package client\n"
    saved = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    assert saved["ownership"]["generated"] == ["src/generated/client/client.go"]
    assert saved["enforcement"]["generation_records"][0]["inputs"] == sorted(result["inputs"], key=lambda row: row["path"])

    # A second exact run may replace only outputs whose Phase 3 ownership hashes still match.
    second = adapter.inspect_adapter(root, "IMPLEMENTATION_PROFILE.yaml", "fixture", execute=True)
    assert second["status"] == "PASS" and second["outputs"] == result["outputs"]
    generated.write_text("package client // human edit\n", encoding="utf-8")
    try:
        adapter.inspect_adapter(root, "IMPLEMENTATION_PROFILE.yaml", "fixture", execute=True)
        raise AssertionError("edited generated output was accepted for replacement")
    except adapter.AdapterError as exc:
        assert "edited" in str(exc) or "ownership" in str(exc)

with tempfile.TemporaryDirectory(prefix="aips-phase4-generator-unsafe-") as temporary:
    root = Path(temporary) / "repo"
    root.mkdir()
    make_repo(root, mode="unexpected")
    result = adapter.inspect_adapter(root, "IMPLEMENTATION_PROFILE.yaml", "fixture", execute=True)
    assert result["status"] == "BLOCKED" and not result["applied"]
    assert not (root / "src/generated/client").exists()

with tempfile.TemporaryDirectory(prefix="aips-phase4-generator-timeout-") as temporary:
    root = Path(temporary) / "repo"
    root.mkdir()
    make_repo(root, mode="sleep", timeout=1)
    result = adapter.inspect_adapter(root, "IMPLEMENTATION_PROFILE.yaml", "fixture", execute=True)
    assert result["status"] == "UNVERIFIED" and not result["applied"]
    assert not (root / "src/generated/client").exists()

with tempfile.TemporaryDirectory(prefix="aips-phase4-generator-rollback-") as temporary:
    root = Path(temporary) / "repo"
    root.mkdir()
    profile_path = make_repo(root)
    first_apply = adapter.inspect_adapter(root, "IMPLEMENTATION_PROFILE.yaml", "fixture", execute=True)
    assert first_apply["status"] == "PASS" and first_apply["applied"], first_apply
    profile_before = profile_path.read_bytes()
    output_before = (root / "src/generated/client/client.go").read_bytes()
    original_replace = os.replace
    replace_calls = [0]

    def fail_profile_replace(source: os.PathLike[str] | str, destination: os.PathLike[str] | str) -> None:
        replace_calls[0] += 1
        if replace_calls[0] == 3:
            raise OSError("injected profile replace failure")
        original_replace(source, destination)

    os.replace = fail_profile_replace
    try:
        try:
            adapter.inspect_adapter(root, "IMPLEMENTATION_PROFILE.yaml", "fixture", execute=True)
            raise AssertionError("injected apply failure did not fail")
        except adapter.AdapterError as exc:
            assert "original output was restored" in str(exc)
    finally:
        os.replace = original_replace
    assert profile_path.read_bytes() == profile_before
    assert (root / "src/generated/client/client.go").read_bytes() == output_before

print("OpenAPI generator adapter lifecycle PASS")
