---
id: database-migration
description: Plan backward-compatible database changes and data backfills with staged
  rollout, lock analysis and recovery checkpoints.
capability: database
estimated_context_cost: low
triggers:
- schema_change_on_live_data
- large_table_backfill
- column_rename_or_split
model_requirements:
  reasoning: high
  coding: normal
  reliability: critical
  minimum_tier: 3
  preferred_tier: 3
---

# Database Migration

Use for schema changes over live or valuable data. Use data-modeling to design a new domain schema before production data exists, and sql-performance when query cost is the primary concern.

## Method

1. Inspect the current schema, data volume/distribution, constraints, indexes, application readers/writers, deploy order, and database engine/version.
2. Plan expand–migrate–contract stages: add compatible structures first, deploy code that tolerates old and new forms, backfill, switch reads, verify, and only then remove old structures.
3. Estimate lock duration, write amplification, replication lag, transaction size, and impact on production traffic. Use resumable, idempotent batches with progress and rate controls for large backfills.
4. Define consistency checks and observability for every stage. Keep old/new writes or reads consistent during transition; include concurrent writes in the plan.
5. State rollback and forward-recovery steps for each stage, including the point after which rollback is no longer safe.
6. Mark deletion, destructive transforms, and irreversible data loss explicitly. Require human approval before execution of those steps.

## Output

Deliver the ordered migration and application rollout, compatibility window, batch/retry strategy, validation queries, lock/replication risks, rollback/recovery plan, and execution approval points. Never assume a migration is reversible because a down script exists.
