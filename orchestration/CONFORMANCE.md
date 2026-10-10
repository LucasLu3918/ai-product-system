# Scenario Conformance

The Agent-facing rules in this document are normative. The generated Human current view and section-anchor history crosswalk live in `docs/human/CONFORMANCE_CURRENT.md` and `docs/human/CONFORMANCE_HISTORY_INDEX.md`; `tests/scenario_coverage.yaml` remains the canonical coverage data.

The retrieval relation extraction lifecycle checks legacy facade behavior against the internal implementation, including masking, relation rows and secret-path exclusion. It does not upgrade lexical evidence to compiler-resolved semantics.

Scenario 198 is lifecycle-covered by `tests/evidence/runtime_context_lifecycle.py` and `scripts/runtime_invariant_matrix.py`. Runtime Context reporting must remain credential-free, and the matrix must retain complete deterministic pair coverage within its declared case bound.

External Eval and red-team producers are normalized through `orchestration/EVAL_INTEROPERABILITY.md`. Their scores and findings remain REVIEW/SIGNAL evidence; a Human-confirmed minimal reproduction becomes a canonical Agent Eval Case before deterministic conformance can rely on it.

EARS validator 測試契約的文件影響限於本 Conformance 規範與對應的人類 Conformance / Technology Guide；需求追蹤實作、規劃範本、scenario registry 或本規範本身改動時，仍按 Requirement Planning 的完整文件閉包更新。

## Purpose


Make AIPS behavioral regression coverage measurable without conflating specification count with executable evidence.

## Registry


Keep Scenario coverage canonical. Optional Coding, Creative, Planning and Security workloads reference existing Cases; absent native task observations remain UNKNOWN even when the deterministic rubric passes.

創作可靠性 Core candidate 保留完整 Gate、媒材拒絕及取消授權回歸。損壞 PNG fixture 必須失敗；合成測試不能替代真實模型與人工品質驗收。

Scenario 230 binds compact fixed-context and task-route behavior to the intelligence context lifecycle and static contracts; route pointers never imply governance authority.

## Scenario 231 — Advisory Security Inventory and Secret-Scanner Shadow

Candidate secret scanning remains mandatory when optional toolchains are omitted.


OpenCode setup evidence does not replace candidate secret scanning, Core Matrix review, or exact-candidate publication checks.

The weekly/manual workflow runs the pinned OSV Scanner reusable workflow and a full-history Gitleaks shadow scan. Both scan outcomes are advisory evidence; the existing required candidate secret scan and `repository` Gate remain unchanged. The workflow has no PR, merge, or publication authority and leaves CodeQL default setup as remotely configured evidence.

## Scenario 232 — Project Check and System Preflight

Project Diagnostics remains read-only and does not perform its suggested recovery action.


OpenCode integration retains system preflight and existing-host lifecycle checks; missing runtime detection is not native acceptance evidence.

`aips project check <path>` reports attachment mode and Project Intelligence freshness without mutation; freshness problems remain informational and only an invalid path fails. `aips system preflight <path>` delegates to the existing update and repository-validation lifecycle. The legacy `aips preflight` route remains supported.

## Scenario 233 — Public CLI Help and Error Contracts

The existing command facade and stable output contract remain in place.


Scenario 236 adds fixed creative CLI routes; preflight and Gate inspection do not launch a provider.

Public command groups expose help with status 0 and return nonzero for unknown subcommands. Keep routing in the shell facade and preserve internal library modules as libraries.

## Scenario 234 — Local Character Artwork Provenance and Composition

Provenance keeps raster validity separate from inference and visual review.


Scenario 236 adds a separate explicit execution boundary for local MFLUX and loopback ComfyUI, including the fixed Z-Image Turbo split-loader graph and local model inventory checks; ComfyUI prompt PNG metadata is removed before AIPS output publication. Character identity and style review remain independent.

Scenario 234/236 also cover deterministic bounded prompt compilation, evidence-ranked model advice, and optional loopback-only vision review. Its separate advisory report cannot complete Human visual review or user acceptance.

The Phase 1 compiler extraction lifecycle additionally binds exact prompt/recommendation output parity, `creative_execution` function and `Blocked` class identity, and invalid-prompt reason parity. These checks do not represent model inference or image-quality acceptance.

The fixture lifecycle covers safe local profile/reference paths, SVG and PNG validation, exact hashes, verified provider/runtime/license provenance, and deterministic non-overwriting SVG composition with correctly typeset Unicode labels. A passing helper or manifest never proves generated character identity fidelity, model execution, or device performance; those require actual assets and separate human visual review.

## Scenario 235 — OpenCode Native Context and Action Guard

Each creative response derives its grant from the current native prompt hook and bounded Session continuation state; transcript recovery, stale prompts and advisory Context cannot restore authority.


Prompt classification keeps its legacy tuple and adds domain, intent, effect, and L0-L3 readiness. A managed V2 plugin resolves the active Session directory, injects a bounded Context before primary model dispatch, and rechecks current Context and target confinement before supported native file permissions. L1 is limited to new creative assets in non-Git workspaces; L2 requires READY/CURRENT project evidence; external actions retain existing Human approval. EPHEMERAL creative sessions receive read-only asset metadata from a private external cache with versioned no-overwrite suggestions. Shell rejects known command/argument side effects but is not a process sandbox. Optional native acceptance uses an isolated loopback mock model to verify actual Context delivery and native file Allow/Deny. Host discovery and execution remain UNVERIFIED without that evidence, so governance remains ADVISORY. `aips harness trace` provides an allowlisted privacy-limited event view. MCP/custom tools and out-of-process writes are outside the guard.

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

Each lifecycle must have one execution owner in repository validation. `runtime_contracts` executes `intelligence_context_lifecycle.py`; `conformance_isolation` retains the artifact-existence check only. The MCP lifecycle executes and validates configuration output for all six advertised clients, so validator modules must not repeat those CLI invocations.

## Agent Eval admission

Cases may bind results to repository-relative system dependencies. The evaluator marks mismatched evidence `STALE` and legacy results `UNBOUND`; neither historical rubric scores nor missing fingerprints claim current-system conformance.

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

The capability extends the existing Execution Profile and Governance path; it does not introduce a Role, Skill or approval gate. Its Isolation Profile may optionally carry `runtime_class`, `minimum_isolation`, `verification_status` and `data_class`; older profiles omit these fields without migration. Scenario 111/114 cover fail-closed risk/data resolution and the synthetic-only E2B verification lane; mock or skipped evidence is not live-provider verification.

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

Scenario 156 validates that normal branch hygiene stays report-only while a separately reviewed one-time manifest may delete only exact EPHEMERAL branch+SHA entries after complete-batch preflight. The manifest main baseline must match the current target tip; any absent or moved ref, non-ephemeral branch or non-integrated branch blocks the batch before deletion. A deletion failure stops the batch, reports completed rows, and the original manifest cannot resume after any row is absent. Persistent/unclassified/pending branches remain preserved.

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

The publication lifecycle evidence also covers the `publish_preflight` compatibility facade delegating post-merge reconciliation to `publish_post_merge` without changing synchronization safeguards.

Preview MUST report working-tree documentation placement and actionable Core Matrix binding guidance before commit; final PASS remains bound to the clean committed candidate and its CI result.

Scenario 165 lifecycle evidence also proves pre-commit working-tree closure, rule attribution, safe Core Matrix rebinding, expected test-count enforcement and label-event validation triggers.

Scenario 165 proves that local publication validation and GitHub Actions share one exact-candidate resolver for base/head, change class, canonical Core Change Test Matrix and documentation diff base. Fast documentation/diff checks run before the expensive Integration Gate; unavailable localhost, Python/Ruff or browser prerequisites are reported as `ENVIRONMENT_BLOCKED`. Local publication checks changed Markdown links and builds the documentation site when documentation paths change.

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

## Scenario 175 — Risk-adaptive bounded Change Impact

Validation-only changes may use bounded source review when the Impact Graph cannot map the repository validator, provided the validator-to-Gate path is evidenced and graph-wide product impact remains explicitly unknown.

Scenario 175 is lifecycle coverage for rebuildable lexical relation indexing, bounded caller/consumer traversal across code and canonical architecture edges, risk-specific depth/history, explicit unknown and truncation states, seed-scoped graph coverage that preserves repository-wide partial status, changed/unchanged affected-node dispositions and READY evidence validation. It does not claim compiler-grade reference resolution.

Current automated inventory: 27 deterministic + 98 lifecycle + 54 agent_eval = 179 / 179; manual 0; uncovered 0.

## Scenario 177 — Runtime Policy Enforcement

Scenario 177 is lifecycle coverage for deny-by-default action authorization, stable action and policy digests, exact expiring Approval Record binding, SAL-aware egress, fresh sandbox allowlist proof, semantic deny/escalate monotonicity, sanitized audit metadata and truthful Claude/Gemini native hook responses. It proves the hooks' observable boundary only; indirect child-process or SDK network access still requires OS/sandbox egress enforcement. Codex remains `ADVISORY`.

Current automated inventory: 27 deterministic + 98 lifecycle + 54 agent_eval = 179 / 179; manual 0; uncovered 0.

## Scenario 179 — Evidence-backed Change Impact Unknown Dispositions

Lifecycle and contract evidence cover structured dispositions, explicit Human review, current in-root file hashes, canonical traversal digests and seed-scope binding. Legacy strings, malformed or stale evidence, incomplete traversal and scope mismatch remain blocking; exact READY diff reconciliation and repository-wide coverage semantics are unchanged.

Current automated inventory: 27 deterministic + 98 lifecycle + 54 agent_eval = 179 / 179; manual 0; uncovered 0.

## Scenario 181 — OpenTelemetry Telemetry Projection & Export

Lifecycle evidence validates bounded existing-event extensions; deterministic OTLP projection/replay; exact pinned GenAI field names; duration spans only for complete timestamp pairs; Gate waiting intervals; independent-review correlation without inherited context; HTTPS/loopback policy; host-only credentials; content/secret rejection; local receiver behavior; and transport-failure degradation without changing AIPS execution results.

Current automated inventory: 27 deterministic + 100 lifecycle + 54 agent_eval = 181 / 181; manual 0; uncovered 0.

## Scenario 182 — Deterministic Execution Ownership

Lifecycle evidence covers scheduler-serialized task claims, active AIPS worktree binding, lease heartbeat/stale/recovery states, actual Git-diff reconciliation, out-of-scope blocking and read-only owner projection. Legacy Task Graph v1 and checkpoints remain valid; current Resource Authorization enforcement stays `ADVISORY`.

The shared deterministic helper extraction keeps caller facades and digest/path/glob contracts stable; its lifecycle evidence does not claim complete repository caller/consumer graph coverage.

Current automated inventory: 27 deterministic + 101 lifecycle + 54 agent_eval = 182 / 182; manual 0; uncovered 0.

## Scenario 183–192 — Planning Package v2


Scenarios 241–256 specify manual routing expectations for the newly admitted engineering and game Skills. Keep them manual until direct deterministic, lifecycle, or Agent Eval evidence exists; a routing case does not prove a playable product or participant testing.

Preserve eligible runtime primary preference and canonical Skill metadata; deterministic registry evidence does not prove semantic model selection or relax existing isolation, review or Human authority.

Scenarios 183–192 cover optional manifest dependency graphs, stable requirement and acceptance traceability, separate Human approvals at Gate 1 and Gate 2, reuse of product and data-modeling capabilities, cross-artifact UX/visual/domain/API references, legacy package compatibility, on-demand e-commerce guidance, actionable structural diagnostics and an end-to-end planning journey. Structural and lifecycle contracts run locally; Scenario 192 remains manual because a real product-specific planning and approval journey requires human decisions.

Current inventory after Scenario 192: 34 deterministic + 103 lifecycle + 54 agent_eval = 191 / 191 automated; 1 manual; 0 uncovered.

## Scenario 199 — Branch cleanup proposal evidence

Lifecycle evidence checks supported ephemeral prefixes, PR state, branch age, integration, read-only proposals and the explicit protected-main exact-manifest cleanup boundary.

## Scenario 200 — Demand-driven CI toolchain planning

Lifecycle evidence checks exact-path optional tooling, full provisioning for unknown or sensitive paths and `tests/validation/mcp_interoperability_contracts.py`, and preservation of mandatory validation stages.

## Scenario 193 — Evidence-driven Implementation Resolution

OpenCode Command and Skill projections preserve canonical source paths and planning authority; native entrypoints do not replace implementation readiness evidence.

