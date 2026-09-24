# Scenario Conformance

## Purpose

Make AIPS behavioral regression coverage measurable without conflating specification count with executable evidence.

## Registry

`tests/scenario_coverage.yaml` is the canonical mapping from Scenario ID/path to coverage classification and evidence.

Allowed coverage:

- deterministic
- lifecycle
- agent_eval — provider-neutral recorded Agent behavior with deterministic observable-output scoring
- manual
- uncovered

Automated coverage is deterministic + lifecycle + agent_eval.

## Admission rules

Every `tests/scenarios/NNN-*.md` file must have exactly one registry entry.

Every entry must:
- use the matching ID/path;
- use an allowed coverage type;
- provide evidence for every non-uncovered type;
- avoid claiming automated coverage without material executable evidence.

No orphan registry entries are allowed.

## Release behavior

Repository validation runs the conformance checker. Missing/duplicate/unknown entries fail validation. `uncovered` is release-blocking under the current registry policy. `manual` is allowed but remains visible as automation debt.

A later change may raise an automation target only through normal System Improvement/Core Change governance; do not silently relabel manual scenarios.

## Reporting

Report total scenarios, each coverage bucket, automated count/percentage and uncovered IDs.

Coverage percentage is evidence metadata, not a quality score and not a substitute for risk-based testing.

## Legacy Scenario reconciliation

Before promoting a legacy `manual` Scenario to automated coverage:

1. compare the Scenario against current canonical System / Orchestration / Runtime contracts;
2. reconcile superseded terminology or behavior first;
3. add direct executable evidence that materially exercises the Scenario;
4. point the registry at the direct evidence;
5. keep judgment-heavy or environment-dependent behavior manual when no truthful automated evidence exists.

Do not preserve an obsolete Scenario merely to keep historical wording stable. Scenario IDs/paths may remain stable while their expected contract is reconciled to the current canonical architecture.

Prefer focused evidence under `tests/evidence/` when this makes one-to-one traceability clearer. Repository validation must execute promoted evidence rather than only checking that the evidence file exists.

## Agent Eval admission

Trajectory Quality Gate 重用 Agent Eval 的 observable-only privacy contract。Trajectory evidence 可被 Scenario registry 綁定為 lifecycle evidence；不得保存 chain-of-thought，也不得把評估結果視為 publication authority。

For `agent_eval`, load `orchestration/AGENT_EVAL.md`.

Registry evidence must include both a concrete `tests/agent_eval/cases/*` Case and a `tests/agent_eval/results/*` recorded Result. Repository validation must run the deterministic scorer and reject stale fingerprints, missing/orphan results, private reasoning fields, secret-like values and rubric failures.

Do not count an eval prompt or rubric by itself as Agent evidence.


## Scenario 126 / 127 current evidence

- Scenario 126 is lifecycle-covered by deterministic Radar collection plus the governed semantic-analysis / Human Decision / isolated Controlled Trial lifecycle evidence. A Trial PASS remains evidence only and requires a separate Human Adoption Decision.
- Scenario 127 is deterministic coverage for Human Documentation Namespace placement: permanent Human-only docs live under `docs/human/`; shared canonical docs are allowlisted; standalone Human artifacts outside that root require explicit registration plus the `HUMAN_` prefix.

These classifications are evidence claims, not quality scores.

## Scenario 128 — Retrieval Intelligence

Scenario 128 is lifecycle-covered by `tests/evidence/retrieval_intelligence_lifecycle.py`. The executable fixture proves target implementation/test retrieval, bounded token assembly, relevant Git-history evidence, dirty-workspace incremental refresh, secret-path exclusion, revision/content provenance and truthful `NOT_CONFIGURED` semantic-provider fallback.

Current automated inventory after Scenario 128:

- deterministic: 20
- lifecycle: 54
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 128 / 128

## Scenario 129 — Retrieval Quality Evaluation

Scenario 129 is lifecycle-covered by `tests/evidence/retrieval_quality_evaluation_lifecycle.py` plus the committed `tests/fixtures/retrieval_quality_corpus.yaml`. The corpus spans Python, Go, TypeScript, SQL, monorepo/shared-module, low-lexical-overlap, synonymy and cross-file-call-chain dimensions. The fixture runs the suite against a declared v0.20-style static topic baseline and current local hybrid retrieval, recomputes Precision@K / Recall@K / F1@K / MRR / history recall / irrelevant-context rate / token use, records latency only as informational evidence, verifies required failures remain release-blocking, verifies diagnostic failures remain explicit gap evidence without failing the whole suite, and proves the report cannot automatically enable providers, change ranking weights or select a new retrieval architecture.

Current automated inventory after Scenario 129:

- deterministic: 20
- lifecycle: 55
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 129 / 129

## Scenario 130 — Structural Retrieval Candidate Trial

Scenario 130 is lifecycle-covered by the same full Retrieval Quality fixture plus `scripts/structural_retrieval_trial.py`. The replay harness explicitly disables structural retrieval for its baseline and explicitly enables the bounded exact-identifier two-hop candidate, proves all required corpus cases avoid regression, and requires the `cross-file-call-chain` diagnostic to improve from incomplete source recall to complete Recall@K.

Trial PASS remains evidence only. Scenario 131 separately records the Human-approved production adoption.

Current automated inventory after Scenario 130:

- deterministic: 20
- lifecycle: 56
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 130 / 130

## Scenario 131 — Structural Retrieval Adoption

Scenario 131 is lifecycle-covered by `tests/evidence/retrieval_intelligence_lifecycle.py`. It proves normal `retrieve` and Turn Context paths enable bounded Structural Retrieval by default, that evidence reports default/enabled selection plus telemetry, and that `--no-structural` explicitly disables only the structural ranking lane for regression/debug comparison.

The adopted implementation remains local/provider-neutral and adds no parser/LSP dependency, Role, Skill, Approval Gate or publication authority.

Current automated inventory after Scenario 131:

- deterministic: 20
- lifecycle: 57
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 131 / 131

## Scenario 132 — Semantic Alias Expansion Candidate Trial

Scenario 132 is lifecycle-covered by the full Retrieval Quality fixture plus the `--trial semantic-alias` mode in `scripts/retrieval_evaluation.py`.

The committed candidate outcome is **FAIL / HOLD**, and the lifecycle evidence intentionally expects the Trial process to exit non-zero. It proves the source-controlled alias expansion candidate:

- regresses the required auth-token-expiry, Go receipt and TypeScript session cases;
- regresses source recall for the already-covered registration diagnostic;
- does not improve the active `synonym-access-rotation` source-recall gap;
- keeps the real semantic provider truthfully `NOT_CONFIGURED`;
- keeps alias expansion disabled by default and reports recommendation `HOLD`;
- cannot auto-adopt itself or enable an embedding provider.

Negative Trial evidence is therefore a valid conformance result. A materially different semantic retrieval candidate requires a separate Human-reviewed Trial.

Current automated inventory after Scenario 132:

- deterministic: 20
- lifecycle: 58
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 132 / 132

## Scenario 133 — Remote Embedding Retrieval Trial Readiness

Scenario 133 is deterministic-covered by `tests/validation/retrieval_embedding_trial_contracts.py`. It validates the remote embedding Trial contract without performing an external provider call during normal repository validation.

The contract proves:

- the Trial reuses a protected secret reference instead of committed credentials;
- source transfer is restricted to the synthetic Retrieval Quality fixture;
- AIPS repository/product source transfer is false;
- missing credentials resolve to `TRIAL_PENDING`;
- provider failure resolves to `TRIAL_BLOCKED`;
- provider/default enablement and adoption without Human decision remain false;
- the dedicated workflow is scoped to the Trial feature branch plus explicit manual dispatch, not every PR/main validation;
- the workflow publishes a Human-readable Job Summary that preserves the distinction between workflow success and Trial PASS/FAIL/PENDING/BLOCKED and gives the next operator action without exposing credential values.

Current automated inventory after Scenario 133:

- deterministic: 21
- lifecycle: 58
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 133 / 133

## Scenario 134 — Provider-Neutral Local-First Embedding Retrieval Trial

Scenario 134 is deterministic-covered by `tests/validation/retrieval_embedding_trial_contracts.py`. It extends Scenario 133 without rewriting its historical remote-readiness evidence.

The contract proves:

- embedding Trial provider selection defaults to `local` and remains explicitly configurable;
- the local runtime dependency, model identifier, dimensions and exact model revision are pinned;
- local readiness is `READY` without `OPENAI_API_KEY`, reports credential_required=false, executes inference runner-local and reports inference_source_transfer=false;
- model artifact download is a dedicated-Trial infrastructure operation, with telemetry disabled, and does not authorize repository/product source transfer;
- the existing OpenAI-compatible adapter remains available only as an explicit optional `remote` provider;
- explicit remote mode without its credential remains truthfully `TRIAL_PENDING`;
- local dependency/model download/load/inference failures resolve to `TRIAL_BLOCKED / HOLD`;
- normal PR/main repository validation does not install or execute the semantic Trial model;
- the same 9-case quality corpus, thresholds and required-regression gates remain unchanged;
- vectors remain ephemeral, no Vector DB is introduced, production/default enablement remains false, and PASS still requires a separate Human Adoption Decision.

Current automated inventory after Scenario 134:

- deterministic: 22
- lifecycle: 58
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 134 / 134


## Scenarios 135–136 — Deterministic Scheduling and Exact-Candidate Integration Gate

Scenario 135 is lifecycle-covered by `tests/evidence/deterministic_scheduler_lifecycle.py`. It proves stable dispatch/fingerprints for the same Task Graph + state, dependency readiness, max-parallel enforcement, canonical Change Boundary locking, resume from persisted task state and fail-closed dependency/cycle behavior.

Scenario 136 is lifecycle-covered by `tests/evidence/integration_gate_lifecycle.py`. It proves exact base/head binding, changed-file/candidate fingerprints, deterministic argv validation, stale checkout BLOCKED behavior, required-check FAIL behavior and zero merge/release authority.

The new system capability reuses Execution Isolation, Run State and Core Change Test Matrix rather than creating parallel ownership/test systems.

Current automated inventory after Scenario 136:

- deterministic: 22
- lifecycle: 60
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 136 / 136

## Scenario 137 — Agent Eval Repeatability

Scenario 137 is lifecycle-covered by `tests/evidence/agent_eval_framework.py` plus the new `agent_eval.py consistency` mode. It proves that multiple independently recorded Results for one exact Case fingerprint can be evaluated as a reliability set without requiring exact wording equality.

The report keeps rubric success and literal response repeatability separate, rejects stale/invalid Result evidence even when a relaxed pass-rate threshold would otherwise pass, and persists only aggregate status/fingerprints rather than private reasoning.

Current automated inventory after Scenario 137:

- deterministic: 22
- lifecycle: 61
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 137 / 137


## Scenario 138 — Resource-Scoped Agent Authorization

Scenario 138 is lifecycle-covered by `tests/evidence/resource_authorization_lifecycle.py` plus the deterministic `scripts/resource_authorization.py` evaluator.

It proves default-DENY behavior, explicit resource/operation grants, Change Boundary enforcement for mutation, rejection of undeclared/protected operations, secret-reference-only configuration and truthful `runtime_enforced=false` reporting.

The capability extends the existing Execution Profile and Governance path; it does not introduce a Role, Skill or approval gate.

Current automated inventory after Scenario 138:

- deterministic: 22
- lifecycle: 62
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 138 / 138

## Scenario 139 — Agent Anomaly Evidence Evaluation

Scenario 139 is lifecycle-covered by `tests/evidence/agent_anomaly_evaluation_lifecycle.py` and `scripts/agent_anomaly_evaluation.py`.

It proves a provider-neutral, offline evaluation lane can reuse Resource Authorization truth against a fixed synthetic corpus and report TP/FP/TN/FN, precision, recall, false-positive rate and false-negative rate without becoming a runtime enforcement component.

The committed 11-case fixture produces TP=6, FP=0, TN=5 and FN=0. This is fixture evidence only, not a general production-accuracy claim. Lifecycle evidence also proves private-reasoning/secret-like inputs are rejected and that intentionally incorrect expected labels make evaluation FAIL.

Every report remains `POST_EXECUTION_EVIDENCE`, `runtime_enforced=false`, `critical_path=false`, `automatic_remediation=false`, and keeps Human/merge/release/publication/protected-operation authority false. PASS recommends only `HUMAN_REVIEW_TRIAL_EVIDENCE`.

Current automated inventory after Scenario 139:

- deterministic: 22
- lifecycle: 63
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 139 / 139

## Scenario 140 — Observable-Event Integration Controlled Trial

Scenario 140 is lifecycle-covered by `tests/evidence/agent_observable_event_trial_lifecycle.py` and `scripts/agent_observable_event_trial.py`.

It binds a current-baseline Human TRIAL Decision to replay-only adapter-export evidence, normalizes only whitelisted fields into the canonical observable-event contract, and reuses the existing Resource Authorization-backed anomaly evaluator.

The 12-case representative replay corpus produces TP=6, FP=0, TN=6 and FN=0. Lifecycle evidence also proves unknown adapters, unmapped payload fields, private reasoning, secret-like values, stale decisions and false live-capture claims fail closed.

The committed result remains non-production evidence: `live_capture_verified=false`, `runtime_enforced=false`, `critical_path=false`, `automatic_remediation=false`, and PASS stops at `HUMAN_REVIEW_TRIAL_RESULT`.

Current automated inventory after Scenario 140:

- deterministic: 22
- lifecycle: 64
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 140 / 140

## Scenario 141 — Trial-backed anomaly adoption and System Improvement Review

Scenario 141 proves that a committed PASS Trial can be adopted from a newer current repository baseline without pretending the original Radar revision is still current.

`scripts/evolution_adoption.py bind-committed` verifies:

- exact prior TRIAL Decision fingerprint;
- exact committed PASS Trial fingerprint;
- current-baseline adoption evidence digest;
- a separate CURRENT Human ADOPT Decision;
- matching candidate/signal identity;
- no runtime/protected authority in the Trial result.

The adoption artifact hands off only to `system_improvement_review`. The approved review adopts an opt-in, metadata-only, adapter-level POST_EXECUTION capture **design direction**, while production hook, persistence, semantic intent governance and automatic remediation remain deferred.

Current automated inventory:

- deterministic: 22
- lifecycle: 65
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 141 / 141

## Scenario 142 — Gemini CLI AfterTool capture Trial

Scenario 142 is lifecycle-covered by `tests/evidence/gemini_observable_event_capture_lifecycle.py`.

It proves the first runtime-specific capture implementation can:

- wire the existing Gemini CLI extension to native `AfterTool`;
- stay disabled by default;
- restrict v1 matching to `read_file|write_file|replace`;
- project only canonical metadata;
- never persist raw `tool_input` / `tool_response`, private reasoning or secret-like values;
- capture 6/6 supported fixtures with zero unexpected event loss;
- degrade/skip malformed or unsupported input without changing tool execution;
- stay monotonic with Resource Authorization and reuse the existing anomaly evaluator;
- assert bounded subprocess overhead in CI.

The source-controlled Trial does not execute a real Gemini CLI binary. Therefore both `live_runtime_execution_verified` and `live_capture_verified` remain false.

Current automated inventory:

- deterministic: 22
- lifecycle: 66
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 142 / 142

## Scenario 143 — Gemini CLI real-runtime verification

Scenario 143 is lifecycle-covered by a dedicated GitHub Actions workflow plus static contracts.

It verifies:

- pinned official Gemini CLI v0.60.0;
- exact candidate SHA identity;
- official extension link/validation;
- real built-in read/write/replace execution;
- real AfterTool hook execution;
- 3/3 expected canonical events and zero unexpected loss;
- actual write/replace workspace mutations;
- zero raw/private/secret payload persistence;
- disabled capture writes no sink.

The model layer is deterministic fake-response input, so the result may set runtime-specific `live_runtime_execution_verified=true` / `live_capture_verified=true`, but must keep provider/model session verification false.

Current automated inventory: deterministic 22, lifecycle 67, agent_eval 54, total 143 / 143.

## Scenario 144 — Optional External Provider Credentials

Scenario 144 deterministically locks the external-provider credential policy.

It proves:

- baseline AIPS operation requires no external Agent/provider credential;
- missing `GEMINI_API_KEY` is `SKIPPED_NOT_CONFIGURED`, never a provider PASS and never a release blocker;
- disabled evidence reports `provider_verification_enabled=false` and `required_for_release=false`;
- provider/model verification truth remains false until real provider evidence exists;
- absent credentials skip provider-specific install/inference steps;
- the provider workflow has no `pull_request` trigger and keeps credential values non-persistent;
- OAuth, Vertex AI, GitHub OIDC/WIF, and other replacement login flows remain disabled unless a later Human Decision explicitly adopts them;
- credential-free Gemini runtime/tool/AfterTool verification remains independent.

Current automated inventory after Scenario 144:

- deterministic: 23
- lifecycle: 67
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 144 / 144

## Scenario 145 — External Credential Dependency Guard

Scenario 145 is deterministically covered by `tests/evidence/external_credential_guard_lifecycle.py` and `scripts/external_credential_guard.py`.

It proves:

- executable/configuration references to external Agent/provider credentials are centrally declared;
- undeclared credentials and undeclared consumers fail repository validation;
- `GEMINI_API_KEY` and `OPENAI_API_KEY` remain optional and cannot become baseline/release requirements;
- workflows consuming external credentials cannot expose them to pull-request code;
- credential-free default lanes do not receive optional provider secrets;
- the Retrieval semantic Trial injects `OPENAI_API_KEY` only in the explicit remote step;
- the guard never reads credential values or calls a provider;
- PASS grants no protected authority.

Current automated inventory after Scenario 145:

- deterministic: 24
- lifecycle: 67
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 145 / 145

## Scenario 146 — Evolution Radar local deterministic pre-analysis

Scenario 146 is lifecycle-covered by `tests/evidence/evolution_radar_lifecycle.py`.

It proves that Evolution Radar can produce a deterministic, credential-free first-pass review queue from already-collected title/metadata evidence and the current Capability Map.

The output may contain category hints, capability hints, recurrence evidence, bounded near-duplicate clusters and HIGH/MEDIUM/LOW Human review priority. These fields are triage metadata only and MUST NOT be interpreted as semantic suitability or adoption state.

Required truth:

- `semantic_suitability_inferred=false`;
- `recommendation_state_mutated=false`;
- semantic recommendations remain `ANALYSIS_PENDING`;
- no external provider credential;
- no additional external network call;
- identical inputs produce identical artifact content;
- artifact is bound to exact repository revision, evidence digest, preanalysis-config digest and Capability Map digest;
- all Human/implementation/merge/release/publication authority remains false.

Current automated inventory after Scenario 146:

- deterministic: 24
- lifecycle: 68
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 146 / 146

## Repository Health reuse

Repository Health / Architecture Drift invokes this existing Scenario Conformance checker for scenario_evidence_drift. This file, tests/scenario_coverage.yaml and scripts/scenario_conformance.py remain the canonical Scenario evidence model; Repository Health must not reimplement or reinterpret Scenario coverage semantics.

Scenario 147 is lifecycle-covered by tests/evidence/repository_health_lifecycle.py. The current v0.38 target is 147 automated Scenarios: 24 deterministic + 69 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.

## Scenario 148 — Repository Health evidence binding

Scenario 148 is lifecycle-covered by `tests/evidence/repository_health_lifecycle.py`. It proves that Repository Health binds all configured audit inputs in a sorted content-digested manifest, exposes missing bound files explicitly, and derives a deterministic evidence fingerprint from repository revision, workspace status, dirty paths, manifest digest and drift output.

Clean Git workspaces report `EXACT_REVISION` and `revision_reproducible=true`. Dirty Git workspaces report `DIRTY_WORKTREE` and `revision_reproducible=false`; non-Git workspaces report `NO_GIT`. Dirty state alone is evidence metadata rather than architecture drift, so the audit does not silently mutate files or reinterpret PASS/DRIFT semantics.

Current automated inventory after Scenario 148:

- deterministic: 24
- lifecycle: 70
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 148 / 148

## Scenario 149 — Repository Health architecture surface inventory

Scenario 149 is lifecycle-covered by `tests/evidence/repository_health_lifecycle.py`. It proves that `config/architecture-surfaces.yaml` deterministically accounts for every Capability Map entry exactly once and binds each major subsystem to required repository paths, canonical docs and validation paths.

Validation paths must be traceable either to Scenario Conformance evidence or to a validation module imported by `tests/validate_repository.py`. Unclassified capabilities, missing surface paths, Capability Map/document mismatches and unbound validation paths produce `architecture_surface_drift`.

The exact-candidate validate workflow also emits and uploads `repository-health-report.json` as review evidence. The artifact is observational only and does not grant remediation, merge, release or publication authority.

Current automated inventory after Scenario 149:

- deterministic: 24
- lifecycle: 71
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 149 / 149


## Scenario 150 — Scheduled Repository Health maintenance

Scenario 150 covers the dedicated Repository Health maintenance workflow. Weekly/manual observation must retain deterministic JSON evidence, publish a Job Summary, create no Issue on PASS, deduplicate DRIFT_DETECTED notification by evidence fingerprint, and leave drift visible as workflow failure. The lane remains Detect + Evidence + Human Review only with no contents-write, remediation, implementation-PR, merge or release authority.

Released Scenario Conformance baseline: 150 / 150 automated = 24 deterministic + 72 lifecycle + 54 agent_eval; manual 0; uncovered 0.

## Scenario 151 — Evolution Radar quarterly deterministic review

Scenario 151 is lifecycle-covered by `tests/evidence/evolution_radar_lifecycle.py`. It proves that quarterly Radar review consumes only valid monthly durable evidence for the requested calendar quarter, binds the exact three months, accumulates recurrence deterministically, and resets quarterly recommendations to `ANALYSIS_PENDING` rather than promoting monthly semantic states.

The quarterly lane performs no additional source collection and requires no external Agent/provider credential. Protected-operation authority remains false.

Released Scenario Conformance baseline: 151 / 151 automated = 24 deterministic + 73 lifecycle + 54 agent_eval; manual 0; uncovered 0.



## Scenario 152 — Technology Intelligence Expansion

Scenario 152 is lifecycle-covered by `tests/evidence/evolution_radar_lifecycle.py` and the Evolution Radar static contracts. It proves six configured community discovery sources with a healthy floor of five successful communities, per-source <= 8, deterministic round-robin raw cap <= 50, provenance/verification roles, shortlist <= 12, semantic queue <= 10, actionable semantic states <= 5, partial semantic application, and primary-source corroboration before explicit community-discovered ADOPT.

Current automated inventory after Scenario 152:

- deterministic: 24
- lifecycle: 74
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 152 / 152

Coverage remains evidence-only and grants no implementation, PR, merge, release, publication or Human-decision authority.

## Scenario 153 — Evolution Evidence Quality and Primary Corroboration

Scenario 153 extends Technology Intelligence with a deterministic evidence-quality contract. Exact source provenance is converted into level 0–4 evidence strength without model inference: single-community discovery = 0, multi-community recurrence = 1, primary source = 2, primary + community = 3, and multiple primary sources = 4.

The minimum advisory ADOPT evidence level is 2. Semantic providers can assess only the evidence metadata produced by deterministic code; they cannot raise evidence strength. Monthly and quarterly rollups preserve the same provenance/quality semantics, and local pre-analysis may use only a bounded evidence-priority bonus.

Current automated inventory after Scenario 153:

- deterministic: 24
- lifecycle: 75
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 153 / 153

Evidence strength is advisory input only and grants no Human-decision, implementation, PR, merge, release or publication authority.



## Scenario 154 — Provider-neutral Controlled Trial Handoff

Scenario 154 keeps the Human-approved Controlled Trial contract usable when the optional OpenAI executor credential is unavailable. Provider resolution is bounded to `auto / openai-codex-action / handoff`; `auto` falls back to credential-free `TRIAL_HANDOFF_READY` instead of misclassifying a missing optional key as a failed experiment.

The handoff binds the exact baseline, Human Decision fingerprint, Trial fingerprint, approved scope/paths, forbidden paths, diff/file limits, worktree-isolation requirement and repository validation command. An external executor cannot self-assert PASS: AIPS deterministic scope/diff/repository validation remains required before PASS/FAIL Trial evidence exists.

Current automated inventory after Scenario 154:

- deterministic: 24
- lifecycle: 76
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 154 / 154

The handoff grants no PR, merge, release, publication or Human-adoption authority.


## Scenario 155 — Evolution Effectiveness Metrics and Feedback Loop

Scenario 155 validates a credential-free monthly effectiveness layer over durable weekly Evolution Radar evidence. It aggregates signal/duplicate volume, shortlist and semantic selection, semantic actionable states, Human Decisions, provider-neutral Trial handoffs, Trial outcomes and Trial→ADOPT bindings, then attributes downstream observations back to exact source provenance.

Per-source ratios are deterministic basis-point calculations. Low-yield, high-failure and zero-actionable conditions may emit Human-review flags only after minimum observation thresholds; automatic source weighting, enable/disable and configuration mutation remain forbidden.

Current automated inventory after Scenario 155:

- deterministic: 24
- lifecycle: 77
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 155 / 155

The monthly workflow requires no external Agent/provider credential and has only `contents: read + issues: write`. Effectiveness evidence cannot authorize implementation, PR, merge or release.


## Scenario 156 — Human-authorized Exact Branch Cleanup

Scenario 156 validates that normal branch hygiene stays report-only while a separately reviewed one-time manifest may delete only exact EPHEMERAL branch+SHA entries after complete-batch preflight. Any moved ref, non-ephemeral branch or non-integrated branch blocks the batch before deletion. Persistent/unclassified/pending branches remain preserved.

## Scenario 157 — Stale Evolution Issue Lifecycle Reconciliation

Scenario 157 binds Issue #79 to the current released truth, preserves COVERED and bounded ADOPT outcomes, keeps provider/model verification false where unproven, and marks semantic-intent governance DEFERRED. The stale Issue becomes ready to close; future positive progression requires fresh current-main evidence and a new Human Decision.

Current automated inventory after Scenario 157:

- deterministic: 24
- lifecycle: 79
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 157 / 157


## Scenario 158 — Verifiable Governance Audit Chain

Scenario 158 adds deterministic lifecycle evidence for long-lived AIPS governance auditability. Approval, security review, release and production boundary events can be canonicalized into a SHA-256 event hash and previous-chain binding. Editing or reordering evidence fails verification; suffix truncation is detectable when the auditor supplies a previously retained expected chain head/event count or an equivalent external checkpoint anchor.

HMAC-SHA256 authentication and Ed25519 signed checkpoints are optional secure-runtime layers. Their secrets/private keys are not baseline credentials and must not be persisted in Git, prompts, audit events or Actions artifacts. The audit ledger is evidence only and cannot create Human approval, merge, release, publication or production authority.

Current automated inventory after Scenario 158:

- deterministic: 24
- lifecycle: 80
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 158 / 158


## Scenario 159 — Portable Governance Audit Bundle

Scenario 159 validates offline transfer of v0.48 governance evidence without introducing a remote audit service. A deterministic bundle binds the exact repository revision, AUDIT.jsonl digest/event count/chain head, selected evidence digests and checkpoint public-key fingerprints. An exported ANCHOR binds that manifest and can be retained independently to detect later truncation or replacement.

Signed histories must verify with their public key before bundle creation. HMAC material and signing private keys are never persisted. Bundle verification detects tampered ledger/evidence/public key/anchor and missing files. The bundle remains evidence only and grants no approval, merge, release, publication or production authority.

Current automated inventory after Scenario 159:

- deterministic: 24
- lifecycle: 81
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 159 / 159


## Scenario 160 — Governance Audit Retention & Verification Policy

Scenario 160 adds deterministic provenance discovery and evidence-lifecycle review over existing portable Governance Audit Bundles. Catalog registration first verifies each bundle, records exact repository revision / chain head / manifest + anchor digests / evidence digests, and maintains a checkpoint key registry.

A checkpoint key ID may appear across multiple bundles only with the same public-key fingerprint; key rotation uses a distinct key ID. SAL 2+ operational defaults require an external retained anchor and SAL 4 registration requires signed checkpoint evidence.

Retention is advisory only. Expired full-bundle thresholds produce REVIEW_DUE plus a minimal digest record for Human review; the helper has no delete/compact operation, automatic_delete=false and deletion_authorized=false. Legal hold overrides time-based review. The configured day counts are operational defaults, not legal or regulatory retention requirements.

Current automated inventory after Scenario 160:

- deterministic: 24
- lifecycle: 82
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 160 / 160


## Scenario 161 — Parallel Runtime Port Isolation

Scenario 161 validates runtime-resource isolation for parallel AIPS-managed worktrees. Repository-scoped atomic lease coordination prevents duplicate AIPS port assignments, occupied host ports are skipped, Task Graph runtime requirements remain deterministic metadata, and the resulting environment manifest provides canonical AIPS port variables plus explicit aliases such as PORT.

Runtime resources have an independent lifecycle: a dirty worktree remains preserved while a stopped server lease can be released; clean isolation removal releases remaining leases; orphaned leases whose isolation is no longer ACTIVE can be reconciled. Bounded reallocation excludes the failed port for address-in-use recovery. v0.51 supports TCP only and grants no additional network, merge, release, publication or Human authority.

