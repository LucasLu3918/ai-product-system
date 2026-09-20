# Agent Observable-Event Capture Design

Status: **ADOPTED DIRECTION — GEMINI CLI FILE-TOOL RUNTIME CAPTURE VERIFIED**

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
critical_path: false  # authorization/result-enforcement semantics only
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

The preferred capture lane remains outside authorization/result enforcement. Runtime lifecycle APIs may still be synchronous from a latency perspective; an implementation MUST state this explicitly instead of using `critical_path=false` to imply asynchronous execution.

A future implementation must use bounded buffering and must surface degraded observability truthfully when events cannot be captured or processed. Capture/evaluator failure must not rewrite the observed tool result and must not silently claim complete evidence.

Durable event retention, cross-runtime correlation and queue recovery are separate future decisions.

## Runtime support truth

Gemini CLI v0.60.0 is now marked live-capture verified only for the exact read_file/write_file/replace local runtime/tool/hook scope proven by Scenario 143. Other runtimes and provider-backed model execution remain unverified.

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

## First runtime-specific implementation Trial — Gemini CLI

Scenario 142 selects Gemini CLI as the first implementation target.

The extension now contains a native `AfterTool` hook wired only to:

- `read_file`;
- `write_file`;
- `replace`.

The limited matcher is deliberate. These file tools allow the v1 event contract to state `network_used=false` without parsing tool arguments or inferring shell/network behavior.

### Opt-in activation

Capture remains disabled by default. A bounded verification run must explicitly provide both:

~~~bash
AIPS_OBSERVABLE_EVENT_CAPTURE=1
AIPS_OBSERVABLE_EVENT_CAPTURE_SINK=/tmp/aips-gemini-events.jsonl
~~~

The sink must be absolute and stay below the system temporary directory. The file is size-bounded and created with owner-only permissions.

### Projection boundary

Gemini CLI AfterTool input may include `tool_input` and `tool_response`. The capture implementation deliberately does not serialize either object. It derives only:

- deterministic event id from session/timestamp/tool identity;
- observed timestamp;
- runtime / adapter ids;
- fixed subject;
- resource id + operation from the allowlisted tool map;
- SUCCESS / FAILED from presence of `tool_response.error`;
- `network_used=false` for the bounded file-tool scope.

This structural projection prevents raw tool arguments, response text, private reasoning and secret-like values from entering the event sink.

### Failure semantics

Capture is non-enforcing but **synchronous**. Gemini CLI waits for AfterTool hooks to finish. The hook always returns `decision=allow`, so missing sink, malformed metadata, unsupported tool or full bounded sink degrades evidence only and must not deny or rewrite the original tool result. The disabled shell path returns allow without starting Python; enabled-hook overhead is bounded and measured in CI. For this Trial, `critical_path=false` refers only to authorization/result-enforcement semantics, while `synchronous_hook=true` and `latency_path=synchronous` state the latency truth.

### Verification truth

Source-controlled CI verifies the official AfterTool-shaped contract and extension wiring, but does not run a real Gemini CLI binary. Therefore this Trial keeps:

~~~yaml
live_runtime_execution_verified: false
live_capture_verified: false
~~~

Scenario 143 completes that gate with the installed Gemini CLI v0.60.0 binary and official `--fake-responses` interface. The real CLI, extension loader, file-tool executor and AfterTool hook are exercised on the exact candidate.

This permits `live_runtime_execution_verified=true` and `live_capture_verified=true` for that narrow scope only. It does not verify a live provider/model API call: provider/model execution evidence remains false and separately scoped.

