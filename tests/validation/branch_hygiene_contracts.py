from __future__ import annotations

import subprocess
import sys

from .static_contracts import ROOT, errors, load_yaml

REQUIRED = (
    ROOT / "config/branch-lifecycle.yaml",
    ROOT / "scripts/branch_hygiene.py",
    ROOT / "config/branch-cleanup-manifest.yaml",
    ROOT / ".github/workflows/branch-hygiene.yml",
    ROOT / "tests/evidence/branch_hygiene_lifecycle.py",
)

for path in REQUIRED:
    if not path.exists():
        errors.append(f"Branch hygiene required file missing: {path.relative_to(ROOT)}")

config_path = ROOT / "config/branch-lifecycle.yaml"
if config_path.exists():
    config = load_yaml(config_path) or {}
    if config.get("version") != 1:
        errors.append("branch lifecycle config version must be 1")
    if config.get("default_branch") != "main":
        errors.append("branch lifecycle default_branch must be main")
    deletion = config.get("deletion") or {}
    if deletion.get("mode") != "report_only":
        errors.append("branch lifecycle deletion.mode must remain report_only")
    if deletion.get("require_integrated_into_default") is not True:
        errors.append("branch lifecycle must require integration into default before deletion candidacy")
    if deletion.get("preserve_unclassified") is not True:
        errors.append("branch lifecycle must preserve unclassified branches")
    if deletion.get("approved_cleanup_manifest") != "config/branch-cleanup-manifest.yaml":
        errors.append("branch lifecycle must bind the exact approved cleanup manifest")
    if deletion.get("apply_only_on_protected_main_push") is not True:
        errors.append("branch cleanup must be restricted to protected-main push")
    persistent = set(config.get("persistent_exact") or [])
    if "main" not in persistent:
        errors.append("branch lifecycle must preserve main")
    if "feature/retrieval-embedding-trial" not in persistent:
        errors.append("branch lifecycle must preserve operational retrieval embedding trial branch")

script = ROOT / "scripts/branch_hygiene.py"
if script.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(script)], cwd=ROOT, text=True, capture_output=True)
    if compiled.returncode != 0:
        errors.append(f"branch hygiene syntax failed: {compiled.stderr.strip()}")
    text = script.read_text(encoding="utf-8")
    for token in ("--remote", "refs/remotes", "--apply-cleanup", "--github-repository", "GITHUB_MERGED_PR_EXACT_HEAD", "exact_manifest_only", "cleanup preflight blocked", '"branch_deletion_authorized": False'):
        if token not in text:
            errors.append(f"branch hygiene remote/report-only contract missing: {token}")

workflow = ROOT / ".github/workflows/branch-hygiene.yml"
if workflow.exists():
    text = workflow.read_text(encoding="utf-8")
    for token in (
        "permissions:",
        "contents: read",
        "fetch-depth: 0",
        "+refs/heads/*:refs/remotes/origin/*",
        "--remote origin",
        "branch_deletion_authorized",
        "needs: report",
        "github.event_name == 'push'",
        "github.ref == 'refs/heads/main'",
        "contents: write",
        "--apply-cleanup config/branch-cleanup-manifest.yaml",
        "--github-repository",
        "GH_TOKEN:",
        "github.token",
        "authorization_scope",
        "exact_manifest_only",
    ):
        if token not in text:
            errors.append(f"branch hygiene workflow contract missing: {token}")
    if "git branch -D" in text:
        errors.append("branch hygiene workflow must not locally force-delete branches")

evidence = ROOT / "tests/evidence/branch_hygiene_lifecycle.py"
if evidence.exists():
    result = subprocess.run([sys.executable, str(evidence)], cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        errors.append(f"branch hygiene lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")


cleanup_manifest = ROOT / "config/branch-cleanup-manifest.yaml"
if cleanup_manifest.exists():
    manifest = load_yaml(cleanup_manifest) or {}
    auth = manifest.get("authorization") or {}
    rows = manifest.get("branches") or []
    if auth.get("type") != "explicit_user_request" or auth.get("scope") != "exact_manifest_only" or auth.get("one_time") is not True:
        errors.append("branch cleanup manifest must contain explicit exact-list one-time authorization")
    if not rows:
        errors.append("branch cleanup manifest must contain approved branches")
    names = [row.get("branch") for row in rows if isinstance(row, dict)]
    if len(names) != len(set(names)):
        errors.append("branch cleanup manifest branch names must be unique")
    for row in rows:
        if not isinstance(row, dict) or not row.get("branch") or len(str(row.get("expected_sha") or "")) != 40:
            errors.append("branch cleanup manifest entries must bind branch + full expected SHA")
        if not isinstance((row or {}).get("merged_pr"), int):
            errors.append("branch cleanup manifest entries must bind merged PR evidence")
