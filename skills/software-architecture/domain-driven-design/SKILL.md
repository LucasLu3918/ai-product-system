---
id: domain-driven-design
capability: software-architecture
applies_when:
  - business_domain_is_complex
  - domain_language_or_boundaries_are_material
  - aggregate_consistency_rules_exist
  - cross_domain_interactions_need_clarity
estimated_context_cost: medium
---

# Domain-Driven Design

DDD is optional and proportional to domain complexity.

Levels:

- **none** — simple CRUD, utility or thin integration work;
- **tactical** — use entities, value objects, aggregates, domain services/events where they clarify real business invariants;
- **strategic+tactical** — use bounded contexts, context maps and ubiquitous language when multiple complex domains or teams require explicit boundaries.

Rules:

- model real business concepts and invariants, not database tables;
- do not create aggregates or repositories purely because DDD terminology exists;
- keep aggregate boundaries small and consistency-driven;
- separate domain language between bounded contexts when meanings differ;
- introducing or changing a bounded context is a material architecture decision and requires preflight recommendation/approval when it affects scope or contracts;
- never perform unrelated repository-wide rewrites solely to “adopt DDD”.
