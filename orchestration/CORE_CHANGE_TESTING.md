# Core Change Testing

Runtime Foundation changes include the bounded Runtime Invariant Matrix and credential-free Context contract in the candidate-specific test matrix. Recompute the matrix and actual diff reconciliation after implementation expands.

For CLI reliability changes, cover side-effect-free help, unknown-argument rejection, implicit/explicit docs-impact checkout routing, gh configuration isolation precedence, invalid venv identity and installed OpenAPI execution from an independent product root. Preserve remote-reference confinement and preview-only generation; fixture evidence is not real-product acceptance. Architecture topology is unchanged by routing fixes.

Recovery changes test implicit and explicit publication roots, configured Intelligence Python, repeat-bootstrap preservation, stale-source finalization and read-only refresh planning. Exercise failure/cancellation/timeouts across classification and unrelated labels, including the embedded workflow metadata resolver. Label-only success needs matching prior full Janitor success; stale base/head/class, missing runs and API failures stay blocking. Bounded CI summaries expose precheck closure and timings without skipping complete candidate Gates.

發布治理、CI workflow、文件影響政策與 preflight validator 屬於 Core 變更。矩陣必須逐項涵蓋身份與訊息隱私、文件影響閉包、Actions runner/action 相容性、Python lifecycle 執行器及遠端 merge 後驗證，並綁定實際候選差異雜湊。CI 的快速 repository preflight 須在強制候選秘密掃描之後、完整依賴與 Chromium 安裝之前，且不可取代完整 Gate。

Use for every Large/Core Change and whenever scope/risk suggests a fixed smoke suite is insufficient.

## Principle

Required testing is derived from the final Change Boundary and actual affected interfaces, not from a generic minimum list.

For Phase 4 generator-adapter changes, the affected-boundary matrix includes the local fake-generator lifecycle: preview and Gate inspection do not execute configured tools; explicit execution checks pinned inputs, deterministic allowlisted output, Phase 3 ownership, timeout handling and rollback. The exact-candidate Integration Gate runs only this fixture, never a project-selected generator.

A green subset does not prove a core change is safe when an affected boundary has no evidence.

When a shared module-extraction lifecycle gains another facade, retain identity checks for each moved public symbol and complete the affected subsystem lifecycle before full repository validation.

## Impact-derived Test Matrix


REST/OpenAPI core changes should include lifecycle evidence for supported-spec validation, local-reference confinement, canonical-baseline comparison, project-native command execution, JUnit operation coverage and revision-bound report freshness.

When Phase 3 enforcement changes, derive separate boundaries for ownership and generation provenance, Profile/language fingerprints, required command evidence, OpenAPI report freshness, report/enforce Gate scope and unchanged legacy Profiles. A report-only observation cannot satisfy a required enforce-mode check; missing or stale evidence never becomes PASS.

For Turn Context, run-event, retrieval, Agent Eval freshness, observed-stage telemetry and review-attestation changes, bind separate boundaries to executable lifecycle evidence. A trusted review matrix stays disabled until its external issuer is configured; tests with fixture keys do not establish a production trust root.

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

For shell CLI module extraction, preserve the public launcher and facade, verify ordered module loading from the resolved checkout, and run the lifecycle from source and installed-symlink entrypoints with a caller working directory outside the repository.

When post-merge reconciliation is extracted, include both the publication lifecycle and module-facade lifecycle evidence in the same exact-candidate matrix.

The completed matrix binds the candidate base and canonical changed-file hash. Evidence must name the local test or lifecycle that ran; unexecuted architecture or migration checks need an explicit, reasoned not-applicable disposition.

Runtime recovery evidence must exercise a linked worktree installer on Bash 3.2, complete-versus-partial interpreter selection, deleted-index metadata, explicit-cache preservation and symlink refusal, redacted HTTP/proxy/DNS/TLS diagnostics, cancelled/newer CI outcomes, and dirty/divergent installed synchronization. pip download cache does not replace fresh candidate Gates.

For publication-preflight changes, run focused lifecycle checks while editing, bind the final Core Matrix to the exact base and changed-file set, then run the complete local Integration Gate once for that fixed candidate. The Gate includes repository validation; PR and main CI remain separate candidate checks.

For CI provisioning or changed-path planner changes, include positive selector cases, unknown-path and malformed-plan fail-closed cases, and proof that required secret scanning, repository validation and the complete Gate remain enabled. Run the full local toolchain for Core candidates even when an ordinary PR can use demand-driven setup.

Eval-as-CI Core Change 必須涵蓋 trace schema、deterministic trajectory rules、privacy rejection、Scenario contract、Evidence Bundle 與 shadow-mode publish boundary；LLM Judge 的非確定性只能作為 evidence，不可取代 deterministic hard constraints。

Prefer deterministic evidence and exact commands/results.

