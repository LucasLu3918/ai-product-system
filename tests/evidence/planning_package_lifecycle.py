#!/usr/bin/env python3
"""Exercise the Planning Package validator against the canonical template."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts/planning_package_validate.py"
TEMPLATE = ROOT / "templates/planning-package"


def run(package: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
    result = subprocess.run([sys.executable, str(VALIDATOR), str(package), "--format", "json"], capture_output=True, text=True)
    try:
        return result, json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"validator did not return JSON: {result.stdout} {result.stderr}") from exc


with tempfile.TemporaryDirectory(prefix="aips-planning-package-lifecycle-") as temp:
    package = Path(temp) / "planning"
    shutil.copytree(TEMPLATE, package)
    result, data = run(package)
    if result.returncode != 0 or data.get("status") != "PASS":
        raise AssertionError(f"canonical planning template must validate: {data} {result.stderr}")

    manifest = package / "PLANNING_MANIFEST.yaml"
    original = manifest.read_text(encoding="utf-8")
    manifest.write_text(original.replace("refs: [OP-001]", "refs: [OP-MISSING]", 1), encoding="utf-8")
    failed, failure = run(package)
    if failed.returncode == 0 or failure.get("status") != "FAIL" or not any("unknown OP reference" in item for item in failure.get("errors", [])):
        raise AssertionError(f"unknown operation references must fail with a useful diagnostic: {failure}")

    manifest.write_text(original + "\nproduct:\n  name: duplicate\n", encoding="utf-8")
    duplicate, duplicate_data = run(package)
    if duplicate.returncode == 0 or not any("duplicate key" in item for item in duplicate_data.get("errors", [])):
        raise AssertionError(f"duplicate YAML keys must be rejected: {duplicate_data}")

    manifest.write_text(original.replace("path: PRODUCT_PLAN.md", "path: ../outside.md", 1), encoding="utf-8")
    escaped, escape_data = run(package)
    if escaped.returncode == 0 or not any("must stay inside" in item for item in escape_data.get("errors", [])):
        raise AssertionError(f"package path traversal must fail closed: {escape_data}")

print("PLANNING PACKAGE LIFECYCLE PASSED")