Scenario 193 covers REST/OpenAPI-first resolution across existing and new projects, four language profiles, technology/architecture decisions, evidence provenance, contract authority, ownership protection, version-aware knowledge, and verification status. Deterministic and lifecycle checks validate profile structure and validator boundaries. Semantic quality across 16 representative contexts remains manual; structural checks do not claim that an Agent recommendation is correct.

Current inventory after Scenario 193: 34 deterministic + 103 lifecycle + 54 agent_eval = 191 automated; 2 manual; 193 total; 0 uncovered.

### Scenario 194 — OpenAPI contract validation and revision-bound evidence

`scripts/openapi_contracts.py` validates OpenAPI 3.0, 3.1 and 3.2 offline, confines local references to the repository, classifies compatibility conservatively, runs declared contract tests without a shell, verifies operation coverage in JUnit, and binds reports to content digests and the exact revision. Unknown classifications, stale evidence and unavailable checks fail closed. Evidence does not authorize breaking changes or establish semantic test quality.

### Scenario 195 — Implementation Resolution deterministic enforcement

`scripts/implementation_enforcement.py` verifies exact-candidate Profile fingerprints, language identity, in-scope ownership, generated input/output hashes, fresh project-command evidence and Phase 2 OpenAPI reports. Lifecycle fixtures cover missing and stale evidence, command timeout, shell refusal, report stability and optional Integration Gate report/enforce modes. These checks do not prove generator execution or semantic test quality.

## Scenario 196 — Explicit OpenAPI client generator adapter

Lifecycle evidence proves preview and the Integration Gate do not execute generators; an explicit local `--execute` uses pinned repository-local tools, staged inputs, bounded execution and allowlisted outputs. It verifies deterministic output, Phase 3 ownership/hash records and atomic rollback, and rejects stale OpenAPI evidence, unsafe paths, unexpected files, timeouts and edited generated outputs. This is execution safety and provenance evidence; it does not prove generated client semantics or provide an operating-system sandbox.

Current inventory after Scenario 196: 34 deterministic + 106 lifecycle + 54 agent_eval = 194 automated; 2 manual; 196 total; 0 uncovered.

**Scenario 197 — Shared OpenAPI client reference pilot.** A temporary standalone Widgets project runs canonical validation, explicit deterministic generation, local HTTP client/consumer tests, operation coverage and exact-candidate Phase 3 inspection. Missing or altered execution reports block the opted-in Profile. This lifecycle covers the reference workflow; product-specific acceptance stays in each product repository.

Current inventory after Scenario 197: 34 deterministic + 107 lifecycle + 54 agent_eval = 195 automated; 2 manual; 197 total; 0 uncovered.

Repository validators are imported only through the explicit ordered `tests/validation/registry.py`. Preserve the current import order and timing labels; keep the ordered error aggregation list separate from import order. Lifecycle evidence remains owned by the explicit evidence runner and must not be duplicated by the registry.

## Scenario 201 — Monthly maintenance reliability evidence

`tests/evidence/maintenance_reliability_lifecycle.py` checks bounded collection, deterministic validation/runtime distributions, explicit hotfix labels, repeated changed paths, heuristic failure categories, exact merge-SHA regression linkage and UNKNOWN behavior for incomplete histories, timestamps or changed-file counts. `tests/validation/maintenance_reliability_contracts.py` checks config bounds and workflow permissions. The monthly workflow may publish an observational report and deduplicated review Issue with Actions/contents/pull-request read and Issue write permissions only; it cannot remediate, change code, create PRs, merge or release. Category names are hints rather than root-cause findings.

The workflow uses the shared Python bootstrap and queues up to 100 same-cohort Issue reports without cancelling a running or pending report. Its timeout remains unset until a successful run establishes a defensible timing baseline.

The shared repository evidence runner uses the exact-candidate CI plan to skip optional OpenAPI-dependent lifecycle checks only when OpenAPI is not selected; it removes that plan from contract and lifecycle subprocess environments. Secret scanning, the required repository aggregate and Integration Gate remain mandatory.

Plan21 Phase 2 uses `tests/evidence/shared_primitives_lifecycle.py` to pin deterministic helper compatibility and retains partial graph coverage.

