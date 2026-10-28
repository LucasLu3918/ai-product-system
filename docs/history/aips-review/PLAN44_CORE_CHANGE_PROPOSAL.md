# Plan44 Core Change Proposal — Publication Diagnostics and Native Failure Evidence

## Purpose

Provide actionable, privacy-safe publication command diagnostics and distinguish a pre-execution AIPS refusal from a native Claude Bash tool failure that occurred after execution started.

## Why this is a Core Change

The change affects a publication security boundary, native runtime event wiring, failure-state truthfulness and shared documentation/conformance contracts.

## Approved Scope

### In scope

- Preserve the stable top-level `COMMAND_FORM_UNSUPPORTED` reason while adding allowlisted detail codes and recovery instructions for pipelines, multiple commands, wrappers, malformed syntax and upstream-setting push options.
- Keep every unsupported form fail-closed; no pipeline, wrapper, or compound command becomes authorized.
- Install a managed Claude `PostToolUseFailure:Bash` hook and report only `native_tool_execution`, a fixed safe error category and a parsed exit code when available.
- Keep PreToolUse denial distinct as `DENIED` / `NOT_EXECUTED`; native failure observation never authorizes, retries, rolls back or mutates publication state.
- Reuse existing `ALREADY_MERGED`, squash merge-tree evidence, Branch Hygiene manifest cleanup, hook health checks, stable phases, redaction and Required Checks behavior.
- Extend Scenario 261, publication unit tests, runtime contracts, Human/Agent docs and the active Core Change Test Matrix.

### Out of scope

- Raw command, stderr, Claude error, prompt, session, credential, absolute path or private local data in diagnostic output or persistent records.
- Changing the authority model, grant consumption, Required Checks, branch protection, merge methods, squash evidence, branch deletion workflow, retry behavior or protected Git policy.
- New persistent ledger, Role, Skill, Capability, approval gate, runtime support claim or architecture component.
- Changing already implemented Squash/ALREADY_MERGED, cleanup-manifest, or hook-health behavior.

## Expected Files

See the exact changed-file list in the active `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` and the final Git publish proposal. The implementation reuses existing modules and adds only this proposal and the improvement review.

## Contracts and Security

`detail_code` values are fixed allowlist entries. The legacy reason code remains stable. The failure event consumes only the official event name, bounded tool identity and host error for local pattern classification; it emits no source error text. Its output states that execution started and failed, without claiming whether an external partial effect occurred. No ledger write or side effect is added.

## Compatibility and Recovery

All additions are compatible with existing diagnostics and Claude settings. Managed-hook removal also removes the new AIPS-owned event while preserving unrelated settings. Reverting the candidate removes the event wiring and diagnostic fields; no schema migration is required.

## Validation

- Focused publication unit tests and runtime contract lifecycle.
- Parser security cases for pipes, multiple commands, malformed syntax and `git push -u`.
- Secret-sentinel redaction and pre-execution versus post-execution state tests.
- Scenario 261 registration, documentation placement/sync and Core Matrix validation.
- Candidate secret scan, complete exact-candidate Integration Gate, required GitHub `repository` status check and revalidation of the exact PR head before merge.

## Documentation and Diagrams

Update the User Guide, Security Assurance, Maintenance, Claude adapter instructions, Human/Agent Conformance and Documentation Sync. Architecture Diagram Impact: N/A; no component topology, deployment unit or authority boundary is added.

## Approved Direction

Status: APPROVED. The Human user approved the Plan44 reuse-first scope in the current task. Constitution impact: NO.
