# Agent Eval Conformance

## Change-aware freshness selection

`config/eval-freshness.yaml` links behavior IDs and affected source-path patterns to stable Eval case IDs. Run `python scripts/agent_eval_freshness.py report --base origin/main` to produce a deterministic, privacy-safe list of cases that need fresh evidence after a change. The report flags missing or stale results but does not execute evaluations or modify cases/results. It does not copy prompts into the report. Scenarios 192, 193 and 224 remain manual until provider-neutral runtime behavior is attested.

Scenario 198 is deterministic lifecycle evidence for runtime resolution and invariant coverage; it does not represent model behavior or grant publication authority.

External producers and Human-confirmed finding promotion are defined by [Eval / Red-Team Interoperability](EVAL_INTEROPERABILITY.md). Imported runs stay advisory; only current canonical Case/Result evidence is eligible for deterministic regression scoring.

Scenario 181 covers trace projection/export independently from Agent Eval. Telemetry spans and token counts are not evaluation scores or regression decisions.

## Purpose

Provide truthful, provider-neutral evidence for Acceptance Scenarios whose contract depends on Agent semantic decisions rather than deterministic repository/runtime mechanics.

Agent Eval does not inspect or score private chain-of-thought. It scores only observable structured outputs.

Scenario 193 Implementation Profile checks are deterministic contract/lifecycle evidence, not Agent Eval scores; semantic resolution quality remains a Human-reviewed question.

Scenario 195 adds exact-candidate deterministic checks for ownership, language, generated hashes and required verification evidence. Its report cannot score semantic technology choice or establish that project test assertions are adequate; those judgments remain in the applicable review path.

## Separation of responsibilities

~~~text
Eval Case
→ Agent execution (any provider/runtime)
→ Observable structured response
→ Recorded Result bound to Case fingerprint
→ Deterministic scorer
→ PASS / FAIL evidence
~~~

The Agent execution and deterministic scorer are separate.

AIPS core does not require a provider SDK and does not claim that CI generated a model response. CI only validates and scores already recorded observable results.

## Case

Case files live under:

~~~text
tests/agent_eval/cases/
~~~

A case contains:

- stable case id + Scenario id;
- the prompt and minimal context needed to exercise the behavior;
- deterministic rubric over observable response fields.

Supported rubric operations:

- `equals`;
- `contains`;
- `excludes`;
- `set_equals`;
- `nonempty`.

Do not encode hidden reasoning expectations in the rubric.

## Result

Validation Shadow graduation metrics remain separate operational evidence: validator-level precision and recall use observed full-run failures, and rates with empty denominators remain null. These metrics do not become Agent Eval outcomes or authorize selective execution.

OpenCode native acceptance is runtime integration evidence, not an Agent task-outcome or production-model quality measure. Preserve its exact-host binding and report arbitrary Shell, MCP/custom-tool and out-of-process effects as unsupported.

Optionally record execution.task_observation with source observed_host, task_completed, human_corrections and false_positives. Summarize only case-bound CURRENT results; absence is UNKNOWN. Recorded outcomes remain self-reported host evidence with UNVERIFIED runtime attestation, separate from deterministic rubric PASS.

Recorded results live under:

~~~text
tests/agent_eval/results/
~~~

Each result contains:

- case_id;
- scenario_id;
- exact case SHA-256 fingerprint;
- provider/model/runtime/execution timestamp metadata;
- observable structured response only.

The provider/model/runtime values are evidence metadata, not routing constraints.

## Freshness

New Cases may declare `system_dependencies` as repository-relative canonical source paths. A Result recorded by an actual Agent run may bind `execution.system_fingerprint` to those exact bytes. The scorer reports `CURRENT`, `STALE`, or `UNBOUND` separately from rubric PASS/FAIL; a mismatched bound result fails. Existing results without such a binding remain historical `UNBOUND` evidence and are never silently relabeled current.

Any material Case change changes its fingerprint.

~~~text
Case changes
→ old Result fingerprint mismatch
→ FAIL / stale
→ rerun Agent
→ record new observable Result
→ deterministic score
~~~

Never update only the fingerprint to make a stale result pass. The Agent response must be rerun against the changed Case.

## Privacy / safety

The OpenAPI generator adapter lifecycle is execution/ownership evidence only, not an Agent Eval result. It persists no raw generator stream; semantic client quality remains subject to project tests and review.

Scenario 197's local Widgets service/client run is lifecycle evidence for a shared reference project. It does not score an Agent decision or establish semantic acceptance for another product; keep its `lifecycle` coverage separate from `agent_eval` results.

Implementation-resolution contract evidence is not Agent Eval evidence. OpenAPI lifecycle tests establish deterministic validator behavior; they do not score semantic recommendation quality or authorize an Agent decision.

Do not persist:

- chain-of-thought;
- private reasoning traces;
- scratchpads;
- prompts containing live secrets;
- credentials or secret-like response values.

Recorded results may include concise decisions, actions, selected roles/skills, artifact names and short user-visible summaries.

## Coverage admission

涵蓋 Scheduler owner lifecycle 的 Eval Scenario 應以實際 Task Graph、active isolation、lease expiry/recovery 與 diff reconciliation 作為 deterministic evidence；不可把 `ADVISORY` authorization 當成 runtime write enforcement。

A Scenario may be classified `agent_eval` only when:

1. the Scenario is current with canonical system behavior;
2. a concrete case materially exercises it;
3. an actual observable Agent result is recorded;
4. the result is fingerprint-bound to that case;
5. deterministic scoring passes;
6. repository validation executes the Agent Eval check.

A case file without a result is not automated evidence.

Scenario 192 (complete Planning Package to implementation readiness) remains `manual` because its product decisions and Gate approvals require a real Human; its structural subcontracts are covered by deterministic and lifecycle tests. Do not create an Agent Eval result from a template or infer approval from a validator PASS.

## Commands

The `aips eval` public commands are dispatched through the stable `bin/aips` and `scripts/aips_cli.sh` entrypoints; internal shell modules remain an implementation detail and do not change the Eval evidence contracts.

~~~bash
aips conformance agent-eval check
aips conformance agent-eval report

python scripts/agent_eval.py fingerprint --case tests/agent_eval/cases/<case>.yaml
python scripts/agent_eval.py score --case <case> --result <result>
~~~

`check` fails for stale, missing, orphan or rubric-failing results. `report` is inspectable reporting and does not turn failed evidence into PASS.

## Repeatability / Consistency Evidence

A single passing Agent Eval run proves one observed execution, not behavioral repeatability. For reliability-sensitive behavior, record multiple independent results for the exact same Case fingerprint and evaluate them with:

~~~bash
aips conformance agent-eval consistency \
  --case tests/agent_eval/cases/<case>.yaml \
  --results-dir <directory-of-independent-results> \
  --min-repetitions 5 \
  --min-pass-rate 1.0
~~~

The consistency report deterministically validates every Result against the exact Case, scores each observable response with the existing rubric, and reports repetition/valid/invalid counts, rubric PASS rate, outcome consistency, unique observable-response fingerprints, and exact response repeatability.

Exact wording does not need to be identical when every response still satisfies the rubric. Response fingerprints make variability visible without copying response text into the aggregate report. Stale fingerprints, private-reasoning fields or secret-like values are invalid evidence and fail the consistency report regardless of the configured pass-rate threshold.

Consistency evidence is measurement, not runtime authority. It does not choose a provider, expose chain-of-thought, authorize tool calls, or replace Human review.

`tests/validation/registry.py` registers `validation.eval_interop_contracts` in repository validation and preserves its existing error-aggregation position. Eval lifecycle evidence remains separately listed and runs once under `tests/validate_repository.py`.

## Real-Task Outcome Evaluation

This protocol compares actual Agent-assisted task runs across a fixed cohort while reusing Agent Eval, Trajectory Eval, and telemetry. It keeps deterministic rubric results, observed task outcomes, trajectory security findings, and telemetry measurements separate.

The protocol is implemented, but the empirical benchmark is **NOT_READY** until a Human selects a fixed real-task cohort and both baseline and candidate runs have comparable, valid observations. Existing regression cases and recorded fixtures are not real-task runs. An absent observation is `UNKNOWN`, never zero or a pass.

### Fixed cohort and comparability

Before collecting a comparison, record a Human-reviewed suite manifest with a stable benchmark ID and ordered task IDs; each task's case ID, Scenario ID, and exact case fingerprint; baseline and candidate repository revisions; the same measurement definitions and execution procedure; and required evidence for each task (a case-bound Agent Eval result and, for security measurement, a run-bound Trajectory Eval result).

Use the same task IDs, case fingerprints, rubric, execution procedure, and eligible task classes on both sides. Provider, model, runtime, run time, and system fingerprint are evidence metadata. A changed case fingerprint, missing result, stale or unbound system evidence, invalid result, or incompatible execution metadata is an explicit comparability failure. Do not silently drop a task to improve a rate.

The suite manifest identifies the cohort; it does not assert that any task has run or passed. Select real tasks from approved, privacy-safe work. Do not copy live prompts or task content into benchmark summaries.

### Measures

Report each measure independently, for baseline and candidate, with numerator, denominator, rate, and evidence status:

- **Task completion:** count `execution.task_observation.task_completed` only when its source is `observed_host`, the result matches the exact case fingerprint, and it is current for its declared system dependencies. A deterministic rubric PASS remains separate.
- **Rework:** report observed `human_corrections` and `false_positives` as separate counts and per-task rates. Missing fields make that measure `UNKNOWN`; they do not mean zero.
- **Security:** report Trajectory Eval `BLOCK` outcomes and hard security/governance findings by task. Missing, invalid, or unbound trajectory evidence is `UNKNOWN`, not a clean result. The evaluator remains in shadow mode and grants no publish authority.
- **Observed cost and duration:** report only token counts and elapsed spans directly observed by an existing adapter or telemetry record. Unknown usage or price stays unknown; do not infer provider cost from model names or missing telemetry.

Keep rubric status, task completion, rework, security, and cost in separate columns. Do not combine them into one quality score.

### Failure retention and readiness

Include every selected task in the report. Retain failed, blocked, invalid, stale, unbound, missing, and incomplete runs with their status and a safe failure category. Do not overwrite a failed run or replace it with a later pass; record a later attempt as another run linked to the same task. Aggregate rates must state the denominator and silently exclude no task.

The comparison is `READY` only when both baseline and candidate have valid observations for every task in the fixed cohort and satisfy the comparability rules. Otherwise report `NOT_READY`, enumerate missing or invalid evidence by task ID, and leave affected rates `UNKNOWN`. Readiness is an evidence state only; it does not authorize execution, policy changes, or publication.

### Privacy and existing tools

Use `aips conformance agent-eval report --format yaml` for current case/result and observed-outcome status, and `aips trajectory evaluate --trace <trace.yaml> --mode shadow --format json` for per-run trajectory evidence. These outputs are not a cross-revision benchmark by themselves; retain a reviewed suite manifest and compare the same cohort under this protocol.

Aggregate reports may contain benchmark/task IDs, case fingerprints, revisions, bounded counts/rates, evaluator status, and safe failure categories. Do not persist prompts, model responses, tool arguments, private reasoning, credentials, or raw traces in an aggregate. Telemetry projection remains allowlisted and is not an Agent Eval score or task-completion signal.

### Current Plan29 #13 evidence

The repository has the measurement components and explicit outcome fields, but its current recorded Agent Eval results contain no `observed_host` task observations. There is no selected real-task cohort or comparable baseline/candidate sample. Therefore no success, rework, or security benchmark rate is claimed, and empirical acceptance remains `NOT_READY` pending real runs.
