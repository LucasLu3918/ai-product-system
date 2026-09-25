#!/usr/bin/env python3
"""Exercise strict scanner, commit-history coverage, and Integration Gate binding."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SCANNER = ROOT / "scripts/check_secret_leakage.py"
POLICY = ROOT / "config/secret-scan.yaml"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if result.returncode:
        raise AssertionError("temporary Git fixture command failed")
    return result.stdout.strip()


def run_scan(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCANNER), "--root", str(root), "--policy", str(POLICY), "--json", *args],
        cwd=root,
        capture_output=True,
        text=True,
    )


def main() -> int:
    token = "ghp_" + ("A" * 40)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        git(root, "init", "-q")
        git(root, "config", "user.name", "Secret Scan Test")
        git(root, "config", "user.email", "secret-scan" + "@example.invalid")
        tracked = root / "docs" / "example.md"
        tracked.parent.mkdir()
        tracked.write_text("Safe placeholder text.\n", encoding="utf-8")
        git(root, "add", "docs/example.md")
        git(root, "commit", "-qm", "baseline")
        base = git(root, "rev-parse", "HEAD")

        tracked.write_text(f"TOKEN={token}\n", encoding="utf-8")
        git(root, "add", "docs/example.md")
        git(root, "commit", "-qm", "add synthetic token")
        exposed_head = git(root, "rev-parse", "HEAD")

        exposed = run_scan(root, "--publication-candidate", "--base", base, "--head", exposed_head)
        require(exposed.returncode == 1, "committed token must fail publication scan")
        require(token not in exposed.stdout and token not in exposed.stderr, "scanner output exposed the token")
        exposed_doc = json.loads(exposed.stdout)
        require(exposed_doc["status"] == "FAIL", "finding must be a FAIL, not a PASS")
        require(any(item.get("revision") for item in exposed_doc["findings"]), "history finding must identify its commit")
        require(len(exposed_doc["policy_sha256"]) == 64 and len(exposed_doc["scanner_sha256"]) == 64, "scan hashes missing")

        tracked.write_text("TOKEN=example-placeholder\n", encoding="utf-8")
        git(root, "add", "docs/example.md")
        git(root, "commit", "-qm", "remove synthetic token")
        cleaned_head = git(root, "rev-parse", "HEAD")
        cleaned = run_scan(root, "--publication-candidate", "--base", base, "--head", cleaned_head)
        require(cleaned.returncode == 1, "removed token must remain blocked because it is in candidate history")
        require(token not in cleaned.stdout and token not in cleaned.stderr, "history scan exposed the token")

        message_file = root / "docs" / "message-only.md"
        message_file.write_text("Safe file content.\n", encoding="utf-8")
        git(root, "add", "docs/message-only.md")
        git(root, "commit", "-qm", "synthetic commit message " + token)
        message_head = git(root, "rev-parse", "HEAD")
        message_scan = run_scan(root, "--publication-candidate", "--base", base, "--head", message_head)
        require(message_scan.returncode == 1, "secret in candidate commit message must fail the history scan")
        require(token not in message_scan.stdout and token not in message_scan.stderr, "commit-message scan exposed the token")

        ignored = root / "ignored.txt"
        ignored.write_text(f"TOKEN={token} # AIPS-SECRET-SCAN-IGNORE-LINE\n", encoding="utf-8")
        strict = run_scan(root, "--strict", "--path", "ignored.txt")
        require(strict.returncode == 1, "strict mode must ignore no inline bypass marker")
        require(token not in strict.stdout and token not in strict.stderr, "strict report exposed the token")

        lockfile = root / "pnpm-lock.yaml"
        generic_value = "Ab9Cd7Ef5Gh3Jk1L" + "m8Np6Qr4St2Uv0Wx"
        lockfile.write_text(f'api_key: "{generic_value}"\n', encoding="utf-8")
        generic = run_scan(root, "--strict", "--path", "pnpm-lock.yaml")
        require(generic.returncode == 0, "lockfile generic assignment should not cause entropy false-positive")
        lockfile.write_text(f"resolved: https://registry.example.invalid/{token}\n", encoding="utf-8")
        provider = run_scan(root, "--strict", "--path", "pnpm-lock.yaml")
        require(provider.returncode == 1, "lockfile provider token must still be detected")
        require(token not in provider.stdout and token not in provider.stderr, "lockfile report exposed the token")

    spec = importlib.util.spec_from_file_location("aips_integration_gate", ROOT / "scripts/integration_gate.py")
    require(spec is not None and spec.loader is not None, "could not load Integration Gate contract")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    profile = {
        "candidate_secret_scan": {
            "required": True,
            "check_id": "mandatory-candidate-secret-scan",
            "scanner": "scripts/check_secret_leakage.py",
            "policy": "config/secret-scan.yaml",
        },
    }
    check = {
        "id": "mandatory-candidate-secret-scan",
        "required": True,
        "candidate_context": True,
        "paths": ["**"],
        "argv": ["python3", "scripts/check_secret_leakage.py", "--policy", "config/secret-scan.yaml", "--publication-candidate"],
    }
    binding = module.candidate_secret_scan_binding(profile, [check], ROOT)
    require(binding is not None and len(binding["scanner_sha256"]) == 64, "candidate scanner binding missing")
    env_check = {
        "id": "candidate-context-contract",
        "category": "test",
        "required": True,
        "candidate_context": True,
        "applies": True,
        "env": {},
        "argv": [
            "python3", "-c",
            "import os,sys; sys.exit(0 if os.getenv('AIPS_GATE_BASE_SHA') == 'base' and os.getenv('AIPS_GATE_HEAD_SHA') == 'head' and os.getenv('AIPS_SECRET_SCAN_POLICY_SHA256') == 'policy-hash' else 1)",
        ],
    }
    env_result = module.run_check(
        env_check,
        candidate_env={
            "AIPS_GATE_BASE_SHA": "base",
            "AIPS_GATE_HEAD_SHA": "head",
            "AIPS_SECRET_SCAN_POLICY_SHA256": "policy-hash",
        },
    )
    require(env_result["status"] == "PASS", "Gate did not pass the resolved candidate context to the scanner command")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        scanner = root / "scripts/check_secret_leakage.py"
        policy_path = root / "config/secret-scan.yaml"
        scanner.parent.mkdir()
        policy_path.parent.mkdir()
        scanner.write_text("scanner-v1\n", encoding="utf-8")
        policy_path.write_text("policy-v1\n", encoding="utf-8")
        temp_profile = {
            "candidate_secret_scan": {
                "required": True,
                "check_id": "secret-scan",
                "scanner": "scripts/check_secret_leakage.py",
                "policy": "config/secret-scan.yaml",
            },
        }
        temp_check = {
            "id": "secret-scan",
            "required": True,
            "candidate_context": True,
            "paths": ["**"],
            "argv": ["python3", "scripts/check_secret_leakage.py", "--policy", "config/secret-scan.yaml", "--publication-candidate"],
        }
        first_binding = module.candidate_secret_scan_binding(temp_profile, [temp_check], root)
        policy_path.write_text("policy-v2\n", encoding="utf-8")
        second_binding = module.candidate_secret_scan_binding(temp_profile, [temp_check], root)
        require(first_binding["policy_sha256"] != second_binding["policy_sha256"], "policy edits must invalidate scan binding")
    try:
        module.candidate_secret_scan_binding(profile, [], ROOT)
    except module.GateError:
        pass
    else:
        raise AssertionError("Gate must reject a missing mandatory scan check")

    print("mandatory candidate secret scanning evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
