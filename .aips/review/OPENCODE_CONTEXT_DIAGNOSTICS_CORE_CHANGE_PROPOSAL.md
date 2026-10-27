# OpenCode Context Overflow Diagnostics Core Change Proposal

## System Improvement Review

See `.aips/review/OPENCODE_CONTEXT_DIAGNOSTICS_SYSTEM_IMPROVEMENT_REVIEW.md`. The existing adapter’s fail-closed size boundary is retained; the change adds bounded diagnostics and recovery guidance only.

## Approved change boundary

1. Extract the existing compaction behavior into a small pure ESM helper and preserve the same 12,000-byte projection and truncation policy.
2. On irreducible compact-projection overflow, return `context_compaction_over_budget`, original/projection/max byte counts, and at most three fixed projection section names with serialized sizes.
3. Keep the OpenCode Context unavailable and deny supported native project file writes before ordinary manifest policy evaluation until a fitting Context is restored; give read-only inspection and refresh-plan commands.
4. Extend the existing OpenCode trace allowlist with bounded numeric sizes and fixed section names; reject unknown names, excess entries, non-integer/negative values and oversized metadata.
5. Extend Scenario 235 and the lifecycle/static contract; update canonical OpenCode and Harness documentation, coverage mapping, changelog and this proposal/matrix.

## Explicit exclusions

- No change to Turn Context generation, upstream manifest selection, compaction fields or byte limit.
- No claim that largest compact sections explain the precise source-manifest origin or historic incident without preserved evidence.
- No prompt, section content, source path, credential, raw CLI output, or new persistent telemetry.
- No permission relaxation, authority change, arbitrary Shell/MCP coverage, new abstraction family, or native Host acceptance claim.

## Required verification

The active `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` binds the final diff to base `571b54fb775bd45136a4fbcef4aa22007b6fdc72` and records focused lifecycle, static contract, privacy, recovery, documentation and exact-candidate Integration Gate evidence. Native OpenCode acceptance is applicable only if the supported host binary is available; otherwise retain `UNVERIFIED` and overall `ADVISORY`.

## Approval

The user selected the implementation scope in the current task. This authorizes implementation only; exact-candidate remote publication remains subject to the Git Publish Approval Gate and required GitHub checks. Merge authority is the user’s explicit request and existing GitHub protections.
