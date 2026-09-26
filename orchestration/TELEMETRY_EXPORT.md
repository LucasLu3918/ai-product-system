# OpenTelemetry Telemetry Projection & Export

## Authority and data flow

```text
CHECKPOINT.yaml + append-only EVENTS.jsonl
        ↓
validated AIPS telemetry projection
        ↓
privacy allowlist → versioned OpenTelemetry mapping
        ↓
optional host-side OTLP/HTTP JSON exporter
        ↓
any compatible observability backend
```

`CHECKPOINT.yaml` and `EVENTS.jsonl` remain the durable run evidence. The OTLP payload is a replaceable projection. Exporting, replaying, or losing telemetry never changes an AIPS run, Gate, approval, tool result, or publication decision.

## Recorded fields

Use `aips telemetry record` to add lifecycle markers to the existing event stream. Only bounded identifiers and allowlisted metadata are accepted. Supported kinds are phase, gate, model, and tool. A started/completed pair produces a duration span. A gate waiting/resumed pair produces a separate wait span; report each wait segment with a distinct operation ID.

For independent review, use a separate review operation and set `--related-operation-id` to the implementation operation. The exporter uses a SpanLink and common AIPS run correlation. It never forwards trace context into a reviewer runtime. Runtime metadata is evidence only: a provider, model, or token count may be recorded only when the adapter genuinely observed it.

Missing start/end markers, invalid timestamps, unpaired events, malformed records, or unavailable usage data are surfaced as `DEGRADED`; the exporter does not invent duration or token counts. The synthetic `aips.run` span covers only the observed lifecycle interval and is labeled `observed_lifecycle_only`.

## Privacy

The projection allows only operation IDs, fixed operation names, provider/model identifiers, input/output token counts, outcome, and lifecycle correlation IDs. It rejects unknown telemetry fields. Prompt text, model output, tool arguments, private reasoning, credentials, and arbitrary runtime payload are never copied to the OTLP payload. Existing event artifacts/evidence are not exported.

GenAI attributes follow the pinned OpenTelemetry GenAI snapshot recorded in `orchestration/schemas/telemetry-export.yaml`. The schema is in development upstream; update the immutable revision only with a reviewed mapping and contract change. AIPS generic workflow and Gate spans use the `aips.*` namespace.

## Configuration and commands

The supplied `config/telemetry-export.yaml` is disabled. Copy it to a private local configuration and set `enabled: true` only for an approved export destination. Remote endpoints require HTTPS; HTTP is accepted only for loopback testing. The optional authorization value is read from the host environment variable named by `authorization_env` and is never stored in run state or printed.

```sh
aips telemetry record --project . --run-id RUN --kind phase --action started \
  --operation-id plan-1 --name planning
aips telemetry record --project . --run-id RUN --kind phase --action completed \
  --operation-id plan-1 --name planning
aips telemetry export --project . --run-id RUN --output /tmp/run-trace.json
aips telemetry replay --project . --run-id RUN --config ./telemetry-export.yaml --send
```

Offline `--output` creates a new file with owner-only permissions and refuses to overwrite. Transmission is permitted only when the CLI flag is present and `enabled: true` in the supplied config. Endpoint, timeout, and payload bounds are validated before the request. Replaying emits deterministic trace/span IDs; whether a backend deduplicates repeated submissions is backend-specific.

## Runtime integrations and cost

The initial capability defines a provider-neutral recording contract. No AIPS runtime is marked as automatically capturing live LLM calls, retrieval, embeddings, or tool arguments. Adapters may record only fields they can verify at the actual operation boundary; absent evidence stays absent. The projection reports token counts but does not calculate cost. Metrics, cost calculation, vendor SDKs, and content capture are outside this capability.

## Failure semantics

Network, timeout, server, or malformed-config failures return sanitized `TELEMETRY_DEGRADED` evidence and do not echo response bodies, endpoint credentials, or raw exceptions. `aips telemetry export --send` exits successfully on a transport/export failure so it cannot become an execution gate; configuration or local projection errors remain command errors. Dedicated exporter tests still fail when a local receiver does not accept the expected payload.
