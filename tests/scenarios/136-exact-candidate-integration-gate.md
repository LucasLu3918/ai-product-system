# Scenario 136 — Exact-Candidate Integration / Janitor Gate

Multiple bounded changes produce one integration candidate before merge.

Expected:
- the gate binds evidence to exact base SHA, head SHA, changed-file hash, validation profile hash and optional Core Change Test Matrix hash;
- the checked-out HEAD must equal the declared candidate head or the gate blocks as stale/mismatched;
- project-native lint, type/static and test commands are argv-based deterministic checks, not LLM judgment;
- applicable required check failure returns FAIL and blocks the required repository aggregate check;
- Core Change Test Matrix is reused when required rather than creating a parallel Janitor matrix;
- PASS is validation evidence only and grants no merge/release/Human authority;
- a changed candidate invalidates the prior fingerprint and must be validated again.

## Base Freshness

For pull requests, Janitor must freshly resolve the current target branch tip and compare it with the candidate's declared base SHA before running expensive checks.

If the target branch has advanced, the candidate is `BLOCKED` as stale and must be regenerated/revalidated. The current base-tip SHA is included in candidate evidence/fingerprints when supplied.
