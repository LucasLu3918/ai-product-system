from __future__ import annotations

import subprocess
import sys

from .static_contracts import ROOT, errors, load_yaml

REQUIRED = (
    ROOT / "orchestration/RESOURCE_AUTHORIZATION.md",
    ROOT / "orchestration/schemas/resource-authorization-profile.yaml",
    ROOT / "templates/automation/RESOURCE_AUTHORIZATION_PROFILE.yaml",
    ROOT / "scripts/resource_authorization.py",
    ROOT / "tests/evidence/resource_authorization_lifecycle.py",
)

for path in REQUIRED:
    if not path.exists():
        errors.append(f"Resource authorization required file missing: {path.relative_to(ROOT)}")

template = ROOT / "templates/automation/RESOURCE_AUTHORIZATION_PROFILE.yaml"
if template.exists():
    data = load_yaml(template) or {}
    if data.get("version") != 1:
        errors.append("resource authorization profile version must be 1")
    if data.get("default_effect") != "DENY":
        errors.append("resource authorization default_effect must remain DENY")
    authority = data.get("authority") or {}
    if any(authority.get(k) is not False for k in (
        "human_approval_granted", "merge_authorized", "release_authorized", "protected_operation_authorized"
    )):
        errors.append("resource authorization template must not grant protected authority")

script = ROOT / "scripts/resource_authorization.py"
if script.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(script)], cwd=ROOT, text=True, capture_output=True)
    if compiled.returncode != 0:
        errors.append(f"resource authorization syntax failed: {compiled.stderr.strip()}")
    text = script.read_text(encoding="utf-8")
    for token in ('default_effect") != "DENY"', '"runtime_enforced": False', '"protected_operation_authorized": False'):
        if token not in text:
            errors.append(f"resource authorization fail-closed contract missing: {token}")

evidence = ROOT / "tests/evidence/resource_authorization_lifecycle.py"
if evidence.exists():
    result = subprocess.run([sys.executable, str(evidence)], cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        errors.append(f"resource authorization lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
