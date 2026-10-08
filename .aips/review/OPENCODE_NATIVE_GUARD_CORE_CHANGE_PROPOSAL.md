# OpenCode Native Context and Guard Core Change Proposal

## System Improvement Review

See `.aips/review/OPENCODE_NATIVE_GUARD_SYSTEM_IMPROVEMENT_REVIEW.md`. The requested four-phase direction is accepted and scoped to existing AIPS abstractions and directly supported OpenCode V2 hooks.

## Purpose

Improve AIPS task-context selection and provide OpenCode V2 with fresh compact Project Intelligence context plus conservative pre-action handling for supported native file operations. Preserve explicit limitations where a hook cannot observe the effect (notably arbitrary shell subprocesses and MCP/custom tools).

## Approved change boundary

1. Classify task **domain**, **intent**, and **effect** as separate outputs while preserving the current `classify_prompt` compatibility surface; route Chinese and English creative asset workflows without conflating file read, discussion, creation, and modification.
2. Add a version-aware OpenCode V2 plugin to the existing managed projection lifecycle. Use documented V2 hooks for model context and supported native action interception. Do not alter user OpenCode JSONC or overwrite unowned plugin files.
3. Connect plugin context/readiness to the existing Project Intelligence Context Manifest and existing high-risk policy context without changing runtime-policy authority. Handle project-root confinement, symlinks, stale/missing evidence, non-Git roots, cache fingerprints and explicit unavailable/error outcomes.
4. Add deterministic lifecycle and boundary evidence for Chinese routing, native hooks, install/upgrade/doctor/uninstall, interruption/recovery, version negotiation, failures, performance and unsupported Shell/MCP cases; update Scenario, adapter truth, docs and architecture projections.

## Constraints and exclusions

- No new Creative Agent, Role, Skill, general Policy Engine, or expansion of `runtime_policy.py` into local filesystem policy.
- Enforcement is only claimed for native actions actually intercepted and verified. Model delivery, arbitrary shell effects, custom tools and MCP write protection remain UNVERIFIED/ADVISORY if not directly proven.
- No prompt persistence; cache only derived context keyed to session, project and relevant source fingerprints.
- V1 receives existing projection compatibility; do not install a V2 plugin into V1 or an unknown runtime.
- Preserve fail-closed readiness for affected writes and never claim plugin failure as successful protection.

## Expected impact and contracts

- Prompt classification producer/consumer: `scripts/turn_intent.py`, Context Manifest and current context CLI output; preserve legacy category/mutation/topics keys.
- Native action decision helper: `scripts/opencode_native_guard.py` exposes deterministic L0–L3 readiness and confined-path decisions for the plugin and evidence suite.
- OpenCode managed filesystem: `scripts/opencode_skill_projection.py`, harness install/status/doctor/uninstall and ownership manifest; preserve collision, digest, symlink and rollback safety.
- Native runtime: versioned V2 plugin hook contract and explicit supported-operation list; no change to external runtime policy contract.
- Evidence/docs: lifecycle tests, validation contracts, conformance scenario, adapter registry, canonical capability registry, documentation placement/sync and affected current architecture views.

## Compatibility, migration and recovery

Additive context fields and plugin files require no project migration. Existing V1 installations retain their projection. Installer updates may add one owned V2 plugin; changed/unowned same-name files block destructive replacement. Interrupted install must preserve its ownership checkpoint and allow safe diagnosis/retry. Uninstall removes only digest-matching owned files. Unknown or unsupported V2 APIs retain files and report a conflict/unknown state.

## Required verification

The active matrix `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` is derived from this boundary and must be recomputed against the final candidate. It includes unit, integration, contract, security, recovery/idempotency, CLI/Harness, docs/schema, native acceptance and exact-candidate local Gate evidence. Remote PR/main CI and merge are separate publication gates.

## Approval

Implementation scope approved by the user request in this task referencing conversation `6ac73779-9fdc-83e8-8ece-0ed1e8723dae`. This records implementation scope only; final publication requires approval bound to the exact candidate under the Git Publish Approval Gate.
