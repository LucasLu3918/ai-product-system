# Scenario 205: Branch cleanup proposal freshness

Given a merged branch candidate, when the read-only cleanup proposal is generated, then it binds the branch SHA, merged PR, date, main baseline, and content fingerprint. Changed branch content or main baseline makes the proposal stale; generation never deletes a branch. Applying an exact manifest also requires its recorded main baseline to equal the current target tip, and any absent manifest ref blocks the complete batch as replay or partial-state evidence.

Evidence: `tests/evidence/branch_hygiene_lifecycle.py`.

Source report artifacts bind their successful main run SHA to the proposal fingerprint. Expired, malformed or unexpected archive members, wrong report source, altered fingerprint or invalid issuer identity block cleanup. Active local Git worktrees are explicitly preserved; the report does not claim visibility into unrelated clones.