Current inventory after Scenario 201: 34 deterministic + 111 lifecycle + 54 agent_eval = 199 automated; 2 manual; 201 total; 0 uncovered.

Plan21 Phase 0 adds a required lifecycle for canonical digest vectors, public CLI byte/exit behavior, and intentionally different path-glob semantics. Its checked-in timing artifact records one exact-main observation only; it changes no runtime behavior and does not add a numbered scenario.

The central validator registry lifecycle also verifies exact-plan browser selection: only a valid `needs_browser: false` plan skips visual and creative render validators, and full validation imports them when no skip is declared.

## Scenario 218 — Evolution Human Relevance Evaluation

Scenario 218 uses deterministic monthly fingerprint sampling and complete Human relevance/actionability labels. It reports shortlist precision/recall and source-level yield; empty, uncertain or incomplete cohorts remain `NOT_READY`, and results grant no source-policy mutation authority.

## Scenario 220 — Parallel advisory fast feedback

Validation Observation 新增相同候選的完整耗時量測與依 Change Class 分組的 P50／P95。重跑不當作新的 PR；歷史紀錄不完整時不授予 selective execution，完整驗證與 required repository check 維持。

Scenario 239 adds bounded source relationship discovery with explicit provenance, truncation and unresolved dynamic behavior; it does not promote graph edges.

Unknown paths continue to select the complete validation profile.

The required validation workflow exports the provisioned Python interpreter to isolated subprocess fixtures before the deterministic Gate, and the publish preflight contract checks that exact step ordering.

The static workflow contract requires PR concurrency groups to include both PR identity and event action, so `opened` and `labeled` events cannot cancel one another; repeated runs for one action still supersede earlier runs, and the `repository` check remains required.


The current creative execution Scenario is registered in the canonical coverage file and represented in the generated Human conformance summary.

Scenario 224 is manual semantic acceptance for runtime-preferred primary routing. Scenario 225 is executable Skill-index lifecycle evidence; it does not prove actual Agent model selection.

Plan17 regression evidence covers numeric diff headers, four browser/OpenAPI combinations, mandatory aggregates, reusable caller keys/permissions, explicit Python and isolated children, recursive placement, signed identity/immutable proposal rejection and atomic deletion races. Missing or malformed capability plans retain the full profile. A latest cancelled check stays INCOMPLETE; replaced old checks are reported as SUPERSEDED.

The pull-request workflow runs the bounded repository preflight in a separate job against the exact candidate. Findings are visible but advisory; the complete Janitor Integration Gate and required repository validation remain independent and unchanged. Label-only events skip this job.

Scenarios 211 and 217 also verify that dependency-review shadow evidence cannot change the required repository outcome and that completed `NOT_READY` observation evidence remains distinct from operational errors.

## Scenario 221 — Dependency Update Risk Classification

Dependency reports preserve Human review and do not merge unrelated pull requests.


`scripts/dependency_impact.py` classifies dependency updates from `config/dependency-policy.yaml` and recommends evidence by class. Unknown packages are `UNCLASSIFIED` / `HIGH`; semantic runtime changes require retrieval regression and semantic trial evidence. The CLI is advisory, requires a human decision, and never authorizes automatic merges or policy edits.

## Scenario 222 — Large Document Measurement Only

文件大小報告附上前十二個既有 H2 閱讀入口，並區分文件與 Canonical machine-readable 來源；仍只回報 WARN，不複製 Registry、搬移文件或縮減 Gate。

Documentation closure metrics are report-only and do not weaken placement requirements.


The size audit measures tracked text/evidence files against 50,000 bytes and reports oversized items as non-blocking `WARN`. It never blocks a Gate and does not archive or move files.



## Scenarios 202–209 — Plan13 current and provenance evidence

The shared Python bootstrap preserves optional constraints on macOS Bash 3.2 by prepending them to its non-empty requirements argument array. Its lifecycle executes the actual shell body for constrained/unconstrained inputs, exact argument quoting and fail-closed empty requirements.

CI always installs Python packages from all four validation requirement files because mandatory full-repository lifecycle fixtures exercise the complete CLI preflight. Candidate-path selection still controls Node and Playwright Chromium installation.

Candidate evidence stays bound to exact paths and reports missing facts as unknown. The current quality ratchet records a Ruff baseline and bounded report-only lifecycle coverage; it does not expand the validated module scope or grant release authority.


