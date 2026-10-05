from __future__ import annotations

from .static_contracts import ROOT, errors

dependency_path = ROOT / ".github/workflows/dependency-review.yml"
scorecard_path = ROOT / ".github/workflows/scorecard.yml"

for path in (dependency_path, scorecard_path):
    if not path.is_file():
        errors.append(f"Missing supply-chain workflow: {path.relative_to(ROOT)}")

if dependency_path.is_file():
    text = dependency_path.read_text(encoding="utf-8")
    if "actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294" not in text:
        errors.append("Dependency Review must pin the verified v5.0.0 action commit")
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
        "ossf/scorecard-action@55891bbd73f2425e97637d96e306fc9d491d0b21",
        "publish_results: true",
        "security-events: write",
        "id-token: write",
        "persist-credentials: false",
    )
    for requirement in requirements:
        if requirement not in text:
            errors.append(f"Scorecard workflow missing required advisory control: {requirement}")
    if any(token in text for token in ("pull_request:", "contents: write", "pull-requests: write", "gh pr merge")):
        errors.append("Scorecard must remain scheduled/manual advisory analysis without PR authority")
