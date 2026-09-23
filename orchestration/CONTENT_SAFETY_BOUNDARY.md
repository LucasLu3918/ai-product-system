# Runtime Content Safety Boundary

## Purpose

The AIPS Runtime Content Safety Boundary is the common, sink-aware safety layer for content that is about to cross a persistence or publication boundary. It complements Secret Handling, Governance Audit, Publish Approval, native runtime hooks and repository-side secret protection; it does not replace any of them.

The implementation is provider-neutral and does not require an external API credential. Deterministic detectors are authoritative for enforcement. Optional semantic detectors may provide advisory signals only.

## Contract

All AIPS-owned persistence paths should call:

```python
safe_emit(sink="governance_audit", payload=event, context=context)
```

The result contains `decision`, `safe_payload`, and redacted `findings`. A finding may contain only its type, detector, location, fingerprint, length, action and confidence. It must never contain the detected value.

Supported decisions are `ALLOW`, `REDACT`, `BLOCK` and `REVIEW`.

## Detection boundaries

- Secrets reuse the deterministic detectors from `scripts/check_secret_leakage.py`.
- PII starts with deterministic email, phone, checksum-valid card and Taiwan ID detection. It is sink- and context-aware; an email is not automatically a violation.
- External content carries provenance such as `trust: UNTRUSTED`. Prompt injection is reported as `INJECTION_SIGNAL`, not as a claim of confirmed compromise.
- A detector failure is fail-closed for commit, PR, release and high-assurance audit sinks, and degraded/drop behavior for low-risk diagnostic sinks.

## Sink policy

Diagnostic and ephemeral sinks redact sensitive values. Durable or public sinks block and require safe regeneration. `git commit` is content-sensitive but does not require Git Publish Approval. Publish authorization and content safety are separate decisions.

The canonical sink manifest is `config/content-safety.yaml`. Any new persistence or publication sink must be registered there and covered by the deterministic Integration Gate.

## Runtime truthfulness

`ENFORCED` applies to AIPS-owned sinks. A verified native hook may report `TOOL_GUARDED`. MCP-only or unsupported host tools remain `ADVISORY`; AIPS must not claim universal interception.

## Delivery stages

1. v0.58.0: kernel, reusable secret detector, deterministic PII baseline, policy engine and AIPS-owned sink integration.
2. v0.59.0: publication and runtime enforcement for commit, push, PR and release content, including indirect body/message files.
3. v0.60.0: provenance, untrusted-content separation, injection signals, tool-action correlation and quarantine.

## Security invariants

- No raw secret or private reasoning is emitted in findings, audit records or observable events.
- Sanitize precedes hash and persistence.
- Public or durable sink policy cannot silently redact a blocked secret.
- Human approval cannot be bypassed by an injection signal.
- Unsupported runtime capability is never upgraded to `TOOL_GUARDED`.
