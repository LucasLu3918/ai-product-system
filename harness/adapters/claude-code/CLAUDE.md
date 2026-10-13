# AIPS Global Turn Harness

For software/product/project work, use the AIPS Turn Context supplied by the UserPromptSubmit hook when available.

If hook context is unavailable, resolve before analysis/mutation:

`aips intelligence context --runtime claude-code --project "$PWD" --prompt "<current user request>"`

Preserve existing Claude/project memory. Existing-project mutations require Intelligence initialization/targeted refresh plus Change Impact before editing.

For publication blocks, use the read-only `aips publish doctor` and `aips publish diagnose --worktree <root> --command '<literal command>'`. Report the stable reason code, phase, safe next step and Required Checks state (unconfigured, fail, pending, missing, cancelled or unavailable); never expose raw GitHub output or infer success from missing evidence. Diagnostics do not execute merge, consume grants or change repository policy. Retry safe read-only observations only; policy/admin changes and merges remain under native Human Authority and host confirmation.

Distinguish AIPS Hook denials from Claude Host Auto Mode denials (e.g. Merge Without Review) and GitHub checks. A Host classifier can reject even a read-only diagnostic before AIPS executes; never claim that a Host error was returned by AIPS or retry with disguised commands. In a user-controlled session, the read-only prepare command can report an independently observed denial using `--host-denied --host-denial-class merge-without-review` (or `read-only-diagnostic`); this does not grant permission.

A verified merge command needs a literal PR number, exactly one enabled merge method, and `--match-head-commit <full-sha>`. `--admin` and `--delete-branch` are forbidden on the protected merge path. Re-run read-only doctor/diagnose after candidate or checks change. The `recovery` field is advisory only: it never triggers native mutation, consumes grants, weakens Required Checks or satisfies Human confirmation. UNAVAILABLE protection evidence is not PENDING. Separate branch cleanup from merging.

## Publication Diagnostics and Recovery

Before continuing a blocked publication, run `aips publish doctor --worktree <candidate-root> --worktree-details` and inspect its phase, reason code, source HTTP status, endpoint, and sanitized error summary. A `403` is an access/evidence failure. A `404` from classic branch protection means no classic rule only after the branch itself is verified; active rules still come from the effective-rules observation. `UNKNOWN` never means unprotected.

Treat `WORKTREE_DIRTY` paths as review evidence. Preserve files whose delivery scope is unclear; do not automatically stash, delete, ignore, or commit them. Push, PR, required-check, and merge blockers belong to separate phases. `ALREADY_MERGED` means stop publication retries and continue with post-merge reconciliation for the exact PR head and merge commit.

Use diagnostics for safe observation and local validation only. Retry a read-only observation when the diagnostic marks the evidence retryable. Host denial, missing Human approval, stale scope, missing/failing required checks, or a changed candidate requires the named approval, review, or revalidation step; diagnostic output never supplies permission to publish or merge.