Creative authorization and multi-item output are recorded under Scenario 238 and the current Core Matrix; this remains local adapter evidence and makes no provider or visual-quality claim.

創作驗證分別記錄命令盤點、合成 tool/provider 測試、native host 驗證及真實模型推論。未提供權重時，品質／設備效能維持未驗證，不以流程通過推定改善成效。

OpenCode runtime changes retain existing Plan13 provenance and maintenance governance; host discovery alone is not enforcement evidence.

Scenario 236's exact-candidate Core Matrix records synthetic creative lifecycle and documentation evidence; it does not claim live engine inference or visual-quality acceptance.

## Scenario 238 — Creative Task Authorization and Multi-item Execution

Creative task authorization remains separate from Git publication; personal PR merge confirmation follows the publication policy and Scenario 240.

Each item retains explicit execution intent and distinct review/acceptance state.


Native OpenCode V2 prompt admission issues a fresh in-memory grant bound to the active session, workspace, actions and bounded output count. A short style selection can derive a new grant only from root-bound, expiring structured continuation state; cancellation, unrelated work, scope expansion and output-cap exhaustion revoke it. Raw prior prompts and transcript context cannot restore authority. Read-only discovery and preflight remain available without a grant.

The synthetic multi-item lifecycle verifies per-item preflight, continue-on-failure, hash-verified resume and recovery after an output succeeds before its checkpoint. Version-only local engine discovery never starts generation. Native OpenCode acceptance verifies grant admission and revocation without invoking image generation; no real model quality or visual acceptance is claimed.

Scenario 239 binds bounded read-only Impact Graph relationship candidates to import, literal CLI dispatch, test, and documentation registry evidence; lifecycle checks confirm source-line provenance, explicit dynamic unknowns, budget truncation, unchanged canonical graph bytes and partial/unknown global coverage.

## Scenario 236 — Local Creative Bundle Execution

Creative lifecycle success does not issue a Git publication grant. The shared CLI dispatch preserves separate creative/publication authorization and is covered by the complete repository validator.

Creative trace summaries record bounded completion, failure and duration samples. The quality benchmark checks confined output digests before showing separately recorded Human dimension ratings; fixtures, valid containers and aggregate timings do not establish visual acceptance.

Synthetic-provider success does not establish real model inference or visual quality.


Project Diagnostics remains a separate read-only command and does not configure or execute the Creative Bundle lifecycle.

Z-Image Turbo generate evidence verifies its fixed dedicated executable, explicit step preservation and rejection of edit, non-Turbo variants and the generic FLUX executable. Existing offline execution, scoped provenance and pending human review apply unchanged.

Scenario 236 extends the existing lifecycle with create-only configuration/discovery, native tool callback envelopes, user-only grant revocation, medium mismatch and corrupt raster rejection. Synthetic fixtures cannot claim installed-model inference, visual acceptance or hardware performance.

Creative readiness evidence also covers read-only fixed-loopback discovery, empty ComfyUI model catalogs, staged command/runtime/model/preflight/inference status, sanitized provider-specific recovery and an advisory Apple Silicon FP8 warning.

Scenario 236 extends the adapter with explicit intent, versioned Profile/Bundle preparation, preflight and a local-only creative tool. Its MFLUX capability map fixes model/operation commands; FLUX.1 edit is single-reference, FLUX.2/Qwen multi-reference edit is bounded, and ComfyUI edit remains single-reference.

The synthetic lifecycle uses fake MFLUX and loopback ComfyUI only. It verifies preflight does not run a generator, explicit execution stays inside non-Git EPHEMERAL scope, model/runtime/license and profile hashes are bound to output provenance, ComfyUI is loopback-only with built-in nodes, edits use a hash-matched staged input, retries are finite, no output is overwritten, review starts PENDING, and traces reject prompts, image data, secrets and paths. Real model execution, device performance and visual quality require a user-configured local engine and independent human inspection; no model is installed or downloaded by validation.

Required install/preflight and legacy-migration lifecycles need all Python validation requirements even for docs-only candidates. Provisioning contracts reject conditional or missing Python requirements and unconditional Chromium downloads; exact-plan optional evidence and browser-download selection remain unchanged.

