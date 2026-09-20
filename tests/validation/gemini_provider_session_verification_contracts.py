from __future__ import annotations

import subprocess

from .static_contracts import ROOT, errors

SCRIPT = ROOT / "scripts/gemini_provider_session_verification.py"

if not SCRIPT.exists():
    errors.append("Gemini provider-session verifier is missing")
else:
    compiled = subprocess.run(
        ["python", "-m", "py_compile", str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if compiled.returncode != 0:
        errors.append(f"Gemini provider-session verifier syntax failed: {compiled.stderr.strip()}")

    text = SCRIPT.read_text(encoding="utf-8")
    if "--fake-responses" in text:
        errors.append("Live provider verifier must not use fake model responses")
    for token in (
        "GEMINI_API_KEY",
        "provider_verification_enabled",
        "required_for_release",
        "SKIPPED_NOT_CONFIGURED",
        "provider_model_execution_verified",
        "live_provider_session_verified",
        "credential_value_persisted",
    ):
        if token not in text:
            errors.append(f"Gemini provider-session verifier missing token: {token}")
    if "BLOCKED_MISSING_CREDENTIAL" in text:
        errors.append("Optional Gemini provider verification must not treat an unconfigured credential as a blocker")
    if "return 2" in text:
        errors.append("Optional Gemini provider verification must exit successfully when no credential is configured")
    if "print(api_key)" in text or "repr(api_key)" in text:
        errors.append("Gemini provider-session verifier must not print credential material")
