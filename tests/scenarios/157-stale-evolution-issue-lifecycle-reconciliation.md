# Scenario 157 — Stale Evolution Issue Lifecycle Reconciliation

## Intent

A completed historical Evolution Radar Issue MUST NOT remain an ambiguous active queue item after its material candidates have durable outcomes or explicit deferral and its original baseline is stale.

## Expected behavior

- bind reconciliation to Issue #79 and the current released baseline;
- mark the original Radar revision as STALE for positive progression;
- preserve durable COVERED outcomes for Agent Eval repeatability and Resource Authorization;
- preserve the bounded Human ADOPT path and real-runtime verification for out-of-band anomaly evidence without inventing provider/model verification;
- keep `live_provider_session_verified=false` and `provider_model_execution_verified=false`;
- explicitly defer semantic-intent governance with no Trial/adoption authority;
- require fresh current-main evidence plus a new explicit Human Decision for any future semantic-intent progression;
- mark the historical Issue ready to close as completed;
- grant no code mutation, runtime enforcement, automatic remediation, merge, or release authority from reconciliation itself.

## Rationale

Closing stale research Issues after durable reconciliation keeps the active work queue truthful without erasing historical evidence or silently converting deferred ideas into decisions.
