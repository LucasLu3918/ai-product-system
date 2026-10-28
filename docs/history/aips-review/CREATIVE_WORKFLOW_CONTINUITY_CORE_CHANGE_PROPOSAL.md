# Creative Workflow Continuity & Reliable Execution

## Purpose

Fix the observed Chinese illustration-intent and OpenCode clarification loop while preserving current-session, bounded creative authorization. Improve local engine diagnostics and recovery guidance, and exercise the existing multi-item workflow against the original three-prompt conversation.

## Why this is a core/large change

The change touches a security-sensitive authorization lifecycle, its OpenCode native adapter, local creative execution diagnostics, and conformance evidence.

## Approved Scope

### In scope

- Recognize Chinese terms such as `立繪` consistently in task routing and creative admission.
- Derive a bounded output budget from a confirmed character/output specification, including two individual character portraits.
- Preserve creative task specification separately from each prompt's authority. A response may receive a fresh, bounded grant only while completing the active creative clarification flow; cancellation, unrelated work, session-root changes, and scope expansion revoke or deny it.
- Improve diagnostic distinction between executable discovery, version-probe health, configured capability, static host compatibility, and real inference. Preserve `UNVERIFIED` when no inference evidence exists.
- Return reason-specific recovery steps for blocked creative actions.
- Reuse `creative generate-set` for independent role Bundles; do not add a new command or agent.
- Add lifecycle and conformance coverage for the original Chinese three-prompt conversation, output limits, revocation, engine failures and partial multi-item recovery.
- Update canonical Human and Agent guidance and applicable architecture diagrams when the final diff confirms impact.

### Out of scope

- New image engines, external/paid image APIs, model downloads, SVG substitutes for requested raster output, or real model inference without separate explicit scope.
- Persistent prompt history, transcript-derived authority, broader Shell/MCP write permissions, arbitrary YAML writes, or overwriting existing outputs.
- Changes to Constitution, Git branch protection, release policy, or unrelated AIPS capabilities.

## Expected Files / Modules

- `scripts/turn_intent.py`
- `scripts/creative_request_policy.py`
- `scripts/creative_execution.py`
- `harness/adapters/opencode/plugin.ts`
- Relevant creative/OpenCode lifecycle tests and `tests/scenarios/238-creative-task-authorization-and-multi-item-execution.md` (or a new adjacent scenario if needed)
- `orchestration/CREATIVE_DIRECTION.md`, `harness/adapters/opencode/AGENTS.md`, and canonical Human docs selected by Documentation Impact
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`

## Impact

### Architecture / Contracts

Extend the existing creative intent, prompt-admission, and `generate-set` contracts. No new provider, command surface, Role, Skill, or Capability is planned. Preserve the user-only grant, current Session root binding, create-only outputs, output cap, no-egress policy, and fail-closed behavior.

### Data / Migration

No durable user data or schema migration. Any pending clarification state is in-memory, bounded to the active Session and discarded on cancellation, unrelated input, session end, or root change. Do not retain raw prompt text in state, trace, or manifest.

### Security / Reliability

Security-boundary change. A short answer must not gain authority from transcript history alone. It is eligible only as a constrained response to the active creative request, with the current user's response granting only the declared actions and maximum output count. Existing cancellation, unrelated-task, scope, overwrite, and missing-engine denials remain blocking.

### Compatibility / Rollback

Keep existing CLI/tool inputs, Bundle format, generate-set semantics, and reason-code compatibility where possible. Additive result diagnostics only. Revert the candidate to restore prior prompt-admission behavior; no migration is required.

### Tests / Validation

The active matrix at `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` covers policy/classification, native OpenCode state and revocation, creative engine diagnostics, multi-item recovery, documentation, privacy and exact-candidate publication. Recompute it after the final diff. Real model inference and host-specific OpenCode acceptance are separately reported as `UNVERIFIED` if the local environment cannot support them.

### Secret / Credential Impact

Secrets required: NO.

No credential acquisition. Review state and logs for raw prompt, image, secret, or local path leakage.

### Documentation / Diagrams

- `docs/ARCHITECTURE.md` Mermaid: assess against actual flow diff; update if the session authorization path changes.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: assess; update if its workflow boundary is affected.
- Human SVG architecture/lifecycle diagrams: assess and record N/A with reason if they do not depict this local creative workflow.

## Risks

- Incorrectly matching a short response could issue a grant outside the user's intended specification. Mitigation: bounded active task, role/count limits, explicit revocation tests, and no transcript-only admission.
- Local MFLUX/ComfyUI inventory cannot prove model compatibility or image quality. Preserve explicit `UNVERIFIED` status and do not download weights.
- OpenCode native runtime may be unavailable or unsupported on this host; synthetic lifecycle evidence cannot substitute for native acceptance.

## Recommendation

Approved narrow extension of the existing creative workflow. Do not duplicate features already covered by creative admission, output limits, local-only discovery, and `generate-set`.

## Proposed Implementation Order

1. Complete targeted Project Intelligence and Change Impact.
2. Implement Chinese intent and structured bounded request/output counting.
3. Implement constrained OpenCode clarification continuation and reason-specific recovery.
4. Improve local diagnostics without inference, downloads, or fallback.
5. Add original-conversation and multi-item lifecycle evidence; update canonical docs and architecture artifacts as required.
6. Reconcile the exact diff to the matrix, run the local Integration Gate, and prepare the exact Git Publish Proposal.

## Approval

Status: APPROVED
Approved by: Human user in Codex chat
Approved at: 2026-10-09 (Asia/Taipei)
Approval record: User replied `核准` to the proposed scope in this task.
Proposal fingerprint: Pending exact-candidate calculation
Scope fingerprint: Pending exact-candidate calculation
