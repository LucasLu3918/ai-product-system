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
