# Scenario 229 — Agent Eval Freshness Selection

## Request

Change one behavior dependency and identify only the Agent Eval cases that need fresh evidence.

## Expected

- A source-controlled dependency map links behavior IDs and path patterns to stable Agent Eval case IDs.
- The deterministic report selects only cases whose dependency patterns match changed paths, lists stale reasons, and does not copy prompts or results into the report.
- Missing or stale result fingerprints are visible; this report does not execute cases or rewrite case/result files.
- Scenarios 192, 193 and 224 remain manual until provider-neutral runtime behavior can be attested.

## Evidence

`tests/evidence/agent_eval_freshness_lifecycle.py` verifies exact selection, no-op selection, unsafe path rejection and manual-scenario preservation.
