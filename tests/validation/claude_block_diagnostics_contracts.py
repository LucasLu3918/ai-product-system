from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def errors() -> list[str]:
    scenario = (ROOT / "tests/scenarios/261-publication-diagnostics-and-safe-recovery.md").read_text(encoding="utf-8")
    guard = (ROOT / "scripts/governance_guard.py").read_text(encoding="utf-8")
    authority = (ROOT / "scripts/publication_authority.py").read_text(encoding="utf-8")
    adapter = (ROOT / "scripts/manage_runtime_adapter.py").read_text(encoding="utf-8")
    observer = (ROOT / "scripts/claude_permission_denied.py").read_text(encoding="utf-8")
    docs_only = (ROOT / "scripts/docs_only_review.py").read_text(encoding="utf-8")
    docs_only_tests = (ROOT / "tests/test_docs_only_review.py").read_text(encoding="utf-8")
    violations = []
    for test_id in ("T01-T07", "T08-T09", "T10-T11", "T12", "T13", "T14", "T15", "T16-T17", "T18"):
        if test_id not in scenario:
            violations.append(f"Scenario 261 is missing {test_id}")
    for token, source in (("parser_evidence", guard), ("failed_segment_index", authority),
                          ("PermissionDenied", adapter), ("claude_auto_mode", observer),
                          ("MAX_RECORDS = 1000", observer), ("days=30", observer),
                          ("--opt-in", docs_only), ("secret_scan", docs_only),
                          ("approval_and_reconciliation", docs_only_tests),
                          ("DOCS_ONLY_REVIEW_ONLY", docs_only_tests)):
        if token not in source:
            violations.append(f"required diagnostic boundary is missing: {token}")
    if '"retry": true' in adapter or '"retry": true' in observer:
        violations.append("PermissionDenied observer must not return retry")
    if "tests_not_applicable" in docs_only:
        violations.append("docs-only classification must not accept a tests_not_applicable assertion")
    return violations


def main() -> int:
    problems = errors()
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print("Claude block diagnostics contracts PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
