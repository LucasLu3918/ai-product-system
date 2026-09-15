# Governance

## Decision levels

- **Local** — reversible implementation detail; agent may decide.
- **Component** — affects one component; agent may proceed when workflow and review allow.
- **Project** — changes public contract, schema, major architecture, product scope, permanent project policy or security posture; human decision normally required.
- **Critical** — destructive, irreversible, production-wide, governance or major compliance impact; explicit human approval required.

## Stop conditions

Stop affected work when:

- a blocking unknown prevents a reliable decision;
- a materially better approach/prerequisite changes the result;
- requirements or applicable instructions materially conflict;
- a public contract, data model, security boundary, cost profile or product scope would materially change;
- a destructive/difficult-to-recover action is requested;
- evidence is insufficient for a claimed performance, cost or safety result;
- required role/capability/skill expertise does not exist.

Do not stop for cosmetic, equivalent or easily reversible local choices. Queue non-blocking questions and ask them together.

## Safety challenge

For high/critical project actions, present: action, impact, principal risks, recovery/rollback, safer alternative when available, and required explicit approval.

## Permissions

- relevant read/search: allowed;
- workspace/local writes inside approved boundary: allowed;
- engineering branch writes: allowed;
- main branch/release/production: gated;
- destructive actions: safety challenge + explicit approval;
- secrets must never be persisted in prompts, state, artifacts or Git.

## Author and reviewer

For material code, architecture, security, data or release changes, final review must be performed by a distinct role instance from the author.

## Project overrides

A current explicit user decision may override project-local instructions inside its approved scope. Material conflicts must be surfaced before implementation. Temporary overrides are recorded with the run and do not become permanent policy unless explicitly approved.
