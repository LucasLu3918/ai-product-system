# Scenario 181 — OpenTelemetry Telemetry Projection & Export

## Goal

Export privacy-safe, replayable traces for one AIPS run while preserving canonical run evidence and Human/Gate authority.

## Given

- A run with `CHECKPOINT.yaml` and append-only `EVENTS.jsonl`;
- optional complete lifecycle markers for phases, Gates, model calls, and tools;
- export disabled unless a caller supplies an enabled config.

## When

- the operator records approved lifecycle metadata and runs offline export or explicit OTLP replay;
- records are malformed, incomplete, or an OTLP endpoint fails.

## Then

- complete marker pairs yield deterministically identified spans with observed timestamps only;
- Gate waiting/resumed yields a separate duration span;
- independent review may link to implementation while inheriting no runtime context;
- exact pinned GenAI attributes are emitted only for recorded provider/model/token values;
- prompts, outputs, tool arguments, reasoning, credentials, and unknown fields never appear in the exported payload;
- default configuration sends nothing; only HTTPS or loopback endpoints are accepted;
- network failure reports `TELEMETRY_DEGRADED` without changing run/Gate/tool outcomes;
- replay does not modify canonical events and produces stable IDs.

## Evidence

`tests/evidence/telemetry_export_lifecycle.py` exercises actual CLI recording, projection, replay, local OTLP receiver delivery, privacy rejection, endpoint policy, and transport failure. `tests/validation/telemetry_export_contracts.py` verifies the exact schema snapshot, command routing, docs and scenario registration.
