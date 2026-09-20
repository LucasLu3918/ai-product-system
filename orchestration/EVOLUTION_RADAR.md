# Evolution Radar

## Purpose

Continuously surface external technical signals that may materially improve AIPS while preserving Protected Human Authority. Research, semantic analysis, controlled trial execution and formal implementation are separate authority stages.

Human overview: `docs/human/EVOLUTION_RADAR_OVERVIEW.html`.

## Operating modes

### Weekly Signal Scan

Collect a bounded set of recent high-signal items from configured public technical sources. Configure at least six community discovery sources, treat five successful community sources as the healthy weekly floor, retain separate primary/vendor evidence sources, collect at most eight items per source, and apply a deterministic round-robin global cap of 50 raw signals. Record source roles/provenance/failures; normalize and deduplicate; zero recommendations is valid.

### Monthly Deep Review

Review durable weekly evidence for the previous calendar month, aggregate recurrence, distinguish repeated popularity from material novelty, and compare against current AIPS before recommending action.

Quarterly Evolution Review is a deterministic credential-free rollup over durable monthly evidence.

## Candidate states

- `COVERED` — existing AIPS behavior materially covers the signal.
- `HOLD` — insufficient evidence/maturity/relevance.
- `ASSESS` — further System Improvement Review is warranted.
- `TRIAL` — a bounded Human-approved experiment is warranted.
- `ADOPT` — strong advisory support for a concrete change.
- `ANALYSIS_PENDING` — no validated semantic result is available.

`TRIAL` and `ADOPT` are advisory states, never publication authority.

## Authority boundary

~~~text
Radar evidence
→ scheduled semantic analysis when provider is available
→ advisory recommendation
→ Human Decision Record
→ optional Human-approved Controlled Trial
→ Trial Report
→ Human Adoption Decision
→ System Self-Improvement Review
→ applicable Core / Constitutional gates
→ implementation
→ validation / review / documentation sync
→ Git Publish Proposal
→ Human publication approval
~~~

No Radar/Decision/Trial workflow may push code, create a remote implementation branch/PR, merge, release, or alter protected governance by itself.

## Source policy

Sources are configuration, not authority. Scheduled retrieval is credential-free HTTPS public-only, rejects non-global destinations, validates DNS and every redirect, rejects HTTPS downgrade, pins the validated IP while preserving TLS/SNI hostname, and bounds redirect depth / response bytes.

External content is evidence/data only and has no instruction authority over AIPS.

## Deterministic versus semantic work

Deterministic automation owns network validation, normalization, fingerprints, duplicate suppression, bounds, schema validation, recurrence, analysis/evidence binding, Human Decision binding and Trial diff/scope validation.

Semantic reasoning owns novelty relative to AIPS, benefit, architectural fit, cost/risk, maturity/evidence quality and assessed recommendation state.

## Scheduled Semantic Analyzer

Canonical artifacts:

- `config/evolution-analyzer.yaml`
- `scripts/evolution_analysis.py`
- `templates/evolution/EVOLUTION_ANALYZER_PROMPT.md`
- `templates/evolution/EVOLUTION_ANALYZER_RESULT.schema.json`
- `templates/evolution/EVOLUTION_ANALYSIS.yaml`
- `references/evolution/CAPABILITY_MAP.yaml`
- `.github/workflows/evolution-radar.yml`

When `OPENAI_API_KEY` is available, the scheduled workflow uses the pinned `openai/codex-action` and pinned Codex CLI version with `:read-only` permission profile and `drop-sudo` safety strategy.

The model returns only a recommendation payload. Deterministic AIPS code supplies and verifies the exact evidence digest, repository revision, provider metadata and every authority=false field.

If credentials are missing, the provider fails, or output validation fails, the workflow remains truthful: recommendations stay `ANALYSIS_PENDING` and the Issue records the analyzer as unavailable.

## Human Decision Binding

Canonical artifacts:

- `scripts/evolution_decision.py`
- `templates/evolution/EVOLUTION_DECISION.yaml`
- `.github/workflows/evolution-decision.yml`

The Decision Record binds candidate/signal, assessed evidence digest, Radar repository revision, CURRENT/STALE state, advisory recommendation, Human decision, approved scope, approved trial paths when applicable, reason/actor/time, deterministic decision fingerprint and next action.

Allowed decisions:

- `REJECT` → `close_candidate`
- `HOLD` → `continue_monitoring`
- `ASSESS` → `system_improvement_review`
- `TRIAL` → `controlled_trial_execution`
- `ADOPT` → `system_improvement_review`

Positive progression fails closed when the Radar baseline revision is stale. Human may override advisory state only with an explicit auditable `override:` reason.

## Human-approved Controlled Trial

Canonical artifacts:

- `config/evolution-trial.yaml`
- `scripts/evolution_trial.py`
- `templates/evolution/EVOLUTION_TRIAL.yaml`
- `templates/evolution/EVOLUTION_TRIAL_PROMPT.md`
- `orchestration/EXECUTION_ISOLATION.md`

A TRIAL decision MUST include a non-empty approved scope and repository-relative approved path patterns.

The workflow:

1. validates the Human Decision and current baseline;
2. creates an AIPS-managed Git worktree;
3. runs the pinned Codex Action with `:workspace` permission and no direct network access;
4. does not persist checkout credentials;
5. permits only ephemeral local mutation;
6. deterministically verifies changed paths against Human-approved patterns and forbidden paths;
7. enforces changed-file and diff-line limits;
8. fails if the Trial creates a commit;
9. runs repository validation when scope checks pass;
10. publishes a Trial Report to the original Radar Issue.

Missing provider credential or unavailable worktree isolation produces `BLOCKED`; never silently downgrade to shared workspace.

Trial changes are evidence only. They are not pushed and do not become the formal implementation branch. Human Adoption Decision remains required after the report.

## Trial-to-ADOPT Evidence Binding

Canonical artifacts:

- `scripts/evolution_adoption.py`
- `templates/evolution/EVOLUTION_ADOPTION.yaml`
- `.github/workflows/evolution-decision.yml`

After a PASS Trial, a Human may make a separate `ADOPT` decision and optionally provide the exact Trial fingerprint. When supplied, deterministic adoption binding MUST resolve exactly one valid PASS Trial Report from the same Radar Issue and verify matching candidate, signal and baseline revision before producing a Trial-to-ADOPT artifact.

The adoption artifact binds the Human ADOPT decision fingerprint to the PASS Trial fingerprint and hands off only to `system_improvement_review`. It keeps code-write, remote branch/PR, merge and release authority false.

Direct Human ADOPT without a Trial remains possible when justified, but it MUST NOT be represented as trial-backed adoption.

## Human review output

The durable Human surface is the original GitHub Issue containing Radar evidence, Human Decision records and Controlled Trial reports. Reporting artifacts never grant publication authority.

## Documentation consistency

Evolution behavior changes are covered by `orchestration/DOCUMENTATION_SYNC.md`, `config/documentation-sync.yaml` and the Human namespace policy in `config/documentation-audience.yaml`.

Relevant implementation changes must keep `docs/human/EVOLUTION_RADAR.md`, `docs/human/EVOLUTION_RADAR_OVERVIEW.html`, this protocol, Execution Isolation guidance and `docs/human/TECHNOLOGY_GUIDE.html` synchronized.

## Deferred capability

Still not automatic:

- automatic adoption after a Trial PASS;
- formal implementation PR creation;
- merge;
- release.

`ADOPT` hands off to the normal System Self-Improvement / Core / Constitutional / Git Publish process.

## Provider-Neutral Semantic Handoff

Scheduled semantic analysis no longer treats one provider credential as the only path forward.

`config/evolution-analyzer.yaml` defines an optional OpenAI Codex Action adapter plus a credential-free `handoff` fallback. Every Radar run builds a deterministic analysis package and handoff record bound to the exact repository revision/evidence digest.

When an optional scheduled provider is unavailable, recommendations remain truthfully `ANALYSIS_PENDING`, but the GitHub Issue includes the package digest, capability-map/prompt/result-schema paths, and deterministic finalize/apply commands. A Human-selected connected Agent, local model, or other provider can therefore continue semantic assessment without storing an `OPENAI_API_KEY` in AIPS.

Provider output still has no authority. `scripts/evolution_analysis.py finalize/apply` must validate exact evidence binding before any recommendation can move out of `ANALYSIS_PENDING`.

