# Agent Observable-Event Capture Design

Status: **ADOPTED DIRECTION — NOT A LIVE RUNTIME CAPABILITY**

This document is the System Improvement Review design handoff for the Issue #79 Agent anomaly candidate after Scenario 140 PASS. It defines the smallest future implementation shape. It does not enable a runtime hook.

## Design objective

Provide provider-neutral, opt-in observable execution metadata to the existing out-of-band anomaly evaluator without changing authorization outcomes, blocking normal tool execution, collecting private reasoning, or granting remediation authority.

## Reuse-first architecture

~~~text
Runtime-native tool execution
→ optional adapter POST_EXECUTION exporter
→ strict sanitizer / whitelist mapper
→ canonical agent-observable-event
→ bounded out-of-band buffer
→ existing deterministic anomaly evaluator
→ evidence-only report
→ Human review
~~~

The design extends the existing Harness adapter layer. It does not introduce a new Role, Skill, authorization system, semantic intent engine, or provider dependency.

## Source contract

A future runtime adapter may declare an observable-event export capability only after runtime-specific evidence verifies that the hook is real and correctly placed after execution.

The exporter may supply only the fields already allowed by `orchestration/schemas/agent-observable-event.yaml`:

- event id and observed timestamp;
- runtime and adapter identity;
- subject;
- resource id;
- operation;
- observed outcome;
- network-used boolean;
- optional Change Boundary.

Prompt text, model response text, tool arguments, private reasoning, chain-of-thought, credential values, environment-secret values and unmapped raw payload are outside the contract.

## Default and authority

Future configuration MUST default to disabled.

~~~yaml
enabled: false
mode: POST_EXECUTION_EVIDENCE
runtime_enforced: false
critical_path: false
automatic_remediation: false
~~~

Anomaly evidence may inform Human review. It MUST NOT turn a deterministic Resource Authorization DENY into ALLOW, grant a protected operation, approve publication, or take remediation action by itself.

## Sanitization

The adapter-specific raw event is transient input. Before a canonical event exists:

1. reject private-reasoning fields;
2. reject secret-like values;
3. reject unmapped fields;
4. validate bounded string lengths and canonical outcomes;
5. normalize only whitelisted fields;
6. fingerprint the normalized event.

Raw payload persistence is not part of the adopted design.

## Failure and backpressure semantics

The capture lane remains outside the critical execution path.

A future implementation must use bounded buffering and must surface degraded observability truthfully when events cannot be captured or processed. Capture/evaluator failure must not rewrite the observed tool result and must not silently claim complete evidence.

Durable event retention, cross-runtime correlation and queue recovery are separate future decisions.

## Runtime support truth

No current adapter is marked live-capture verified by this release.

A future adapter implementation must demonstrate:

- verified runtime-native post-execution hook semantics;
- canonical mapping conformance;
- zero private-reasoning/secret leakage in the bounded test corpus;
- bounded overhead measurements;
- explicit event-loss/degradation evidence;
- Resource Authorization monotonicity;
- scenario and integration evidence on an exact candidate.

Only then may `live_capture_verified` become true for that specific runtime integration.

## Future implementation gate

The next engineering step is intentionally deferred. A later Human-approved change must select one concrete runtime adapter and run a bounded live-capture implementation Trial.

That later scope must not include semantic intent governance or automatic remediation unless separately approved.

## Architecture diagram impact

Current-state architecture diagrams are intentionally unchanged because this release does not add a live runtime path. This document is the future-state design diagram until a verified runtime implementation exists.
