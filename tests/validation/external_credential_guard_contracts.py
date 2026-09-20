from __future__ import annotations

import subprocess
import sys

from .static_contracts import ROOT, errors, load_yaml

REQUIRED = (
    ROOT / "config/external-credentials.yaml",
    ROOT / "scripts/external_credential_guard.py",
    ROOT / "tests/evidence/external_credential_guard_lifecycle.py",
    ROOT / "orchestration/EXTERNAL_CREDENTIAL_DEPENDENCY_GUARD.md",
)

for path in REQUIRED:
    if not path.exists():
        errors.append(f"External credential guard required file missing: {path.relative_to(ROOT)}")

config_path = ROOT / "config/external-credentials.yaml"
if config_path.exists():
    config = load_yaml(config_path) or {}
    policy = config.get("policy") or {}
    if policy.get("external_credentials_required_for_baseline") is not False:
        errors.append("external credential guard must keep baseline credential-free")
    if policy.get("external_credentials_required_for_release") is not False:
        errors.append("external credential guard must keep release credential-free")
    for name in ("GEMINI_API_KEY", "OPENAI_API_KEY"):
        entry = (config.get("credentials") or {}).get(name) or {}
        if entry.get("optional") is not True:
            errors.append(f"{name} must remain optional")
        if entry.get("required_for_baseline") is not False or entry.get("required_for_release") is not False:
            errors.append(f"{name} must not become baseline/release required")

script = ROOT / "scripts/external_credential_guard.py"
if script.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(script)], cwd=ROOT, text=True, capture_output=True)
    if compiled.returncode != 0:
        errors.append(f"external credential guard syntax failed: {compiled.stderr.strip()}")

    audit = subprocess.run(
        [sys.executable, str(script), "audit", "--config", str(config_path), "--root", str(ROOT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if audit.returncode != 0:
        errors.append(f"external credential guard audit failed: {audit.stdout.strip()} {audit.stderr.strip()}")

evidence = ROOT / "tests/evidence/external_credential_guard_lifecycle.py"
if evidence.exists():
    result = subprocess.run([sys.executable, str(evidence)], cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        errors.append(f"external credential guard lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
