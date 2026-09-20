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

The detector reports missing_capability_targets, architecture_surface_drift, orphan_capability_surfaces, stale_documentation_links, scenario_evidence_drift, and workflow_contract_drift.

## Baseline reconciliation

The first v1 baseline reconciles one already-observed drift rather than suppressing it: the existing Integration Gate implementation is registered as capability integration-gate. Repository Health itself is registered as repository-health-architecture-drift.

## Explicit Architecture Surface Inventory

`config/architecture-surfaces.yaml` is the deterministic major-surface inventory. It groups every Capability Map entry into exactly one architecture surface and binds that surface to required repository paths, canonical documentation and validation paths.

Repository Health verifies:

- every current Capability Map ID is classified exactly once;
- every declared required path exists;
- every canonical document exists and is actually declared by one of the surface's Capability Map entries;
- every validation path exists and is bound either by Scenario Conformance evidence or by the top-level repository validator;
- bounded guard/gate discovery still catches newly introduced guard/gate scripts that were not added to the inventory.

This removes the previous blind spot where a non-guard/gate subsystem could exist without deterministic architecture accounting. The inventory remains explicit rather than semantic: adding a genuinely new architecture capability requires updating the Capability Map and inventory together.

## False-positive / false-negative boundary

The detector still avoids semantic inference over arbitrary source files. Architecture coverage is complete relative to the source-controlled Capability Map plus explicit surface inventory, while bounded guard/gate discovery remains a secondary safety net. Repository Health does not infer whether an arbitrary file is a new subsystem.

## Evidence and Human review

Status is PASS or DRIFT_DETECTED. PASS means only that configured consistency contracts hold. Version 1 is Detect + Evidence + Human Review only and performs no remediation.

Every report keeps credential_required=false, external_network_required=false, automatic_remediation_performed=false and every automatic-remediation, code-change, branch/PR, merge, release and publication authority field false. Repository Health evidence cannot authorize protected operations or credential acquisition.

## Complete evidence binding

Repository Health builds a deterministic input manifest for every configured file that can affect the audit:

- the Repository Health config itself;
- Capability Map plus canonical capability documentation targets;
- configured core capability surfaces and bounded discovered guard/gate files;
- documentation binding sources and required targets;
- the Scenario registry, Scenario inventory, Scenario checker and non-external evidence references;
- Integration Gate / repository-validation contract files.

Each existing entry records a SHA-256 digest; missing bound files remain explicit with `exists=false` and `digest=null`. The sorted manifest has its own digest.

The report then computes an evidence fingerprint over repository revision, workspace binding state, dirty paths, manifest digest and drift result. This is evidence identity only; it does not create approval authority.

## Dirty-worktree truth

A clean Git checkout reports:

- `status=EXACT_REVISION`;
- `revision_reproducible=true`.

A Git checkout with staged, unstaged or untracked files reports:

- `status=DIRTY_WORKTREE`;
- `revision_reproducible=false`;
- the exact sorted dirty paths.

A non-Git workspace reports `NO_GIT` rather than inventing a revision.

Dirty state is not architecture drift by itself. The audit may still be `PASS` when configured consistency contracts hold, but the evidence cannot be described as exact-revision reproducible. Restoring identical inputs restores the same deterministic manifest/fingerprint.

The source-controlled policy is `evidence_binding.manifest=complete` and `dirty_workspace=report_non_reproducible`.

## CI evidence artifact

The required `.github/workflows/validate.yml` job emits `repository-health-report.json` from the exact checked-out candidate and uploads it as a short-retention GitHub Actions artifact. Artifact publication does not change Repository Health execution semantics: the audit itself remains credential-free, performs no external provider call and has no automatic-remediation or protected-operation authority.
