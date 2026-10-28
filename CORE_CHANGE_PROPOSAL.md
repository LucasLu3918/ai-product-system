# Core Change Proposal

## Purpose

Allow the mandatory AIPS candidate scanner to pass KOHAMI's unchanged `main` baseline without changing or deleting its existing source files or the full INP evidence JSON.

## Why this is a core/large change

The change alters the mandatory publication security scanner and the bound scan policy used across AIPS projects. It affects publication eligibility and must preserve fail-closed behavior for real secrets and incomplete scans.

## Proposed Scope

### In scope

- Recognize only the demonstrated generated-password and parameterized SQL expressions as non-literal values for the generic assignment detector.
- Keep known credential detectors and generic high-entropy literal detection active.
- Add an 8,000,000-byte ceiling for JSON files while keeping the 2,000,000-byte ceiling for other text files; block oversized JSON and all other incomplete inputs.
- Add scanner regressions, update the candidate-scan scenario and canonical security/maintenance guidance, then run the system validation and exact-candidate scan.
- Satisfy the AIPS documentation-impact closure for content-safety and publication placements in the architecture, installation, conformance, project-intelligence, technology and user guidance.

### Out of scope

- Editing KOHAMI `main` baseline source or deleting/reformatting its raw metrics evidence.
- Disabling detectors, adding repository-specific findings allowlists, or changing publication authority or protected-branch policy.
- Changing the AIPS Constitution or adding new roles, skills, or gates.

## Expected Files / Modules

- `scripts/check_secret_leakage.py`
- `config/secret-scan.yaml`
- `tests/test_secret_scan_baseline_compat.py`
- `tests/scenarios/176-mandatory-candidate-secret-scanning.md`
- `docs/ARCHITECTURE.md`, `docs/human/ARCHITECTURE_OVERVIEW.md`, `docs/human/CONFORMANCE.md`, `docs/human/INSTALLATION.md`, `docs/human/PROJECT_INTELLIGENCE.md`, `docs/human/TECHNOLOGY_GUIDE.md`, `docs/human/USER_GUIDE.md`
- `docs/human/SECURITY_ASSURANCE.md`, `docs/human/MAINTENANCE.md`, `orchestration/CONFORMANCE.md`, `orchestration/CONTENT_SAFETY_BOUNDARY.md`
- Exact-candidate `docs/qa/CORE_CHANGE_TEST_MATRIX.yaml` and required change-impact evidence.

## Impact

### Architecture / Contracts

No public API changes. The scanner policy accepts one additional optional limit and preserves fallback compatibility for policy files without it.

### Data / Migration

No data migration or source-data edits. JSON is still scanned as UTF-8 text; the larger bound is JSON-only and remains finite.

### Security / Reliability

False-positive recognition is limited to the two observed source-expression forms. Known token/private-key detectors remain unchanged. High-entropy literal assignments remain blocked. Non-JSON files over 2 MB and JSON files over 8 MB remain blocked.

### Compatibility / Rollback

Old policy documents retain their existing 2 MB behavior through the fallback. Reverting the scanner and policy restores current blocking behavior. KOHAMI publication remains blocked until the required scanner evidence and checks pass.

### Tests / Validation

Impact-derived Test Matrix:

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Secret scanner | Required | Required: generated expression, parameterized SQL, real high-entropy literal | Required: final tree and `base..head` history | Required: policy validation and candidate binding | N/A: no user-facing runtime | Required: sensitive detectors stay active, >2 MB JSON scanned, over-limit inputs fail closed | Required: rollback by reverting scanner/policy; no data migration | Required: publication scan path uses same policy | Required: scenario and canonical guidance | N/A for product-flow E2E |

Recompute trigger if scope expands: changes to other detectors, formats, authority checks, scanner invocation, or repository baseline files.

Required release/CI evidence: focused scanner tests, publication lifecycle tests, repository validation, exact-candidate Integration Gate, AIPS candidate/history scan, and required `repository` check on the AIPS PR.

### Secret / Credential Impact

Secrets required: NO

Approved acquisition mechanism: N/A

Leakage/redaction review: synthetic values only; scanner findings remain redacted.

Rotation/revocation plan if exposure is found: N/A; any real credential finding remains blocking.

### Documentation / Diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: N/A — no topology or component boundary changes.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: N/A — no topology changes.
- Human SVG architecture/lifecycle diagrams: N/A — no workflow authority changes.

## Risks

- A narrowly missed expression could leave a harmless baseline blocked; do not broaden recognition without a new review.
- A detector regression could hide a credential; negative-path tests must prove literal credentials still fail.
- The JSON limit increases worst-case per-file memory compared with the current 2 MB cap; the 8 MB bound is finite and does not change other file types.
- The first system preflight completed update/dependency checks and refreshed the global harness, but its repository validation was interrupted while a creative lifecycle subprocess did not return. Full validation remains required.

## Recommendation

Approve this narrow AIPS scanner core change. Keep the existing baseline files and metrics unchanged, and publish the scanner repair through its own protected `main` PR only after its complete validation evidence is ready.

## Proposed Implementation Order

1. Complete the scanner regression tests and exact candidate/history behavior.
2. Update the canonical scenario and security/maintenance documentation.
3. Build the exact Core Change Matrix from the final changed-file set and run the required AIPS validation.
4. Obtain code review, publish the AIPS PR, wait for its exact required check, and merge only with a fresh protected-branch observation.
5. Re-run the KOHAMI candidate scan with the merged AIPS scanner, then resume the already authorized KOHAMI PR and merge workflow.

## Approval

Status: APPROVED BY USER
Approved by: User in Codex conversation
Approved at: 2026-10-24 08:47 UTC
Approval record: User selected “核准提案並授權 AIPS PR／合併（建議）” for this exact proposal and authorized continuation to the KOHAMI PR.
Proposal fingerprint:
Scope fingerprint:
