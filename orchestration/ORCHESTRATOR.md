# Orchestrator

Local publication validation uses the shared Runtime Context resolver so the selected interpreter and its required capabilities are consistent with the Integration Gate.

Internal module extraction preserves the established CLI/import facade and requires focused identity plus subsystem lifecycle evidence; it does not change publication approval or merge authority.

Before publication, diagnose configuration selection separately from authentication and connectivity. Reuse a verified Python 3.12 environment; preview documentation closure before edits, run affected checks during development and one complete local Gate after the candidate is fixed. Installed OpenAPI tools operate on an explicit product root; real-product acceptance requires that product service and native tests.

The orchestrator coordinates work. It is not a super-role and cannot override governance or accepted user/project decisions.

## Minimal algorithm

When a task requires client generation, resolve the canonical OpenAPI contract, local tool/version, ownership and native verification first. The adapter preview does not execute; invoke its local `--execute` path only on the user's explicit instruction. The Gate remains inspection-only.

發布前先執行快速 documentation-impact gate；CI 再依序執行強制候選秘密掃描與 repository preflight，才安裝完整驗證相依套件並進入 Integration Gate。候選的每筆 commit message 與 author/committer identity 均需符合公開發布政策。

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
17. Build the Execution Profile and bounded subagent contexts; resolve `shared | worktree | sandbox` through `orchestration/EXECUTION_ISOLATION.md` before creating a writer workspace. When policy requests automatic resolution, include risk, minimum isolation and data class; high/critical or explicitly untrusted execution requires a verified sandbox and may not downgrade. When parallel worktrees need local servers, carry declared Task Graph `isolation.runtime.ports` into the same Execution Isolation lifecycle and inject the returned runtime environment instead of hard-coding shared ports. When material runtime/tool/resource access is needed, bind a `orchestration/RESOURCE_AUTHORIZATION.md` profile and evaluate the declared resource + operation before execution; default is DENY and authorization evidence never grants protected publication/Human authority. When approved work decomposes into multiple writable tasks, freeze a Structured Task Graph and route readiness/parallel dispatch through `orchestration/DETERMINISTIC_SCHEDULER.md` instead of repeated LLM coordination.
18. For primary planning, persist the Reproducible Planning Package and complete Gate 1 / Gate 2.
19. Select model/tools; route deterministic processing to helpers.
20. Implement inside the approved Change Boundary using valid project-native conventions.
21. For UI work, run applicable V1/V2 Visual Consistency Repair.
22. Run required tests/security/quality/review. Before merge/publication of the exact integration candidate, run the mandatory credential-free secret scan over its final tree and `base..head` history, then run `orchestration/INTEGRATION_GATE.md` with the project Validation Profile and applicable Core Change Test Matrix; FAIL/BLOCKED evidence stops the candidate.

The validation workflow keeps Gate and Repository Health evidence in the CI runner temporary directory until checks finish, then uploads those files as artifacts. This preserves exact-revision evidence for the repository validator.

Both validation and docs-site workflows use Node 24 with `npm ci` and the repository lockfile; setup-node caches against `package-lock.json`. Publication Preflight reports the repository's enabled merge methods and distinguishes GitHub API network/access failures without changing the Human-controlled merge route.

Protected `main` publication must wait for the exact PR candidate's required `repository` aggregate to pass.

For a candidate built in a shared workspace, first snapshot the intended head and validate it in a clean worktree. Unrelated dirty changes must remain outside the candidate; a changed-files hash or Matrix computed before the final commit is invalid after scope changes.
23. Compare actual diff/contract effects against declared Change Impact; unexpected material impact requires review and possibly scope reapproval.
24. Refresh only affected Intelligence/Impact Graph topics; preserve user Overrides and canonical authoritative pointers.
25. Regenerate Project Intelligence Review HTML only when initial bootstrap or material Intelligence/Override changes warrant it.
26. Complete LOCAL_COMPLETE / Production Enablement / PRODUCTION_VERIFIED rules when applicable.
27. Persist state/provenance only in permitted stores and before remote publication run Git Publish Approval.

## System Update Preflight


Resolve bounded Context before implementation: prove selected-path relevance, allocate Recall from the shared Core/Recall/temporal budget, preserve canonical source pointers on index failure, and apply runtime content safety before emitting derived or retrieved text.

The orchestrator must not implement project mutations using an unverified stale local system.

Use `aips preflight <project>`, which:

- requires the system repo to be clean/on `main`;
- fetches `origin/main` and uses only fast-forward pulls;
- blocks divergent history instead of auto merging/rebasing;
- requires explicit review for a MAJOR version change;
- re-executes the updated CLI, validates the system and records `.ai/SYSTEM.yaml`.

