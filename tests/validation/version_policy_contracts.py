from __future__ import annotations

import subprocess
import sys

from .static_contracts import ROOT, errors, load_yaml

required = (
    ROOT / "config/version-tag-policy.yaml", ROOT / "scripts/version_tag_policy.py",
    ROOT / "config/github-ruleset-policy.yaml", ROOT / "scripts/github_ruleset_policy.py",
    ROOT / "tests/evidence/version_policy_lifecycle.py", ROOT / ".github/workflows/release-readiness.yml", ROOT / "scripts/install.ps1",
)
for path in required:
    if not path.is_file():
        errors.append(f"Version/ruleset policy artifact missing: {path.relative_to(ROOT)}")

tag_script = ROOT / "scripts/version_tag_policy.py"
if tag_script.is_file():
    text = tag_script.read_text(encoding="utf-8")
    for token in ("READY_FOR_EXPLICIT_RELEASE_APPROVAL", "tag_write_authorized", "existing_tag_sha", "historical_backfill", "--candidate-sha", "--expected-version"):
        if token not in text:
            errors.append(f"Version tag policy missing contract token: {token}")
    policy = load_yaml(ROOT / "config/version-tag-policy.yaml")
    requirements = policy.get("requirements") or {}
    if requirements.get("missing_stable_tag_fails_closed") is not True or requirements.get("stable_install_or_update_fallback") != "none":
        errors.append("Stable installer/update must fail closed without a verified release tag")
install_script = ROOT / "scripts/install.sh"
if install_script.is_file() and "bootstrapping from main" in install_script.read_text(encoding="utf-8"):
    errors.append("Stable installation must not silently fall back to mutable main")
windows_installer = ROOT / "scripts/install.ps1"
if windows_installer.is_file():
    text = windows_installer.read_text(encoding="utf-8")
    if '[ValidateSet("stable", "main")][string]$Channel = "stable"' not in text or "--channel __CHANNEL__" not in text:
        errors.append("Windows WSL installer must expose and forward an explicit stable/main channel")
rules_script = ROOT / "scripts/github_ruleset_policy.py"
if rules_script.is_file():
    text = rules_script.read_text(encoding="utf-8")
    for token in ("source_complete", "required_checks_added", "activation_authorized", "api_write_performed"):
        if token not in text:
            errors.append(f"GitHub ruleset policy missing contract token: {token}")
release_workflow = ROOT / ".github/workflows/release-readiness.yml"
if release_workflow.is_file():
    text = release_workflow.read_text(encoding="utf-8")
    for token in ("workflow_dispatch:", "contents: read", "release-readiness-evidence", "scripts/version_tag_policy.py"):
        if token not in text:
            errors.append(f"Release readiness workflow missing contract token: {token}")
    if "contents: write" in text or "git push" in text or "gh release create" in text:
        errors.append("Release readiness workflow must not publish tags or releases")
if all(path.is_file() for path in required):
    result = subprocess.run([sys.executable, str(ROOT / "tests/evidence/version_policy_lifecycle.py")], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        errors.append(f"Version/ruleset lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
