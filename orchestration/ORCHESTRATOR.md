# Orchestrator

The orchestrator coordinates work. It is not a super-role and cannot override governance or accepted user/project decisions.

## Minimal algorithm

1. Bootstrap project `.ai/` state when present.
2. Run preflight: material recommendation, unknown, risk, conflict and capability-gap checks.
3. If the request targets an existing project, discover applicable instructions before generic skills.
4. If a material decision is needed, present the smallest useful option set and stop affected work.
5. Classify intent; choose one primary work mode.
6. Detect project state (`greenfield`, `brownfield`, `unknown`).
7. Build a minimal Context Manifest.
8. Resolve the primary role, then only necessary supporting roles.
9. Resolve capabilities and leaf skills from task evidence.
10. Build an Execution Profile from business impact, complexity, risk and selected skill requirements.
11. Decide whether bounded subagents are useful; resolve each subagent model/context independently.
12. Select eligible model/tools using minimum sufficient intelligence.
13. Execute inside the approved intent/change boundary.
14. Expand context or model tier only when documented evidence shows a gap.
15. Run independent review with an independently resolved reviewer tier where required.
16. Validate acceptance criteria and artifacts.
17. Persist state, temporary overrides, provenance and next actions.

## Existing-project instruction discovery

For each target path:

1. find project/root `AGENTS.md` if present;
2. walk toward the target path and collect nearer scoped `AGENTS.md` files;
3. load only accepted ADRs/contracts/standards relevant to the change;
4. load project-local skills relevant to the task;
5. add global skills only for remaining expertise gaps.

Nearest scoped instructions beat broader instructions. Current explicit user decisions beat project-local instructions inside the approved scope, but material conflicts must be surfaced before implementation.

## Preflight

Interrupt only for choices that materially change product behavior, contract, architecture, security, data, cost, scope or recoverability. Batch non-blocking questions.

If expertise is missing, prefer:

```text
existing skill reuse → new narrow skill → new capability → new role
```

Do not create a permanent/high-authority role without user approval.

## Context expansion

An active role may request missing context rather than preloading everything.

```yaml
reason: "SQL profiling shows the affected query dominates latency"
request:
  roles: [database-engineer]
  skills: [sql-performance]
scope:
  - affected query
  - relevant schema/indexes
```

Approve only the smallest sufficient expansion.

## Delegation and subagents

Use a subagent only when the task benefits from a separate bounded specialty, parallel read-only analysis or independent review. Do not create subagents merely because the platform supports them.

For every subagent resolve:

```text
objective → scope → role/skills → minimal context → model tier → permissions → expected output
```

Skills supply model requirement hints; the Model Router makes the final tier/model choice. Business importance, technical complexity, risk, privacy and failure cost are considered together. Critical risk may raise the minimum tier.

Subagents do not inherit the full primary context or model automatically. They request context/model escalation when evidence shows the assigned profile is insufficient. The single-writer rule still applies.

## Single writer

Analysis/review may run in parallel. One writer owns a change boundary by default.

## Architecture preflight

1. Inspect current architecture/conventions first.
2. Prefer the existing/simple structure when adequate.
3. Apply Clean Architecture dependency principles without forcing a reference folder layout.
4. Enable DDD only to the justified level: none, tactical, or strategic+tactical.
5. Use TDD for testable behavior; use characterization tests before risky legacy changes with insufficient coverage.
6. CQRS, event sourcing, microservices, saga or broad architecture rewrites require evidence and a material decision before adoption.

Never refactor unrelated code merely to make the repository resemble a reference architecture.
