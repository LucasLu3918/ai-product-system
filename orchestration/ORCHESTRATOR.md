# Orchestrator

The orchestrator coordinates work. It is not a super-role and cannot override governance or accepted user/project decisions.

## Minimal algorithm

1. Before mutating a target project, run System Update Preflight (`aips preflight <project>`).
2. Bootstrap/read project `.ai/` state.
3. Run task preflight: material recommendation, unknown, risk, conflict and capability-gap checks.
4. Detect whether the task creates/revises the primary product/project plan.
5. For a primary planning task, resolve the persistence workspace before authoring the authoritative plan; if absent, ask the user.
6. If the request targets an existing project, discover applicable instructions before generic skills.
7. If a material decision is needed, present the smallest useful option set and stop affected work.
8. Classify intent; choose one primary work mode.
9. Detect project state (`greenfield`, `brownfield`, `unknown`).
10. Classify Product Baseline SAL / Change Security Impact / Reliability Impact when relevant.
11. Build a minimal Context Manifest.
12. Resolve the primary role, then only necessary supporting roles, including Security Engineer when required by Effective SAL.
13. Resolve capabilities and leaf skills from task evidence and assurance requirements.
14. Build an Execution Profile from business impact, complexity, risk, assurance and selected skill requirements.
15. Decide whether bounded subagents are useful; resolve each subagent model/context independently.
16. For primary planning, create/persist the Reproducible Planning Package and run cross-role consistency review, including planning-stage security review for SAL 3–4.
17. Gate 1: wait for human Planning Package approval.
18. After Gate 1, derive Initial Implementation Items + Recommended Implementation Flow.
19. Gate 2: wait for explicit human implementation approval.
20. Select eligible model/tools using minimum sufficient intelligence.
21. Execute inside the approved intent/change boundary.
22. Expand context, security review depth or model tier only when documented evidence shows a gap.
23. Run independent review with an independently resolved reviewer tier where required.
24. For SAL 3–4 affected work, persist Security Review evidence and run the Security Release Gate.
25. Validate acceptance criteria and artifacts.
26. Persist state, temporary overrides, provenance, assurance profile, exact system version/commit and next actions.

## System Update Preflight

The orchestrator must not implement project mutations using an unverified stale local system.

Use `aips preflight <project>`, which:

- requires the system repo to be clean/on `main`;
- fetches `origin/main` and uses only fast-forward pulls;
- blocks divergent history instead of auto merging/rebasing;
- requires explicit review for a MAJOR version change;
- re-executes the updated CLI, validates the system and records `.ai/SYSTEM.yaml`.

It updates the AI Product System only. Target-project source updates remain a separate user/project decision.

## Reproducible Planning Package

Load `orchestration/PLANNING_PACKAGE.md` when the request defines the authoritative product/project blueprint.

The planning package must be persisted outside the chat and sufficiently complete that another competent AI agent or human team can reproduce substantially the same intended product without hidden conversation context.

Do not claim planning completion if applicable product, UX, visual/key-visual, API/contract, architecture, testing/delivery or decision records are missing.

Implementation requires both Planning Package approval (Gate 1) and Implementation Readiness approval (Gate 2).

## Risk-Proportional Security Assurance

Use `docs/SECURITY_ASSURANCE.md`.

For planning, establish Product Baseline SAL and Reliability Impact. For every material change, classify Change Security Impact from the actual Change Boundary and protected assets touched.

Critical risk floors override average scoring. High-value financial/stored-value boundaries are security boundaries, including payments, refunds, settlement, balances, points/credits/vouchers/coupons with economic value, redemption, transfer and withdrawal.

SAL 3–4 activates independent Security Engineer review as applicable. SAL 4 unresolved High/Critical findings block release.

Do not run full-product SAL 4 review for a cosmetic change that does not touch a protected boundary.

## Existing-project instruction discovery

For each target path:

1. find project/root `AGENTS.md` if present;
2. walk toward the target path and collect nearer scoped `AGENTS.md` files;
3. load only accepted ADRs/contracts/standards relevant to the change;
4. load project-local skills relevant to the task;
5. add global skills only for remaining expertise gaps.

Nearest scoped instructions beat broader instructions. Current explicit user decisions beat project-local instructions inside the approved scope, but material conflicts must be surfaced before implementation.

## Task Preflight

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

## System self-change

When this repository itself changes, the final review must include the Documentation Impact Gate in `docs/MAINTENANCE.md`. A system change is incomplete if affected docs, flows, diagrams, examples, scenarios, templates/schemas, VERSION or CHANGELOG are stale.
