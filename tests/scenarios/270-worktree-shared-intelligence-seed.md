# Scenario 270: Worktree Shared Intelligence Seed

## Given

- A local Git repository has a primary worktree whose external Project Intelligence store is `READY`.
- A new worktree of the same repository has no external store yet.
- Another, unrelated repository also has a `READY` store in the same user config `projects/` directory.

## When

- `aips intelligence bootstrap` runs in the new worktree.
- Only a watched source path changes, first in an unrelated file and then in a watched file, inside the new worktree.
- A source store contains a symlink, or the target store already holds a non-Intelligence directory, or a copy fails.

## Then

- The new worktree reports `SEEDED` from the primary store (selection `primary_worktree`), reports freshness `CURRENT`, and the identity change appears only as the observation `worktree_identity_seeded_from_same_repository`.
- Output contains no absolute path of another worktree; the manifest records provenance (`seeded_from` project id and git head, `seeded_into` target identity).
- Unrelated commits keep the seeded store `CURRENT`; a watched source change makes only the affected topic `STALE`.
- Only allowlisted Intelligence artifacts are copied; retrieval metadata, reviews, lock files and ad hoc notes are not. The source store is never written.
- The unrelated repository's store is never a source; a forged repository identity is never a source; a copied store in another worktree keeps `worktree_identity_changed` as a STALE reason.
- A symlink in the source store, a symlinked store entry, or a copy error refuses or fails the seed with a stable reason code, leaves no partial store, and falls back to normal initialization with the observation `intelligence_seed_fallback:<reason_code>`.
- `aips intelligence gc` keeps a seeded store while its own worktree exists, even after the source store is removed, and lists it as an orphan only after its own worktree is removed.

## Evidence

- `tests/evidence/intelligence_worktree_seed_lifecycle.py`
- `tests/test_intelligence_worktree_seed.py`
- `tests/test_intelligence_task_freshness.py`
