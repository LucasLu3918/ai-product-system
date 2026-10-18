# Plan45 Core Change Proposal — Publication Scan Diagnostics

## System Improvement Review

- Problem: personal-mode publication scans run before complete static command validation, and scanner `ScanError` failures can collapse into a generic diagnostic gap.
- Existing coverage: stable `PublicationError` reason codes, safe diagnostic mapping, optional allowlisted diagnostic ledger, exact candidate/worktree fingerprints, prepare-generated native invocations, and fail-closed unknown errors already exist.
- Reuse: extend those publication and scanner abstractions; no new logger, command generator, authority gate, or role.
- Security: preserve fail-closed behavior; never emit raw exception text, original command text, secret values, or file contents. Scanner failures stay non-retryable and cannot authorize publication.
- Compatibility: add stable reason codes and safe metadata without changing authority semantics, response envelopes, or ledger schema.
- Constitution impact: NO. Human authority, merge approval, and high-assurance grants remain unchanged.
- Architecture impact: no topology change; publication authority continues to depend on the scanner and Hook consumer.

## Approved Change Boundary

1. Give secret scan failures structured stable codes, phase/component, retryability, and safe recovery guidance, including invalid policy/expired allowlist, candidate/base/object/file read failures, and unknown scanner failures.
2. Validate literal publication command shape before candidate/history scanning. Complete candidate, security, remote, PR and authority validation remains mandatory afterward.
3. Reuse diagnostic IDs and the optional redacted ledger to correlate the failure; no raw details are persisted.
4. Extend unit, Hook/CLI lifecycle, failure-injection and redaction tests; update Scenario 261 and its evidence registry, complete the Documentation Impact-required canonical architecture, security, installation, Intelligence, technology, conformance, content-safety, user and maintenance guidance, changelog, and exact-candidate Core Matrix.
5. Reuse the already implemented `aips publish prepare` invocation output and worktree/candidate binding from current `main`.

## Exclusions

- No change to Git push/merge authority, native Human confirmation, external high-assurance grants, required checks, release behavior, or `lucas-lab` PR #148.
- No new publication command generator or diagnostic storage system.
- No retry of a failed publication or scanner bypass.

## Impact and Validation

Inputs are parsed argv, candidate Git refs/tree/history, scanner policy, and scanner results. Outputs are an existing-schema redacted diagnostic or a denial before any publication side effect. There is no persisted schema migration. Consumers are `publication_authority`, `check_secret_leakage`, `governance_guard`, the existing publication CLI, and Scenario 261 tests.

Validation includes focused scanner/authority/diagnostic tests, Hook/CLI lifecycle, no-side-effect assertions, secret/raw-error redaction, Scenario 261 conformance, docs closure, mandatory candidate secret scan, full repository validation and exact-candidate Integration Gate. Browser/E2E is N/A because no UI or service changes. Full remote `repository` checks remain required before merge.

## Approval

User approved this exact direction in the current task: “核准，照此範圍實作” (2026-10-18). The task explicitly targets a new AIPS PR to `main`.
