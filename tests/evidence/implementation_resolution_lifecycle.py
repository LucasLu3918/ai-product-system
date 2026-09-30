#!/usr/bin/env python3
"""Exercise the profile validator CLI and the four language profile contracts."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts/implementation_profile_validate.py"
TEMPLATE = ROOT / "templates/implementation/IMPLEMENTATION_PROFILE.yaml"


def run(profile: Path, language: Path | None = None) -> tuple[subprocess.CompletedProcess[str], dict]:
    command = [sys.executable, str(VALIDATOR), str(profile), "--format", "json"]
    if language:
        command.extend(["--language-profile", str(language)])
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return result, json.loads(result.stdout)


with tempfile.TemporaryDirectory(prefix="aips-implementation-profile-") as directory:
    profile = Path(directory) / "profile.yaml"
    profile.write_bytes(TEMPLATE.read_bytes())
    result, report = run(profile, ROOT / "references/languages/go/PROFILE.yaml")
    assert result.returncode == 2, (result.returncode, report, result.stderr)
    assert report["structural_status"] == "PASS", report
    assert report["implementation_status"] == "BLOCKED", report

    for language in ("go", "php", "python", "dotnet"):
        result, report = run(profile, ROOT / "references/languages" / language / "PROFILE.yaml")
        assert result.returncode == 2, (language, result.returncode, report, result.stderr)
        assert report["structural_status"] == "PASS", (language, report)

    invalid = Path(directory) / "invalid.yaml"
    invalid.write_text(profile.read_text(encoding="utf-8").replace("authority: unresolved", "authority: invented"), encoding="utf-8")
    result, report = run(invalid)
    assert result.returncode == 1 and report["structural_status"] == "FAIL", (result.returncode, report)

print("Implementation Resolution lifecycle PASS: CLI exit states, provenance, four language profiles, and invalid enum rejection.")
