from __future__ import annotations

import subprocess
import sys

from .static_contracts import ROOT, errors

required = (
    ROOT / "config/version-tag-policy.yaml", ROOT / "scripts/version_tag_policy.py",
    ROOT / "config/github-ruleset-policy.yaml", ROOT / "scripts/github_ruleset_policy.py",
    ROOT / "tests/evidence/version_policy_lifecycle.py",
)
for path in required:
    if not path.is_file():
        errors.append(f"Version/ruleset policy artifact missing: {path.relative_to(ROOT)}")

tag_script = ROOT / "scripts/version_tag_policy.py"
if tag_script.is_file():
    text = tag_script.read_text(encoding="utf-8")
    for token in ("READY_FOR_EXPLICIT_RELEASE_APPROVAL", "tag_write_authorized", "existing_tag_sha", "historical_backfill"):
        if token not in text:
            errors.append(f"Version tag policy missing contract token: {token}")
rules_script = ROOT / "scripts/github_ruleset_policy.py"
if rules_script.is_file():
    text = rules_script.read_text(encoding="utf-8")
    for token in ("source_complete", "required_checks_added", "activation_authorized", "api_write_performed"):
        if token not in text:
            errors.append(f"GitHub ruleset policy missing contract token: {token}")
if all(path.is_file() for path in required):
    result = subprocess.run([sys.executable, str(required[-1])], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        errors.append(f"Version/ruleset lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
