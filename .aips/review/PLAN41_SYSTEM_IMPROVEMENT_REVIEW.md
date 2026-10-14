# Plan41 System Improvement Review

## Decision

**Fit: suitable with bounded implementation.** Reuse the existing Content Safety scanner and native pre-commit Hook. Add a read-only diagnostic entry point that invokes the same commit candidate scanner. Do not introduce a new gate, role, capability, skill, remote service, or persistent diagnostic store.

## Problem and evidence

The current commit Hook can deny a candidate after Content Safety finds a protected value, but the denial path discards the finding and emits only a generic blocked message. Commit candidates also use non-strict ignore-marker handling, staged blobs are decoded with replacement characters regardless of format, and staged read/scanner errors do not preserve a safe, actionable classification. This makes legitimate denials hard to distinguish from scanner failures and gives media/binary inputs no reliable format boundary.

## Reuse and alternatives

Keep `scripts/content_safety.py`, `scripts/check_secret_leakage.py`, `scripts/governance_guard.py`, and the existing M4A inspector as the policy and scanner foundation. Factor candidate inspection so Hook and read-only CLI call the same implementation. A separate scanner or generic policy gate would duplicate authority and increase drift. Batched Blob caching is deferred because cache invalidation and retention add privacy and correctness risk without being required for this fix.

## Approved scope

The Human explicitly approved the complete Plan41 Core Change scope on 2026-10-15 (Asia/Taipei), replying: **「核准 Plan41 完整範圍」**. The scope is: structured and redacted denial diagnostics; stable failure classification; a read-only commit diagnose CLI sharing Hook scanning; strict ignore-marker semantics for protected commit content; bounded format-aware media metadata handling; fail-closed unsupported, malformed, unreadable, oversized, or scanner-failure cases; focused tests, scenario/conformance updates, and recursive documentation closure.

## Invariants and risk controls

- Secret, PII, and injection findings retain their current `BLOCK` policy.
- Never include matched content, command arguments, raw exceptions, credential values, absolute paths, or untrusted filenames in diagnostics.
- Use safe repository-relative locations only after sanitization; diagnostics carry a stable reason code, phase, category/detector, diagnostic ID, retryability, and Traditional Chinese recovery guidance.
- Unknown/malformed binary data and any incomplete scan fail closed with an explicit safe reason.
- The CLI is read-only and limited to inspecting a Git commit candidate; it cannot authorize, stage, commit, push, merge, or alter Hook decisions.
- Preserve Human Authority, Required Checks, and Git Publish Approval Gate without modification.
- No new runtime dependency or default audit store.

## Architecture and validation

This change improves observability and scanner coverage inside the existing content-safety path. It does not change the publication topology or grant authority. The approved Core Change test matrix is `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`; evidence must be filled from executed checks before completion. The project change-impact artifact records known callers and the partial limits of generated impact traversal.
