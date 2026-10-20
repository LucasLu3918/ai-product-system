from __future__ import annotations

import sys

from .static_contracts import ROOT, errors

sys.path.insert(0, str(ROOT / "scripts"))
from dependency_impact import require_pinned_action

dependency_path = ROOT / ".github/workflows/dependency-review.yml"
scorecard_path = ROOT / ".github/workflows/scorecard.yml"
inventory_path = ROOT / ".github/workflows/security-inventory.yml"

for path in (dependency_path, scorecard_path, inventory_path):
    if not path.is_file():
        errors.append(f"Missing supply-chain workflow: {path.relative_to(ROOT)}")

if dependency_path.is_file():
    text = dependency_path.read_text(encoding="utf-8")
    errors.extend(require_pinned_action(text, "actions/dependency-review-action", label="Dependency Review", min_version="v5.0.0"))
    if "fail-on-severity: high" not in text:
        errors.append("Dependency Review must block newly introduced high or critical vulnerabilities")
    if "pull_request:" not in text or "contents: read" not in text or "pull-requests: read" not in text:
        errors.append("Dependency Review must run for PRs with read-only minimum permissions")
    if any(token in text for token in ("contents: write", "pull-requests: write", "secrets.", "OPENAI_API_KEY")):
        errors.append("Dependency Review must not request write authority or provider credentials")

if scorecard_path.is_file():
    text = scorecard_path.read_text(encoding="utf-8")
    requirements = (
        "schedule:",
        "workflow_dispatch:",
        "publish_results: true",
        "security-events: write",
        "id-token: write",
        "persist-credentials: false",
    )
    for requirement in requirements:
        if requirement not in text:
            errors.append(f"Scorecard workflow missing required advisory control: {requirement}")
    errors.extend(require_pinned_action(text, "ossf/scorecard-action", label="Scorecard workflow", min_version="v2.4.4", expected_count=1))
    if any(token in text for token in ("pull_request:", "contents: write", "pull-requests: write", "gh pr merge")):
        errors.append("Scorecard must remain scheduled/manual advisory analysis without PR authority")

if inventory_path.is_file():
    text = inventory_path.read_text(encoding="utf-8")
    requirements = (
        'cron: "12 12 * * 1"',
        "workflow_dispatch:",
        "security-events: write",
        "--include-git-root -r ./",
        "fetch-depth: 0",
        'GITLEAKS_ENABLE_COMMENTS: "false"',
        'GITLEAKS_ENABLE_UPLOAD_ARTIFACT: "false"',
        "Outcome parity:",
    )
    for requirement in requirements:
        if requirement not in text:
            errors.append(f"Security inventory workflow missing advisory control: {requirement}")
    errors.extend(require_pinned_action(text, "google/osv-scanner-action/.github/workflows/osv-scanner-reusable.yml", label="Security inventory workflow", expected_count=1))
    errors.extend(require_pinned_action(text, "gitleaks/gitleaks-action", label="Security inventory workflow", min_version="v3.0.0", expected_count=1))
    if any(token in text for token in ("pull_request:", "contents: write", "pull-requests: write", "gh pr merge")):
        errors.append("Security inventory must remain scheduled/manual advisory analysis without PR authority")
    if text.count("continue-on-error: true") < 2:
        errors.append("Both scheduled security scanner outcomes must remain nonblocking")
