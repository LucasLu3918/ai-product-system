# Engineering Change

Use for modifications to an existing repository.

```text
Identify Target
→ Discover Scoped Project Instructions
→ Inspect Relevant Code/Tests/Contracts
→ Conflict + Better-Approach Preflight
→ Change Boundary
→ Change Security Impact / Reliability Impact
→ Architecture/Test/Security Strategy
→ Implement
→ Independent Review or Multi-Perspective Review
→ Author Fix + Targeted Re-review when needed
→ Quality Gate
→ Persist State
```

Rules:

- current explicit user decisions lead project execution under system safety guardrails;
- nearest applicable `AGENTS.md` beats broader project instructions;
- project ADR/contracts/standards and project-local skills are loaded before generic skills when relevant;
- detect stack/conventions from repository evidence;
- load only affected files, roles and leaf skills;
- classify Effective SAL when the Change Boundary touches auth, sensitive data, externally exposed interfaces, high-value business logic or other protected assets;
- high-value financial/stored-value boundaries impose the applicable critical security floor;
- a high-risk product does not automatically require a full high-SAL review for unrelated cosmetic changes;
- use TDD for testable behavior when practical;
- add characterization coverage before risky legacy behavior changes when needed;
- preserve current architecture when adequate; use Clean Architecture/DDD proportionally;
- do not perform unrelated cleanup, public contract changes or architecture redesign without material preflight/approval;
- one-task overrides stay temporary unless permanent policy change is explicitly approved.


For large/core/high-risk changes, use `orchestration/MULTI_REVIEW.md` and only the specialist perspectives justified by the Change Boundary. The Author remains the writer.

For existing visual/UI cleanup, route the visual portion through `orchestration/VISUAL_POLISH.md` rather than silently redesigning.
