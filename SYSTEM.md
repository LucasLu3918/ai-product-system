# System Router

## Main pipeline

```text
User Request
→ System Update Preflight
→ Workspace Bootstrap
→ Task Preflight
→ Primary Planning Detection
→ Human decision only when materially required
→ Intent + Work Mode
→ Project State
→ Risk / Assurance Classification
→ Instruction Discovery (existing projects)
→ Minimal Context Manifest
→ Role + Skill Resolution
→ Execution Profile / bounded Subagents when useful
→ Model + Tool Routing
→ Execute
→ Independent Review
→ Artifact / Quality Gate
→ Persist State + System Provenance
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
4. broader project standards and root `AGENTS.md`;
5. project-local skills and references;
6. global AI Product System skills;
7. agent inference.

Skills provide expertise, not governance authority.

If the current user instruction materially conflicts with an existing project rule, contract or architecture decision, surface the conflict and recommendation before implementation. After the user decides, follow that decision inside its approved scope.

A one-task override is temporary unless the user explicitly approves changing permanent project policy. Permanent changes should update the appropriate project record (`AGENTS.md`, ADR, contract or standard).

## Unknown classification

- `blocking` — must be decided before affected work continues;
- `important` — collect before its decision point;
- `deferrable` — record and continue;
- `safe_default` — may propose a clearly marked default.

## Capability gap

If existing roles/skills cannot reliably perform the task, stop affected work. Propose the smallest extension in this order:

```text
reuse existing skill
→ create a narrow skill
→ create a capability grouping
→ create a new role only when responsibility/authority truly differs
```

Permanent or high-authority additions require human approval.

## Agent/model routing

Selected skills describe reasoning/coding/reliability needs; they never hard-code a provider model. Build one Execution Profile for the primary task and one for each bounded subagent. Resolve model tier independently using business impact, technical complexity, risk, privacy, context and expected total cost.

Subagents receive only the context required for their objective. Do not delegate vague work or duplicate the full primary context. Escalate tier/context when evidence shows the assignment is insufficient; de-escalate after the difficult portion is complete. See `orchestration/MODEL_ROUTING.md`.

## System-change maintenance

When modifying this AI Product System itself, first use the System Self-Improvement Protocol; Core Change Approval normally applies before implementation, and the Git Publish Approval Gate applies before remote publication. Also pass the Documentation Impact Gate in `docs/MAINTENANCE.md`. Assess related documentation, flows, Mermaid architecture diagrams, examples, scenarios, schemas/templates, VERSION and CHANGELOG. Update affected artifacts; explicitly treat unaffected artifacts as N/A rather than editing them unnecessarily.

## Completion

A task is complete only when its acceptance criteria, required review, required artifacts and persisted workspace state are satisfied. Producing code or prose alone is not completion.

For a primary planning task, completion of the Planning Package means the persisted plan is ready for Gate 1 review; it does **not** imply implementation approval.

For SAL 3–4 affected work, completion also requires the applicable Security Review evidence and Security Release Gate.
