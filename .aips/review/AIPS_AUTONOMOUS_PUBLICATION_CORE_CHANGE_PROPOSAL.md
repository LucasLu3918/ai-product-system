# Core Change Proposal — AIPS Autonomous Publication and Recovery

## Approved scope

The user approved implementation from `plan31`, limited to the AI Product System (AIPS); Lucas Lab repository settings and rulesets are excluded. The user also explicitly approved the task-scoped Human authorization semantics. This proposal records implementation scope and does not replace validation or exact-candidate publication checks.

Extend the existing publication authority, planning, and native-hook boundaries to:

- report safe, actionable causes when staged publication content cannot be inspected;
- recognize `feat/` as an engineering branch prefix;
- preserve isolated clean publication candidates and resumable, idempotent live-state observation;
- support `gh pr merge --auto` only with exact PR/head binding and verified non-empty required checks;
- keep high-assurance external grants, existing personal-mode native confirmations, and all fail-closed boundaries.

## System improvement review

- **Appropriateness:** Suitable as a bounded extension of the existing publication system.
- **User problem:** Publication diagnosis and recovery should be predictable, while the requested PR can merge after repository checks.
- **Existing coverage:** `publication_authority.py`, `publication_planning.py`, `governance_guard.py`, and Scenario 240 already implement exact candidate binding, scanning, live PR reuse, merge checks, and recovery.
- **Reuse:** Extend these modules and their existing tests; no parallel publisher, new role, skill, capability, or approval gate.
- **Security:** A task-level user request cannot be converted into a general-purpose grant by agent-authored files. Keep native per-merge confirmation for personal mode. Keep the external issuer as the only high-assurance authority, and never infer Human approval from a planning artifact.
- **Compatibility:** Additive branch/CLI behavior; preserve safe defaults and reject empty or unknown required-check results.
- **Tests:** Unit, hook, authority, recovery, no-required-check, stale head, and exact candidate checks; complete local Integration Gate and remote PR checks.
- **Constitution:** Approval semantics are acknowledged, but no constitutional text or general authority rule is changed. This implementation preserves the existing Human authorization source and native confirmation boundary.
- **Excluded:** Lucas Lab files/settings/rulesets, direct `main` pushes, `--admin`, bypass, automatic grant issuance, branch deletion, and agent-written authorization records.

## Impact and documentation

Targets are the existing publication authority, hook, preflight CLI, their unit tests, Scenario 240 and its conformance projections, architecture and relevant publication guidance, and this proposal/matrix/Change Impact record. The repository-wide Impact Graph is partial; direct module callers and human/runtime consumers are reviewed manually, and no global completeness claim is made.

## Publication

Target `origin` / `LucasLu3918/ai-product-system`, PR to `main`; merge only after the exact candidate Gate and required remote checks pass. User request explicitly authorizes a PR and merge for this change. No direct push to `main`, release, admin bypass, or Lucas Lab change.
