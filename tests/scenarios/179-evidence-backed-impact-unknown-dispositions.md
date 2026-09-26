# 179. Evidence-backed Change Impact unknown dispositions

## Scenario

Change Impact must preserve discovered uncertainty while allowing an explicitly reviewed, evidence-backed resolution, mitigation, or accepted limitation. Approval stays fail closed for legacy strings, OPEN or malformed entries, missing Human review, stale or out-of-root file evidence, and traversal evidence that is incomplete or bound to a different seed scope.

## Acceptance criteria

- Structured unknowns retain a stable ID and description, a bounded disposition, a substantive resolution, evidence, and explicit Human review.
- `OPEN` remains unresolved; `RESOLVED`, `MITIGATED`, and `ACCEPTED_LIMITATION` pass only with valid evidence and approved Human review.
- Legacy string entries remain readable and block `IMPLEMENTATION_APPROVED` and `READY`.
- Repository-file evidence is repository-relative, resolves inside the project root including symlinks, is a regular readable file, and matches its SHA-256.
- Traversal evidence matches the canonical digest of the recorded report, is complete and unresolved-free, and references a scope included in that report; scoped coverage does not upgrade global coverage.
- `READY` still requires the exact clean Git base/head, binary diff digest, changed-file set, declared target paths, and reviewed traversal node dispositions.
- No data migration, automatic semantic decision, external lookup, or new runtime role is introduced.

## Evidence

- `tests/validation/change_impact_resolution_contracts.py`
- `tests/evidence/change_impact_resolution_lifecycle.py`
- `scripts/project_intelligence.py`
- `templates/intelligence/CHANGE_IMPACT.yaml`
