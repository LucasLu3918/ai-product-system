# Core Change Proposal: Evidence-Backed Change Impact Unknown Dispositions

## Purpose

Allow a Change Impact record to preserve each discovered unknown together with a reviewable resolution, mitigation, or accepted limitation. The implementation gate may treat an item as closed only when its disposition has a substantive decision, verifiable evidence, and explicit Human review.

## Why this is a core/large change

Change Impact controls whether high-risk repository changes may proceed. Its current validator treats every non-empty `unknowns` list as unresolved, while its schema provides no representation for a reviewed disposition. This creates a governance dead end for bounded graph coverage and evidence-backed mitigations. A permissive fix could weaken the safety boundary, so the data contract, validator, lifecycle tests, and documentation must change together.

## System Improvement Review

- **Appropriateness:** Appropriate. This extends an existing gate contract rather than adding a new gate or capability.
- **User problem:** AIPS cannot record evidence that resolves or contains a discovered uncertainty without deleting the uncertainty itself.
- **Existing coverage:** `scripts/project_intelligence.py::validate_impact_document` rejects every non-empty `unknowns`; `templates/intelligence/CHANGE_IMPACT.yaml` defines only a string list. Traversal can report seed-scoped graph coverage, but the Change Impact approval contract cannot represent its reviewed disposition.
- **Reuse / extension candidates:** Extend the existing Change Impact document, validator, traversal lifecycle evidence, and current core-change test matrix.
- **Lower-layer alternative:** A one-off manual review could explain the decision but would not be machine-checkable or reusable across projects. A project-local workaround would duplicate the same governance logic.
- **Context / token cost:** Small and on-demand; no new always-loaded role, skill, capability, or runtime service.
- **Security / reliability:** Fail closed for legacy strings, open/invalid dispositions, missing or stale evidence, absent Human approval, and mismatched traversal scope. Never upgrade repository-wide coverage from seed-scoped evidence.
- **Backward compatibility:** Existing string entries remain valid syntax and continue to block approval. New structured entries are additive.
- **Scenario / test impact:** Add one lifecycle scenario and focused contract, integrity, compatibility, and CLI validation.
- **Human docs impact:** Explain how to review a resolved, mitigated, or accepted limitation and why global coverage remains distinct from scoped coverage.
- **Agent docs impact:** Update the Change Impact workflow and canonical template with required fields and review steps.
- **Architecture diagram impact:** Update the Change Impact flow in `docs/ARCHITECTURE.md`; high-level system and SVG diagrams are N/A because component topology and authority do not change.
- **Constitution impact:** NO. Human Authority, publication authority, and existing protected boundaries remain unchanged.
- **Recommended AIPS solution:** Add typed dispositions to the existing `unknowns` collection and validate evidence/review at implementation approval. Preserve legacy fail-closed behavior and defer actual-diff node disposition checks until READY.
- **Additional optimization candidates:** None included.

## Proposed Scope

### In scope

- Structured Change Impact unknowns with `OPEN`, `RESOLVED`, `MITIGATED`, and `ACCEPTED_LIMITATION` states.
- Verifiable repository-file evidence bound to SHA-256 digests and scoped traversal evidence bound to the recorded traversal report.
- Explicit review metadata for every closed disposition.
- Validation at `IMPLEMENTATION_APPROVED` and `READY`, while preserving final diff reconciliation requirements at READY.
- Legacy string compatibility with unchanged fail-closed behavior.
- Canonical template, Agent and Human guidance, architecture flow, scenario, validators, and changelog/version updates.

### Out of scope

- Making incomplete evidence pass.
- Treating scoped coverage as repository-wide graph completeness.
- Automatically deciding that a limitation is acceptable or resolving semantics with an LLM.
- Changing protected Human Authority, release authority, runtime enforcement, or publication controls.
- Migrating old Change Impact artifacts automatically.

## Expected Files / Modules

- `scripts/project_intelligence.py`
- `templates/intelligence/CHANGE_IMPACT.yaml`
- `orchestration/CHANGE_IMPACT.md`
- `docs/human/PROJECT_INTELLIGENCE.md`
- `docs/ARCHITECTURE.md`
- `config/documentation-sync.yaml`
- `config/documentation-placement.yaml`
- `config/architecture-surfaces.yaml`
- `tests/validation/change_impact_resolution_contracts.py`
- `tests/evidence/change_impact_resolution_lifecycle.py`
- `tests/validate_repository.py`
- `tests/validation/static_contracts.py`
- `tests/validation/conformance_isolation.py`
- `tests/scenario_coverage.yaml`
- `tests/scenarios/179-evidence-backed-impact-unknown-dispositions.md`
- `VERSION`
- `CHANGELOG.md`
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`

## Impact

### Architecture / Contracts

The Change Impact contract gains a backward-compatible structured item form. Approval validation distinguishes unresolved items from evidence-backed reviewed dispositions. The existing traversal output and final Git reconciliation remain canonical.

### Data / Migration

No persistent application data changes. Existing string-based records remain readable and continue to block approval when non-empty; no automatic migration is performed.

### Security / Reliability

Closed dispositions require a bounded enum, a non-empty resolution, verifiable evidence, and explicit Human review. File evidence must remain inside the project root and match its recorded digest. Traversal evidence must be complete, non-truncated, unresolved-free, and match its declared seed-scoped coverage. Malformed or stale evidence blocks approval.

### Compatibility / Rollback

The schema extension is additive. Rollback removes the validator behavior and template guidance without touching stored project data. Existing artifacts continue to fail closed as before.

### Tests / Validation

Run targeted unit/contract/lifecycle/CLI tests, scenario conformance, static and documentation contracts, the repository validator, and the exact-candidate Integration Gate.

### Secret / Credential Impact

Secrets required: NO.

No credentials or user prompt content are needed. Evidence references contain repository paths, hashes, bounded traversal metadata, and explicit review references only.

### Documentation / Diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: AFFECTED — clarify the evidence disposition check inside the existing Change Impact gate.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: N/A — no component topology or authority change.
- Human SVG architecture/lifecycle diagrams: N/A — no component or lifecycle topology change.

## Risks

- Weakly validated evidence could make an unsafe change appear resolved; mitigate with strict types, path containment, digest matching, traversal checks, and Human review.
- A human may accept a scoped limitation; require the limitation and scope to remain explicit and prohibit global coverage claims.
- Old artifacts cannot distinguish reviewed decisions; preserve legacy blocking behavior and require explicit review before converting them.

## Recommendation

Proceed with the narrow additive contract and fail-closed validator described above.

## Proposed Implementation Order

1. Add the structured contract and deterministic validator with focused tests.
2. Add lifecycle/CLI evidence and regression coverage for legacy and malformed records.
3. Update Agent/Human guidance, architecture flow, synchronization contracts, and Scenario 179.
4. Run the impact-derived test matrix, repository validation, and exact-candidate Integration Gate.

## Approval

Status: APPROVED
Approved by: User
Approved at: 2026-09-26
Approval record: User explicitly approved implementation of first-class evidence-backed Change Impact unknown dispositions while preserving the global graph limitation.
Proposal fingerprint: pending
Scope fingerprint: pending
