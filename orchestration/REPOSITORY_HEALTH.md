# Repository Health / Architecture Drift

## Purpose

Detect deterministic drift between the architecture AIPS declares and the repository surfaces that actually exist. This source-controlled consistency layer does not replace Project Intelligence, Change Impact, Documentation Consistency, Scenario Conformance, Integration Gate, or External Credential Dependency Guard.

## Reuse boundaries

- references/evolution/CAPABILITY_MAP.yaml remains the capability identity and canonical documentation index.
- scripts/scenario_conformance.py remains the Scenario registry/evidence authority; Repository Health calls it instead of reimplementing Scenario semantics.
- config/integration-gate.yaml and scripts/integration_gate.py remain the exact-candidate validation path.
- Documentation Consistency remains responsible for changed-file documentation impact.
- External Credential Dependency Guard remains responsible for external credential consumers and secret exposure.
- Change Impact remains responsible for proposed-change affected surfaces and test planning.

## Deterministic checks

Run:

    python scripts/repository_health.py audit --config config/repository-health.yaml

The v1 detector reports missing_capability_targets, orphan_capability_surfaces, stale_documentation_links, scenario_evidence_drift, and workflow_contract_drift. Its report binds the exact digests of config/repository-health.yaml, references/evolution/CAPABILITY_MAP.yaml, and tests/scenario_coverage.yaml plus the current repository revision when Git is available.

## Baseline reconciliation

The first v1 baseline reconciles one already-observed drift rather than suppressing it: the existing Integration Gate implementation is registered as capability integration-gate. Repository Health itself is registered as repository-health-architecture-drift.

## False-positive / false-negative boundary

The detector uses explicit source-controlled surfaces and bounded guard/gate discovery. It avoids semantic inference over arbitrary source files, reducing false positives. A new architecture surface that is not a guard/gate script can remain undetected until added to config/repository-health.yaml or another deterministic inventory; this is an explicit v1 false-negative tradeoff.

## Evidence and Human review

Status is PASS or DRIFT_DETECTED. PASS means only that configured consistency contracts hold. Version 1 is Detect + Evidence + Human Review only and performs no remediation.

Every report keeps credential_required=false, external_network_required=false, automatic_remediation_performed=false and every automatic-remediation, code-change, branch/PR, merge, release and publication authority field false. Repository Health evidence cannot authorize protected operations or credential acquisition.
