# Scenario 010 — Adaptive Subagent Model Routing

## Request

> Optimize the order API, investigate database latency, and review security risk. Use subagents if useful.

## Expected

- Preflight first; no unnecessary delegation.
- Primary task gets an Execution Profile.
- SQL bottleneck evidence may activate `database-engineer` + `sql-performance` as a bounded read-only subagent.
- Security-sensitive behavior may activate `security-engineer` + `secure-design` as an independent reviewer.
- Each subagent receives only relevant project context and skills.
- Skill metadata contributes model requirements but does not name a provider model.
- Model tier is independently resolved per agent from business impact, complexity, risk, privacy and cost.
- Critical risk can raise the minimum tier.
- Agents escalate instead of guessing when assigned intelligence/context is insufficient.
- One writer owns the code change boundary.

## Must not

- Send the full repository/context to every subagent.
- Use the strongest model for every subtask by default.
- Allow a skill to force a concrete provider/model name.
- Run multiple writers against the same change boundary without an explicit coordination mechanism.
