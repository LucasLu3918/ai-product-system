# Core Change Testing

發布治理、CI workflow、文件影響政策與 preflight validator 屬於 Core 變更。矩陣必須逐項涵蓋身份與訊息隱私、文件影響閉包、Actions runner/action 相容性、Python lifecycle 執行器及遠端 merge 後驗證，並綁定實際候選差異雜湊。CI 的快速 repository preflight 須在強制候選秘密掃描之後、完整依賴與 Chromium 安裝之前，且不可取代完整 Gate。

Use for every Large/Core Change and whenever scope/risk suggests a fixed smoke suite is insufficient.

## Principle

Required testing is derived from the final Change Boundary and actual affected interfaces, not from a generic minimum list.

A green subset does not prove a core change is safe when an affected boundary has no evidence.

## Impact-derived Test Matrix

Before implementation, start from `templates/review/CORE_CHANGE_TEST_MATRIX.yaml` and maintain the active candidate at `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`.

Assess each materially affected boundary against applicable evidence:

- static / lint / type checks;
- unit tests;
- integration tests;
- public/internal contract tests;
- end-to-end / smoke tests;
- security tests and secret-leakage checks;
- migration / rollback / recovery tests;
- concurrency / idempotency / replay tests;
- CLI / Harness lifecycle tests;
- documentation / schema / generated-artifact validation.

N/A requires a concrete reason.

## Recompute rule

If implementation expands the Change Boundary or reveals new consumers/contracts:

~~~text
scope expands
→ recompute test matrix
→ execute newly applicable tests
→ re-review affected evidence
~~~

Do not keep the original smaller matrix merely because it is already green.

## Strict completion rule

A Large/Core Change is not complete when:

- an applicable required test is failing;
- an affected boundary has no evidence and no justified N/A;
- tests were disabled/removed merely to obtain green CI;
- actual diff materially exceeds the tested Change Boundary;
- required security/secret handling evidence is missing.

## Evidence

Eval-as-CI Core Change 必須涵蓋 trace schema、deterministic trajectory rules、privacy rejection、Scenario contract、Evidence Bundle 與 shadow-mode publish boundary；LLM Judge 的非確定性只能作為 evidence，不可取代 deterministic hard constraints。

Prefer deterministic evidence and exact commands/results.

For system/Harness/CLI changes, include executable lifecycle tests rather than documentation-only validation.

For API/contract/data changes, include producer/consumer compatibility where applicable.

For schema/persistence changes, include migration and recovery/rollback evidence where applicable.

For security/credential changes, include secret leakage/redaction and relevant negative-path tests.
Every Remote Git publication candidate also requires a credential-free strict scan of its final tree and complete `base..head` history; Core Change evidence must bind the exact scanner and policy inputs.

## Review

Multi-Perspective Review compares:

~~~text
Final Change Boundary
↔ Test Matrix
↔ Actual Diff
↔ Test / Security Evidence
~~~

Material mismatch requires additional testing or explicit scope correction before PASS.


## Integration Gate enforcement

Use `aips publish preview --base <base> --change-class <class>` before committing to include staged, unstaged and untracked paths in recursive documentation, matrix-binding, content-safety and configured Git identity previews. Findings include categories only, never candidate PII or configured email values. `aips publish matrix-sync --base <base>` refreshes only the canonical matrix base/hash fields; boundary, evidence, blockers and readiness remain subject to review before the Gate can accept the matrix.

Before merge/publication of an integration candidate, use `orchestration/INTEGRATION_GATE.md`.

For Large/Core changes, the existing Impact-derived Test Matrix remains authoritative for applicability. The Integration Gate may require the matrix and binds:

~~~text
exact base/head candidate
↔ actual changed files
↔ Validation Profile
↔ Core Change Test Matrix
↔ deterministic command results
~~~

A stale candidate, missing required matrix, unresolved blocker, failed required command or unreconciled actual diff blocks the candidate.

The independent-review mechanism is implemented but its PR enforcement is currently **disabled by default**: the active Core Change Matrix sets `review_evidence.required: false` because no trusted runtime-attestation verifier is connected. Core Changes may opt in by setting the matrix field to `true` after configuring that verifier. When enabled, `VERIFIED` requires matching base/head and changed-file fingerprints, an exact review-packet fingerprint, distinct execution identities, no inherited implementer context, read-only authority, and runtime attestation. `SELF_CHECK`, missing attestation (`UNVERIFIED`), stale evidence, or failed evidence cannot satisfy the requirement. The Integration Gate checks these deterministic bindings; it does not score semantic review quality or authorize merge.

Before publication, run the shared preflight from a clean candidate worktree. It must resolve the same base/head and change class that CI will use, verify recursive documentation placement, and reject a stale Core Matrix or browser launch prerequisite before expensive lifecycle checks.

Integration Gate PASS is evidence only. It never supplies Human approval, merge authority, publication authority, architecture approval or risk acceptance.

## Conditional CI enforcement

The publication preview reports the required Core Matrix base/hash binding and a synchronization command before commit. Synchronization resets the matrix to DRAFT and retains human scope/evidence review; it never grants READY automatically.

AIPS CI resolves `standard | large | core` from explicit PR change-class labels. Large/Core candidates require the bound Core Change Test Matrix. Standard changes remain Matrix-optional unless a narrow Validation Profile path rule identifies a governance-core surface. Do not use broad rules such as all `scripts/**` or all `config/**` merely to force Matrix usage.

`aips publish plan` reports label/matrix mismatches before publication. `aips publish preflight` runs the same resolver as CI; a green validation performed with a different change class or matrix path is not CI-parity evidence.
## Content Safety Core Change Evidence

Runtime Content Safety Boundary changes require detector, sink, publication, provenance and documentation evidence. The active Core Change Matrix must bind the exact candidate changed-file set and include security negative paths.

Runtime Policy Enforcement Core Changes also reconcile action and policy digest binding, approval expiry/scope drift, runtime capability truthfulness, high-risk sandbox fail-closed behavior, semantic deny/escalate monotonicity, audit redaction and the exact candidate file-set binding.
