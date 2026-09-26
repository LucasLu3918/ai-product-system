# Agent Eval Conformance

External producers and Human-confirmed finding promotion are defined by [Eval / Red-Team Interoperability](EVAL_INTEROPERABILITY.md). Imported runs stay advisory; only current canonical Case/Result evidence is eligible for deterministic regression scoring.

## Purpose

Provide truthful, provider-neutral evidence for Acceptance Scenarios whose contract depends on Agent semantic decisions rather than deterministic repository/runtime mechanics.

Agent Eval does not inspect or score private chain-of-thought. It scores only observable structured outputs.

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

Do not persist:

- chain-of-thought;
- private reasoning traces;
- scratchpads;
- prompts containing live secrets;
- credentials or secret-like response values.

Recorded results may include concise decisions, actions, selected roles/skills, artifact names and short user-visible summaries.

## Coverage admission

A Scenario may be classified `agent_eval` only when:

1. the Scenario is current with canonical system behavior;
2. a concrete case materially exercises it;
3. an actual observable Agent result is recorded;
4. the result is fingerprint-bound to that case;
5. deterministic scoring passes;
6. repository validation executes the Agent Eval check.

A case file without a result is not automated evidence.

## Commands

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
