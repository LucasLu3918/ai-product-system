# System Router

## Main pipeline

```text
Agent Session / User Request
→ Turn-Aware Harness Context Resolution when installed
→ System Update Preflight for mutation
→ Canonical Repository / Workspace Identity Resolution
→ Project Mode + Intelligence Store Resolution (EPHEMERAL external cache / ATTACHED local)
→ Task Preflight / Requirement Readiness
→ External Context Resolution when needed
→ Primary Planning / Full Product Delivery Detection
→ Human decision only when materially required
→ Intent + Work Mode
→ Project State
→ Runtime-native + Project Instruction Resolution
→ Project Intelligence readiness/freshness
→ Initial read-only bootstrap or targeted refresh when required
→ Change Impact Guard before existing-project mutation
→ Risk / Assurance + Quality Classification
→ Secret / Credential Handling when credentials are in scope
→ Creative / Brand / Capability Routing when relevant
→ Instruction Discovery (existing projects)
→ Minimal Context Manifest
→ Role + Skill Resolution
→ Execution Profile / bounded Subagents when useful
→ Execution Isolation Resolution (shared / worktree / verified sandbox)
→ Runtime Resource Lease Resolution when parallel tasks need host ports
→ Model + Tool Routing
→ Deterministic Automation when suitable
→ Execute
→ Impact-derived Tests for Large/Core changes
→ Independent or Multi-Perspective Review
→ Author Fix / Targeted Re-review when needed
→ Artifact / Quality Gate
→ LOCAL_COMPLETE for complete products
→ Production Enablement only when requested/approved
→ Release Readiness + PRODUCTION_VERIFIED when production is in scope
→ Persist State + System Provenance / targeted Intelligence refresh
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
- if the project is ATTACHED, record exact system version + commit in `.ai/SYSTEM.yaml`;
- if the project is not attached, remain EPHEMERAL and do **not** create `.ai/` automatically.

If update cannot be completed safely, stop implementation and surface the reason.

Read-only explanation/research that does not mutate a project does not need to modify local state solely to satisfy this rule.

## Global Agent Harness

Use `harness/HARNESS_PROTOCOL.md`, `orchestration/TURN_HARNESS.md` and `orchestration/HARNESS_RESOLUTION.md`.

The Harness is available after installation, but full AIPS orchestration activates only for applicable product/project/software work.

Rules:

- resolve a compact current Turn Context rather than preloading the AIPS repository;
- preserve runtime-native and project-native instructions;
- report runtime capability accurately: TURN_NATIVE / CONTEXT_ALWAYS / SESSION_ONLY / MANUAL / UNSUPPORTED;
- use reversible managed composition when a shared runtime instruction/config surface is required;
- every turn may resolve context, but repository-wide discovery is not repeated every turn.

Project modes:

~~~text
No .ai/
→ EPHEMERAL
→ no project-local AIPS state
→ reusable Intelligence may live in ~/.config/aips/projects/<project-id>/

Explicit aips attach
→ ATTACHED
→ .ai/intelligence/ + normal persistent workspace
~~~

EPHEMERAL remains non-invasive to project source.

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

## Project Identity

Use `orchestration/PROJECT_IDENTITY.md` for canonical repository/workspace identity.

- repository-wide coordination uses `repository_id`;
- workspace-scoped Intelligence / Run State uses `workspace_id`;
- `project_id` remains a compatibility alias for `workspace_id`;
- Run Resume fingerprints product workspace state and excludes AIPS-owned `.ai/` state;
- different worktrees of one repository share repository-level Single Writer coordination.

## Project Intelligence

For existing projects, use `orchestration/PROJECT_INTELLIGENCE.md` and `orchestration/CHANGE_IMPACT.md`.

Project Intelligence replaces Project Knowledge as the canonical reusable understanding layer.

Rules:

- register authoritative runtime/project sources in SOURCE_REGISTRY instead of copying them;
- initialize existing-project Intelligence with read-only breadth-first discovery;
- use External Project Intelligence Cache in EPHEMERAL mode and `.ai/intelligence/` in ATTACHED mode;
- keep readiness, human review and freshness as separate states;
- use branch/worktree/dirty-path-aware targeted refresh;
- keep Impact Graph machine-readable;
- generate HTML deterministically as a review view only;
- store human additions/exceptions/exclusions in PROJECT_OVERRIDES.yaml;
- before mutation, create/resolve Change Impact and compare actual diff against declared impact;
- Project Intelligence never replaces current security/reliability verification.

Existing `.ai/knowledge/` is migration input only; new reusable conclusions are written to Project Intelligence.

## Quality planning

For complete products/material product plans, use `orchestration/QUALITY_PLANNING.md`.

Use Q1/Q2/Q3 as adjustable baselines across Performance, Security, Usability, Reliability, Maintainability, Resource/Cost and Delivery Time. Convert vague expectations into targets/budgets + verification evidence where practical. Use range + confidence for time/cost estimates.

## Project state

- `greenfield` — new product/system;
- `brownfield` — existing product/repository;
- `unknown` — inspect before deciding.

Project state is not a work mode.

## Security / Reliability Assurance

For product planning and for changes that may affect protected assets, resolve a Risk Profile using `orchestration/schemas/risk-profile.yaml` and `docs/human/SECURITY_ASSURANCE.md`.

Keep separate:

- Product Baseline SAL (Security Assurance Level);
- Change Security Impact;
- Effective SAL for the affected Change Boundary;
- Reliability Impact.

Do not average away critical dimensions. Payments, stored value, economically redeemable points/credits/vouchers/coupons and similar financial integrity boundaries impose a SAL 4 floor when affected.

A high-risk product does not force every cosmetic change through SAL 4. Reclassify based on the actual Change Boundary and protected assets touched.

SAL 3–4 affected work activates the required Security Engineer review, evidence and release gate. SAL 4 unresolved High/Critical findings block release.

Security Assurance informs Model Routing but is not the same as Model Tier.

### Secret / Credential Handling

When implementation, testing, deployment, API integration or debugging requires credentials, load orchestration/SECRET_HANDLING.md.

Rules:

- secrets are runtime inputs/references, never source code, prompts, Project Intelligence, generated HTML, fixtures, logs or review artifacts;
- prefer managed/workload identity → approved secret manager → protected CI/CD store → OS/runtime credential store → runtime environment;
- do not ask the user to paste a secret into chat when a secure provider/connector/store can supply it;
- authenticated integration begins only after secure acquisition, least privilege and redaction are verified;
- unavailable credentials make the authenticated operation BLOCKED, never hard-coded;
- Security Review uses deterministic secret scanning where practical and never repeats a discovered secret value.

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

External platform/safety constraints and AIPS constitutional/governance rules remain mandatory. Preserve runtime-native instructions rather than overwriting them.

Inside the project execution layer, resolve applicable instructions approximately as:

1. current explicit user instruction / accepted current user decision;
2. runtime-native instructions according to their native scope/precedence;
3. nearest applicable scoped project instructions such as `AGENTS.md`;
4. accepted project decisions / ADRs and authoritative contracts;
5. broader official project standards/documentation and root instructions;
6. approved Project Overrides + current Project Intelligence (derived, non-governing);
7. project-local skills and references;
8. global AI Product System skills;
9. agent inference.

When the Agent runtime mandates a different precedence, follow the runtime/platform rule and surface material conflicts rather than pretending AIPS can override it.

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

Search the current indexes and relevant existing Skill bodies first and record overlap. Permanent or high-authority additions require human approval.

For a new Skill, complete the New Skill Admission contract in orchestration/CAPABILITY_INCUBATION.md: narrow responsibility, positive/non-triggers, inputs/outputs/boundaries, context cost/model needs, cross-project reuse rationale, routing scenarios, unique ID/path, and secret/private-config check. Project-specific convention or one-off automation belongs in Project Intelligence or project/run tooling instead.

## Core Change Testing

For every Large/Core Change, load orchestration/CORE_CHANGE_TESTING.md.

Derive required tests from the final Change Boundary. Every materially affected boundary must have applicable evidence or a concrete N/A reason. Recompute the matrix if scope expands. Failing required tests, missing affected-boundary evidence, or untested material diff blocks completion/release.

## Deterministic automation

Before spending model reasoning on repeatable data processing, check `orchestration/DETERMINISTIC_AUTOMATION.md`.

Prefer an existing tool or a small Shell/Python helper when the step is rule-based and verifiable. Return structured JSON/YAML summaries and keep large raw evidence outside model context until needed.

Do not automate subjective/complex reasoning solely to reduce tokens.

## Agent/model routing

Selected skills describe reasoning/coding/reliability needs; they never hard-code a provider model. Build one Execution Profile for the primary task and one for each bounded subagent. Resolve model tier independently using business impact, technical complexity, risk, privacy, context and expected total cost.

Subagents receive only the context required for their objective. Do not delegate vague work or duplicate the full primary context. Escalate tier/context when evidence shows the assignment is insufficient; de-escalate after the difficult portion is complete. See `orchestration/MODEL_ROUTING.md`.

## System-change maintenance

When modifying this AI Product System itself, first use the System Self-Improvement Protocol; Core Change Approval normally applies before implementation, and the Git Publish Approval Gate applies before remote publication. Also pass the Documentation Impact Gate in `docs/human/MAINTENANCE.md`. Assess related documentation, flows, Mermaid architecture diagrams, examples, scenarios, schemas/templates, VERSION and CHANGELOG. Update affected artifacts; explicitly treat unaffected artifacts as N/A rather than editing them unnecessarily.

## Completion

A task is complete only when its acceptance criteria, required review, required artifacts and persisted workspace state are satisfied. Producing code or prose alone is not completion.

For a primary planning task, completion of the Planning Package means the persisted plan is ready for Gate 1 review; it does **not** imply implementation approval.

For SAL 3–4 affected work, completion also requires the applicable Security Review evidence and Security Release Gate.

For a complete product, local completion is explicitly `LOCAL_COMPLETE`. If production was not requested, this can be the completed delivery state after the user declines/defer Production Enablement.

When production delivery is part of the approved scope, completion requires Release Readiness, applicable staging verification, production promotion, post-deploy verification and persisted evidence before `PRODUCTION_VERIFIED`. Code generation alone is not completion.

## Enforceable Governance

Approval semantics remain Human-governed, but approval validity may be machine-verifiable.

Rules:

- bind approved proposal/scope to canonical SHA-256 fingerprints;
- material scope drift becomes APPROVAL_STALE and stops the affected protected action;
- report runtime context capability separately from governance enforcement capability;
- native tool guards enforce only deterministic policy and never create approval authority;
- structured routing explanations record outcomes/reasons only, never private chain-of-thought;
- v0.11 protects Git publication first; broader destructive-operation interception remains deferred.


## Verifiable Governance Audit Chain

Use orchestration/GOVERNANCE_AUDIT.md when durable auditability is required across approval, security, publication, release or production boundaries.

- extend existing Enforceable Governance; do not create a parallel approval gate;
- record observable governance events only, never private reasoning, prompts or credentials;
- SHA-256 event + chain hashes are credential-free baseline evidence;
- HMAC-SHA256 and Ed25519 checkpoints are optional secure-runtime layers, not baseline provider credentials;
- authenticated/signed existing history must verify before append;
- audit evidence remains downstream of Human authority.
- use the portable bundle mode when exact ledger anchors, public keys and evidence digests must be transferred to an offline/later auditor; independently retain the exported ANCHOR when truncation/resubmission resistance matters.

## Execution Isolation

Execution isolation is an Execution Profile capability, not a new Role, Skill or approval gate.

- `shared` uses the current project workspace and must not be described as isolated;
- `worktree` creates a real AIPS-owned Git worktree outside the project source tree;
- `sandbox` requires a verified provider; without one the mode is UNSUPPORTED/BLOCKED rather than emulated with a temporary directory;
- one ACTIVE writer owns a Change Boundary by default, including across AIPS-managed worktrees;
- cleanup removes only AIPS-owned, clean managed worktrees and preserves dirty worktrees plus the managed branch.

Use `orchestration/EXECUTION_ISOLATION.md` and `scripts/execution_isolation.py`. Worktree isolation may also own repository-scoped TCP port leases and emit a runtime environment manifest for parallel dev/test servers. Port leases use atomic AIPS registry coordination plus host availability probes; they never bypass governance, Change Impact, Resource Authorization, test or approval requirements.

## Deterministic Scheduler

After semantic planning has produced an approved bounded task decomposition, repeated coordination is deterministic.

~~~text
Human-approved scope
→ LLM Planner / Orchestrator once
→ Structured Task Graph
→ dependency readiness + stable ordering + Change Boundary locks
→ bounded worktree writers
~~~

Use `orchestration/DETERMINISTIC_SCHEDULER.md` and `scripts/deterministic_scheduler.py`. The Scheduler cannot invent tasks, expand scope, resolve architecture/requirement conflicts, approve risk, merge or release. The same graph + task state produces the same scheduling decision/fingerprint.

## Integration Gate (Janitor)

Before merge/publication of an exact candidate, deterministic validation binds base/head SHAs, changed-file hash, Validation Profile and any required Core Change Test Matrix to one candidate fingerprint.

Project-native lint/static/type/test/security commands are declared as argv arrays. A stale candidate or required failure returns BLOCKED/FAIL. PASS is evidence only; it grants no Human, merge or release authority.

The existing protected-main `repository` required check remains compatible: GitHub Actions runs `janitor` first, then the `repository` aggregate can succeed only when Janitor succeeds. See `orchestration/INTEGRATION_GATE.md`.

## Durable Run State

For multi-step work that may be interrupted, reuse Workspace State and per-run artifacts rather than depending on chat history.

~~~text
workflow step
→ checkpoint
→ structured event evidence
→ interruption
→ resume request
→ revision/freshness verification
→ CURRENT: continue from checkpoint
→ STALE: refresh/revalidate before continuing
~~~

Rules:

- checkpoints are compact resume state, not transcripts;
- EVENTS.jsonl records structured lifecycle evidence only;
- never persist prompts, private chain-of-thought, credentials or unnecessary sensitive payloads;
- ATTACHED projects persist under `.ai/runs/<run-id>/`;
- EPHEMERAL projects use the external AIPS project cache and do not create `.ai/`;
- HEAD, branch, workspace identity or dirty-state drift marks resume state STALE;
- AIPS-owned checkpoint/state writes do not count as product workspace drift;
- the Agent must re-evaluate affected Intelligence/tests/approvals before continuing.

## Scenario Conformance

Acceptance Scenario count is a specification inventory, not proof that each behavior is executable-tested.

Use `tests/scenario_coverage.yaml` + `scripts/scenario_conformance.py` to maintain an explicit mapping:

~~~text
Scenario
→ coverage type
→ evidence
→ conformance report
~~~

Coverage types:

- `deterministic` — rule/schema/helper behavior executable without model judgment;
- `lifecycle` — executable multi-step system/runtime lifecycle evidence;
- `agent_eval` — provider-neutral recorded Agent behavior scored against an observable deterministic rubric;
- `manual` — reviewed specification with no claimed automated evidence;
- `uncovered` — no acceptable evidence yet.

Never upgrade a Scenario to automated coverage merely because a related validator exists. Evidence must materially test that Scenario's contract.

For semantic behavior that depends on Agent judgment, use `orchestration/AGENT_EVAL.md`:

~~~text
provider-neutral Eval Case
→ actual Agent observable response
→ fingerprint-bound recorded Result
→ deterministic rubric scoring
→ agent_eval evidence
~~~

Do not persist or score private chain-of-thought. A Case without a recorded passing Result is not agent_eval coverage.

## v0.27 reliability hardening

AIPS extends existing components rather than adding new authority layers:

- Evolution Radar produces a credential-free provider-neutral semantic handoff whenever an optional scheduled analyzer is unavailable.
- Deterministic Scheduler blocks any potentially writable task that omits Change Boundary; only explicit read-only tasks may run boundary-free.
- Integration/Janitor Gate can bind a freshly fetched target-branch tip and blocks stale PR bases before running candidate checks.

These are validation/research/execution hardening rules only. Protected Human Authority, Git Publish Approval, merge authority and release authority remain unchanged.


## Governance Audit Retention / Verification

For long-lived Governance Audit evidence, use config/governance-audit-retention.yaml and scripts/governance_audit_retention.py.

- catalog registration verifies an existing v0.49 bundle before indexing it;
- SAL thresholds can require an independently retained anchor and signed checkpoint evidence;
- checkpoint key rotation uses distinct key IDs; one key ID with a changed fingerprint fails closed;
- catalog-find supports deterministic provenance discovery without a remote database;
- retention-plan is advisory only and uses an explicit as-of date;
- legal hold overrides time thresholds;
- REVIEW_DUE never authorizes deletion or compaction;
- no secret/private key, source absolute path or new Agent/provider credential is persisted or required.

## MCP Interoperability Gateway

MCP-compatible hosts may use `harness/MCP_GATEWAY.md` and `aips mcp serve` as a portable local stdio access plane.

- MCP Resources expose canonical Role / Skill / selected orchestration sources on demand.
- MCP Prompts assemble reusable review/planning context; the host model still performs semantic reasoning.
- MCP Tools expose bounded deterministic/read-only AIPS helpers and cannot create Human, publish, merge, release or production authority.
- MCP-only integration is governance `ADVISORY`; it cannot claim interception of host-native shell/file/git tools.
- Runtime-native adapters remain authoritative for verified TURN_NATIVE / TOOL_GUARDED behavior.
- v0.52 does not add a provider/model call, external credential requirement, remote MCP service or automatic client-config mutation.
