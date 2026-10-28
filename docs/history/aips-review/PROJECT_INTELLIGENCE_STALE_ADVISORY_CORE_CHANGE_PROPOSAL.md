# Core Change Proposal — READY Stale Project Intelligence Advisory

## Purpose

Allow ordinary confined local L2 source writes to proceed when Project Intelligence is semantically READY but its derived freshness is STALE, while keeping staleness visible and preserving every independent hard stop.

## Why this is a Core Change

The change adjusts Turn Context fail policy and a native runtime permission guard that authorize local writes. An overly broad relaxation could bypass missing context, unsafe targets or unresolved authority conflicts, so the boundary requires explicit evidence.

## Approved Scope

The user approved this scope in the current task: for READY Project Intelligence with STALE freshness, remove staleness as the sole denial for ordinary confined local L2 source writes. Preserve stops for missing sources/protocols, insufficient readiness, UNKNOWN, instruction conflicts, path escapes, creative writes, and external/high-risk operations. Update Turn Context, OpenCode guard, corresponding documentation and lifecycle tests. Do not change `.ai` persistence modes or the Constitution.

### In scope

- `scripts/project_intelligence.py`: keep STALE and targeted refresh visible; do not add `intelligence_stale` as a fail-closed reason when readiness is READY.
- `scripts/opencode_native_guard.py`: allow READY+STALE confined supported local L2 writes, including manifests with only the legacy stale reason; deny all other closed reasons.
- Lifecycle and contract evidence for READY+STALE allow and the independent denial cases.
- Turn Harness, Project Intelligence, Human Harness and architecture overview policy text.
- A focused scenario, the System Improvement Review and this proposal, plus the active Core Change Test Matrix.

### Out of scope

- Changing `.ai` storage or EPHEMERAL/ATTACHED behavior, refreshing Intelligence automatically, bypassing Change Impact, or changing readiness requirements.
- Relaxing UNKNOWN, missing protocol/source, authority conflict, path confinement, creative, external action, Shell/MCP or high-risk controls.
- Constitution, Human Authority, publication/merge authority, new runtime components, data stores or dependencies.

## Impact and compatibility

No schema, persistent data, migration, event or runtime topology changes. The existing freshness field, targeted refresh list and manifest shape remain unchanged. The guard tolerates only the exact legacy stale-only failure reason when the manifest independently proves READY+STALE; other failures still deny.

## Architecture Diagram Impact

N/A — no component topology, deployment unit or data-flow topology changes.

## Validation

- Focused Project Intelligence Context and OpenCode lifecycle evidence.
- OpenCode contract validation and repository validation.
- Exact-candidate Core Change Integration Gate, documentation closure and candidate secret scan.
- Remote PR `repository` check on the exact head and post-merge `main` verification.

## Approval

Status: APPROVED. Human approval was received in the current task after the exact scope above was presented.