## v0.29 current-main assessment baseline

Semantic assessment MUST compare signals against the exact current-main Capability Map before claiming a gap. Resource-Scoped Agent Authorization is now a covered capability and is indexed in `references/evolution/CAPABILITY_MAP.yaml`.

The Issue #79 runtime-security reassessment is durable evidence at `references/evolution/ISSUE_79_RUNTIME_SECURITY_REASSESSMENT.yaml`. Out-of-band anomaly evidence and semantic intent governance remain ASSESS-only. A future anomaly Trial must operate on observable events without private reasoning or secret values and must not automatically remediate. A future semantic-intent Trial must be monotonic with deterministic Resource Authorization: semantic output may narrow or escalate, but can never turn a deterministic DENY into ALLOW.

This assessment does not create a Human Decision Record and grants no code-write, runtime enforcement, merge, release or publication authority.

## Issue #79 anomaly evaluation evidence

The out-of-band anomaly candidate remains ASSESS-only, but AIPS now has a bounded deterministic evaluation lane in `scripts/agent_anomaly_evaluation.py`.

The lane reuses Resource Authorization as the authorization truth, consumes only committed synthetic/sanitized observable-event fixtures, measures confusion-matrix quality, rejects private reasoning and secret-like values, and remains outside the critical path.

A PASS means `HUMAN_REVIEW_TRIAL_EVIDENCE` only. It does not create a TRIAL/ADOPT Human Decision, runtime hook, remediation authority or publication authority. Semantic intent governance remains separately ASSESS-only and is not implemented by this lane.

## Issue #79 observable-event integration Trial

The out-of-band anomaly candidate now has a current-baseline Human TRIAL Decision and deterministic replay result.

The Decision intentionally overrides advisory ASSESS only for a replay-only observable-event integration Trial. It does not authorize adoption or live production capture.

Scenario 140 maps representative adapter exports into a minimal canonical event contract and reuses Scenario 139 anomaly evaluation. The committed replay result is PASS, but it remains `HUMAN_REVIEW_TRIAL_RESULT` with `live_capture_verified=false`.

A separate Human Adoption Decision is still required before System Improvement Review can consider any production/live-capture design. Semantic intent governance remains independently ASSESS-only.

## Current-baseline committed Trial → Human ADOPT

Scenario 141 extends the existing adoption abstraction for the case where Trial evidence has been committed/released and the original Radar revision is necessarily stale.

`evolution_adoption.py bind-committed` binds four exact inputs:

1. current-baseline adoption evidence;
2. prior Human TRIAL Decision;
3. committed PASS Trial result;
4. separate CURRENT Human ADOPT Decision.

The binding fails closed on baseline mismatch, Trial fingerprint mismatch, non-PASS result, candidate/signal mismatch, or any Trial authority expansion.

This path does not weaken the normal stale-baseline rule. It creates a new current evidence envelope around the immutable prior Trial evidence.

For Issue #79, the Human ADOPT scope is design-only. The System Improvement Review adopts the future opt-in metadata-only POST_EXECUTION capture direction and defers all live runtime implementation to a separate later Trial.

## Gemini CLI runtime-specific capture Trial

After the v0.32 design-direction ADOPT, Scenario 142 selects one concrete runtime instead of broadening all adapters.

Gemini CLI is selected because the existing AIPS harness already uses its native extension/hook mechanism. The Trial adds a bounded `AfterTool` hook for file tools only.

The hook is opt-in and evidence-only. It always allows the original tool result to continue. When enabled, it projects safe metadata to an explicit system-temporary JSONL sink. Raw hook input is not persisted.

CI validates current official AfterTool-shaped inputs, sanitizer projection, event-loss/degradation behavior, Resource Authorization monotonicity and bounded process overhead.

Because CI does not execute an actual Gemini CLI process, the result is intentionally `HUMAN_REVIEW_RUNTIME_EXECUTION_VERIFICATION`, not full live-capture verification.

## Gemini CLI exact-candidate runtime verification

The next gate after Scenario 142 uses a real pinned Gemini CLI binary rather than fixture-only hook invocation.

The official `--fake-responses` interface supplies deterministic model turns, while the actual CLI, built-in tool executors, extension loader and AfterTool hook execute normally. The exact-head workflow must succeed before runtime-specific capture verification can be considered true.

