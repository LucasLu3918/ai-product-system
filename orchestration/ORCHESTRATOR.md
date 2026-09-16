# Orchestrator

The orchestrator coordinates work. It is not a super-role and cannot override governance or accepted user/project decisions.

## Minimal algorithm

1. When entered through the Global Harness, resolve runtime/project context and applicability with `aips harness resolve`.
2. If the request is unrelated to product/project/software work, continue normal conversation without loading full AIPS.
3. Before mutating a target project, run System Update Preflight (`aips preflight <project>`).
4. Resolve Project Mode: load/persist `.ai/` only in ATTACHED mode; remain non-persistent in EPHEMERAL mode.
5. If the target is the AI Product System itself, run System Self-Improvement Review and Constitution Impact Check; wait for direction approval.
6. Detect whether the request is a large/core change; if so, create the Core Change Proposal and obtain explicit approval before implementation.
7. Run task preflight and resolve requirement status (READY / NEEDS_CLARIFICATION / BLOCKED).
8. Resolve required user-provided external sources using connector-first External Context Resolution.
9. Detect whether the task creates/revises the primary product/project plan and whether complete product delivery is in scope.
10. For a primary planning task, resolve the persistence workspace before authoring the authoritative plan; if absent, ask the user.
11. For existing projects, compose runtime-native + scoped project instructions/authoritative docs, then load only relevant Project Knowledge; targeted-discover only remaining gaps.
12. For complete products/material product plans, resolve Q1/Q2/Q3 Quality Planning before architecture is locked.
13. If a material decision is needed, present the smallest useful option set and stop affected work.
14. Classify intent; choose one primary work mode.
15. Detect project state (`greenfield`, `brownfield`, `unknown`).
16. Classify Product Baseline SAL / Change Security Impact / Reliability Impact when relevant.
17. Build a minimal Context Manifest including only relevant runtime/project/knowledge context.
18. Resolve the primary role and only necessary supporting roles.
19. Resolve capabilities and leaf skills from task evidence and assurance requirements.
20. Build an Execution Profile from business impact, complexity, risk, assurance and selected skill requirements.
21. Decide whether bounded subagents are useful; resolve each subagent model/context independently.
22. For primary planning, create/persist the Reproducible Planning Package and run cross-role consistency review.
23. Gate 1: wait for human Planning Package approval.
24. After Gate 1, derive Initial Implementation Items + Recommended Implementation Flow.
25. Gate 2: wait for explicit human implementation approval.
26. Select eligible model/tools using minimum sufficient intelligence; route deterministic processing to tools/helpers where suitable.
27. Execute inside the approved boundary, including provider-neutral observability instrumentation required by the Quality Profile.
28. For existing UI polish, run V1/V2 Visual Consistency Repair as applicable.
29. Resolve independent review depth; large/core/high-risk work uses the needed Multi-Perspective Review Panel.
30. Consolidate findings, return them to the original Author for fixes, then run targeted re-review unless the Change Boundary materially expanded.
31. For SAL 3–4 affected work, persist Security Review evidence and run the Security Release Gate.
32. Validate LOCAL_COMPLETE criteria for complete products.
33. If production was explicitly requested, continue Production Enablement; otherwise ask whether to continue only after LOCAL_COMPLETE.
34. When production is in scope, evaluate exact-candidate Release Readiness and verify production before PRODUCTION_VERIFIED.
35. Extract lessons and refresh only affected Project Knowledge / Visual Profile topics when persistence is enabled.
36. Persist state/provenance only where the current Project Mode permits it.

## System Update Preflight

The orchestrator must not implement project mutations using an unverified stale local system.

Use `aips preflight <project>`, which:

- requires the system repo to be clean/on `main`;
- fetches `origin/main` and uses only fast-forward pulls;
- blocks divergent history instead of auto merging/rebasing;
- requires explicit review for a MAJOR version change;
- re-executes the updated CLI, validates the system and records `.ai/SYSTEM.yaml`.

It updates the AI Product System only. Target-project source updates remain a separate user/project decision.

Preflight does not attach an EPHEMERAL project. Only `aips attach` enables persistent `.ai/` state.

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

Use `orchestration/REQUIREMENT_CLARIFICATION.md`.

Interrupt only for choices that materially change product behavior, contract, architecture, security, data, cost, scope or recoverability. Use safe professional defaults for non-material ambiguity and ask the smallest useful question when a user decision is truly needed. Do not begin broad implementation while status is NEEDS_CLARIFICATION or BLOCKED.

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


## End-to-end product delivery

Use `orchestration/PRODUCT_DELIVERY.md` when the user requests a complete product rather than an isolated change.

The Product Workspace remains the System of Record. Create/update `PRODUCT.yaml` so another Agent can discover Deployment Units, contracts, commands, environments, delivery state and observability without replaying chat context.

Frontend/backend separation means independent Deployment Units. Do not split repositories unless project evidence justifies multi-repo.

For production delivery:
1. verify the local environment;
2. run applicable automated tests and deterministic security checks;
3. run independent security/quality review required by risk;
4. build an exact Release Candidate;
5. deploy to staging when applicable;
6. run staging smoke/E2E/security verification;
7. evaluate `orchestration/RELEASE_READINESS.md`;
8. obtain any required production approval;
9. promote the exact candidate;
10. run post-deploy health/smoke/log/metric checks and rollback/roll-forward when verification fails.

Release Readiness is one consolidated readiness decision, not a replacement for constitutional/governance/security approvals.


## External context resolution

Use `orchestration/EXTERNAL_CONTEXT_RESOLUTION.md` for user-provided Jira/Confluence/Drive/GitHub/other external references. Prefer exact connectors/MCP/apps, guide authorization when needed, preserve the pending task, and resume after authorization. Ask for manual content only after supported retrieval paths fail.

## Visual implementation polish

Use `orchestration/VISUAL_POLISH.md` when an existing UI looks awkward/inconsistent but the approved direction should be preserved. Prefer token/shared-component fixes and verify rendered screenshots/responsive/states before PASS.

## Multi-perspective review and learning

Use `orchestration/MULTI_REVIEW.md` for large/core/high-risk changes. Resolve reviewer perspectives from the actual Change Boundary, run bounded read-only review in parallel where useful, normalize/deduplicate findings, and keep the original Author as the writer.

After fixes, re-review only affected findings/diffs/tests unless scope expanded. Persist lessons at run/project level when useful; recommend System Capability improvement to the user only when evidence is repeated/generalizable.


## Project Knowledge

Use `orchestration/PROJECT_KNOWLEDGE.md`.

The Knowledge Index is a navigation/cache surface. It never outranks AGENTS, ADR, contracts or official docs. Prefer authoritative pointers; persist derived knowledge only when it is stable and expensive to rediscover. Refresh only topics affected by watched paths/signals.

## Quality Planning

Use `orchestration/QUALITY_PLANNING.md` for complete products and material product plans. Q1/Q2/Q3 are baselines, not rigid bundles. Feed measurable targets/budgets into architecture, implementation verification and Release Readiness.

## Local and production milestones

A complete product normally reaches `LOCAL_COMPLETE` first. If production was not requested initially, ask whether to continue. If production was requested initially, continue into Production Enablement without a redundant confirmation. `PRODUCTION_VERIFIED` requires post-deploy verification.