It updates the AI Product System only. Target-project source updates remain a separate user/project decision.

Preflight does not attach an EPHEMERAL project. Only `aips attach` enables persistent `.ai/` state.
Publication Preflight lifecycle evidence isolates optional Python module probes from loopback/browser blocker checks, keeping host capability failures distinct from product validation results.

## Reproducible Planning Package

Load `orchestration/PLANNING_PACKAGE.md` when the request defines the authoritative product/project blueprint.

The planning package must be persisted outside the chat and sufficiently complete that another competent AI agent or human team can reproduce substantially the same intended product without hidden conversation context.

Do not claim planning completion if applicable product, UX, visual/key-visual, API/contract, architecture, testing/delivery or decision records are missing.

Implementation requires both Planning Package approval (Gate 1) and Implementation Readiness approval (Gate 2).

## Risk-Proportional Security Assurance

Use `docs/human/SECURITY_ASSURANCE.md`.

For planning, establish Product Baseline SAL and Reliability Impact. For every material change, classify Change Security Impact from the actual Change Boundary and protected assets touched.

Critical risk floors override average scoring. High-value financial/stored-value boundaries are security boundaries, including payments, refunds, settlement, balances, points/credits/vouchers/coupons with economic value, redemption, transfer and withdrawal.

At runtime, the action envelope carries destination, data classes, protected assets, Change Boundary and effective SAL into deterministic policy evaluation. SAL3/4 external egress requires exact approval plus independently verified sandbox networking; hooks alone do not cover indirect sockets.

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


Resolve the managed AIPS interpreter through `orchestration/RUNTIME_CONTEXT.md`: the CLI floor is Python >=3.12, explicit `AIPS_PYTHON` selection is checked against it, and validation compatibility claims come from the canonical system-facts matrix.

For publication-bound Core/Large work, load the final candidate Change Impact and Core Matrix evidence after implementation, recheck documentation closure and candidate identity, then run the exact-candidate Integration Gate before presenting the Git Publish Proposal. Candidate evidence does not authorize merge, tag creation or repository policy writes.

Turn Context classifies write intent with explicit intent overrides and respects the target file's scoped runtime instructions. The compact YAML view is the default; callers that need the complete manifest can request `--full` or JSON.

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

When parallel Task Graph execution is enabled, claim only scheduler-dispatched work inside its active AIPS worktree. Preserve the task lease and base revision across recovery; reconcile the actual Git diff before marking completion. Resource authorization remains advisory until a native write guard is verified.

Concurrent Run State and telemetry producers serialize writes through one append-only event stream. A failed optional observation degrades its evidence and never fabricates completion or changes the workflow's primary gate.

The Parallel Run Dashboard projects checkpoint and event facts for observation only. Resume continues to use canonical Run State and existing authority checks.

Use `orchestration/RUN_RESUME.md` for substantial workflows that can span turns/sessions.

Checkpoint after material phase transitions, approvals, implementation completion, test/review completion or blockers. Resume never means blindly continue: compare stored project revision/current evidence first and route stale state through the applicable freshness/impact/review checks.

Do not serialize full conversation or private reasoning into run state.

## v0.27 deterministic hardening

When emitting a Structured Task Graph, treat tasks as writable by default. Set `read_only: true` only when the task has no writes; otherwise declare a non-empty Change Boundary.

For Evolution Radar semantic work, prefer the generated provider-neutral handoff when no scheduled provider is available rather than inventing a recommendation. For PR integration, stale target-base evidence must route back to refresh/revalidation rather than proceeding with an old PASS.

## Change-class handoff to Integration Gate

After merge, post-merge checkout and installed-version reconciliation run through the established publication CLI facade and retain fast-forward-only safeguards.

Large/Core work remains blocked from remote publication until documentation closure, the candidate-bound test matrix, mandatory secret scan and exact Integration Gate pass; publication approval names the final files, commit plan and target branch.

Installed product CLI acceptance keeps the required AIPS runtime dependencies separate from optional OpenAPI validator packages. Require an explicit setup command before contract validation; exercise the installed entrypoint from a product root containing no AIPS scripts, then retain platform installation and exact-candidate Gates.

Resolve publication target from explicit --project-root or the active AIPS checkout, and disclose source/target/Python selection. Reuse prepared dependencies for focused checks, then run one exact-candidate local Gate. Dependency workflow updates carry their required documentation closure and candidate-bound Matrix; PR and main CI retain independent full validation.

For a fixed Core candidate, finish the documentation closure and bind the reviewed Matrix before the single complete local Gate run. The local entrypoint must resolve Python 3.12, OpenAPI validation modules and any Node/VitePress docs-build requirements before beginning expensive lifecycle work.