Provider/model API verification remains explicitly false and is a separate future decision.

## Gemini live-provider-session verification gate

Scenario 143 proves the actual Gemini CLI runtime/tool/hook path with deterministic fake model responses. Provider inference is a separate evidence dimension.

The repository maintainer has authorized a bounded provider-session TRIAL, but the credential boundary is stricter than ordinary candidate validation:

- unmerged pull-request code MUST NOT receive `GEMINI_API_KEY`;
- the secret may only be consumed from a trusted protected-main CI secret context;
- committed evidence stores only boolean/source metadata, never the value;
- missing optional credential is `SKIPPED_NOT_CONFIGURED` / `NOT_CONFIGURED_BY_POLICY`, not a release blocker;
- provider verification cannot grant runtime enforcement, remediation, merge, release or publication authority.

Until trusted-main provider execution succeeds, `live_provider_session_verified` and `provider_model_execution_verified` remain false.

<!-- AIPS_PROVIDER_CREDENTIAL_POLICY_V1 -->
## Optional Provider Credential Policy

External provider credentials are optional capability inputs, not AIPS platform prerequisites.

- default: credential-dependent provider features are disabled;
- activation: only when the exact expected credential is explicitly configured;
- missing credential: emit `SKIPPED_NOT_CONFIGURED` / `NOT_CONFIGURED_BY_POLICY`, never infer PASS;
- release semantics: absence of an optional provider credential is non-blocking;
- fallback: prefer deterministic/provider-neutral evidence paths already available;
- alternate authentication: do not introduce OAuth, Vertex AI, OIDC/WIF, or another login flow unless a later Human Decision explicitly authorizes it.

Gemini runtime verification and observable-event capture remain independent of live provider/model verification.

## External Credential Dependency Guard

External Agent/provider credential references are now centrally inventoried by `config/external-credentials.yaml` and audited by `scripts/external_credential_guard.py`.

Evolution Radar remains provider-neutral when no external semantic credential is configured. The deterministic research/evidence package and handoff continue without a provider key; missing optional credentials cannot become baseline/release blockers.

The guard also prevents new credential consumers from bypassing review or exposing secrets to pull-request code.

## Deterministic local pre-analysis

After raw weekly/monthly evidence is validated, AIPS runs a credential-free deterministic pre-analysis before any optional semantic provider.

The pre-analysis may only use already-collected signal title/metadata, source-controlled local rules, recurrence metadata and the current Capability Map. It performs no additional external network request.

Allowed output:

- deterministic category hints;
- existing-capability hints;
- bounded title-token near-duplicate clusters;
- HIGH / MEDIUM / LOW Human review priority.

Forbidden interpretation:

- review priority is not suitability;
- no COVERED / HOLD / ASSESS / TRIAL / ADOPT state may be inferred;
- semantic recommendation state remains `ANALYSIS_PENDING`;
- no Human Decision or implementation/publication authority is created.

The artifact is content-deterministic and bound to the exact evidence digest, repository revision, local-preanalysis configuration digest and Capability Map digest. Semantic analysis remains a separate optional layer.

## Capability Map repository-health reconciliation

The Evolution Capability Map includes integration-gate and repository-health-architecture-drift. Repository Health verifies source-controlled architecture consistency but does not mutate Radar semantic state, recommendation state, Human decisions or implementation authority.

## Quarterly Deterministic Review

Quarterly Review reuses durable monthly Radar evidence and does not perform a second external source collection. On the first day of January, April, July and October, the scheduled workflow reviews the previous calendar quarter.

The deterministic rollup binds the quarter and its three calendar months, aggregates recurrence by signal fingerprint, records the number of valid monthly evidence bundles and emits a new Human-review Issue. Monthly semantic recommendation states are not promoted: quarterly recommendations return to `ANALYSIS_PENDING` until a validated semantic result is separately bound.

This lane requires no external Agent/provider credential, introduces no additional source-network collection, and grants no code-change, implementation-PR, merge, release or publication authority.



## Technology Intelligence Expansion

