from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from .static_contracts import ROOT, errors, load_yaml

WORKFLOW = ROOT / ".github/workflows/gemini-runtime-verification.yml"
SCRIPT = ROOT / "scripts/gemini_cli_runtime_verification.py"
MANIFEST = ROOT / "harness/adapters/gemini-cli/gemini-extension.json"
RESULT = ROOT / "references/evolution/ISSUE_79_GEMINI_RUNTIME_VERIFICATION_RESULT.yaml"

for path in (WORKFLOW, SCRIPT, MANIFEST, RESULT):
    if not path.exists():
        errors.append(f"Gemini real-runtime verification file missing: {path.relative_to(ROOT)}")

if MANIFEST.exists():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    envs = {item.get("envVar") for item in (manifest.get("settings") or [])}
    for name in ("AIPS_OBSERVABLE_EVENT_CAPTURE", "AIPS_OBSERVABLE_EVENT_CAPTURE_SINK"):
        if name not in envs:
            errors.append(f"Gemini extension manifest must declare {name} for runtime sanitization")

if SCRIPT.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Gemini real-runtime verifier syntax failed: {compiled.stderr.strip()}")

if WORKFLOW.exists():
    text = WORKFLOW.read_text(encoding="utf-8")
    required = (
        "@google/gemini-cli@0.60.0",
        "gemini_cli_runtime_verification.py",
        "AIPS_EXPECTED_HEAD_SHA",
        "git rev-parse HEAD",
    )
    for token in required:
        if token not in text:
            errors.append(f"Gemini runtime workflow missing exact-candidate token: {token}")

if RESULT.exists():
    report = load_yaml(RESULT) or {}
    truth = report.get("runtime_truth") or {}
    if truth.get("live_runtime_execution_verified") is not True:
        errors.append("Gemini real-runtime result must expect real CLI runtime execution")
    if truth.get("live_capture_verified") is not True:
        errors.append("Gemini real-runtime result must expect runtime-specific live capture verification")
    if truth.get("live_provider_session_verified") is not False:
        errors.append("Gemini real-runtime result must not overclaim a live provider session")
    enforcement = report.get("enforcement") or {}
    if enforcement.get("runtime_enforced") is not False or enforcement.get("automatic_remediation") is not False:
        errors.append("Gemini real-runtime verification must not enable enforcement/remediation")

for hook_name in (
    "aips-turn-context.sh",
    "aips-governance-guard.sh",
    "aips-observable-event-capture.sh",
):
    hook_path = ROOT / "harness" / "adapters" / "gemini-cli" / "hooks" / hook_name
    if hook_path.exists():
        hook_text = hook_path.read_text(encoding="utf-8")
        if 'cd -P "$(dirname "${BASH_SOURCE[0]}")"' not in hook_text or 'pwd -P' not in hook_text:
            errors.append(f"Gemini hook wrapper must resolve symlinked extension path physically: {hook_name}")

if SCRIPT.exists():
    verifier_text = SCRIPT.read_text(encoding="utf-8")
    for token in (
        '"experimental": {"extensionConfig": True}',
        'workspace / ".env"',
        'AIPS_OBSERVABLE_EVENT_CAPTURE=1',
        'AIPS_OBSERVABLE_EVENT_CAPTURE=0',
    ):
        if token not in verifier_text:
            errors.append(f"Gemini real-runtime verifier missing official extension-settings evidence: {token}")
