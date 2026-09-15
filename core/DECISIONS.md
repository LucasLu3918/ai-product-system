# Consolidated Architecture Decisions

This file is the compact record of accepted design decisions. Use a new ADR only for future material architecture changes that need their own rationale/history.

| Topic | Accepted decision |
|---|---|
| Agent model | Role + Capability/Skill + Context + Task |
| Human authority | Protected Human Authority |
| Context loading | Hierarchical progressive context resolution |
| Autonomy | Governed Autonomy |
| Preflight | Material recommendation/unknown/risk/capability-gap check before implementation |
| Existing projects | Inspect first; discover scoped instructions; establish change boundary; avoid unrelated refactors |
| Project precedence | Current explicit user decision > scoped project instructions/decisions > project skills > global skills, under system safety guardrails |
| Scoped instructions | Nearest applicable `AGENTS.md` wins over broader project scope |
| Overrides | One-task overrides remain temporary unless the user approves a permanent policy change |
| Testing | TDD by default for testable behavior; appropriate strategy elsewhere; characterization tests for risky untested legacy behavior |
| Review | Author and final reviewer are separate for material changes |
| Work routing | Intent-based Work Modes; greenfield/brownfield is project state |
| Skills | Small, reusable, independently loadable leaf knowledge; skills have expertise but no governance authority |
| Capability gaps | Reuse skill → new skill → new capability → new role; stop before guessing |
| Model selection | Privacy-aware adaptive routing using minimum sufficient intelligence |
| Multi-agent model routing | Primary/subagents resolve models independently from business impact, complexity, risk and skill hints; use bounded context, escalation/de-escalation and minimum sufficient intelligence |
| Dynamic facts | Verify changing prices, versions and limits at runtime |
| Artifacts | Required outputs must be persisted in the project workspace |
| State | Workspace persistent state supports resume/handoff |
| Permissions | Least privilege and isolated change |
| Concurrency | Parallel read/review allowed; one writer per change boundary by default |
| Architecture | Clean Architecture principles where useful; DDD activated by domain complexity; avoid pattern-driven overengineering |
