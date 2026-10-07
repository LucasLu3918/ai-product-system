---
id: data-modeling
capability: database
estimated_context_cost: medium
triggers:
- domain_model
- entity_relationships
- business_invariants
- data_ownership
- schema_evolution_planning
model_requirements:
  reasoning: high
  coding: normal
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
---

# Data Modeling

Model domain concepts and data ownership before selecting a storage schema.

## Positive triggers

- a product or system needs entity boundaries, relationships or business invariants;
- data ownership, lifecycle, sensitive fields or schema evolution affect architecture;
- API behavior depends on domain state transitions.

## Non-triggers

- query latency or index tuning (use `sql-performance`);
- selecting a database without domain evidence;
- duplicating an existing canonical domain model.

## Method

1. Extract domain terms from accepted requirements, policies and user workflows.
2. Define domain concepts, identity, ownership and relationships. If Domain-Driven Design is selected for the affected domain, apply its bounded contexts, aggregates and value objects via `skills/software-architecture/domain-driven-design/SKILL.md`; ordinary data modeling does not require those abstractions.
3. Record lifecycle/state machines and enforceable business invariants.
4. Assign stable `DOM-NNN` IDs and map concepts to requirement IDs.
5. Identify ownership, sensitive/protected data, integration boundaries and retention constraints.
6. Describe persistence implications and schema evolution risks without prematurely selecting SQL or a vendor.

## Output

Use `templates/planning-package/DOMAIN_MODEL.md`. Data modeling does not replace Architecture or Security review. For financial behavior, make authorization, idempotency/replay, concurrency, audit, reconciliation and recovery requirements explicit when applicable.
