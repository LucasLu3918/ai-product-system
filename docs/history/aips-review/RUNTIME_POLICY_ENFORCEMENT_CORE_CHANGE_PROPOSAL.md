# Core Change Proposal: Runtime Policy Enforcement

## System Improvement Review

- **Appropriateness:** Suitable as a core extension of existing Resource Authorization, Runtime Content Safety, Governance Guard, Approval Binding, Governance Audit, Runtime Adapters and Execution Isolation.
- **User problem:** High-risk tool actions may occur before later workflow/release gates. Existing resource authorization is pre-execution evidence and does not provide a common action-level decision and enforcement contract.
- **Recommended solution:** Add a deterministic provider-neutral Runtime Policy Enforcement contract and evaluator; connect the existing verified pre-tool hooks only to actions they can reliably normalize; bind runtime approvals to exact actions; require verified sandbox/network enforcement where hooks cannot observe indirect network activity.
- **NeMo:** Optional semantic provider trial only. NeMo must never decide authorization or widen deterministic ALLOW/DENY. Current NVIDIA IORails tool validation is experimental and limited to OpenAI Chat Completions `openai`/`nim`; it is not an AIPS cross-runtime enforcement layer.
- **Reuse:** Extend existing `governance_guard.py`, Resource Authorization, Approval Record, Governance Audit, adapter registry and verified sandbox contract. Do not add Roles, Skills, approval gates, audit subsystems or a second data classification system.
- **Constitution impact:** NO. Preserve protected Human Authority, approval and publication semantics. This change adds an execution policy boundary without changing who may approve or merge.

## Scope

### In scope

- Versioned Runtime Action Envelope and declarative deterministic policy schema.
- `ALLOW`, `DENY`, `REQUIRE_APPROVAL`, and `BLOCKED` decision contract; deny-overrides; fail-closed invalid/missing policy behavior.
- Action digest binding tool, operation, destination, normalized arguments, data labels, Change Boundary and effective SAL; execution must match the evaluated digest.
- Extend existing Approval Record verification for narrow, expiring runtime-action scopes; do not create a separate approval store or approval authority.
- Integrate policy evaluation with Claude `PreToolUse` and Gemini `BeforeTool` where normalized action data is available; preserve current Git publication checks. Codex remains `ADVISORY`; generic runtimes remain `UNSUPPORTED`.
- SAL3/4 external egress policy plus verified sandbox/network controls; document the limits of shell hooks and indirect child processes.
- Sanitized critical-boundary audit events through existing Governance Audit; never persist raw payloads/secrets.
- Optional semantic provider interface and deterministic synthetic adapter contract/evaluation fixtures. No mandatory NeMo dependency, live provider credential, or model call in the enforcement path.
- Update architecture and security guidance, diagrams, documentation placement/coverage, lifecycle evidence and deterministic negative-path tests.

### Out of scope

- Claiming universal or non-bypassable interception for `TOOL_GUARDED` hooks.
- Replacing OS/sandbox egress controls with command parsing or NeMo.
- Automatically creating approvals, bypassing human authority, or allowing semantic output to override deterministic DENY/BLOCKED.
- Making NeMo a mandatory dependency or running provider-backed/live network tests.
- Changing Constitution, adding new Roles/Skills/Gates, or publishing a release.

## Change Boundary

- Runtime action and policy schema/evaluator.
- Existing governance hook integration, approval fingerprint/expiry checking, sanitized audit interaction and supported adapter declarations.
- SAL/data-label/external-destination policy and sandbox enforcement contract.
- Focused lifecycle, contract, security and synthetic semantic-provider evidence.
- Human/agent docs, architecture diagram, documentation placement/coverage and candidate-bound Core Change Matrix.

## Security and compatibility

- No credential value is accepted in the action envelope; references only.
- Missing or invalid labels, policy, approval binding, action digest or required enforcement capability cannot result in ALLOW.
- Deterministic DENY wins; semantic checks can only deny or escalate.
- Existing publication flows retain current behavior unless explicitly covered by the runtime action contract.
- Existing adapter truthfulness is preserved; a hook does not imply network sandboxing.
- No persistent data migration is intended. Existing Approval Records remain valid for their current operation; runtime actions require the additional exact digest/scope and expiry fields.

## Validation

Use `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`. Required evidence covers schema/evaluator contracts, approval/action drift and expiry, hook response formats, unsupported runtime blocking, semantic monotonicity, audit redaction, sandbox network deny/allowlist behavior, existing publication-guard regression, docs/schema/conformance and exact candidate reconciliation. Live NeMo/network provider evidence is explicitly `NOT_RUN` unless the existing approved synthetic lane can verify locally without external credentials.

## Approval

- **Status:** APPROVED
- **Approved by:** User
- **Approval reference:** User request in the current Codex task: “請幫我依照建議實作所有事項，本地驗證完後需完成遠端pr合至main”; scope derives from the preceding plan5 implementation brief.
- **Approved scope:** Exact scope and exclusions above. PR publication and merge into `main` are explicitly requested. Scope changes affecting authority, required providers, live credentials, or data transfer require renewed approval.
- **Approved at:** 2026-09-25 (Asia/Taipei)
