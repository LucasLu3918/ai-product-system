from __future__ import annotations

from .static_contracts import ROOT, errors

WORKFLOW = ROOT / ".github/workflows/gemini-provider-session-verification.yml"

if not WORKFLOW.exists():
    errors.append("Gemini provider-session workflow is missing")
else:
    text = WORKFLOW.read_text(encoding="utf-8")
    if "pull_request:" in text:
        errors.append("Gemini provider-session workflow must never run on pull_request")
    required = (
        "push:",
        "branches: [main]",
        "workflow_dispatch:",
        "permissions:",
        "contents: read",
        "secrets.GEMINI_API_KEY",
        "SKIPPED_NOT_CONFIGURED",
        "provider_verification_enabled",
        "required_for_release",
        "steps.credential.outputs.present == 'true'",
        "steps.credential.outputs.present != 'true'",
        "AIPS_EXPECTED_SHA",
        "git rev-parse HEAD",
        "@google/gemini-cli@0.60.0",
        "gemini_provider_session_verification.py",
    )
    for token in required:
        if token not in text:
            errors.append(f"Gemini provider-session workflow missing token: {token}")
    for forbidden in (
        "BLOCKED_MISSING_CREDENTIAL",
        "google-github-actions/auth",
        "GOOGLE_GENAI_USE_VERTEXAI",
        "GOOGLE_API_KEY",
    ):
        if forbidden in text:
            errors.append(f"Optional Gemini provider workflow contains disallowed auth/blocking token: {forbidden}")
    if 'echo "$GEMINI_API_KEY"' in text or "printenv GEMINI_API_KEY" in text:
        errors.append("Gemini provider-session workflow must not print credential material")
