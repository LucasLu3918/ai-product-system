# Orchestrator

The orchestrator coordinates work. It is not a super-role and cannot override governance or accepted user/project decisions.

## Minimal algorithm

1. Resolve current runtime/project/turn context through the Global Harness when installed.
2. If the request is unrelated to product/project/software work, continue normal conversation without heavy AIPS context.
3. Before mutating a target project, run System Update Preflight (`aips preflight <project>`).
4. Resolve project mode and Intelligence store: ATTACHED uses `.ai/intelligence/`; EPHEMERAL may use external AIPS cache without writing into the repository.
5. If the target is AIPS itself, run System Self-Improvement Review and Constitution Impact Check.
6. Detect large/core change and obtain Core Change Approval before implementation.
7. Resolve requirement readiness and required external sources.
8. Detect primary planning/full product delivery.
9. For existing projects, compose runtime-native + scoped project instructions/authoritative docs via SOURCE_REGISTRY-aware resolution.
10. Resolve Project Intelligence:
    - missing + mutation/broad project task → read-only initial bootstrap;
    - CURRENT → reuse;
    - STALE → targeted refresh only;
    - PARTIAL/BLOCKED → expand only required evidence.
11. For an existing-project mutation, resolve Change Boundary and Change Impact (input/output/data/event/consumer/security/invariant compatibility) before editing.
12. For complete products/material product plans, resolve Q1/Q2/Q3 Quality Planning before architecture is locked.
13. If a material human decision is needed, present the smallest useful option set and stop affected work.
14. Classify intent/work mode/project state/risk.
15. Build a minimal Turn Context Manifest and load only relevant Intelligence topics/evidence.
16. Resolve the primary role and only necessary supporting roles/skills.
17. Build the Execution Profile and bounded subagent contexts; resolve `shared | worktree | sandbox` through `orchestration/EXECUTION_ISOLATION.md` before creating a writer workspace. When approved work decomposes into multiple writable tasks, freeze a Structured Task Graph and route readiness/parallel dispatch through `orchestration/DETERMINISTIC_SCHEDULER.md` instead of repeated LLM coordination.
18. For primary planning, persist the Reproducible Planning Package and complete Gate 1 / Gate 2.
19. Select model/tools; route deterministic processing to helpers.
20. Implement inside the approved Change Boundary using valid project-native conventions.
21. For UI work, run applicable V1/V2 Visual Consistency Repair.
22. Run required tests/security/quality/review. Before merge/publication of the exact integration candidate, run `orchestration/INTEGRATION_GATE.md` with the project Validation Profile and applicable Core Change Test Matrix; FAIL/BLOCKED evidence stops the candidate.
23. Compare actual diff/contract effects against declared Change Impact; unexpected material impact requires review and possibly scope reapproval.
24. Refresh only affected Intelligence/Impact Graph topics; preserve user Overrides and canonical authoritative pointers.
25. Regenerate Project Intelligence Review HTML only when initial bootstrap or material Intelligence/Override changes warrant it.
26. Complete LOCAL_COMPLETE / Production Enablement / PRODUCTION_VERIFIED rules when applicable.
27. Persist state/provenance only in permitted stores and before remote publication run Git Publish Approval.

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

Use `docs/human/SECURITY_ASSURANCE.md`.

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

For multiple approved writer tasks, the Deterministic Scheduler may dispatch them concurrently only when their canonical Change Boundaries do not overlap. Boundary locking is mechanical enforcement of this existing rule, not a relaxation of it.

## Architecture preflight

1. Load current Project Intelligence + authoritative project sources first; bootstrap/refresh only if insufficient.
2. Prefer the existing/simple structure when adequate.
3. Apply Clean Architecture dependency principles without forcing a reference folder layout.
4. Enable DDD only to the justified level: none, tactical, or strategic+tactical.
5. Use TDD for testable behavior; use characterization tests before risky legacy changes with insufficient coverage.
6. CQRS, event sourcing, microservices, saga or broad architecture rewrites require evidence and a material decision before adoption.

Preserve valid native conventions and never refactor unrelated code merely to make the repository resemble a reference architecture. Unsafe or demonstrably broken conventions are not propagated blindly.

## System self-change

When this repository itself changes, the final review must include the Documentation Impact Gate in `docs/human/MAINTENANCE.md`. A system change is incomplete if affected docs, flows, diagrams, examples, scenarios, templates/schemas, VERSION or CHANGELOG are stale.


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

For multi-task execution after planning, use `orchestration/DETERMINISTIC_SCHEDULER.md`: planning/replanning remains reasoning work, while dependency readiness, stable ordering, parallel slots and Change Boundary locks are deterministic.

For merge-candidate verification, use `orchestration/INTEGRATION_GATE.md`: exact base/head identity, project-native validation commands and candidate fingerprints are deterministic evidence and never create approval authority.


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


## Project Intelligence

Use `orchestration/PROJECT_INTELLIGENCE.md` and `orchestration/CHANGE_IMPACT.md`.

Project Intelligence is the canonical existing-project reuse layer. Prefer SOURCE_REGISTRY pointers to authoritative instructions/docs, use IMPACT_GRAPH for dependency traversal, and preserve explicit human decisions in PROJECT_OVERRIDES.

Initial bootstrap is read-only. EPHEMERAL projects may use external cache; ATTACHED projects use `.ai/intelligence/`. Do not full-rescan on every turn.

`orchestration/PROJECT_KNOWLEDGE.md` exists only for v0.8 migration compatibility.

## Quality Planning

Use `orchestration/QUALITY_PLANNING.md` for complete products and material product plans. Q1/Q2/Q3 are baselines, not rigid bundles. Feed measurable targets/budgets into architecture, implementation verification and Release Readiness.

## Local and production milestones

A complete product normally reaches `LOCAL_COMPLETE` first. If production was not requested initially, ask whether to continue. If production was requested initially, continue into Production Enablement without a redundant confirmation. `PRODUCTION_VERIFIED` requires post-deploy verification.

## Approval binding and protected operations

Before a protected publication operation, resolve the active Approval Record and verify its canonical scope fingerprint against the current candidate.

~~~text
approved proposal/scope
→ canonical fingerprint
→ current candidate / operation
→ deterministic verification
   ├─ match → runtime may allow
   └─ mismatch / missing → APPROVAL_STALE → stop
~~~

Do not infer machine-bound approval from vague context. Runtime guards are enforcement transport; architectural/security reasoning remains in orchestration/review.

## Checkpoint and resume

Use `orchestration/RUN_RESUME.md` for substantial workflows that can span turns/sessions.

Checkpoint after material phase transitions, approvals, implementation completion, test/review completion or blockers. Resume never means blindly continue: compare stored project revision/current evidence first and route stale state through the applicable freshness/impact/review checks.

Do not serialize full conversation or private reasoning into run state.