Plan21 helper consolidation preserves covered canonical fingerprints and keeps unresolved source relationships partial.

Scenario 209 also covers the read-only repository governance snapshot lifecycle, including UNKNOWN surfaces and stable fingerprints.

Scenario 207 verifies declared bootstrap imports and dependency consistency, and confirms malformed or missing modules fail closed.
It also verifies Maintenance Reliability's shared bootstrap, Repository Health's provisional timeout and exact-revision serialization, Evolution Effectiveness's same-period non-cancelling queue, and Validation Observation's retained timeout without coalescing independent evidence runs.

The public AIPS shell CLI keeps `bin/aips` as its thin launcher and `scripts/aips_cli.sh` as the checkout-resolving facade; implementation modules are loaded relative to that resolved checkout. `tests/evidence/aips_cli_module_extraction_lifecycle.py` covers source and symlink entrypoints from an unrelated working directory.

Scenario 204 的 module-extraction evidence 斷言 temporal query 與 Evolution pre-analysis 的 facade object identity，並檢查 deterministic current-mode availability、canonical path 與 digest。

Scenario 211 binds Dependency Review and scheduled Scorecard permissions/action SHAs. Scenario 212 validates complete shadow evidence before human review, and Scenario 213 checks the quality debt ceiling and deterministic SemVer properties. None independently grants release or selective-validation authority.

The Human current summary and Human/Agent history crosswalk are generated from this protocol, `docs/human/CONFORMANCE.md`, and `tests/scenario_coverage.yaml` by `scripts/conformance_summary.py`. Edit authoritative sources, regenerate, and verify with `aips conformance summary current|history --output <path>`; retained historical sections keep their anchors. The eight scenarios cover Evolution completeness, validation shadow/replay, module facades, branch proposals, conformance views, workflow bootstrap, tag provenance and ruleset policy.

### Scenarios 214–219 — Plan15 operational closure

These lifecycle scenarios bind release-channel readiness, runtime constraints, quality debt, full-run validation observations, human Evolution relevance labels, and validation taxonomy alignment to focused evidence. The read-only observation collector installs its declared profile under `constraints/tested.txt` before importing the collector; missing dependency or incomplete evidence remains `NOT_READY`. Its 15-minute timeout is provisional from only two runs at about 31 seconds, so it is not a reliable P95. It has no concurrency group that could replace pending scheduled or manual evidence. These scenarios retain full validation, human decision authority, and fail-closed behavior when evidence is incomplete.

- Scenario 208 requires exactly one empty canonical `## Unreleased` section before release readiness; malformed or pending entries block.
Plan19's module-extraction lifecycle continues to verify the Project Intelligence facade and stable imports; freshness selection reports affected Eval cases while preserving manual scenarios 192, 193 and 224.
### Scenario 223 — Evolution Radar exclusion attribution

Verifies deterministic pre-analysis exclusion reasons and counts without changing Human decision authority.
## Scenario 210 — Python runtime support policy

The OpenCode lifecycle runs with the selected validation Python. OpenCode itself is detected separately and is never downloaded by Harness installation.

Scenario 210 is lifecycle-covered by `tests/evidence/install_preflight_lifecycle.py` and `tests/evidence/system_facts_lifecycle.py`. It verifies the Python >=3.12 floor across explicit selection, old managed venv repair, doctor diagnostics, canonical facts, and the scheduled 3.12–3.14 compatibility workflow.

## Scenario 237 — Read-only Project Diagnostics and Recovery Guidance

Scenario 240 covers the personal publication default and high-assurance opt-in, including PR/merge separation and the accepted current-origin trust boundary.

The governance validator executes signed publication lifecycle regressions in `tests/test_publication_authority.py`, including actual Hook deny envelopes and SQLite concurrent single-use consumption. Fixture keys never establish an external production issuer.

Its read-only diagnostic path remains separate from creative Profile compilation, model recommendation and local visual-review actions.

Recovery suggestions remain read-only and conditional across missing, stale, partial and blocked Intelligence. The lifecycle does not invoke the suggested bootstrap, refresh or finalization action.

Scenario 237 binds reason-code recovery output, format parity, privacy redaction and no-write behavior to lifecycle evidence. It does not assert live Host or MCP execution.
