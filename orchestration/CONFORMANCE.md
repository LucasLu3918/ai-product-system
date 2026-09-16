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
