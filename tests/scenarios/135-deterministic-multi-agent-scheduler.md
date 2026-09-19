# Scenario 135 — Deterministic Multi-Agent Scheduler

A Human-approved plan contains independent and dependent tasks that may execute in parallel worktrees.

Expected:
- LLM/planning produces a structured Task Graph once; scheduling decisions are deterministic code;
- the same graph + state produces the same dispatch decision and fingerprint;
- dependency readiness is enforced without LLM reasoning;
- overlapping Change Boundaries cannot be dispatched concurrently;
- `max_parallel` is enforced deterministically;
- resume uses persisted task state rather than chat history;
- failed/stale dependencies block downstream work instead of being guessed around;
- the scheduler cannot expand scope, approve architecture, merge or release.
