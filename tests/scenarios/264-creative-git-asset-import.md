# Scenario 264: Explicit Git Creative Asset Import

## Purpose

Allow a user to place a reviewed local creative asset in a Git worktree when explicitly requested, while preserving the existing default denial and create-only integrity guarantees.

## Preconditions

- The source asset is a regular supported image or SVG in a non-Git EPHEMERAL workspace.
- The user-selected destination is the exact root of a Git worktree.
- The target uses a supported matching extension and its parent directory already exists.
- The target is absent.

## Expected behavior

1. Candidate creation without `--allow-git-destination` rejects a Git destination.
2. Explicit opt-in records `GIT_OPT_IN` in the source-hash-bound candidate.
3. Import revalidates candidate and source hashes, project roots, path confinement, and target absence before creating the exact target.
4. An existing/appeared target, changed source, edited candidate, symlink/path escape, unsupported format, nested `.git` path, or Git source fails closed.
5. Candidate replay remains create-only; the second import cannot overwrite the first result.
6. Git index bytes remain unchanged. Import never stages, commits, pushes, or grants publication authority.
7. Existing EPHEMERAL candidates remain readable and retain their previous behavior.

## Evidence

`tests/evidence/opencode_integration_lifecycle.py` runs the source candidate/import lifecycle and checks default rejection, opt-in success, hash binding, target replay, nested Git metadata rejection, and unchanged index state. The general repository validation also runs on the exact candidate.

## Limits

Local lifecycle evidence does not grant commit or publication authority and does not replace the separate Git publication workflow.
