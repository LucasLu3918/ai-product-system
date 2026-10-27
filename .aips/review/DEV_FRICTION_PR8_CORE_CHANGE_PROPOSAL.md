# Core Change Proposal — Dev Friction PR8: Worktree Shared Intelligence

## Purpose

Stop every new worktree of a repository from starting with a MISSING Project Intelligence store. Claude Code creates many agent worktrees, and each one re-initialized Intelligence from scratch, while `worktree_identity_changed` marked copied or moved stores STALE. This change seeds a new worktree's external store from a READY store of the same repository (copy-on-write), and treats a seeded worktree identity change as an observation only when the seeding provenance proves it.

## Why this is a Core Change

The change touches Project Intelligence bootstrap, the freshness decision that feeds the fail-closed Turn Context policy, and the external store lifecycle used by garbage collection. A wrong source selection could copy another repository's knowledge, and a wrong freshness proof could hide a stale store. The boundary therefore needs explicit evidence.

## Approved Scope

Status: APPROVED. The Human approved the full AIPS dev-friction plan (`aips-dev-friction-plan.md`), including decision D7 (worktree-shared Intelligence: a new worktree copies the same repository's store and then writes separately). This proposal covers exactly PR8 of that plan and does not expand it:

1. A worktree without an external store is seeded from the READY store of the same repository before normal initialization. Seeding runs in `bootstrap`, the only path that creates a store.
2. Same-repository proof, source selection and the copied artifact set are fixed and deterministic (see Design).
3. Freshness treats a `worktree_identity` mismatch as an observation only when the seeding provenance proves it; otherwise today's `worktree_identity_changed` STALE reason is kept.
4. Seeding is cheap and fail-safe: any refusal or error falls back to normal initialization with a diagnostic observation and no partial store.
5. `aips intelligence gc` needs no behavior change; a seeded store records its own worktree root, so GC keeps it exactly as it keeps any other store.

### Out of scope

- ATTACHED stores (`.ai/intelligence` inside a worktree), retrieval index sharing (the SQLite index stays per workspace in the cache home), the Turn Context fail policy, Change Impact, readiness rules, profiles (PR10), publication authority, and the Constitution.

## Design

### Source selection (deterministic)

Candidates are the worktrees that `git worktree list` reports for the current repository, excluding the current worktree. A candidate qualifies only when all of these hold:

- its `git rev-parse --git-common-dir` equals the current worktree's common git directory;
- it has no `.ai` directory (only external stores are sources);
- its AIPS `repository_id` equals the current `repository_id`;
- its external store is the canonical store of its own `workspace_id` directly under `<config>/projects/`, is not a symlink, and resolves inside `projects/`;
- its manifest has the current schema version, `state.readiness == READY`, `project.repository_id` equal to the current one, and a recorded `project.root` that resolves to the candidate worktree path.

Order: the primary worktree first, then the most recent `verified.verified_at`, then the lowest `workspace_id`. The first candidate is the source; its `selection` is `primary_worktree` or `most_recent_ready_store`.

### Copy and provenance

- Copied (allowlist): `PROJECT_INTELLIGENCE.yaml`, `SOURCE_REGISTRY.yaml`, `PROJECT_OVERRIDES.yaml`, `IMPACT_GRAPH.yaml`, `TEMPORAL_ASSERTIONS.yaml`, `DISCOVERY.yaml`, and `topics/*.md|*.yaml`.
- Excluded: `RETRIEVAL_INDEX.yaml` (retrieval metadata pointing at a cache database), `reviews/` (re-rendered), `.writer.lock`, unrecognized notes, and everything outside the store (`changes/`).
- Any symlink anywhere in the source store refuses the seed (`source_contains_symlink`), so nothing is read through a link.
- The copy goes to a staging directory beside the target and is renamed into place only after the manifest is written, so a partial store is never visible.
- Only the copied manifest changes: `project.root` is set to the new worktree (so GC and reviews point at a live path), and a `provenance` block records `seeded_from` (source project id, source verified git head, source `worktree_identity`, selection) and `seeded_into` (target project id, target `worktree_identity`, `repository_id`), plus artifact counts. `project.worktree_identity` keeps the source value until the next finalize or refresh, which is what the freshness proof checks. No other worktree path is written into the manifest or printed.
- The source store is only read. Seeding never takes the source writer lock and never writes into it.

### Freshness

`freshness()` keeps `worktree_identity_changed` as a STALE reason unless `seeded_worktree_change_proven()` holds: `seeded_from.worktree_identity` equals the stored identity, and `seeded_into` names the current worktree identity, workspace id and repository id. A proven change is recorded as the observation `worktree_identity_seeded_from_same_repository`. A store copied into a different worktree does not carry a matching `seeded_into`, so it stays STALE.

Seeded stores then run the normal freshness checks: watched committed paths between the source head and the new HEAD, and watched dirty or changed source hashes. Only affected topics become STALE.

### Fallback and diagnostics

`seed_worktree_store()` never raises. A refusal returns `REFUSED` with a stable reason code (`target_store_is_symlink`, `target_store_not_empty`, `source_contains_symlink`, `source_manifest_missing`, `source_manifest_unusable`). An I/O or parse error returns `FAILED` with `seed_error`. Both leave no staging directory and fall back to today's normal initialization, whose result carries `observations: ["intelligence_seed_fallback:<reason_code>"]`. No source, which is the normal first-worktree case, returns `NO_SOURCE` without an observation.

### Behavior summary

- Before: a new worktree reports `MISSING`; `bootstrap` walks and analyzes the repository from scratch; a copied store reports `worktree_identity_changed` as STALE.
- After: a new worktree whose repository has a READY store reports `SEEDED` with `CURRENT` freshness (or only the affected topics STALE). The copy is independent; no re-analysis; the turn context's `MISSING` fail-closed reason applies only until bootstrap runs.

### Garbage collection

No change to `gc_external_stores`. A seeded store's recorded root is its own worktree, so it is an orphan only when that worktree is removed. It never depends on the source store.

## Impact and compatibility

- Additive manifest field `provenance`; existing manifests and stores without it behave exactly as before.
- New observation names `worktree_identity_seeded_from_same_repository` and `intelligence_seed_fallback:<reason>`; no reason code is removed.
- No schema version change and no migration. Seeding happens only when the target has no manifest and no content, so existing stores are never overwritten.
- The turn context still reports `MISSING` for a brand-new worktree until `bootstrap` runs; this change does not add a read-path write.

## Architecture Diagram Impact

N/A — no component topology, deployment unit or runtime boundary changes. The change adds one internal module (`scripts/project_intelligence_seed.py`) inside the existing Project Intelligence store lifecycle.

## Validation

- Unit: `tests/test_intelligence_worktree_seed.py` (seeding from primary and most recent READY source, copy set, copy-on-write, forged repository identity, cross-repository refusal, symlink refusal in source and target paths, copy-error fallback, non-empty target refusal, proven and unproven identity change).
- Lifecycle: `tests/evidence/intelligence_worktree_seed_lifecycle.py` (before MISSING and after SEEDED, watched versus unrelated commits, output without another worktree path, gc keeps the seeded store until its own worktree is removed, symlink fallback observation).
- Regression: `tests/test_intelligence_task_freshness.py` and the existing Intelligence lifecycle evidence scripts.
- Scenario 270, `scripts/capability_registry.py check`, `tests/validate_repository.py`, and repository preflight.

## Limitations

- Only worktrees that git still lists can be sources; the store of a removed worktree is not used.
- ATTACHED `.ai` stores are not seeded.
- The retrieval index is not shared; each workspace builds its own cache, as before.
- A seeded store is copied at its source verified state. Its own freshness must still be checked against the new worktree's HEAD and dirty state.

## Approval

Status: APPROVED for the PR8 scope above, as part of the Human-approved dev-friction plan (decision D7).