The CI changed-path plan controls only optional toolchain installation. It does not reduce the candidate's required validations or change the approved change class; unknown path or plan evidence fails closed to full provisioning.

The exact-candidate runner also gives child processes the selected Python directory first in `PATH`; a direct script invocation has the same nested interpreter selection as the prepared local wrapper.

Repository validation may remove duplicate syntax-compilation and lifecycle subprocesses only when each unique evidence lifecycle still has one owning invocation and the complete Integration Gate remains mandatory.

When an OpenAPI contract affects implementation, include offline validation, canonical-baseline compatibility review and project-native contract tests in the quality handoff. `UNKNOWN`, unavailable, stale or failed evidence blocks only the dependent work and remains explicit for Human review.

When a project opts into Phase 3 Implementation Resolution enforcement, bind the applicable changed paths to an exact Profile fingerprint, declared ownership, selected language Profile, generated source/output hashes and current-run quality/contract evidence. Run project-native command collection explicitly in the trusted local/CI context; the Integration Gate verifies those artifacts without executing candidate Profile commands. Start with report mode to confirm applicability, then enable enforce mode for the approved path scope.

Publication-readiness changes include the selected checkout, local documentation/build checks, Gate environment preflight and initial PR classification label in the proposal and exact-candidate evidence.

The publication plan records the change-class label for the initial PR create request. An invalid GitHub CLI login is `AUTH_REQUIRED`; network or sandbox connectivity failure is `NETWORK_UNAVAILABLE`. Recovery steps differ, and credential or raw CLI output is never included.

GitHub may emit a separate `labeled` event even when the label is supplied during PR creation. Group validation runs by PR number. Candidate changes and Core/Large classification-label changes may supersede an in-progress run; unrelated label events skip the expensive Gate without cancelling active candidate validation. The required aggregate reports a successful no-op only when that explicit skipped-label case also has matching successful full Janitor evidence for the same PR/head/base/change class. Missing, stale, failed or unfinished evidence blocks; the aggregate uses actions-read metadata without downloading artifacts.

Before commit, use the publication preview to inspect the complete working-tree file set, recursive documentation requirements and matrix hash. Synchronize only the selected checkout's canonical matrix binding after the scope is complete, then review the invalidated matrix evidence before Gate execution. Use the installed CLI against an explicit target for post-merge reconciliation when the target checkout may contain an older script.

Treat Matrix `NEEDS_WORK` from a DRAFT status, remaining blockers, unreconciled diff or stale binding as an implementation task. Clear it before running the exact-candidate Gate; a preview readiness result never authorizes publication.

Eval-as-CI is a Core Change capability. The Orchestrator must route it through the Core Change Test Matrix, reuse existing Agent Eval / Scenario Conformance contracts, start trajectory evaluation in shadow mode, and preserve Human authority over Git Publish.

When a repository PR represents an already approved Large/Core Change, preserve that classification into deterministic CI with `aips:large-change` or `aips:core-change`. Integration Gate uses the change class only to select evidence requirements; it does not create semantic classification or approval authority.

For a fixed local candidate, schedule one complete Publication Preflight after focused development checks; it includes repository validation. PR and main retain separate complete CI Gates, with an optional timing artifact to guide later performance work. Timing evidence grants no merge or publication authority.

Before requesting Git publication approval, run the shared publication plan/preflight, resolve protected-branch routing, and present the exact candidate after diff-aware documentation checks pass. After merge, fast-forward a clean local `main` only when it is an ancestor of the fetched target, preserving a backup branch first. If histories diverged, reconcile only equivalent trees with a backup; otherwise stop for Human review.

When Core Change Testing requires independent review, schedule a separate read-only `INDEPENDENT_REVIEW` task over the bounded packet and exact candidate. The Integration Gate must consume evidence from a trusted runtime attestation verifier; absent or stale attestation blocks required review rather than falling back to self-check.
## Runtime Content Safety Boundary

After merge, use the updated checkout CLI `publish post-merge --fetch --sync-installed --apply` to verify target main and the registered installed system. Installed synchronization refuses dirty/wrong-branch, different remote, stale target and divergent history; it never resets the installation or grants publication authority.

The orchestrator routes AIPS-owned persistence through `safe_emit` and keeps content safety separate from publish authorization. Untrusted external content carries provenance and cannot grant protected tool authority.

`bin/aips` is the public thin launcher: it resolves the repository root and forwards arguments to `scripts/aips_cli.sh`. Keep command dispatch, installed-link behavior, exit status, and user-visible output compatible while implementation modules are extracted incrementally.
