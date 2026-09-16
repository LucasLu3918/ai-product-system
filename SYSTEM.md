# System Router

## Main pipeline

```text
User Request
→ System Update Preflight
→ Workspace Bootstrap
→ Task Preflight / Requirement Readiness
→ External Context Resolution when needed
→ Primary Planning / Full Product Delivery Detection
→ Human decision only when materially required
→ Intent + Work Mode
→ Project State
→ Existing Project Knowledge Index / targeted discovery when relevant
→ Risk / Assurance + Quality Classification
→ Creative / Brand / Capability Routing when relevant
→ Instruction Discovery (existing projects)
→ Minimal Context Manifest
→ Role + Skill Resolution
→ Execution Profile / bounded Subagents when useful
→ Model + Tool Routing
→ Deterministic Automation when suitable
→ Execute
→ Independent or Multi-Perspective Review
→ Author Fix / Targeted Re-review when needed
→ Artifact / Quality Gate
→ LOCAL_COMPLETE for complete products
→ Production Enablement only when requested/approved
→ Release Readiness + PRODUCTION_VERIFIED when production is in scope
→ Persist State + System Provenance / Knowledge refresh
```

## System Update Preflight

Before any **mutating implementation session**, run:

```bash
aips preflight <target-project-path>
```

The preflight updates the **AI Product System repository**, not the target project's Git repository.

Rules:

- system repo must be clean and on `main`;
- fetch `origin/main`;
- update only with `git pull --ff-only`;
- never auto merge/rebase divergent system history;
- a MAJOR version change requires explicit review and `--allow-major`;
- after update, re-exec the updated CLI and validate the repository;
- initialize the project's minimum `.ai/` workspace when missing;
- record exact system version + commit in `.ai/SYSTEM.yaml`.

If update cannot be completed safely, stop implementation and surface the reason.

Read-only explanation/research that does not mutate a project does not need to modify local state solely to satisfy this rule.

## System Self-Improvement

When the request changes this AI Product System itself, load `orchestration/SYSTEM_SELF_IMPROVEMENT.md`.

Before implementation:

1. evaluate whether the suggestion is appropriate;
2. identify overlap/redundancy and simpler alternatives;
3. propose additional optimizations when they materially improve the design;
4. assess backward compatibility, context/token cost, role/gate proliferation and affected scenarios;
5. check semantic Constitution impact;
6. present the System Improvement Review and wait for user direction confirmation.

If the proposal touches the Constitution semantically, stop and run the Constitutional Change Gate. Constitutional modification requires a second explicit approval after affected Articles and risks are explained.

Prefer Skill/Template → Workflow/Work Mode → System/Orchestration → Governance → Constitution.

## Core Change Approval Gate

Before implementing a large or core change, first present a Change Proposal and stop for explicit user approval.

Trigger by semantic impact, not file count alone. Typical triggers include:

- core governance/orchestrator/runtime behavior;
- public API/contract or data model changes;
- authentication/authorization/security boundaries;
- financial/stored-value/high-value business logic;
- cross-domain/component changes;
- broad refactors, framework/runtime/database migrations;
- breaking changes, production topology or other hard-to-reverse changes.

The proposal must state purpose, in-scope/out-of-scope areas, expected files/modules, architecture/API/data/security/migration impact, test/documentation impact, risks, recommendation and proposed implementation order.

If approved scope materially expands during execution, stop and obtain approval again.

## Git Publish Approval Gate

Before any remote Git publication that changes a branch/ref or is intended for PR/release:

1. show the complete changed-file list;
2. summarize the change by logical feature;
3. show validation/review evidence and unresolved items;
4. propose atomic commits grouped by logical capability, not by file;
5. show target remote/branch and planned PR/release action;
6. stop for explicit user approval.

Local preparation/commit objects may be created before this gate. Do not update remote refs or publish a PR/release until approval. If the file list, commit plan, target or material scope changes after approval, re-run this gate.

## Task Preflight

Before implementation, check only what can materially change the outcome:

- blocking unknowns;
- a clearly better approach or prerequisite;
- scope, contract, architecture, security, cost or destructive risk;
- missing role/capability/skill expertise;
- instructions that materially conflict;
- security assurance or reliability impact that materially changes review/gating.

If the request is not implementation-ready, load `orchestration/REQUIREMENT_CLARIFICATION.md`. Use READY / NEEDS_CLARIFICATION / BLOCKED, ask only materially blocking questions, offer concrete options/defaults, and do not begin broad implementation until the goal is READY.

If a material choice exists, present a concise option set, recommend one, and stop affected work until the user decides. Batch non-blocking questions instead of interrupting repeatedly.

Never invent project facts. When expertise can reduce user burden, propose a professional solution rather than asking the user to design it for the agent.

## Primary Planning Detection

If the request creates or materially revises the **primary product/project definition** that future implementers will rely on, use the Reproducible Planning Package protocol in `orchestration/PLANNING_PACKAGE.md`.

