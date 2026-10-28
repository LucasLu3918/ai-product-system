# Plan41 Core Change Proposal: Commit Safety Diagnostics

## Human decision

**Approved** by explicit user response on 2026-10-15 (Asia/Taipei): **「核准 Plan41 完整範圍」**.

## Objective

Make commit-safety Hook denials explainable and actionable without exposing protected content, while making Hook and read-only CLI inspection share one scanner and preserving all existing safety and publication authority boundaries.

## Scope

1. Refactor commit candidate inspection into a shared implementation used by the native Hook and a read-only `aips safety diagnose commit` command.
2. Return stable, structured, content-redacted diagnostics for findings and failure paths. Include safe reason code, phase, source, category/detector, sanitized repository-relative location where available, diagnostic ID, retryability, and Traditional Chinese remediation. Never return matched text, raw arguments, raw exception messages, secret values, absolute paths, or unsafe filenames.
3. Apply strict ignore-marker semantics to protected commit scans so content cannot opt out of publication scanning.
4. Inspect supported media metadata with bounded format-aware handling for PNG, JPEG, WebP, M4A, and MP3. Unsupported or malformed media/binary data, oversized inputs, read failures, and incomplete scanner execution fail closed with a distinct safe classification.
5. Preserve the existing Secret, PII, and Injection Signal `BLOCK` policy and all Human Authority, Required Checks, and Git Publish Approval Gate behavior.
6. Add unit, integration, CLI/Hook, failure-injection, redaction, and scenario coverage. Resolve recursive documentation impacts and update Traditional Chinese Human guidance.

## Exclusions

No policy relaxation, new gate/role/skill/capability, external service, dependency, default audit store, write-capable CLI, cache/batching layer, or publication authorization change. Cache/batching is deferred pending independent evidence that it is needed.

## Impact limits

Impact traversal for this repository has partial consumer-graph coverage. Manually verify the bounded call chain through `content_safety`, `governance_guard`, `check_secret_leakage`, M4A inspection, Hook adapters, CLI dispatch/help, tests, scenario registry, and documentation impact resolver. Record any residual graph uncertainty as a limitation rather than asserting exhaustive discovery.

## Required completion evidence

Complete `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` with exact candidate/base SHA, actual changed file set, scope recomputation, local focused and integration checks, security/redaction checks, CLI/Hook behavior, scenario/conformance evidence, recursive documentation closure, and any remaining blockers. Run Git Publish Approval Gate on the exact final candidate before remote publication.
