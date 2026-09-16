# Governance

## Decision levels

- **Local** — reversible implementation detail; agent may decide.
- **Component** — affects one component; agent may proceed when workflow and review allow.
- **Project** — changes public contract, schema, major architecture, product scope, permanent project policy or security posture; human decision normally required.
- **Critical** — destructive, irreversible, production-wide, governance or major compliance impact; explicit human approval required.

## Stop conditions

Stop affected work when:

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
