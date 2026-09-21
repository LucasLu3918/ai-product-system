# Governance

## Authority

Internal authority order:

~~~text
CONSTITUTION
→ GOVERNANCE
→ SYSTEM / ORCHESTRATOR
→ PROJECT ACCEPTED DECISIONS / SCOPED INSTRUCTIONS
→ WORK MODE
→ ROLE / SKILL
→ TASK EXECUTION
~~~

No lower layer may override the Constitution.

## System Self-Improvement

Changes to this AI Product System require a System Improvement Review before implementation. The system evaluates the suggestion rather than blindly accepting it.

If a proposal semantically changes the Constitution, ordinary approval is insufficient: disclose affected Articles and risks and obtain explicit Constitutional Approval.

Prefer lower-authority changes whenever they can solve the problem.

## Core Change Approval

Large/core changes require an approved Change Proposal before implementation. Core means semantic impact, not merely a large file count.

Typical triggers: governance/orchestrator behavior, public contracts, schemas/migrations, auth/security boundaries, financial/stored-value logic, cross-domain changes, broad refactors, runtime/framework/database migrations, production topology and breaking changes.

If actual scope materially exceeds the approved proposal, stop and request approval again.

## Git Publish Approval

Remote Git publication is gated. Before a remote branch/ref update intended for collaboration, PR or release, present changed files, logical change summary, validation evidence, atomic commit plan, target branch/remote and planned publication action. Wait for explicit user approval.

Commits are grouped by logical capability and should be independently reviewable/revertible. Do not split commits merely by file.

For multi-file engineering changes, prefer an atomic remote branch update: assemble and validate the complete approved logical change before creating/updating the remote engineering ref. Tool/API limitations must not cause one remote commit/push per file or publish knowingly incomplete intermediate states. Local/intermediate commits are allowed when useful; remote incremental publication is exceptional and should be deliberate (for example, collaboration or diagnostic CI), with the reason included in the publish plan.

If a PR is already open and follow-up changes are required, batch the approved logical correction into one consolidated remote branch update when practical. Repository validation still runs on PR synchronization, but superseded in-progress validation should be cancellable by CI concurrency policy.

If the publish plan materially changes after approval, re-approval is required.

## Decision levels

- **Local** — reversible implementation detail; agent may decide.
- **Component** — affects one component; agent may proceed when workflow and review allow.
- **Project** — changes public contract, schema, major architecture, product scope, permanent project policy or security posture; human decision normally required.
- **Critical** — destructive, irreversible, production-wide, governance or major compliance impact; explicit human approval required.

## Stop conditions

Stop affected work when:

- a required System Improvement, Constitutional, Core Change or Git Publish approval is missing;

- System Update Preflight cannot safely update/validate the local AI Product System before a mutating implementation session;
- a primary planning task has no specified persistence workspace;
- a Planning Package is awaiting Gate 1 approval;
- Initial Implementation Items / Recommended Implementation Flow are awaiting Gate 2 approval;
- a blocking unknown prevents a reliable decision;
- a materially better approach/prerequisite changes the result;
- requirements or applicable instructions materially conflict;
- a public contract, data model, security boundary, cost profile or product scope would materially change;
- a destructive/difficult-to-recover action is requested;
- evidence is insufficient for a claimed performance, cost or safety result;
- required role/capability/skill expertise does not exist;
- a SAL 3–4 affected change lacks required independent Security Review/evidence;
- a SAL 4 affected change has unresolved High/Critical security findings.

Do not stop for cosmetic, equivalent or easily reversible local choices. Queue non-blocking questions and ask them together.

## Planning gates

For tasks that create or materially revise the authoritative product/project plan:

- persist the complete Reproducible Planning Package in the resolved workspace;
- Gate 1 is required before the plan is considered accepted;
- after Gate 1, derive Initial Implementation Items + Recommended Implementation Flow;
- Gate 2 is required before implementation begins.

Chat alone is not the System of Record for authoritative planning.

## Safety challenge

For high/critical project actions, present: action, impact, principal risks, recovery/rollback, safer alternative when available, and required explicit approval.

## Permissions

- relevant read/search: allowed;
- workspace/local writes inside approved boundary: allowed;
- engineering branch writes: allowed;
- main branch/release/production: gated;
- destructive actions: safety challenge + explicit approval;
- secrets must never be persisted in prompts, state, artifacts or Git.

## Security assurance and release

Use `docs/SECURITY_ASSURANCE.md`.

Security review depth follows the affected Change Boundary, not blindly the whole product baseline. Critical security floors cannot be averaged away.

For SAL 3–4 affected work, persist required security evidence. For SAL 4, unresolved High/Critical findings require BLOCK unless governance permits and records an explicit accepted-risk decision.

Security Engineer review is independent from the implementation author for material SAL 3–4 security boundaries.

## Author and reviewer

For material code, architecture, security, data or release changes, final review must be performed by a distinct role instance from the author.

## Project overrides

A current explicit user decision may override project-local instructions inside its approved scope. Material conflicts must be surfaced before implementation. Temporary overrides are recorded with the run and do not become permanent policy unless explicitly approved.

## System repository maintenance

Changes to the AI Product System itself must pass the Documentation Impact Gate before release. A behavioral change must not be published while affected documentation, architecture diagrams, examples, tests/scenarios, templates/schemas, VERSION or CHANGELOG remain stale.

## Approval Binding and Enforcement

Existing approval gates are not duplicated by enforcement tooling.

When machine-verifiable approval is used:

- persist an Approval Record using `templates/governance/APPROVAL_RECORD.yaml`;
- canonicalize proposal/scope fields before hashing;
- bind approval to intended branch/files/boundaries/operations and candidate commit when applicable;
- invalid fingerprint, missing approval or material actual-scope drift is `APPROVAL_STALE`;
- runtime enforcement may tighten an operation but never grants Human approval.

Governance enforcement capability is independent from context injection capability.


## Verifiable Governance Audit Evidence

For long-lived auditability, governance-boundary events may be written to the tamper-evident ledger in orchestration/GOVERNANCE_AUDIT.md after existing Approval/Security/Release authority is evaluated.

~~~text
Human Approval / Security Decision / Release Gate
→ existing enforcement
→ protected action
→ verifiable audit event
~~~

Audit events never create approval authority. Baseline integrity uses deterministic SHA-256 event and chain hashes without credentials. Secure runtimes may add HMAC-SHA256 authentication and Ed25519 signed checkpoints. Secret/private key material stays outside Git, prompts, state and artifacts. Existing authenticated/signed history must verify before append.