Weekly discovery uses two source roles: `community` for technical-community discovery evidence and `primary` for direct vendor/project evidence. Deduplication MUST preserve `source_ids`, `source_roles` and verification status. A signal is `DISCOVERY_ONLY` when only community evidence exists, `PRIMARY_SOURCE` when primary evidence exists alone, and `PRIMARY_CORROBORATED` when both roles support the exact fingerprint.

The research funnel is deterministic and bounded:

~~~text
per-source candidates <= 8
→ round-robin global raw signals <= 50
→ deterministic Human shortlist <= 12
→ near-duplicate-aware semantic queue <= 10
→ actionable semantic recommendations <= 5
~~~

Signals outside the semantic queue remain `ANALYSIS_PENDING`. Partial semantic analysis is explicitly reported as PARTIAL coverage and is applied only to the selected fingerprints. A semantic provider MUST NOT produce `ADOPT` for a signal whose explicit provenance contains `community` but no `primary` role. Forum/community popularity is discovery evidence, never sufficient adoption evidence.

Source failures are durable evidence. Falling below the healthy community floor produces `DEGRADED` coverage but MUST NOT fabricate missing signals or silently substitute unconfigured sources.


## Evidence quality and primary-source corroboration

Technology Intelligence source provenance is normalized into deterministic evidence-quality metadata before semantic reasoning:

~~~text
level 0 = one community source only
level 1 = multiple community sources, no primary source
level 2 = at least one primary source
level 3 = primary + community corroboration
level 4 = multiple independent primary sources
~~~

The minimum deterministic evidence level for advisory `ADOPT` is 2. The semantic provider cannot create, upgrade or rewrite the evidence level; it may only reason over the bound evidence package. Pre-analysis may use a bounded evidence-quality bonus for Human review ordering, but evidence strength itself is not a semantic suitability decision.

Monthly and quarterly rollups MUST preserve source counts, exact provenance and evidence level. No evidence-quality state grants Human Decision, implementation, Trial execution, PR, merge, release or publication authority.


## Provider-neutral Controlled Trial handoff

Controlled Trial provider selection is now `auto / openai-codex-action / handoff`. The Human TRIAL Decision and exact Trial Plan remain provider-independent.

When `auto` cannot resolve the optional OpenAI credential, AIPS emits `TRIAL_HANDOFF_READY` rather than treating credential absence as Trial failure. The handoff binds the exact repository baseline, decision/trial fingerprints, approved scope and paths, forbidden paths, file/diff limits, required worktree isolation and deterministic repository validation command.

A compatible external Agent may execute the bounded contract, but `external_executor_may_claim_pass=false`. Provider output alone is not Trial PASS evidence. PASS/FAIL remains valid only after AIPS deterministic scope, diff, commit-boundary and repository-validation checks. Handoff grants no code publication, PR, merge, release or Human-adoption authority.


## Evolution Effectiveness feedback

The monthly effectiveness layer measures the observed value of the Technology Intelligence funnel without becoming a self-modifying source policy.

It reads durable weekly Radar evidence plus embedded/pre-existing deterministic pre-analysis, semantic analysis, Human Decision, Trial handoff/result and Trial→ADOPT artifacts. The report is bound to the exact cohort month, repository revision, Issue manifest and deterministic input digest.

Per-source evidence includes collected, shortlisted, semantic-selected, actionable, Trial-decision, PASS-Trial, adoption and failure counts plus deterministic basis-point ratios. Review flags are emitted only after configured minimum observations.

The following MUST remain false:

- automatic source weight changes;
- automatic source enable/disable;
- automatic source/config mutation;
- code-change / PR / merge / release authority.

Effectiveness flags inform Human source-policy review only. They do not change `config/evolution-sources.yaml`, do not create implementation branches, and do not alter Protected Human Authority.


## Historical Radar Issue reconciliation

A stale historical Radar Issue may be closed only after a durable reconciliation binds material candidates to current truth: terminal COVERED/HOLD outcomes, bounded ADOPT evidence, or explicit DEFERRED state.

Issue #79 is reconciled in `references/evolution/ISSUE_79_LIFECYCLE_RECONCILIATION.yaml`. Its semantic-intent candidate remains DEFERRED with no Trial authority. Future positive progression MUST start from fresh current-main evidence and a new explicit Human Decision; a closed stale Issue cannot provide positive-progression authority.
