---
id: sql-performance
description: Diagnose SQL query and database performance using query plans, indexes and measured
  workload evidence.
capability: database
estimated_context_cost: low
triggers:
- sql_bottleneck_evidence
model_requirements:
  reasoning: high
  coding: normal
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
---

# Sql Performance

Load only after evidence implicates database/SQL. Inspect execution plans, cardinality, indexes, query shape, N+1 behavior, locking and data volume. Avoid index proliferation; verify improvement under representative workload.
