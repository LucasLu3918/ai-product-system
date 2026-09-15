# System Router

## Main pipeline

```text
User Request
→ Workspace Bootstrap
→ Preflight
→ Human decision only when materially required
→ Intent + Work Mode
→ Project State
→ Instruction Discovery (existing projects)
→ Minimal Context Manifest
→ Role + Skill Resolution
→ Execution Profile / bounded Subagents when useful
→ Model + Tool Routing
→ Execute
→ Independent Review
→ Artifact / Quality Gate
→ Persist State
```

## Preflight

Before implementation, check only what can materially change the outcome:

- blocking unknowns;
- a clearly better approach or prerequisite;
- scope, contract, architecture, security, cost or destructive risk;
- missing role/capability/skill expertise;
- instructions that materially conflict.

If a material choice exists, present a concise option set, recommend one, and stop affected work until the user decides. Batch non-blocking questions instead of interrupting repeatedly.

Never invent project facts. When expertise can reduce user burden, propose a professional solution rather than asking the user to design it for the agent.

## Project state

- `greenfield` — new product/system;
- `brownfield` — existing product/repository;
- `unknown` — inspect before deciding.

Project state is not a work mode.

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

## Completion

A task is complete only when its acceptance criteria, required review, required artifacts and persisted workspace state are satisfied. Producing code or prose alone is not completion.
