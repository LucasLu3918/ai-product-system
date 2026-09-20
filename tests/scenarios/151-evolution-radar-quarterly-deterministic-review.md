# Scenario 151 — Evolution Radar Quarterly Deterministic Review

## Intent

AIPS MUST be able to build a quarterly Human-review evidence bundle without requiring an external Agent/provider credential or repeating source retrieval.

## Expected behavior

- The quarterly review consumes only valid durable monthly Evolution Radar evidence whose bound month belongs to the requested calendar quarter.
- The review records the exact quarter, the three expected calendar months and the number of monthly evidence bundles consumed.
- Recurrence is accumulated deterministically by signal fingerprint.
- Quarterly recommendations are reset to `ANALYSIS_PENDING`; monthly semantic states are not promoted into a new quarterly suitability conclusion.
- The quarterly lane does not perform an additional external source collection or require `OPENAI_API_KEY`, `GEMINI_API_KEY` or another provider credential.
- Invalid quarter formats fail closed.
- Output authority remains evidence/Human-review only: code change, branch/PR, merge and release authorization stay false.
