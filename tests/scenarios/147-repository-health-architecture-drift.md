# Scenario 147 — Repository Health / Architecture Drift Deterministic Detection

AIPS must deterministically detect drift between source-controlled architecture declarations and repository reality without an LLM, external Agent key, or external network request.

The audit must fail for missing Capability Map targets, unmapped discovered guard/gate scripts, stale canonical documentation references, Scenario evidence drift, or missing Integration Gate/repository-validation wiring. Identical inputs produce identical evidence and baseline PASS requires every drift class empty.

credential_required=false, external_network_required=false, automatic_remediation_performed=false, and all code-change, branch/PR, merge, release, publication and automatic-remediation authority fields remain false.

This is Detect + Evidence + Human Review only; it cannot repair files, bypass Integration Gate, weaken External Credential Dependency Guard, or create a second Change Impact framework.