Examples include a new product, major redesign, platform plan, broad architecture/product plan, or other authoritative blueprint.

For these tasks:

1. resolve the target workspace before creating the authoritative plan;
2. if the user did not specify a workspace, ask where to persist it;
3. persist a complete Planning Package;
4. run cross-document/cross-role consistency review;
5. **Gate 1:** wait for user approval/revision of the persisted plan;
6. after Gate 1 approval, derive Initial Implementation Items + Recommended Implementation Flow;
7. **Gate 2:** ask whether to proceed and wait for explicit implementation approval;
8. only then begin implementation.

Simple bugfixes, isolated API changes, narrow research and local refactors do not require a full product Planning Package.

## End-to-end product delivery

When the user requests a complete product, load `orchestration/PRODUCT_DELIVERY.md` and `orchestration/QUALITY_PLANNING.md`.

Key rules:
- create one discoverable Product Workspace and root `PRODUCT.yaml`;
- treat frontend/backend/worker/etc. as Deployment Units; do not force separate Git repositories;
- default to a monorepo unless ownership, permission, release cadence, scale or service boundaries justify multi-repo;
- persist a Q1/Q2/Q3 Quality Profile with applicable measurable targets;
- provide a reproducible local start/test path;
- implement applicable structured logging/health/metrics/tracing/audit hooks before production vendor selection;
- run applicable static/unit/integration/contract/E2E/security/performance/usability/reliability/build checks;
- treat `LOCAL_COMPLETE` as the default complete-product milestone;
- if production was not explicitly requested, ask whether to continue only after `LOCAL_COMPLETE`;
- use staging by default for material production systems;
- consolidate production conditions in `orchestration/RELEASE_READINESS.md`;
- production automation never bypasses risk-proportional approval, secret protection, migration/recovery or security rules;
- production Done includes post-deploy health/smoke/observability verification.

## Project knowledge

For existing projects, use `orchestration/PROJECT_KNOWLEDGE.md`.

Load authoritative project instructions/docs first. Then read `.ai/knowledge/KNOWLEDGE_INDEX.yaml` when present and load only topics relevant to the current task.

If reusable project knowledge is missing, use targeted Project Knowledge Discovery rather than scanning every file. Persist only expensive-to-rediscover, stable knowledge not already covered by AGENTS/ADR/contracts/official docs. Prefer pointers over duplicated content.

Project Knowledge has no governance authority and never replaces active security/reliability verification.

## Quality planning

For complete products/material product plans, use `orchestration/QUALITY_PLANNING.md`.

Use Q1/Q2/Q3 as adjustable baselines across Performance, Security, Usability, Reliability, Maintainability, Resource/Cost and Delivery Time. Convert vague expectations into targets/budgets + verification evidence where practical. Use range + confidence for time/cost estimates.

## Project state

- `greenfield` — new product/system;
- `brownfield` — existing product/repository;
- `unknown` — inspect before deciding.

Project state is not a work mode.

## Security / Reliability Assurance

For product planning and for changes that may affect protected assets, resolve a Risk Profile using `orchestration/schemas/risk-profile.yaml` and `docs/SECURITY_ASSURANCE.md`.

Keep separate:

- Product Baseline SAL (Security Assurance Level);
- Change Security Impact;
- Effective SAL for the affected Change Boundary;
- Reliability Impact.

Do not average away critical dimensions. Payments, stored value, economically redeemable points/credits/vouchers/coupons and similar financial integrity boundaries impose a SAL 4 floor when affected.

A high-risk product does not force every cosmetic change through SAL 4. Reclassify based on the actual Change Boundary and protected assets touched.

SAL 3–4 affected work activates the required Security Engineer review, evidence and release gate. SAL 4 unresolved High/Critical findings block release.

Security Assurance informs Model Routing but is not the same as Model Tier.

## Work mode

Choose the smallest mode matching the user intent. See `work-modes/README.md`.

## Creative and Brand routing

For visual or brand work:
- load an approved Brand Profile first when one exists;
- prioritize user-provided assets and references;
- use `orchestration/CREATIVE_DIRECTION.md` when direction is vague or trend-sensitive;
- use `orchestration/BRAND_SYSTEM.md` for reusable brand creation/refinement;
- lock the approved direction before broad implementation when mismatch would be costly;
- run `visual-quality-review` for material visual deliverables.

Styles under `references/creative/styles/` are reference data, not separate skills.

## External context

When a task depends on a user-provided external URL/reference, load `orchestration/EXTERNAL_CONTEXT_RESOLUTION.md`.

Prefer the exact connected source. If a connector/MCP/app exists but needs authorization, guide authorization and preserve the pending task so work resumes afterward. Only ask the user to paste/upload content after supported connection/public-access fallbacks are exhausted.

## Visual implementation polish

When an existing UI is directionally correct but visually awkward/inconsistent, use `orchestration/VISUAL_POLISH.md` instead of restarting Creative Direction.

