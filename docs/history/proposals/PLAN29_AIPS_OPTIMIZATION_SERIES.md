# Plan29 AIPS Optimization Series

Date: 2026-10-11
Baseline: `main` at `8eaf16983d816a1fc8ad08d31eb8cd2b908e4bdc`, AIPS `0.82.0`
Approval: Human approved the 13-item, Phase 0–5 implementation scope in this task on 2026-10-11.

## System Improvement Review

### User problem

AIPS has broad engineering and governance capabilities, but the Plan29 review identifies gaps in lifecycle reconciliation, real-host evidence, recovery, quality measurement, cost evidence, maintainability, and real-task outcome evaluation.

### Proposed solution and appropriateness

The 13 recommendations are suitable as a staged optimization series. AIPS already contains the primary systems involved, so implementation should extend existing modules, protocols, and tests. Each material workstream is an independent, exact-candidate PR; no single change should combine all 13 boundaries.

### Existing coverage and reuse

The series reuses branch hygiene and release readiness, native runtime adapters, Creative execution and repair, Project Intelligence, Validation Shadow, existing facades, telemetry, Evolution Radar, security/dependency checks, document-size and capability registries, and Agent/Trajectory evaluation. No new global Role, Skill, Capability, or approval gate is proposed.

### Lower-layer and context cost

Keep project-specific evidence and benchmark control data in scoped reports and fixtures. Keep new behavior in existing adapters, deterministic scripts, and project workflows. Load large reports and historical evidence on demand. Do not add always-loaded system context solely to describe this series.

### Security, reliability, compatibility

Preserve Human authority, exact-SHA publication checks, report-only branch cleanup, explicit release authorization, privacy defaults, and unknown runtime status. Extend report schemas additively and preserve existing CLI/import facades. Do not infer real-host success from static registration or fixture passes.

### Constitution impact

**NO.** The series preserves the Constitution's existing Human authority, truthfulness, protected safety, and scope-integrity rules. Any proposal to weaken or redefine those invariants is outside this approval and requires the separate Constitutional Change Gate.

### Additional optimization candidates

None added beyond the 13 approved recommendations.

## Core Change Proposal

### Why this is a core/large change

The series crosses runtime adapters, release and branch publication, CI policy, security, multiple core facades, and evidence schemas. It can affect Human authority, compatibility, test selection, and claims made about system reliability.

### Approved scope

- Implement the 13 recommendations below through the Phase 0–5 order.
- Start each workstream from a fresh remote `main` baseline, resolve its own Change Impact, and bind a Core Change Test Matrix to its final diff.
- Create or update an engineering PR only after local validation and candidate content-safety checks.
- Merge only the exact, current PR candidate after required checks pass.

### Explicit boundaries

- Stable release work prepares and validates readiness only. Creating a release tag or publishing a GitHub Release requires a separate explicit decision.
- Branch lifecycle reports are advisory and read-only. They never delete branches, close PRs, rebase, merge, or create an authorized cleanup manifest.
- Selective CI execution remains disabled until the existing graduation evidence threshold is met and the required Human decision is recorded.
- OpenCode protection levels and image quality claims require the corresponding native or human evidence. Unknown remains visible.
- No external provider credential is introduced or transmitted as part of this series.

### Implementation order and status

| # | Phase | Workstream | Existing candidates | Acceptance focus | Status |
|---:|---|---|---|---|---|
| 1 | 0 | PR and branch lifecycle reconciliation | `scripts/branch_hygiene.py`, `config/branch-lifecycle.yaml`, branch-hygiene workflow | Exact main/branch/PR evidence; `KEEP`, `SUPERSEDED`, `REBASE_REQUIRED`, `CLEANUP_CANDIDATE`; report-only authority | Complete — PR #305 merged |
| 2 | 1 | Stable release readiness | `scripts/version_tag_policy.py`, release-readiness workflow | Readiness, install/upgrade/rollback evidence; no release publication | Complete — existing exact-candidate gate and install/update lifecycle verified; rejected divergent updates preserve installed state |
| 3 | 1 | OpenCode native reliability | OpenCode adapter, native guard, compatibility matrix | Version-bound host evidence and explicit unsupported-effect status | Complete — exact-host acceptance reports unsupported Shell, MCP/custom-tool, and out-of-process effects; legacy reports remain \`UNVERIFIED\` |
| 4 | 2 | Creative image quality and repair | `creative_repair.py`, quality benchmark, existing evidence | Cross-profile dataset, scoped repair, separate model/check/compiler failures, human acceptance | Planned |
| 5 | 1 | Project Intelligence recovery | `project_diagnostics.py`, `project_intelligence.py` | Reproducible missing/stale/ephemeral/blocked recovery plans without hidden writes | Planned |
| 6 | 2 | Creative workspace asset import | Creative bundle and workspace profile | Hash-bound import candidate, destination/overwrite checks, Change Impact | Planned |
| 7 | 3 | Selective validation evidence | Validation Shadow and graduation policy | Baseline precision, false-negative evidence, current threshold; keep full validation enabled | Planned |
| 8 | 3 | Core facade extraction | `creative_execution.py`, `project_intelligence.py`, `retrieval_intelligence.py` | Stable public identity, CLI/import compatibility, subsystem lifecycle evidence | Planned |
| 9 | 3 | Context/token/runtime cost evidence | telemetry export, run traces, Context budget | Privacy-bounded measurements with authoritative token sources and unknown cost preserved | Planned |
| 10 | 4 | Evolution Radar effectiveness | Radar analysis, evaluation reports | Precision/recall and actionable yield; preserve negative findings | Planned |
| 11 | 4 | Security and dependency governance | Ruleset snapshots, secret/PII scanners, dependency impact | VERIFIED versus UNKNOWN, narrow digest handling, categorized dependency evidence | Planned |
| 12 | 4 | Documentation and capability maintenance | document-size audit, registry projections, canonical docs | Reduce duplicated maintenance without deleting required security or historical evidence | Planned |
| 13 | 5 | Real-task outcome evaluation | Agent Eval, Trajectory Eval, telemetry | Fixed task set, comparable baseline, success/rework/security measures, failures retained | Planned |

Each row is a candidate for incremental implementation, not a claim that its desired outcome already exists. Reuse existing implementations and close a workstream without a code change when current evidence already satisfies its acceptance focus.

## Phase outputs

1. **Phase 0 — Baseline:** branch/PR inventory, reconciliation evidence, and this approved optimization backlog.
2. **Phase 1 — Reliability and delivery:** host acceptance and recovery contracts, plus release readiness evidence.
3. **Phase 2 — Creative quality:** benchmark, repair evidence, and workspace transfer contract.
4. **Phase 3 — Engineering cost:** validation evaluation, facade compatibility evidence, and cost baseline.
5. **Phase 4 — Long-term governance:** research effectiveness, security regression, and documentation impact evidence.
6. **Phase 5 — Outcome review:** before/after task evidence and a release-candidate decision. This decision does not authorize publication.

## Approval

Status: APPROVED
Approved by: Human user in this task
Approval reference: `core_change_scope_approved_for_13_items_in_phases_0_to_5`
Approved scope: 13 workstreams in the order and authority limits above.
Constitutional change: No.
Publication: Engineering PRs and merge of each exact, validated PR were explicitly requested; tag/release, branch deletion, and unrelated PR merges were not.
