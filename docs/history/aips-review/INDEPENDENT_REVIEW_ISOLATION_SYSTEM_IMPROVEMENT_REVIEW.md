# System Improvement Review: Independent Review Isolation

## Decision

Appropriate: YES — adopt as a Core/Orchestration capability extension for v0.62.0.

## User problem

AIPS already separates Reviewer and Author duties and defaults reviewers to read-only. It does not yet provide a consistent structured contract proving that a specific review used a distinct execution, fresh bounded context, canonical evidence, read-only authority, and the exact candidate being integrated.

## Proposed solution

Add `SELF_CHECK` and `INDEPENDENT_REVIEW` modes. Extend the existing Context Manifest and Task Graph, add a deterministic allowlist-based Review Packet Builder, validate independence evidence and exact-candidate freshness, and keep semantic judgment with the Reviewer while the Integration Gate checks evidence only.

## Existing coverage and reuse

- Reuse `orchestration/MULTI_REVIEW.md` and existing Author-fix / targeted re-review loop.
- Reuse `orchestration/schemas/context-manifest.yaml`, `orchestration/schemas/task-graph.yaml`, `scripts/deterministic_scheduler.py`, the Core Change Test Matrix, and the existing Integration Gate.
- Extend the existing read-only / no-write-set rule; add no Role or parallel Gate.
- Preserve context minimization, canonical evidence, human approval authority, and no-private-reasoning persistence.

## Design adjustments

- Reviewer context is an evidence allowlist, not “diff only”; necessary surrounding code, ADRs, contracts, and project instructions remain available.
- Independence does not require a different model/vendor. Same execution or inherited Implementer context cannot qualify.
- Do not semantically detect chain-of-thought or sanitize Implementer transcripts. Build reviewer inputs only from explicitly classified canonical evidence.
- AIPS may validate structured runtime evidence, but it must report `UNVERIFIED` when the active runtime cannot attest execution/context isolation; declarations alone do not prove a runtime boundary.
- Two-pass review uses evidence-first findings, then structured factual clarification with cited evidence, followed by targeted re-review.

## Impact

- Context/token cost: bounded to the selected evidence packet; no full transcript propagation.
- Security/reliability: strengthens least-context, least-authority, privacy, and stale-review handling. Missing or contradictory proof fails closed when independent review is required.
- Backward compatibility: Task Graph and Context Manifest extensions remain optional for existing non-review tasks; old review flows remain `SELF_CHECK` unless supported evidence is present.
- Constitution: NO. Human, security, publication, and merge authority do not change.
- Roles/Gates: no new Role or approval Gate.
- Human documentation: update the architecture overview and maintenance/conformance docs where behavior changes.
- Agent documentation: update review, orchestration, scheduler, integration, and schema contracts.
- Architecture diagrams: AFFECTED. Show evidence packet construction, isolated read-only Reviewer execution, review evidence, and exact-candidate Integration Gate validation.

## Recommendation and implementation order

1. Persist the Core Change proposal and impact-derived matrix.
2. Specify review and evidence contracts in existing docs/schemas.
3. Implement deterministic packet/evidence validation and scheduler enforcement.
4. Bind required review evidence to Integration Gate candidate checks.
5. Add direct lifecycle scenarios, update diagrams/docs, validate and prepare a PR.

## Activation Status

The capability is implemented, but PR enforcement is deferred and disabled in the active Core Change Matrix until a trusted runtime-attestation verifier is available. The opt-in evidence contract remains fail-closed when explicitly required.

## Approval

Status: APPROVED
Approved by: User
Approved at: 2026-09-25 (conversation instruction)
Approval record: User approved implementation of all plan6 recommendations and local verification, then approved retaining the mechanism while disabling strict PR enforcement until future activation.
