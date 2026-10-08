# Repository Health / Architecture Drift

## Purpose

Detect deterministic drift between the architecture AIPS declares and the repository surfaces that actually exist. This source-controlled consistency layer does not replace Project Intelligence, Change Impact, Documentation Consistency, Scenario Conformance, Integration Gate, or External Credential Dependency Guard.

## Reuse boundaries

Repository Health keeps path and digest facade signatures stable over shared primitives; generated Architecture Surface projections continue to derive from the canonical Capability Registry.

- config/capability-registry.yaml is the canonical capability and architecture-surface source. scripts/capability_registry.py generates the compatible Capability Map and architecture-surface indexes.
- scripts/scenario_conformance.py remains the Scenario registry/evidence authority; Repository Health calls it instead of reimplementing Scenario semantics.
- config/integration-gate.yaml and scripts/integration_gate.py remain the exact-candidate validation path.
- Documentation Consistency remains responsible for changed-file documentation impact.
- External Credential Dependency Guard remains responsible for external credential consumers and secret exposure.
- Change Impact remains responsible for proposed-change affected surfaces and test planning.

## Deterministic checks

Run:

    python scripts/repository_health.py audit --config config/repository-health.yaml
    python scripts/capability_registry.py check

The detector reports missing_capability_targets, architecture_surface_drift, orphan_capability_surfaces, stale_documentation_links, scenario_evidence_drift, and workflow_contract_drift.

## Baseline reconciliation

The first v1 baseline reconciles one already-observed drift rather than suppressing it: the existing Integration Gate implementation is registered as capability integration-gate. Repository Health itself is registered as repository-health-architecture-drift.

## Explicit Architecture Surface Inventory

The existing Harness runtime surface owns the creative executor, its Bundle template, Scenario, and lifecycle evidence; generated projections must remain in sync with the canonical registry.

The Harness runtime surface includes the OpenCode native plugin, direct-action guard, creative metadata profile, privacy trace and their lifecycle/native acceptance evidence; generated inventory remains derived from the Capability Registry.

The harness-runtime surface includes OpenCode native guard decisions and the managed V2 plugin projection; architecture projections remain generated from the Capability Registry.

`config/capability-registry.yaml` owns capability metadata and the deterministic major-surface inventory. `references/evolution/CAPABILITY_MAP.yaml` and `config/architecture-surfaces.yaml` retain their v1 consumer formats and are generated projections. The default check is read-only; run `python scripts/capability_registry.py generate` only after editing the canonical registry.

Repository Health verifies:

- registry metadata is valid and both generated projections exactly match it;
- every current capability ID is classified exactly once;
- every declared required path exists;
- every canonical document exists and is actually declared by one of the surface's Capability Map entries;
- every validation path exists and is bound either by Scenario Conformance evidence or by the top-level repository validator;
- bounded discovery catches newly introduced guard, gate, scheduler, ratchet, export and hygiene scripts that were not added to the inventory.

This removes the previous blind spot where an important subsystem could exist without deterministic architecture accounting. The inventory remains explicit rather than semantic: adding a genuinely new architecture capability requires updating the canonical registry and regenerating both compatibility indexes.

## False-positive / false-negative boundary

The detector still avoids semantic inference over arbitrary source files. Architecture coverage is complete relative to the source-controlled canonical registry and explicit surface inventory, while bounded discovery remains a secondary safety net. Repository Health does not infer whether an arbitrary file is a new subsystem.

## Evidence and Human review

Status is PASS or DRIFT_DETECTED. PASS means only that configured consistency contracts hold. Version 1 is Detect + Evidence + Human Review only and performs no remediation.

Every report keeps credential_required=false, external_network_required=false, automatic_remediation_performed=false and every automatic-remediation, code-change, branch/PR, merge, release and publication authority field false. Repository Health evidence cannot authorize protected operations or credential acquisition.

## Complete evidence binding

Repository Health builds a deterministic input manifest for every configured file that can affect the audit:

- the Repository Health config itself;
- canonical Capability Registry, generated Capability Map, generated surface inventory, capability documentation and validation evidence;
- configured core capability surfaces and bounded discovered guard/gate files;
- documentation binding sources and required targets;
- the Scenario registry, Scenario inventory, Scenario checker and non-external evidence references;
- shared Publication Preflight、Integration Gate 與 repository-validation contract files；GitHub workflow 必須呼叫 `scripts/publish_preflight.py`，再由其委派 `scripts/integration_gate.py`。

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


## Scheduled maintenance observation

`.github/workflows/repository-health.yml` runs a credential-free Repository Health audit on a weekly schedule and on manual dispatch. It checks out the exact default-branch revision, emits `repository-health-report.json`, uploads the report as a short-retention Actions artifact, and writes a concise Job Summary.

A PASS run produces evidence only. A `DRIFT_DETECTED` run creates at most one open GitHub Issue per deterministic evidence fingerprint, then fails the workflow so the drift is visible in Actions. Duplicate notification suppression is fingerprint-based and does not mutate Repository Health truth.

The scheduled workflow may use the GitHub control plane to publish its artifact, summary and drift Issue, but the detector itself still reports `external_network_required=false`: no external Agent/provider call is required to compute the audit. The workflow has no contents-write permission and cannot modify repository files, create implementation branches/PRs, merge, release or remediate findings.

OpenCode adapter source and lifecycle evidence are registered under the existing Harness surface; generated architecture projections remain derived from capability registry.
