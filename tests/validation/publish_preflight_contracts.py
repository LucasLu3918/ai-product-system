from __future__ import annotations

import subprocess
import sys

from .static_contracts import ROOT, errors

required = (
    "scripts/publish_preflight.py",
    "scripts/repository_preflight.py",
    "tests/evidence/publish_preflight_lifecycle.py",
    "tests/scenarios/165-ci-parity-publication-preflight.md",
)
for rel in required:
    if not (ROOT / rel).is_file():
        errors.append(f"Publication preflight artifact missing: {rel}")

cli = (ROOT / "bin/aips").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
intelligence = (ROOT / "scripts/project_intelligence.py").read_text(encoding="utf-8")
for phrase in ("publish plan|preflight|post-merge", "publish_preflight_cmd", "aips docs impact"):
    if phrase not in cli:
        errors.append(f"bin/aips missing publication preflight contract: {phrase}")
for phrase in ("scripts/publish_preflight.py run", "--labels \"$PR_LABELS\"", "AIPS_GATE_BASE_TIP"):
    if phrase not in workflow:
        errors.append(f"validate workflow missing shared publication resolver: {phrase}")
for phrase in ("def refresh(root:", "REFRESHED_EQUIVALENT_TREE", "SEMANTIC_REFRESH_REQUIRED"):
    if phrase not in intelligence:
        errors.append(f"Project Intelligence equivalent-tree refresh missing: {phrase}")

evidence = ROOT / "tests/evidence/publish_preflight_lifecycle.py"
if evidence.is_file():
    proc = subprocess.run([sys.executable, str(evidence)], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode:
        errors.append(f"Publication preflight lifecycle failed: {proc.stdout.strip()} {proc.stderr.strip()}")