When a validation contract immediately executes a Python helper or lifecycle script, that execution also checks Python syntax. Avoid a separate `py_compile` subprocess for the same file in the same path. Assign each lifecycle evidence script one owning invocation in the full repository validator; reference its result from other contracts instead of running the identical lifecycle twice. Keep syntax-only compilation for Python files that are not otherwise executed by the affected validation path.

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

Preview and Gate share the same required Matrix readiness conditions: executable status, no blockers, reconciled actual diff, and matching base/hash. A preview with any outstanding condition reports `NEEDS_WORK`; `READY_FOR_GATE` remains a planning signal, not Gate PASS.

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

CI workflow or publication-preflight changes must test the relevant event pairs and recovery path: a newer candidate event or Core/Large classification-label change supersedes an in-progress run for that PR; unrelated label changes cannot cancel active validation and skip the expensive Gate; and the current candidate still produces the required aggregate. Post-merge reconciliation tests must prove clean ancestor fast-forward through the installed CLI even when the target script is stale, backup preservation and no ref mutation for dirty or divergent histories. Matrix routing tests must prevent writes to the wrong checkout; remote diagnostics must distinguish network failure from authentication failure without exposing raw CLI output.

The independent-review mechanism is implemented but its PR enforcement is currently **disabled by default**: the active Core Change Matrix sets `review_evidence.required: false` because no trusted runtime-attestation verifier is connected. Core Changes may opt in by setting the matrix field to `true` after configuring that verifier. When enabled, `VERIFIED` requires matching base/head and changed-file fingerprints, an exact review-packet fingerprint, distinct execution identities, no inherited implementer context, read-only authority, and runtime attestation. `SELF_CHECK`, missing attestation (`UNVERIFIED`), stale evidence, or failed evidence cannot satisfy the requirement. The Integration Gate checks these deterministic bindings; it does not score semantic review quality or authorize merge.

Before publication, run the shared preflight from a clean candidate worktree. It must resolve the same base/head and change class that CI will use, verify recursive documentation placement, and reject a stale Core Matrix or browser launch prerequisite before expensive lifecycle checks.

For local publication, the same preflight checks the explicit repository root, required Python/Ruff modules, loopback binding and browser launch before starting the Integration Gate. Changed Markdown links and the VitePress build run before full lifecycle validation when docs/package paths are part of the candidate.

Run focused checks during development, then one exact-candidate Gate after the commit is fixed; its required `repository-validation` already executes the full repository validator. The optional timing JSON records each contract import and lifecycle duration for diagnosis. CI retains full PR and post-merge main Gates, and timing evidence never substitutes for a passing check.

Integration Gate PASS is evidence only. It never supplies Human approval, merge authority, publication authority, architecture approval or risk acceptance.

The validator registry may include conservative path metadata for a deterministic shadow plan. Shadow plans record `would_run` / `would_skip`, but every validator still executes. Replay checks caller-supplied recorded runs for false-negative skips; absence of a complete historical corpus must be reported, not inferred as zero failures. Only a separately approved, evidence-backed governance change may enable selective execution.
Publication Preflight lifecycle evidence must isolate optional Python module probes from loopback/browser blocker assertions so host dependency availability cannot change the tested diagnostics.

Its `run` lifecycle must also verify that fast preflight and Integration Gate receive a child `PATH` headed by the selected Python directory, independent of the inherited shell `PATH`.

## Conditional CI enforcement

The publication preview reports the required Core Matrix base/hash binding and a synchronization command before commit. Synchronization resets the matrix to DRAFT and retains human scope/evidence review; it never grants READY automatically.

AIPS CI resolves `standard | large | core` from explicit PR change-class labels. Large/Core candidates require the bound Core Change Test Matrix. Standard changes remain Matrix-optional unless a narrow Validation Profile path rule identifies a governance-core surface. Do not use broad rules such as all `scripts/**` or all `config/**` merely to force Matrix usage.

`aips publish plan` reports label/matrix mismatches before publication. `aips publish preflight` runs the same resolver as CI; a green validation performed with a different change class or matrix path is not CI-parity evidence.

Publication Preflight lifecycle tests must cover the enabled merge-method response and separately exercise repository-metadata API access failures. Keep network/auth diagnostics redacted, and verify latest-label routing when a newer PR event supersedes an older run.
## Content Safety Core Change Evidence

Runtime Content Safety Boundary changes require detector, sink, publication, provenance and documentation evidence. The active Core Change Matrix must bind the exact candidate changed-file set and include security negative paths.

Runtime Policy Enforcement Core Changes also reconcile action and policy digest binding, approval expiry/scope drift, runtime capability truthfulness, high-risk sandbox fail-closed behavior, semantic deny/escalate monotonicity, audit redaction and the exact candidate file-set binding.

For CLI and validation modularization, the boundary matrix must cover direct source-checkout invocation, installed symlink invocation, argument and exit-status compatibility, validator import order and timing labels, error aggregation order, single-owner lifecycle execution, and publication-policy output equivalence.