Current automated inventory after Scenario 161:

- deterministic: 24
- lifecycle: 83
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 161 / 161

## Scenario 162 — MCP Interoperability Gateway

Scenario 162 lifecycle evidence executes the real local stdio MCP server with the official MCP Python Client. It verifies negotiated protocol 2026-07-28, Tools / Resources / Resource Templates / Prompts, canonical Role/Skill reads, deterministic Scheduler delegation, workspace path confinement and explicit ADVISORY authority metadata.

The MCP gateway does not execute a provider model and cannot intercept host-native tools. Existing native adapters remain separate. A dedicated exact-candidate workflow also installs pinned Codex CLI 0.155.1 and verifies AIPS MCP registration/discovery without provider inference.

Current automated inventory after Scenario 162:

- deterministic: 24
- lifecycle: 84
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 162 / 162

## Scenario 163 — Human Documentation Site & Canonical Placement

Lifecycle evidence validates the topic-oriented Human documentation placement contract, VitePress site source/build boundary, managed Unix installer, truthful Windows WSL launcher, backward-compatible bootstrap wrapper, and install/doctor/uninstall lifecycle.

Current automated inventory after Scenario 163:

- deterministic: 24
- lifecycle: 85
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 163 / 163

## Scenario 164 — MCP Tool-Only Host Compatibility

Scenario 164 extends the existing local stdio gateway for MCP Hosts that expose Tools but not Resources or Prompts. Read-only catalog/read/workflow Tools reuse canonical Role, Skill, allowlisted protocol and workflow definitions; no copied registry or provider-model execution is introduced.

Official MCP Python Client lifecycle evidence verifies tool annotations, canonical content, Security Review context, invalid-id failure, workspace confinement and deterministic review-only Cursor / Windsurf / GitHub Copilot CLI / Amp / Codex / generic configuration output. MCP remains ADVISORY and native adapters remain separate.

Current automated inventory after Scenario 164:

- deterministic: 24
- lifecycle: 86
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 164 / 164
## Scenario 165 — CI-Parity Publication Preflight

Scenario 165 lifecycle evidence also proves pre-commit working-tree closure, rule attribution, safe Core Matrix rebinding, expected test-count enforcement and label-event validation triggers.

Scenario 165 proves that local publication validation and GitHub Actions share one exact-candidate resolver for base/head, change class, canonical Core Change Test Matrix and documentation diff base. Fast documentation/diff checks run before the expensive Integration Gate; unavailable localhost/browser prerequisites are reported as `ENVIRONMENT_BLOCKED`.

Lifecycle evidence also covers ignored local metadata, recursive documentation impact, safe tree-equivalent post-squash reconciliation and fail-closed Project Intelligence revision refresh. Publication, destructive reconciliation and merge authority remain Human-controlled.

Current automated inventory after Scenario 165:

- deterministic: 24
- lifecycle: 87
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 165 / 165

Scenario 166 extends the Project Intelligence conformance surface with revision-aware temporal assertions and deterministic `current`, `as-of`, `between` and `why` queries. Its lifecycle evidence verifies validity intervals, supersession, provenance and fail-closed UNKNOWN handling without introducing a second documentation or authority model.
## Runtime Content Safety Scenarios

Scenario 173 verifies that the Parallel Run Dashboard presents sanitized, read-only run projections across parallel workspaces without exposing prompts, reasoning, secrets or mutation authority.

The content safety contract is exercised by scenarios 168–172 and the `tests/test_content_safety.py` lifecycle. New sinks, detectors or failure-mode changes require matching deterministic evidence.

## Scenario 174 — EARS Requirement Traceability

Scenario 174 is deterministic coverage for the optional Planning Package requirements registry. `tests/validation/ears_requirement_contracts.py` exercises valid functional/non-functional records plus invalid EARS labels, duplicate IDs, missing acceptance criteria and missing verification methods. It also invokes the CLI to check JSON PASS/FAIL reports and zero/non-zero exit codes for valid/invalid input. This validates the record shape and trace links; it does not infer natural-language semantics or upgrade evidence references into passing test results.

Current automated inventory: 27 deterministic + 93 lifecycle + 54 agent_eval = 174 / 174; manual 0; uncovered 0.
