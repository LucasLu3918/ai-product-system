# System Improvement Review: Read-only Project Diagnostics

Appropriateness: **APPROPRIATE**. This is a narrow usability improvement over existing read-only diagnostics.

User problem: Project status, Harness resolution, Project Intelligence readiness and MCP capability inspection are separate commands. Users may see a blocked or partial state without an actionable recovery sequence.

Proposed solution: Add `aips project diagnose <project-path>` to aggregate existing read-only signals into a concise text, YAML or JSON report with stable reason codes, safe messages, next actions and verification commands.

Existing coverage: `aips project check`, `aips harness resolve`, `aips intelligence status`, `aips mcp inspect`, and `aips doctor` already expose parts of the state. No unified, path-scoped report or consistent PI recovery guidance was found.

Reuse / extension candidates: Extend the existing `aips project` CLI namespace and call the current `aips doctor`, resolver/status and MCP inspect interfaces. Preserve `project check` behavior.

Lower-layer alternative: Documentation alone would explain the commands but would not aggregate current readiness or reason codes. Extending an existing project command would risk changing its established output contract; a new additive subcommand is the smallest compatible seam.

Context / token cost: On-demand only; one bounded command invocation, no turn-bootstrap cost and no new dependency.

Security / reliability: Read-only; fixed subprocess arguments, bounded timeouts, no raw subprocess output, prompts, environment values, credentials or project source excerpts in the report. Static MCP capability and Harness configuration do not prove live host execution; native effects remain `UNVERIFIED`.

Backward compatibility: Additive CLI and output contract. No migration, cache creation, project attachment, refresh, indexing, or automatic repair.

Scenario / test impact: Add Scenario 237 and a lifecycle evidence script covering missing/partial PI recovery guidance, structured formats, timeouts/failures, invalid project paths, privacy and no-write behavior.

Human docs impact: Update Installation, Project Intelligence, Conformance and the generated System Reference command inventory.

Agent docs impact: No bootstrap or global protocol change; keep the recovery behavior documented in the existing Project Intelligence guide.

Architecture diagram impact: `docs/ARCHITECTURE.md`, `docs/human/ARCHITECTURE_OVERVIEW.md`, and lifecycle SVGs are **N/A**. The additive CLI composes existing read-only interfaces and introduces no new subsystem, data store, runtime authority or lifecycle transition.

Constitution impact: **NO**. No Human authority, precedence, safety boundary, approval or publication semantics change.

Recommended AIPS solution: Implement only the additive read-only command and its recovery instructions. Keep deeper OpenCode native E2E work, semantic analyzers, token telemetry, model/image workflow work, CI optimization, module extraction, release changes and maintenance automation out of scope.

Additional optimization candidates: Defer OpenCode live-session reliability work and usage/cohort measurement until a supported reproducible evidence environment is available. No additional optimization is approved in this slice.

Expected scope: CLI helper/dispatch/help, focused lifecycle evidence, Scenario 237, canonical human docs and generated command/capability references, changelog, review artifacts and exact-candidate test matrix.

Risks: Child diagnostics can be unavailable because of missing dependencies or runtime permissions. These cases must be reported as `UNKNOWN` with bounded guidance and must never claim successful native enforcement.

Approval: User approved this compact scope in the current Codex task with “核准”. This approval covers implementation only; exact remote publication remains subject to the Git Publish Approval Gate.
