# Scenario 205: Branch cleanup proposal freshness

Given a merged branch candidate, when the read-only cleanup proposal is generated, then it binds the branch SHA, merged PR, date, main baseline, and content fingerprint. Changed branch content or main baseline makes the proposal stale; generation never deletes a branch.

Evidence: `tests/evidence/branch_hygiene_lifecycle.py`.
