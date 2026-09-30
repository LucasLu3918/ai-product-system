# Scenario 194 — OpenAPI validity, compatibility and evidence provenance

## Purpose

Validate REST/OpenAPI inputs, classify compatibility only against an explicitly canonical baseline, execute project-native contract tests, and reject stale evidence without granting approval authority.

## Cases

- Valid OpenAPI 3.0, 3.1 and 3.2 documents pass the pinned validator; malformed and unsupported documents fail closed.
- Internal and repository-local references are bounded to the repository root. Network references, path traversal, symlink escapes and missing references are rejected without network access.
- Removing an operation/response or adding a required parameter is `BREAKING`; an optional operation/parameter addition is `NON_BREAKING`; component/schema, security and unclassified changes are `UNKNOWN`.
- Non-canonical or unresolved baselines are `BLOCKED`; no report automatically approves a breaking change.
- Contract-test evidence requires a successful argv-only command, non-empty non-skipped JUnit tests and coverage for every operation ID.
- Reports bind exact spec/JUnit hashes and Git revision; content or revision drift returns `STALE`. Raw command output is not persisted.

## Limits

JUnit operation-name coverage proves declared test coverage evidence only. Project test assertions and semantic compatibility remain subject to Human review. Ownership/drift gate enforcement remains Phase 3.
