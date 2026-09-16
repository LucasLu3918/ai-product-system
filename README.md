# AI Product System

A platform-agnostic, filesystem-native operating system for AI-assisted product work.

It turns a natural-language request into the **smallest safe execution plan**: safely update the system, preflight important decisions, persist authoritative planning when needed, select one work mode, load only required roles/skills/project context, choose an eligible cost-effective model/tool set, execute inside scope, independently review material work, and persist results/state.

## Quick start

On a new computer:

```bash
mkdir -p ~/Developer
cd ~/Developer
gh repo clone LucasLu3918/ai-product-system
cd ai-product-system
./scripts/bootstrap.sh
aips doctor
```

Initialize a target project:

```bash
aips init /path/to/project
```

Before every mutating implementation session:

```bash
aips preflight /path/to/project
```

See `docs/INSTALLATION.md` for install/update/uninstall behavior.

## Core behavior

```text
Request
→ Safe System Update Preflight
→ Task Preflight
→ Primary Planning Detection
→ Reproducible Planning Package + Gate 1/2 when applicable
→ decision only when material
→ Work Mode
→ project/scoped instruction discovery when needed
→ minimum Role + Skill + Context
→ Execution Profile / bounded Subagents when useful
→ minimum sufficient Model + Tools
→ Execute
→ Independent Review
→ Persist + System Version/Commit
```

Key rules:

- never silently invent missing project facts;
- recommend materially better approaches before implementation;
- stop when required expertise does not exist and propose the smallest capability extension;
- primary product/project planning must be physically persisted in a user-specified workspace; if no workspace is given, ask;
- authoritative planning must be complete enough for another capable AI/human team to reproduce substantially the same intended product;
- planning approval and implementation approval are separate gates;
- current explicit user decisions lead project execution, while system safety guardrails remain mandatory;
- in existing projects, nearest scoped `AGENTS.md` beats broader scope and project-local knowledge beats generic skills;
- use Clean Architecture principles and DDD proportionally, not ceremonially;
- use TDD for testable behavior and characterization tests for risky legacy changes when appropriate;
- verify dynamic prices, versions and limits at runtime;
- one writer owns a change boundary by default;
- Primary Agent, Subagent and Reviewer models are resolved independently from task risk/complexity and Skill hints;
- system updates never auto merge/rebase and major-version changes require explicit review;
- system changes must pass the Documentation Impact Gate so docs, flows, diagrams and tests stay synchronized.

## Start here

- Agent entry: `AGENTS.md`
- Router: `SYSTEM.md`
- User guide: `USER_GUIDE.md`
- Installation/lifecycle: `docs/INSTALLATION.md`
- Architecture diagrams: `docs/ARCHITECTURE.md`
- Planning protocol: `orchestration/PLANNING_PACKAGE.md`
- Maintenance: `docs/MAINTENANCE.md`
- Examples: `examples/EXAMPLES.md`
- Accepted decisions: `core/DECISIONS.md`
- Release history: `CHANGELOG.md`

## Compact repository structure

```text
ai-product-system/
├── AGENTS.md
├── SYSTEM.md
├── USER_GUIDE.md
├── bin/aips
├── scripts/bootstrap.sh
├── docs/
├── core/
├── orchestration/
├── work-modes/
├── roles/INDEX.yaml
├── roles/*/ROLE.md
├── capabilities/INDEX.yaml
├── skills/INDEX.yaml
├── skills/*/SKILL.md
├── templates/
│   └── planning-package/
├── adapters/
└── tests/scenarios/
```

The indexes are routing metadata. Agents should read a selected role/skill body only after the index indicates it is relevant.

Project-specific truth stays in the target project workspace, normally under `.ai/`; it is not copied into this system repository.
