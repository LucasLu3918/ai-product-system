# Core Change Proposal: OpenTelemetry Telemetry Projection & Export

## Purpose

Add an opt-in, provider-neutral OTLP traces projection for AIPS durable run evidence, with replay, bounded lifecycle instrumentation, privacy-safe GenAI metadata, host-side credentials, and non-blocking exporter failures.

## Why this is a core/large change

This adds a CLI capability and changes how AIPS run event evidence can represent lifecycle and verified telemetry attributes. It crosses persistence, observability, privacy, credential, runtime-adapter and documentation boundaries.

## Proposed Scope

### In scope

- Keep CHECKPOINT.yaml and append-only EVENTS.jsonl authoritative.
- Add deterministic projection and replay export for one selected run.
- Add bounded, allowlisted lifecycle and model/tool usage event recording without prompt/output/argument capture.
- Emit OTLP/HTTP JSON traces with AIPS workflow spans and GenAI spans only when the recorded fields support them.
- Pin the GenAI mapping profile to an immutable upstream revision and test exact emitted attributes.
- Keep endpoint credentials host-side; fail closed on unsafe endpoint/configuration and report export degradation without changing the AIPS operation result.
- Preserve independent-review isolation; correlate by run identifier and SpanLink, never inherited runtime context.
- Add lifecycle, contract, privacy, CLI and Scenario Conformance evidence.
- Update human and agent docs, architecture diagrams, VERSION and CHANGELOG.

### Out of scope

- Replacing AIPS durable run state with OTel.
- Prompt, model response, tool argument, private reasoning or credential capture.
- AIPS cost calculation, broad metrics adoption, vendor-specific SDKs, new roles/skills/gates/state stores, historical migration, or claiming live runtime capture for adapters without exact runtime evidence.

## Expected Files / Modules

- `config/documentation-placement.yaml`, `config/telemetry-export.yaml`, `bin/aips`, `scripts/telemetry_record.py`, `scripts/telemetry_projection.py`, `scripts/telemetry_export.py`
- `orchestration/TELEMETRY_EXPORT.md`, `orchestration/AGENT_OBSERVABLE_EVENT_CAPTURE_DESIGN.md`, `orchestration/schemas/telemetry-export.yaml`, `orchestration/CONFORMANCE.md`, `orchestration/DOCUMENTATION_SYNC.md`, `orchestration/EVAL_INTEROPERABILITY.md`, `orchestration/AGENT_EVAL.md`
- `tests/evidence/telemetry_export_lifecycle.py`, `tests/validation/telemetry_export_contracts.py`, `tests/validation/conformance_isolation.py`, `tests/scenarios/181-opentelemetry-telemetry-export.md`, `tests/scenario_coverage.yaml`, `tests/validate_repository.py`
- `docs/ARCHITECTURE.md`, `docs/human/ARCHITECTURE_OVERVIEW.md`, `docs/human/TECHNOLOGY_GUIDE.md`, `docs/human/USER_GUIDE.md`, `docs/human/CONFORMANCE.md`, `docs/human/DOCUMENTATION_MAP.md`, `docs/human/DOCUMENTATION_SYNC.md`, `docs/human/SECURITY_ASSURANCE.md`, `docs/human/assets/system-overview.svg`, `VERSION`, `CHANGELOG.md`
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`, this proposal, and EPHEMERAL Change Impact evidence.

Mapping snapshot selected for the initial implementation: `open-telemetry/semantic-conventions-genai@0c87594975195608dc91b3f702e250a7b240c151`. It is an immutable tested snapshot, not a claim that this is the upstream repository's current HEAD. Update only through an explicit mapping review.

## Impact

### Architecture / Contracts

Add a projection/export lane after canonical run evidence. `EVENTS.jsonl` may carry only a validated, bounded telemetry attribute object for approved event kinds. OTel output is replaceable derived evidence.

### Data / Migration

Additive event fields only; old records remain valid. No run-state migration. Replay must preserve deterministic trace/span identifiers for the same run evidence.

### Security / Reliability

Default disabled; exact field allowlist; endpoint HTTPS except loopback; credential values resolved only from named host environment variables; bounded payload, timeout, and response handling; exporter failure never changes workflow/Gate outcomes. Independent review uses links/correlation only.

### Compatibility / Rollback

Existing AIPS runs and commands remain valid. Rollback is disabling/removing the optional exporter; canonical events remain readable. No dependency added to default install.

### Tests / Validation

Impact-derived matrix is in `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`. Required: deterministic projection/replay, valid OTLP receiver contract, lifecycle pairing and missing-data behavior, privacy/secret rejection, credential and endpoint negative paths, exporter failure semantics, CLI routing, scenario conformance, complete repository validation and secret scanning.

### Secret / Credential Impact

Secrets required: NO for local receiver validation; optional named environment variable for a configured remote OTLP endpoint.

Approved acquisition mechanism: caller-provided host environment only. No credential prompts or persistence.

Leakage/redaction review: test that auth values, prompts, responses, tool arguments and private reasoning never enter output/logs.

Rotation/revocation plan if exposure is found: revoke at backend, remove from host environment, rescan complete candidate history.

### Documentation / Diagrams

- `docs/ARCHITECTURE.md` Mermaid: AFFECTED — new canonical-evidence projection/export flow.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: AFFECTED — explain trust and failure boundaries.
- `docs/human/assets/system-overview.svg`: AFFECTED — show opt-in host-side projection/export lane.
- Other human SVG diagrams: N/A — run lifecycle/auth topology not otherwise changed.

## Risks

- Existing events lack complete lifecycle timestamps and input/output token splits; emit only what is recorded and expose incomplete coverage.
- The GenAI semantic conventions evolve quickly; the exact immutable source revision must be recorded and re-evaluated for future updates.
- Remote GitHub publication may be blocked if host authentication remains invalid.

## Recommendation

Implement as an additive projection/export capability. The user explicitly approved this complete boundary with “依照建議實作所有事項，本地驗證完後需完成遠端pr合至main”. No Constitution semantics change.

## Proposed Implementation Order

1. Finalize approved Change Impact and exact immutable mapping profile.
2. Implement event validation/recording and deterministic projection.
3. Implement opt-in host-side OTLP/HTTP JSON export and replay CLI.
4. Add lifecycle, privacy, security, failure, CLI and scenario evidence.
5. Update architecture, user/agent docs, diagram, version and changelog.
6. Complete impact reconciliation, the Core test matrix, repository validation and publication preflight.

## Approval

Status: APPROVED
Approved by: Human (current task instruction)
Approved at: 2026-09-26T15:10:33Z
Approval record: user message in Codex task “依照建議實作所有事項，本地驗證完後需完成遠端pr合至main”
Proposal fingerprint: sha256:c215e25d12eb297802d5623d05cc555068ca74093391b5c3bd772a9ed278098f
Scope fingerprint: sha256:86083031fc8c3168dde4b1af1dce7275fe16927fd43133800e6b048107b994c1
