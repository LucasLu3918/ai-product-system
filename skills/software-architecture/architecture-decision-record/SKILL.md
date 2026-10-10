---
id: architecture-decision-record
description: Record a consequential technical decision with context, alternatives,
  trade-offs, consequences and review conditions.
capability: software-architecture
estimated_context_cost: low
triggers:
- technology_choice
- irreversible_architecture_decision
- architecture_tradeoff
model_requirements:
  reasoning: high
  coding: none
  reliability: high
  minimum_tier: 2
  preferred_tier: 2
---

# Architecture Decision Record

Use for consequential, cross-cutting, costly-to-reverse, or externally visible technical choices. Do not create an ADR for a small implementation detail. Follow the target project’s existing decision-record location and format; use docs/adr/ only when no convention exists.

## Method

1. State the decision to make, its context, constraints, and forces. Separate verified facts from assumptions.
2. List viable alternatives, including keeping the current design. Compare them against the same requirements, lifecycle cost, security, reliability, and migration dimensions.
3. Record the selected option and why it wins; make rejected options and their trade-offs explicit.
4. Describe consequences, implementation/migration work, compatibility effects, and risks.
5. Define evidence or events that should trigger reconsideration. Link related requirements, proposals, and superseded ADRs.

## Output

Use a concise record with title/ID, status, date, context, decision drivers, alternatives, decision, consequences, and review triggers. An ADR preserves rationale; it does not grant approval for a protected action.
