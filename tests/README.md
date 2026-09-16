# Scenario Acceptance Tests

These are behavioral regression tests for the operating system, not application unit tests.

For each scenario verify:

- selected work mode is minimal and correct;
- unrelated roles/skills are not loaded;
- required preflight stop occurs only when material;
- existing-project instruction precedence is respected;
- artifacts/review/state requirements are applied;
- the system does not invent missing facts or claim unmeasured results.

A change to routing/governance should be checked against all scenarios before release.

## Conformance Registry

Scenario Markdown files define expected behavior. Their existence alone is not test evidence.

`tests/scenario_coverage.yaml` records whether each Scenario is deterministic, lifecycle, agent-eval, manual or uncovered and points to its evidence. Run:

~~~bash
aips conformance check
aips conformance report
~~~

Do not mark a Scenario automated unless its evidence materially exercises that Scenario.

### Agent Eval

Semantic Scenarios use:

~~~text
tests/agent_eval/cases/
tests/agent_eval/results/
scripts/agent_eval.py
~~~

A committed Case alone is not evidence. A Result must come from an actual Agent execution, bind to the exact Case fingerprint, contain observable output only, and PASS deterministic scoring.

~~~bash
aips conformance agent-eval check
aips conformance agent-eval report
~~~

Private chain-of-thought, scratchpads and live secrets must never be stored in Agent Eval results.

## Direct Evidence

`tests/evidence/` contains focused executable evidence for Scenario contracts that would otherwise be hidden inside broad repository validation.

Promotion rule:

~~~text
current canonical behavior
→ reconcile Scenario if stale
→ direct executable evidence
→ registry reclassification
→ repository validator executes the evidence
~~~

Do not create an evidence file merely to raise the automated percentage. It must materially exercise the Scenario it claims to support.

## Validation Modules

The stable entrypoint remains:

~~~bash
python tests/validate_repository.py
~~~

The entrypoint is intentionally a small aggregator. Validation logic is grouped under `tests/validation/` by subsystem, while focused Scenario evidence remains under `tests/evidence/`.

Do not make callers depend on individual validation modules; CI and users should continue to invoke the stable top-level entrypoint.
