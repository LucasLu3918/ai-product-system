"""Validate report-only document size policy and lifecycle behavior."""
from __future__ import annotations

import subprocess
import sys

import yaml

from .static_contracts import ROOT, errors

policy_path = ROOT / "config/document-size-policy.yaml"
script_path = ROOT / "scripts/document_size_audit.py"
lifecycle_path = ROOT / "tests/evidence/document_size_audit_lifecycle.py"
for path in (policy_path, script_path, lifecycle_path):
    if not path.is_file():
        errors.append(f"Missing document size audit artifact: {path.relative_to(ROOT)}")

if policy_path.is_file():
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
    if policy.get("hot_document_max_bytes") != 50000 or policy.get("threshold_behavior") != "WARN":
        errors.append("Document size threshold must be exactly 50000 bytes and informational WARN")
    if policy.get("gate_blocking") is not False or policy.get("archive_or_move") is not False:
        errors.append("Document size auditing must not block Gate or archive/move files")

if script_path.is_file() and lifecycle_path.is_file():
    result = subprocess.run([sys.executable, str(lifecycle_path)], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        errors.append(f"Document size audit lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
