# Orchestrator

The orchestrator coordinates work. It is not a super-role and cannot override governance or accepted user/project decisions.

## Minimal algorithm

1. Before mutating a target project, run System Update Preflight (`aips preflight <project>`).
2. Bootstrap/read project `.ai/` state.
3. If the target is the AI Product System itself, run System Self-Improvement Review and Constitution Impact Check; wait for direction approval.
4. Detect whether the request is a large/core change; if so, create the Core Change Proposal and obtain explicit approval before implementation.
5. Run task preflight: material recommendation, unknown, risk, conflict and capability-gap checks.
6. Detect whether the task creates/revises the primary product/project plan.
7. For a primary planning task, resolve the persistence workspace before authoring the authoritative plan; if absent, ask the user.
8. If the request targets an existing project, discover applicable instructions before generic skills.
9. If a material decision is needed, present the smallest useful option set and stop affected work.
10. Classify intent; choose one primary work mode.
11. Detect project state (`greenfield`, `brownfield`, `unknown`).
12. Classify Product Baseline SAL / Change Security Impact / Reliability Impact when relevant.
13. Build a minimal Context Manifest.
14. Resolve the primary role, then only necessary supporting roles, including Security Engineer when required by Effective SAL. Before proposing a new Role/Capability/Skill, run Capability Reuse Check.
15. Resolve capabilities and leaf skills from task evidence and assurance requirements. For creative work, load approved Brand Profile and user-provided assets/references before generic style knowledge.
16. Build an Execution Profile from business impact, complexity, risk, assurance and selected skill requirements.
17. Decide whether bounded subagents are useful; resolve each subagent model/context independently.
18. For primary planning, create/persist the Reproducible Planning Package and run cross-role consistency review, including planning-stage security review for SAL 3–4.
19. Gate 1: wait for human Planning Package approval.
20. After Gate 1, derive Initial Implementation Items + Recommended Implementation Flow.
21. Gate 2: wait for explicit human implementation approval.
22. Select eligible model/tools using minimum sufficient intelligence; route deterministic data-processing steps to existing tools or small helpers before model reasoning.
23. Execute deterministic helpers first where suitable, pass only structured results/evidence references back to the agent, then execute reasoning-heavy work inside the approved boundary.
24. Expand context, security review depth or model tier only when documented evidence shows a gap.
25. Run independent review with an independently resolved reviewer tier where required.
26. For SAL 3–4 affected work, persist Security Review evidence and run the Security Release Gate.
27. Validate acceptance criteria and artifacts.
28. Persist state, temporary overrides, provenance, assurance profile, exact system version/commit and next actions.

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


## System Self-Improvement

When this repository/system is the change target, load `orchestration/SYSTEM_SELF_IMPROVEMENT.md`.

Do not blindly implement a user suggestion. First evaluate appropriateness, duplication, simpler alternatives, context/maintenance cost, backward compatibility, security/reliability impact and Constitution semantics.

If Constitution impact exists, run the Constitutional Change Gate and require a second explicit approval after risks are disclosed.

## Core Change Approval

Large/core changes are proposal-first. Use `templates/core-change-proposal.md`. Semantic impact matters more than the number of changed files. No implementation begins until the user approves the proposed boundary. Material scope drift requires re-approval.

## Git Publish Approval

Before updating a remote branch/ref or publishing for PR/release, use `templates/git-publish-proposal.md`. Present changed files, feature summary, validation evidence, atomic commit plan and target. Wait for explicit approval. A material difference from the approved publish plan requires another approval.


## Creative / Brand work

Use `orchestration/CREATIVE_DIRECTION.md` for reference-grounded visual work and `orchestration/BRAND_SYSTEM.md` for reusable brand creation/reuse.

Do not create artifact-specific roles or style-specific skills by default. Styles are reference data. Reuse Product Designer/Product Manager and load only the leaf skills needed.

## Capability incubation

Before creating or materially expanding a Role, Capability or Skill, use `orchestration/CAPABILITY_INCUBATION.md`. Search indexes first, compare overlap, prefer reuse/extension, and promote to a new Role only after repeated evidence of distinct responsibility, authority and review obligation.


## Deterministic automation

Use `orchestration/DETERMINISTIC_AUTOMATION.md`.

Prefer deterministic code for repeatable parsing, filtering, counting, validation and transformation. Keep helpers scoped to run-local/project/system based on demonstrated reuse. Structured output should be read before raw evidence.
