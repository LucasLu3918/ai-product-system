# 176. Mandatory Candidate Secret Scanning

## Scenario

When an AIPS Git publication candidate is prepared, the existing built-in scanner must deterministically check the exact final tree and each commit in `base..head`. The check is required by the Integration Gate, bound to the candidate, policy and scanner hashes, and does not rely on an Agent remembering to run it or on external credentials.

## Acceptance criteria

- A high-confidence synthetic secret in the final tree fails the candidate.
- A secret added in one commit and deleted in a later commit still fails the candidate history scan.
- Strict publication mode ignores no inline line/file bypass markers.
- Lockfiles suppress only the generic secret-assignment detector; provider tokens and private-key patterns remain enabled.
- Unreadable, oversized, unknown-format, invalid-policy, expired-allowlist or incomplete-history inputs are BLOCKED, never PASS.
- Findings and CI evidence never include secret values; reports contain bounded metadata and hashes only.
- Integration Gate refuses a missing/non-required/path-filtered scanner check and binds base/head, changed-file hash, policy hash and scanner hash into the candidate fingerprint.
- Local publication preflight and GitHub Actions use the same scanner and policy; CI scans before installing expensive validation dependencies.
- The existing `repository` required context remains the branch-protection aggregate. Human Git Publish Approval remains authoritative.
- Gitleaks, GitGuardian and platform scanning remain optional defense-in-depth; no external credential is required for baseline.

## Evidence

- `tests/evidence/secret_scan_publication_lifecycle.py`
- `tests/evidence/secret_safety.py`
- `tests/validation/runtime_contracts.py`
- `config/integration-gate.yaml`
