# Plan40 Core Change Proposal: Publication Prepare, Hook, and Diagnostics

## Problem and evidence

Plan40 asks for publication failures to retain their actual cause across read-only Prepare, Claude Code PreToolUse, and publication diagnostics, while making candidate observations and lifecycle state comparable and safely traceable.

On current `main` (`c2cc2136a48237177e30ceb71984cce5d75a34f4`), `PublicationError` falls back to message-prefix inference and finally `PUBLICATION_REJECTED`. A concrete reproduced example is `validate_personal_action()` raising `personal mode permits only the current engineering branch`; this message has no mapping and becomes the generic rejection. An AST inventory found 79 constructors without explicit reason codes in the reviewed publication authority, planning, diagnostics, Guard, and issuer code; 60 are in `publication_authority.py`. This establishes a structural cause for generic diagnostics, though it does not claim that this exact message caused the user's original denial.

Prepare, Hook and diagnostic outputs also do not expose one consistent set of safe, comparable candidate and runtime observations. Prepare can return `PLANNED` with `next_step: PUSH`, while authorization and execution are separate facts that must remain explicit. The existing `governance_audit` module supports an integrity-chained ledger, but publication diagnostics have no lookup by Diagnostic ID.

## Appropriateness and recommendation

- **Appropriateness:** Suitable. The failure is in the existing publication diagnostic contracts and can be repaired at their current authority boundaries.
- **Existing coverage / reuse:** Extend `PublicationError`, Prepare and Hook output, and the existing `governance_audit` ledger. Keep the current CLI facade and doctor.
- **Lower-layer alternative:** Fix call-site reason codes and shared output projections rather than adding a new Gate, Role, Capability, Skill, service, or ledger.
- **Context and token cost:** No bootstrap or per-turn context requirement is added; lookup is explicit and on demand.
- **Security and reliability:** Preserve redaction and fail-closed policy. Optional audit append failure must not change Hook allow/deny or publication authority. Do not create a default ledger.
- **Compatibility:** Add fields and lookup behavior; preserve existing keys, entry points and exit behavior. No data migration.
- **Constitution:** NO. Human Authority and protected safety semantics remain unchanged.
- **Architecture diagrams:** N/A. Existing components and authority flow remain unchanged; documentation describes additive observations and optional use of the current ledger.

## Approved scope

- Assign explicit stable reason codes at publication error call sites. Preserve known reason codes; use a separate stable internal diagnostic gap code when the cause is unknown. Never expose raw exception text.
- Make Prepare and Hook expose comparable, allowlisted worktree identity, candidate SHA, target ref, publication mode and AIPS runtime version observations. These fields are diagnostic evidence, not an authorization token.
- Clarify planned, awaiting authority, authorized, executed and blocked states. A suggested `PUSH` step does not mean authorized; do not report execution until observed.
- Optionally record a redacted diagnostic event only when `AIPS_GOVERNANCE_AUDIT_LEDGER` is already configured. Add read-only lookup by Diagnostic ID through the existing publish diagnose command and report integrity status. No new default persistence. Trace failure does not change the underlying decision.
- Add focused regression tests and update the existing publication scenario, CLI/Human/Claude/OpenCode guidance, affected orchestration contracts and active Core Change Test Matrix.
- Close the documentation impact resolver's full recursive requirements for publication-preflight, Harness, security, resource authorization, creative-boundary, scenario, skill-explorer and release-history topics.

## Out of scope

- Changing branch protection, credentials, authority policy, proposal requirements, Host confirmations, Human Authority, required checks, secret scanning, or remote repositories.
- Changing the protected push or merge operation form.
- Creating a new Gate, ledger, default persistent storage, service, role, capability, or unrelated optimization.
- Changing the Constitution or claiming repository-wide Impact Graph completeness.

## Impact and verification

The approved Change Impact artifact is stored in the task's EPHEMERAL Project Intelligence cache under `plan40-publication-diagnostics`; global Impact Graph coverage remains partial. The bounded consumer review includes publication CLI dispatch, Prepare, Claude Hook, audit ledger, focused tests, Scenario 261, and the listed docs. Final reconciliation must match the exact candidate diff and changed paths.

Validation evidence comprises focused regression cases for reason classification, unknown failures, observation drift, scan failures, Host denial, Human Authority, audit lookup, ledger integrity, redaction and failure isolation, plus relevant scenario/contract checks and the repository's exact-candidate Integration Gate. The active security-boundary test matrix and required repository check remain in force before merge.

## Risks and mitigations

- **Incorrect reason mapping:** Keep codes stable, bind each mapping to an explicit call-site test, and preserve redacted unknown-error handling.
- **False authorization/execution claim:** Make lifecycle status independent from `next_step`; test Host denial and Human Authority separately.
- **Observation leakage or misuse:** Allowlist values, redact paths and commands, and ensure observation fingerprints do not grant authority.
- **Audit failure changes policy result:** Treat trace as optional and test append failure under both allow and deny outcomes.
- **Partial graph:** Keep repository-wide coverage explicitly partial and reconcile the exact declared consumer paths manually.

## Approval

Status: APPROVED
Approved by: Human user
Approval reference: User reply in this task: “核准上述完整範圍（建議）”.
Approved at: 2026-10-14 (UTC; exact timestamp recorded in the EPHEMERAL Change Impact artifact).

## Approved documentation scope expansions

The initial implementation approval was supplemented by two explicit user approvals after the documentation impact resolver identified recursive requirements outside the original target set:

1. Approval to add the initial 15 required architecture, Harness, installation, Human-index and orchestration documents and update Change Impact.
2. Approval to add the further 8 required Security Assurance and orchestration documents and complete recursive closure.

The final resolved documentation impact preview covers 43 changed/declared paths, reports `complete: true`, and has no remaining required additions. All 23 recursively required documents are included in the candidate and Change Impact target set. This approval does not claim complete repository-wide Impact Graph coverage.
