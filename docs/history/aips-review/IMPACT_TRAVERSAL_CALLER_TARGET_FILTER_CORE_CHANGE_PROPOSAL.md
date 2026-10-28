# Core Change Proposal: Exact caller target filtering in bounded impact traversal

## Problem

Retrieval Intelligence selected same-name caller rows before resolving each call to its definition path. A large number of unrelated symbols could therefore consume the relevant edge budget and produce `TRUNCATED/max_edges` even when the target had few or no callers. Resolving candidates only after that limit created a false incomplete result.

## Approved scope

- Resolve indexed lexical caller candidates to their exact target path and line before charging the relevant-edge budget.
- Add a separate bounded raw-candidate inspection budget, exposed in traversal limits and report counts.
- Keep overflow fail-closed as `TRUNCATED/caller_candidate_limit`.
- Preserve consumer traversal, public facade, risk policy, index schema, authority, and repository-wide coverage semantics.
- Update direct lifecycle/contract evidence, Scenario 175, canonical policy and human documentation, placement triggers, and the Core Change Test Matrix.

No API, persisted schema, runtime role, governance authority, or external service changes are proposed.

## Bounds and behavior

For Python callers, exact target path and line filtering occurs before the relevant-edge limit; other languages retain existing lexical resolution. At most `min(max_edges × 10, 3,000)` raw caller rows are processed per traversal; one additional row may be fetched as an overflow sentinel, and the reported fetched-row count includes it. Unresolved rows remain explicit evidence; if additional raw rows exist after the candidate budget, traversal reports truncation and cannot establish completeness.

## Evidence and verification

- Positive lifecycle: hundreds of unrelated same-name calls do not hide exact-path callers or consume their edge budget.
- Negative lifecycle: candidate scan exhaustion reports `caller_candidate_limit`, stays within the configured sentinel bound, and remains truncated.
- Negative lifecycle: exact resolved callers beyond the remaining edge budget report `max_edges` rather than `COMPLETE`.
- Contract: traversal defaults and the 10x multiplier remain explicit.
- Affected-boundary Gate: lifecycle, contract, validator/docs placement, CLI facade, security/budget, and repository Integration Gate.
- Re-run and validate the original WebM scanner traversal after implementation.

## Risk and compatibility

The additional query work is linearly capped by the explicit candidate budget. Existing relevant edge/node/depth caps continue to apply. Consumer traversal and CLI/facade shapes remain compatible except for additive candidate count/limit evidence fields. A stale index, unresolved target, or candidate overflow cannot become complete evidence.

Architecture diagram: not applicable; module boundaries and call direction are unchanged.

## Approval and status

Scope approved by the user in the Codex task on 2026-10-28 UTC: exact-target filtering with bounded candidate scanning and additional security validation. Implementation is in progress; the Core Change Test Matrix remains DRAFT until full evidence and final diff binding are reconciled.
