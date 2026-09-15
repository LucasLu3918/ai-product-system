# Engineering Change

Use for modifications to an existing repository.

```text
Identify Target
→ Discover Scoped Project Instructions
→ Inspect Relevant Code/Tests/Contracts
→ Conflict + Better-Approach Preflight
→ Change Boundary
→ Architecture/Test Strategy
→ Implement
→ Independent Review
→ Quality Gate
→ Persist State
```

Rules:

- current explicit user decisions lead project execution under system safety guardrails;
- nearest applicable `AGENTS.md` beats broader project instructions;
- project ADR/contracts/standards and project-local skills are loaded before generic skills when relevant;
- detect stack/conventions from repository evidence;
- load only affected files, roles and leaf skills;
- use TDD for testable behavior when practical;
- add characterization coverage before risky legacy behavior changes when needed;
- preserve current architecture when adequate; use Clean Architecture/DDD proportionally;
- do not perform unrelated cleanup, public contract changes or architecture redesign without material preflight/approval;
- one-task overrides stay temporary unless permanent policy change is explicitly approved.
