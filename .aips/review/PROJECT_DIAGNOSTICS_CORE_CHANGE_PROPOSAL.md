# Core Change Proposal: Read-only Project Diagnostics

## Purpose and classification

Add a single on-demand view over existing Project Intelligence, runtime/Harness and MCP static diagnostics. The user-facing gap is fragmented status and recovery guidance, not the absence of underlying checks. This is a core CLI contract change because it adds a public project command.

## Approved scope

- Add `aips project diagnose <project-path> [--runtime <id>] [--format text|yaml|json]`.
- Reuse existing `aips doctor`, Project Intelligence status, Harness resolver and MCP inspect interfaces with bounded subprocess timeouts.
- Return stable status, reason code, concise safe message, next action and verification command per check.
- Provide recovery guidance for missing, partial and stale Project Intelligence without executing the suggested repair.
- Preserve `UNVERIFIED` limits for live host behavior and MCP connectivity.
- Add lifecycle evidence, Scenario 237, synchronized Human documentation and generated public-command references.

## Exclusions and limits

- No write, bootstrap, attach, index, refresh, installation, cache creation, or automatic repair.
- No raw subprocess output, prompts, environment values, credentials, project source excerpts or image data in reports.
- No new persistence, dependency, role, skill, capability authority, MCP tool, host hook, policy engine, or Constitution change.
- No claim that configured Hooks, tools, or MCP clients execute successfully in a live host.
- No OpenCode native E2E expansion, token telemetry, semantic analyzer, model/image workflow, CI optimization, module extraction, release/tag, or maintenance automation work.

## Expected files / modules

- `scripts/project_diagnostics.py`
- `scripts/aips_cli/project.sh`, `scripts/aips_cli/dispatch.sh`, `scripts/aips_cli/help.sh`, `scripts/project_diagnostics.py`
- `tests/evidence/project_diagnostics_lifecycle.py`, `tests/scenarios/237-read-only-project-diagnostics.md`, `tests/scenario_coverage.yaml`
- Canonical Human docs and generated references: `docs/ARCHITECTURE.md`; `docs/human/ARCHITECTURE_OVERVIEW.md`, `CONFORMANCE.md`, `CONFORMANCE_CURRENT.md`, `CONFORMANCE_HISTORY_INDEX.md`, `DOCUMENTATION_MAP.md`, `DOCUMENTATION_SYNC.md`, `EVOLUTION_RADAR.md`, `HARNESS.md`, `INSTALLATION.md`, `MAINTENANCE.md`, `PROJECT_INTELLIGENCE.md`, `SECURITY_ASSURANCE.md`, `SYSTEM_REFERENCE.md`, `TECHNOLOGY_GUIDE.md`, `USER_GUIDE.md`, and `index.md`
- `config/capability-registry.yaml`, generated `config/architecture-surfaces.yaml`, and `config/system-facts.yaml`
- `harness/HARNESS_PROTOCOL.md`, `harness/adapters/opencode/AGENTS.md`, `harness/adapters/opencode/COMPATIBILITY.md` and mapped Orchestration contracts: `CHANGE_IMPACT.md`, `CONFORMANCE.md`, `CREATIVE_DIRECTION.md`, `DETERMINISTIC_SCHEDULER.md`, `DOCUMENTATION_SYNC.md`, `EXECUTION_ISOLATION.md`, `GITHUB_RULESET_POLICY.md`, `INTEGRATION_GATE.md`, `ORCHESTRATOR.md`, `PROJECT_INTELLIGENCE.md`, `RELEASE_READINESS.md`, `REPOSITORY_HEALTH.md`, and `RUNTIME_CONTEXT.md`
- `CHANGELOG.md`, active review artifacts, and `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`

## Impact

### Architecture / contracts

Additive CLI entrypoint and machine-readable report shape; existing commands keep their current behavior. Reports are advisory diagnostic snapshots.

### Data / migration

No stored data, project-local files, cache writes, schema migration or cleanup.

### Security / reliability

Fixed subprocess argv, bounded timeout and output capture, allowlisted reason/message/action mapping, no raw child output. Unavailable checks remain `UNKNOWN`; native effects remain `UNVERIFIED`.

### Compatibility / rollback

Additive command. Rollback removes the command and its docs/evidence; no persisted data to migrate.

### Tests / validation

Impact-derived Test Matrix:

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Project diagnosis report and child command failures | required | required | lifecycle | JSON/YAML/text schema | local CLI | privacy/no-write | recovery suggestions only | required | docs sync | Migration N/A: no writes or persisted state |
| Project Intelligence status recovery | required | lifecycle | existing status CLI | reason-code/action contract | local CLI | cache remains untouched | missing/partial/stale cases | required | docs sync | Automatic recovery is excluded |
| Runtime/Harness and MCP diagnostic scope | required | — | bounded local resolver/inspect | status contract | local CLI | no live enforcement claim | — | required | conformance docs | Live Host E2E N/A: external host evidence unavailable and explicitly out of scope |

Required release/CI evidence: focused lifecycle, CLI static contracts, Scenario conformance, capability projection consistency, documentation sync/build, strict candidate secret scan and full exact-candidate Integration Gate.

### Secret / credential impact

Secrets required: **NO**

Approved acquisition mechanism: N/A.

Leakage/redaction review: Output is constructed from fixed reason codes and allowlisted status fields; child stdout/stderr and environment values are never included.

Rotation/revocation plan: N/A.

### Documentation / diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: **N/A** — composes existing read-only interfaces without changing architecture boundaries.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: **N/A** — no new subsystem or data flow.
- Human SVG architecture/lifecycle diagrams: **N/A** — no lifecycle or authority transition is added.

## Risks

Child diagnostics may be unavailable under incomplete runtime dependencies or restricted process permissions. The command must report `UNKNOWN`, omit raw error details, and keep repair steps advisory.

## Recommendation

Implement the compact read-only CLI slice. Keep every broader plan23 recommendation separate.

## Proposed Implementation Order

1. Add report helper and additive CLI route.
2. Add focused lifecycle and Scenario 237.
3. Synchronize canonical documentation and generated references.
4. Reconcile exact diff, run focused and full local validation, then prepare the exact-candidate Git Publish Proposal.

## Approval

Status: APPROVED FOR IMPLEMENTATION
Approved by: Human user in this Codex task
Approved at: 2026-10-09T10:20:34+08:00
Approval record: User approved the compact diagnostics slice with “核准”; after the exact-candidate documentation gate exposed 27 additional mapped Human/Agent documents, the user explicitly approved synchronizing that full closure.
Proposal fingerprint: pending exact-candidate reconciliation
Scope fingerprint: pending exact-candidate reconciliation
