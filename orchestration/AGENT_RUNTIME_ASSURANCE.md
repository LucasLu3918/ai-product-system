# Agent Runtime Assurance

## Purpose

Extend Resource Authorization and Agent Eval with provider-neutral evidence for two questions without creating a second runtime authority system:

1. Pre-execution intent evidence: does an independently assessed declared intent remain compatible with an operation that Resource Authorization already permits?
2. Post-execution anomaly evidence: did observed execution events violate declared Resource Authorization or Change Boundary constraints?

The capability is evidence-only unless a verified runtime adapter separately consumes it as a deny condition.

## Authority rule

Agent Runtime Assurance can only narrow existing permission.

~~~text
Resource Authorization = DENY
→ intent evidence can never convert it to ALLOW

Resource Authorization = ALLOW
+ Intent Assessment = ALIGNED
→ COMPATIBLE pre-execution evidence

Resource Authorization = ALLOW
+ Intent Assessment = AMBIGUOUS / MISALIGNED / HIGH_RISK
→ BLOCKED evidence
~~~

COMPATIBLE is not a tool-call grant. Normal Governance, Change Boundary, Human approval, Git Publish, destructive-operation and release rules still apply.

## Provider-neutral semantic intent binding

Build a deterministic request with aips assurance intent-request. A Human-selected Agent/provider may return only structured assessment fields: state, confidence, concise summary, evidence references and provider/model/time metadata.

Private reasoning, chain-of-thought and secret-like values are prohibited. Finalization binds the assessment to the exact request fingerprint and authorization-profile fingerprint.

AIPS core does not require a semantic provider. Missing semantic evidence never widens permission.

## Out-of-band anomaly evidence

Observed runtime events may be audited after execution with aips assurance postflight.

The deterministic auditor detects at least:

- successful operations that Resource Authorization would deny;
- observed unsupported operations;
- subject/profile mismatch;
- network use where the matching grant declares network_allowed=false.

Expected runtime denials are counted but are not anomalies.

The report uses POST_EXECUTION_EVIDENCE, is outside the critical execution path, and fixes automatic_remediation=false. It never changes Git refs, credentials, runtime permissions, Human decisions or production state.

## Relationship to existing capabilities

- Resource Authorization remains the ordinary resource/operation least-privilege contract.
- Execution Isolation remains workspace/writer isolation and Change Boundary ownership.
- Agent Eval remains observable semantic behavior conformance and repeatability evidence.
- Security Assurance remains risk-scaled security review and release evidence.
- Agent Runtime Assurance only binds intent evidence and audits observed execution against those existing contracts.
