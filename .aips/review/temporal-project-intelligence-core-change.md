# Core Change Proposal — Temporal Project Intelligence

## Purpose

Extend Project Intelligence so AIPS can answer current, historical and evolutionary architecture questions using Git revision semantics, explicit provenance and supersession relationships.

## Why this is a core/large change

The change affects canonical Intelligence schemas, deterministic CLI behavior, Retrieval SQLite projection, Change Impact semantics, migration behavior, architecture documentation and conformance tests.

## Proposed Scope

### In scope

- Add `TEMPORAL_ASSERTIONS.yaml` as a canonical temporal assertion ledger.
- Add bitemporal valid/observed metadata with Git revision ancestry as the authoritative validity axis.
- Add deterministic `CURRENT`, `AS_OF`, `BETWEEN` and `WHY` query semantics.
- Add optional temporal validity and provenance to Impact Graph v2 while keeping v1 readable.
- Project temporal data into rebuildable SQLite tables.
- Define safe unknown-history migration behavior and conflict reporting.
- Document Change Impact and context-loading integration.
- Add acceptance and lifecycle tests for replacement, branch divergence, unknown history, supersession and index rebuild.

### Out of scope

- Neo4j or another external graph database.
- Per-commit graph snapshots.
- New Role, Skill, Capability or Approval Gate.
- Automatic semantic rule mining, embeddings or cross-repository temporal graphs.
- Constitutional, Human Authority or approval-semantics changes.

## Expected Files / Modules

- `scripts/temporal_intelligence.py`
- `scripts/project_intelligence.py`
- `scripts/retrieval_intelligence.py`
- `templates/intelligence/TEMPORAL_ASSERTIONS.yaml`
- `templates/intelligence/IMPACT_GRAPH.yaml`
- `orchestration/PROJECT_INTELLIGENCE.md`
- `orchestration/CHANGE_IMPACT.md`
- `docs/ARCHITECTURE.md`
- `docs/human/ARCHITECTURE_OVERVIEW.md`
- temporal validation/lifecycle tests and scenario documentation

## Impact

### Architecture / Contracts

Canonical YAML remains authoritative. SQLite remains a rebuildable cache. Current Snapshot remains the fast default; historical evidence is loaded only for temporal queries.

### Data / Migration

Existing v1 graph data remains readable. Migration never invents a historical start revision; unknown history is explicit and queryable only where evidence permits.

### Security / Reliability

No new secrets or external services. Fail closed for malformed intervals, invalid revisions and broken supersession references. Conflicts are reported, never silently resolved.

### Compatibility / Rollback

The new artifact is additive. Removing the SQLite cache and rebuilding from canonical YAML must remain supported. Existing non-temporal queries retain current behavior.

### Tests / Validation

See `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` after implementation. Required evidence includes unit, CLI, migration/recovery, SQLite rebuild, contract and documentation validation.

### Documentation / Diagrams

- `docs/ARCHITECTURE.md`: AFFECTED — temporal canonical and query flow is new.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: AFFECTED — human-facing architecture summary must describe the new layer.
- Human SVG diagrams: N/A — no SVG source is currently required for this flow.

## Risks

- Incorrect ancestry handling could return a future rule for a historical revision.
- Migration could imply history that cannot be proven.
- Stale temporal indexes could diverge from YAML if rebuild behavior is incomplete.
- Scope drift into general graph querying would increase complexity without current evidence.

## Recommendation

Proceed with the narrow local-first, revision-aware extension. Preserve current materialized behavior and keep unknown history explicit.

## Proposed Implementation Order

1. Schema and validator.
2. Git revision resolver and query semantics.
3. Impact Graph v2 compatibility.
4. Rebuildable SQLite projection.
5. Change Impact and context documentation.
6. Acceptance tests, repository validation and final reconciliation.

## Approval

Status: APPROVED_BY_USER_REQUEST
Approved by: user
Approved at: 2026-09-23
Approval record: current user request to implement the approved `plan2` direction through completion
