#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from github_ruleset_policy import assess as assess_rules
from version_tag_policy import evaluate as evaluate_tag


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    sha = "a" * 40
    empty_changelog = "# Changelog\n\n## Unreleased\n\n## 0.73.0\n- Released.\n"
    require(evaluate_tag("0.73.0", sha, sha, None, changelog_text=empty_changelog)["status"] == "READY_FOR_EXPLICIT_RELEASE_APPROVAL",
            "exact main candidate should be ready for a separate release decision")
    require(evaluate_tag("0.73.0", sha, sha, None, "0.72.0", empty_changelog)["status"] == "BLOCKED",
            "a candidate whose VERSION differs from the requested release must be blocked")
    require(evaluate_tag("0.73.0", sha, "b" * 40, None, changelog_text=empty_changelog)["status"] == "BLOCKED",
            "a pre-merge candidate must not become tag-ready")
    require(evaluate_tag("0.73.0", sha, sha, "b" * 40, changelog_text=empty_changelog)["status"] == "BLOCKED",
            "moved/existing mismatched tags must be blocked")
    ready = evaluate_tag("0.73.0", sha, sha, None, changelog_text=empty_changelog)
    require(ready["tag_write_authorized"] is False and ready["historical_backfill"] is False,
            "readiness must never authorize tag writes or historical backfill")
    cases = (
        ("# Changelog\n\n## Unreleased\n- pending\n\n## 0.73.0\n", "non-empty Unreleased section must block"),
        ("# Changelog\n\n## 0.73.0\n- released\n", "missing Unreleased heading must block"),
        ("## Unreleased\n\n## Unreleased\n", "duplicate Unreleased headings must block"),
        ("##Unreleased\n", "malformed Unreleased heading must block"),
    )
    for changelog, message in cases:
        require(evaluate_tag("0.73.0", sha, sha, None, changelog_text=changelog)["status"] == "BLOCKED", message)
    require(evaluate_tag("0.73.0", sha, sha, None)["status"] == "BLOCKED",
            "unavailable changelog content must fail closed")

    desired = {"required_status_checks": ["repository"], "bypass_actors": []}
    require(assess_rules({}, desired)["status"] == "UNKNOWN", "incomplete API snapshot must fail closed")
    current = {
        "source_complete": True, "branch_protection": {"required_checks": ["repository"]},
        "rulesets": [], "bypass_actors": [],
    }
    report = assess_rules(current, desired)
    require(report["status"] == "NO_CHANGE", "matching current policy must produce no-change assessment")
    require(report["activation_authorized"] is False and report["api_write_performed"] is False,
            "assessment must remain read-only")
    expanded = assess_rules({**current, "branch_protection": {"required_checks": []}}, desired)
    require(expanded["required_checks_added"] == ["repository"], "diff must disclose every newly required check")
    require((ROOT / "config/version-tag-policy.yaml").exists()
            and (ROOT / "config/github-ruleset-policy.yaml").exists(), "policy configuration must be present")
    print("VERSION / RULESET POLICY LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
