# Core Change Proposal: Context Integrity and Preflight Feedback

## Purpose

Correct misleading task freshness and advisory-only context budgets; require real Git reconciliation before Change Impact can reach `READY`; report retrieval cache failures with an actionable safe fallback; and surface candidate content/identity issues before expensive validation.

## Why this is a core/large change

It changes the Turn Context contract, runtime hook output, governance validation semantics and publication preflight for multiple consumers.

## Proposed Scope

### In scope

- Derive capsule and task freshness from the current complete scan; claim irrelevance only when selected scope is mapped and every affected change is known.
- Sanitize all inline derived text with the existing Runtime Content Safety Boundary and enforce one deterministic assembled context budget with truncation metadata.
- Validate `READY` Change Impact against resolvable Git base/head, the actual diff digest and actual changed paths; retain syntax validation for draft states.
- Return privacy-safe retrieval-index failure codes and remediation while preserving source-pointer fallback.
- Add cheap staged/unstaged candidate safety and configured Git identity checks to publication preview.
- Add lifecycle, CLI, negative-path, scenario and documentation coverage.

### Out of scope

- Constitution, authority precedence, project persistence formats, new roles/skills/gates, semantic retrieval providers, publishing authority and merge policy.

## Expected Files / Modules

- `scripts/project_intelligence.py`, `scripts/retrieval_intelligence.py`, `scripts/turn_context_hook.py`, `scripts/publish_preflight.py`
- `tests/evidence/`, `tests/validation/`, `tests/scenarios/`, `tests/scenario_coverage.yaml`
- `orchestration/`, `docs/ARCHITECTURE.md`, `docs/human/PROJECT_INTELLIGENCE.md`, `docs/human/MAINTENANCE.md`
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`

## Impact

### Architecture / Contracts

Additive manifest diagnostics; stricter validation for `READY`; unchanged canonical authority and fallback sources.

### Data / Migration

No canonical schema migration. Existing placeholder `READY` artifacts require reconciliation before they can validate.

### Security / Reliability

Reuse `safe_emit(sink="runtime_log")` for derived text. Unknown freshness remains fail-closed for mutations. Index failure never removes canonical pointers. Publication preflight only reports blockers.

### Compatibility / Rollback

Draft and implementation-approval artifacts remain readable. Consumers may ignore added manifest fields. Rollback is a source revert; no index or canonical project-data migration.

### Tests / Validation

Impact-derived matrix is `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`; it binds the final base/head and changed-file digest and requires local lifecycle, CLI, safety, scenario, repository and remote CI evidence.

### Secret / Credential Impact

Secrets required: NO

Approved acquisition mechanism: N/A

Leakage/redaction review: exercise fake email/secret values through Core, temporal, override and retrieval context; ensure preview findings expose categories only.

Rotation/revocation plan if exposure is found: N/A; use synthetic fixtures only.

### Documentation / Diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: AFFECTED — revise Project Intelligence flow to show proven relevance, enforced context assembly and post-diff Git reconciliation.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: AFFECTED — clarify bounded context and truthful fallback semantics.
- Human SVG architecture/lifecycle diagrams: AFFECTED — update `docs/human/assets/project-intelligence-overview.svg` to show relevance proof, context budgets, safe fallback and Git-bound READY.

## Risks

- Conservative relevance can report `STALE` more often until project topic watches are complete.
- `READY` validation becomes stricter for placeholder legacy evidence.
- Token estimate is deterministic character-based estimation, not the downstream model tokenizer; the hard bound applies to the documented estimator and rendered hook payload.

## Recommendation

Extend the existing context, safety, preflight and Change Impact abstractions. Do not add a parallel gate or persist prompts/usage telemetry.

## Proposed Implementation Order

1. Add boundary tests and Git-backed Change Impact validator.
2. Correct freshness and safe, budgeted context assembly.
3. Add index diagnostics and early candidate checks.
4. Update flow docs/scenario/matrix; validate exact candidate locally and in CI.

## Approval

Status: APPROVED
Approved by: User
Approved at: 2026-09-24
Approval record: User requested implementation of all previously reviewed improvements, local verification, and remote PR merge to `main`.

Scope fingerprint: changed-files hash `87f928e31bed3179997b4ec59892b00a69539778535166749efa3c23e2856bfd` (base `704797c2032e96c312ba4bb3bcf0f0dde1115d65`).
Proposal fingerprint: sha256:9a1344032f7aae82dd25eae39510bd261bfad74743f10ec1e0b18c1cf6688e2e
