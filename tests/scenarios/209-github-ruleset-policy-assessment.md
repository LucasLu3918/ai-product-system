# Scenario 209: GitHub ruleset policy assessment

Given a complete read-only snapshot of branch protection, rulesets, required checks, and bypass actors, when it is compared with the candidate policy, then the report shows policy differences and newly required checks. Incomplete or denied inputs remain UNKNOWN, preserve existing protection, and never activate rulesets or write settings.

Evidence: `tests/evidence/version_policy_lifecycle.py` and `tests/evidence/repository_governance_snapshot_lifecycle.py`.
