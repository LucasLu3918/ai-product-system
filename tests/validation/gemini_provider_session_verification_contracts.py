from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from .static_contracts import ROOT, errors

SCRIPT = ROOT / "scripts/gemini_provider_session_verification.py"
EXTENSION = ROOT / "harness/adapters/gemini-cli"

if not SCRIPT.exists():
    errors.append("Gemini provider-session verifier is missing")
else:
    compiled = subprocess.run(
        [sys.executable, "-m", "py_compile", str(SCRIPT)],
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

    with tempfile.TemporaryDirectory(prefix="aips-gemini-provider-disabled-contract-") as tmp:
        output = Path(tmp) / "result.json"
        env = dict(os.environ)
        env.pop("GEMINI_API_KEY", None)
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--extension",
                str(EXTENSION),
                "--output",
                str(output),
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            errors.append(f"Gemini optional no-key verifier path failed: {result.stdout.strip()} {result.stderr.strip()}")
        elif not output.exists():
            errors.append("Gemini optional no-key verifier path did not write evidence")
        else:
            doc = json.loads(output.read_text(encoding="utf-8"))
            expected = {
                "status": "SKIPPED_NOT_CONFIGURED",
                "credential_present": False,
                "provider_verification_enabled": False,
                "required_for_release": False,
                "live_provider_session_verified": False,
                "provider_model_execution_verified": False,
            }
            for key, value in expected.items():
                if doc.get(key) != value:
                    errors.append(f"Gemini optional no-key evidence mismatch for {key}: {doc.get(key)!r}")
