# 178 — Independent Review Isolation

## Intent

Verify that a code review is called independent only when the review run has an exact, bounded evidence packet, no inherited implementer context, a distinct execution identity, and read-only authority supported by runtime attestation.

## Setup

- Build a review packet from allowlisted repository evidence and bind it to base SHA, head SHA, and the changed-file fingerprint.
- Schedule a review task that depends on the completed implementation task, declares `INDEPENDENT_REVIEW`, has `context_inheritance: none`, and has no write set.
- Supply structured review evidence and runtime attestation for the exact packet.

## Assertions

1. The packet has a deterministic fingerprint, an explicit allowlist, and bounded UTF-8 inputs; path traversal, secret/PII findings, and prohibited context classes are rejected.
2. A verified report requires different implementation and reviewer execution IDs, a clean read-only permission declaration, matching candidate and packet fingerprints, and verified runtime attestations.
3. Missing runtime evidence is `UNVERIFIED`; mismatch is `STALE` or `FAILED` as appropriate. Neither state satisfies a required independent review.
4. A required review that is not `VERIFIED` blocks downstream scheduler work and fails the Integration Gate.
5. Self-check is never upgraded to independent review by labels, prompt differences, or shared-session output.
6. The deterministic validator checks evidence structure and binding only. It does not claim to judge semantic review quality or authorize merge/release.

## Evidence

- `tests/validation/review_isolation_contracts.py`
- `tests/evidence/review_isolation_lifecycle.py`
- `tests/evidence/integration_gate_lifecycle.py`
