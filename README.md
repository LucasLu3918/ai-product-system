# AI Product System

A platform-agnostic, filesystem-native operating system for AI-assisted product work.

It turns a natural-language request into the **smallest safe execution plan**: preflight important decisions, select one work mode, load only required roles/skills/project context, choose an eligible cost-effective model/tool set, execute inside scope, independently review material work, and persist results/state.

## Core behavior

```text
Request
→ Preflight
→ decision only when material
→ Work Mode
→ project/scoped instruction discovery when needed
→ minimum Role + Skill + Context
→ Execution Profile / bounded Subagents when useful
→ minimum sufficient Model + Tools
→ Execute
→ Independent Review
→ Persist
```

Key rules:

- never silently invent missing project facts;
- recommend materially better approaches before implementation;
- stop when required expertise does not exist and propose the smallest capability extension;
- current explicit user decisions lead project execution, while system safety guardrails remain mandatory;
- in existing projects, nearest scoped `AGENTS.md` beats broader scope and project-local knowledge beats generic skills;
- use Clean Architecture principles and DDD proportionally, not ceremonially;
- use TDD for testable behavior and characterization tests for risky legacy changes when appropriate;
- verify dynamic prices, versions and limits at runtime;
- one writer owns a change boundary by default.
- Primary Agent, Subagent and Reviewer models are resolved independently from task risk/complexity and Skill hints; subagents receive only bounded context.

## Start here

- Agent entry: `AGENTS.md`
- Router: `SYSTEM.md`
- User guide: `USER_GUIDE.md`
- Examples: `examples/EXAMPLES.md`
- Accepted decisions: `core/DECISIONS.md`

## Compact repository structure

```text
ai-product-system/
├── AGENTS.md
├── SYSTEM.md
├── USER_GUIDE.md
├── core/
├── orchestration/
├── work-modes/
├── roles/INDEX.yaml
├── roles/*/ROLE.md
├── capabilities/INDEX.yaml
├── skills/INDEX.yaml
├── skills/*/SKILL.md
├── templates/
├── adapters/
└── tests/scenarios/
```

The indexes are routing metadata. Agents should read a selected role/skill body only after the index indicates it is relevant.

Project-specific truth stays in the target project workspace, normally under `.ai/`; it is not copied into this system repository.
