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
