# Scenario 125 — Agent Eval Conformance Lifecycle

Expected:
- Agent Eval check discovers cases/results, scores each pair and reports summary counts;
- all committed agent_eval evidence must PASS before repository validation passes;
- stale, missing, orphan or rubric-failing evidence blocks check;
- report mode remains inspectable without turning a failing eval into valid evidence.
