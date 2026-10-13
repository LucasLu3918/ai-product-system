from __future__ import annotations

import subprocess
import sys

from .cli_source import cli_implementation
from .static_contracts import ROOT, errors

required = (
    "scripts/publish_preflight.py",
    "scripts/browser_runtime.py",
    "scripts/repository_preflight.py",
    "tests/evidence/publish_preflight_lifecycle.py",
    "tests/scenarios/165-ci-parity-publication-preflight.md",
)
for rel in required:
    if not (ROOT / rel).is_file():
        errors.append(f"Publication preflight artifact missing: {rel}")

cli = (ROOT / "bin/aips").read_text(encoding="utf-8") + "\n" + cli_implementation(ROOT)
workflow = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
intelligence = (ROOT / "scripts/project_intelligence.py").read_text(encoding="utf-8")
for phrase in ("publish doctor [--worktree", "publish preview|plan|preflight|matrix-sync|post-merge", "publish_preflight_cmd", "aips docs impact", "--project-root", "Integration Gate project root"):
    if phrase not in cli:
        errors.append(f"bin/aips missing publication preflight contract: {phrase}")
for phrase in ("scripts/publish_preflight.py run", "--labels \"$PR_LABELS\"", "AIPS_GATE_BASE_TIP", "unlabeled"):
    if phrase not in workflow:
        errors.append(f"validate workflow missing shared publication resolver: {phrase}")
preflight_source = (ROOT / "scripts/publish_preflight.py").read_text(encoding="utf-8")
for phrase in ("worktree-details", "publication_planning.doctor"):
    if phrase not in preflight_source:
        errors.append(f"publication doctor missing diagnostic contract: {phrase}")
planning_source = (ROOT / "scripts/publication_planning.py").read_text(encoding="utf-8")
for phrase in ("Read-only, phase-separated publication evidence", "protection_policy_evidence"):
    if phrase not in planning_source:
        errors.append(f"publication doctor missing diagnostic contract: {phrase}")
python_handoff = 'echo "AIPS_VALIDATION_PYTHON=$(python -c \'import sys; print(sys.executable)\')" >> "$GITHUB_ENV"'
if python_handoff not in workflow:
    errors.append("validate workflow must pass its installed Python interpreter to isolated CLI fixtures")
elif workflow.index("Install deterministic Playwright Chromium") > workflow.index(python_handoff):
    errors.append("validate workflow must select the full validation Python after optional dependencies are installed")
elif workflow.index(python_handoff) > workflow.index("deterministic integration gate"):
    errors.append("validate workflow must export the full validation Python before the deterministic integration gate")
for phrase in ("def refresh(root:", "REFRESHED_EQUIVALENT_TREE", "SEMANTIC_REFRESH_REQUIRED", "set disposition to reviewed_safe, requires_change or unknown"):
    if phrase not in intelligence:
        errors.append(f"Project Intelligence equivalent-tree refresh missing: {phrase}")

repository_preflight = (ROOT / "scripts/repository_preflight.py").read_text(encoding="utf-8")
for phrase in ("AIPS_VALIDATION_VENV", "AIPS_VALIDATION_PYTHON", "openapi_spec_validator"):
    if phrase not in cli + (ROOT / "scripts/publish_preflight.py").read_text(encoding="utf-8"):
        errors.append(f"local validation environment contract missing: {phrase}")
for phrase in (
    "AIPS_NODE_BINARY",
    "AIPS_VITEPRESS_NODE_MODULES",
    "Node.js 24 or newer",
    "package-lock.json",
    "installed VitePress version does not match",
    "registerHooks",
    "No package install or registry access is attempted",
):
    if phrase not in repository_preflight:
        errors.append(f"offline documentation build contract missing: {phrase}")
workflow_pins = {
    ".github/workflows/docs-site.yml": "actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346 # v5.0.1",
    ".github/workflows/e2b-sandbox-verification.yml": "actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f # v6.0.0",
}
for rel, expected in workflow_pins.items():
    if expected not in (ROOT / rel).read_text(encoding="utf-8"):
        errors.append(f"Node 24 action pin mismatch: {rel}")

evidence = ROOT / "tests/evidence/publish_preflight_lifecycle.py"
if evidence.is_file():
    proc = subprocess.run([sys.executable, str(evidence)], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode:
        errors.append(f"Publication preflight lifecycle failed: {proc.stdout.strip()} {proc.stderr.strip()}")

planning_tests = subprocess.run(
    [sys.executable, str(ROOT / "tests/test_publication_planning.py")],
    cwd=ROOT, capture_output=True, text=True, check=False,
)
if planning_tests.returncode:
    errors.append("Publication planning lifecycle failed: " + planning_tests.stderr[-2000:])

diagnostics_tests = subprocess.run(
    [sys.executable, str(ROOT / "tests/test_publication_diagnostics.py")],
    cwd=ROOT, capture_output=True, text=True, check=False,
)
if diagnostics_tests.returncode:
    errors.append("Publication diagnostics lifecycle failed: " + diagnostics_tests.stderr[-2000:])

for rel in ("scripts/publication_diagnostics.py", "tests/test_publication_diagnostics.py"):
    if not (ROOT / rel).is_file():
        errors.append(f"Publication Doctor artifact missing: {rel}")
for rel in ("harness/adapters/claude-code/CLAUDE.md", "harness/adapters/codex/AGENTS.md", "harness/adapters/opencode/AGENTS.md", "docs/human/USER_GUIDE.md"):
    text = (ROOT / rel).read_text(encoding="utf-8")
    if "aips publish doctor" not in text or "Required Checks" not in text:
        errors.append(f"Publication diagnostics guidance missing: {rel}")