Defaults:
- Preserve Before Redesign;
- Consistency First;
- whole-project vague cleanup requests route to V2 Product Consistency Sweep;
- use/create `docs/design/PROJECT_VISUAL_PROFILE.yaml` when reusable visual knowledge is valuable;
- classify outlier vs valid variant/exception before fixing;
- map material findings to DOM/component/computed style/token when tooling permits;
- shared token/component fixes before page-specific patches;
- rendered before/after + responsive/state verification before PASS when the UI can be run.

## Multi-perspective review

For large/core/high-risk changes where one reviewer is insufficient, load `orchestration/MULTI_REVIEW.md`.

Resolve only relevant existing reviewer roles. Reviews are bounded/read-only by default, findings are normalized/deduplicated, the original Author performs fixes, and re-review is targeted unless the Change Boundary expanded.

After material review, extract run/project/system-capability lessons. Permanent system capability changes require user-approved System Self-Improvement; never silently train/modify Roles or Skills from one review.

## Progressive context

```text
Bootloader
→ Work Mode
→ Role index
→ Selected Role
→ Skill index
→ Selected leaf skills
→ Relevant project context
→ Context Expansion only when evidence shows a gap
```

Do not preload unrelated roles, skills, references or repository files.

## Existing-project instruction precedence

System guardrails are never overridden by project files. Inside the project execution layer, resolve applicable instructions in this order:

1. current explicit user instruction / accepted current user decision;
2. nearest applicable scoped `AGENTS.md` (nearest scope wins over broader scope);
3. accepted project decisions / ADRs and authoritative contracts;
4. broader official project standards/documentation and root `AGENTS.md`;
5. current Project Knowledge cache/index (derived knowledge only, never governance);
6. project-local skills and references;
7. global AI Product System skills;
8. agent inference.

Skills provide expertise, not governance authority.

If the current user instruction materially conflicts with an existing project rule, contract or architecture decision, surface the conflict and recommendation before implementation. After the user decides, follow that decision inside its approved scope.

A one-task override is temporary unless the user explicitly approves changing permanent project policy. Permanent changes should update the appropriate project record (`AGENTS.md`, ADR, contract or standard).

## Unknown classification

- `blocking` — must be decided before affected work continues;
- `important` — collect before its decision point;
- `deferrable` — record and continue;
- `safe_default` — may propose a clearly marked default.

## Capability gap

Before creating or expanding a Role, Capability or Skill, load `orchestration/CAPABILITY_INCUBATION.md`.

Required order:

```text
Reuse existing
→ Extend existing
→ New narrow Skill
→ New Capability only when routing benefits
→ New Role only for distinct responsibility + authority + review obligation
```

Search the current indexes first and record overlap. Permanent or high-authority additions require human approval.

## Deterministic automation

Before spending model reasoning on repeatable data processing, check `orchestration/DETERMINISTIC_AUTOMATION.md`.

Prefer an existing tool or a small Shell/Python helper when the step is rule-based and verifiable. Return structured JSON/YAML summaries and keep large raw evidence outside model context until needed.

Do not automate subjective/complex reasoning solely to reduce tokens.

## Agent/model routing

Selected skills describe reasoning/coding/reliability needs; they never hard-code a provider model. Build one Execution Profile for the primary task and one for each bounded subagent. Resolve model tier independently using business impact, technical complexity, risk, privacy, context and expected total cost.

Subagents receive only the context required for their objective. Do not delegate vague work or duplicate the full primary context. Escalate tier/context when evidence shows the assignment is insufficient; de-escalate after the difficult portion is complete. See `orchestration/MODEL_ROUTING.md`.

## System-change maintenance

When modifying this AI Product System itself, first use the System Self-Improvement Protocol; Core Change Approval normally applies before implementation, and the Git Publish Approval Gate applies before remote publication. Also pass the Documentation Impact Gate in `docs/MAINTENANCE.md`. Assess related documentation, flows, Mermaid architecture diagrams, examples, scenarios, schemas/templates, VERSION and CHANGELOG. Update affected artifacts; explicitly treat unaffected artifacts as N/A rather than editing them unnecessarily.

## Completion

A task is complete only when its acceptance criteria, required review, required artifacts and persisted workspace state are satisfied. Producing code or prose alone is not completion.

For a primary planning task, completion of the Planning Package means the persisted plan is ready for Gate 1 review; it does **not** imply implementation approval.

For SAL 3–4 affected work, completion also requires the applicable Security Review evidence and Security Release Gate.

For a complete product, local completion is explicitly `LOCAL_COMPLETE`. If production was not requested, this can be the completed delivery state after the user declines/defer Production Enablement.

When production delivery is part of the approved scope, completion requires Release Readiness, applicable staging verification, production promotion, post-deploy verification and persisted evidence before `PRODUCTION_VERIFIED`. Code generation alone is not completion.
