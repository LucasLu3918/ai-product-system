# AIPS Global Turn Harness

For software/product/project work, use the AIPS Turn Context supplied by the UserPromptSubmit hook when available.

If hook context is unavailable, resolve before analysis/mutation:

`aips intelligence context --runtime claude-code --project "$PWD" --prompt "<current user request>"`

Preserve existing Claude/project memory. Existing-project mutations require Intelligence initialization/targeted refresh plus Change Impact before editing.

For publication blocks, use the read-only `aips publish doctor` and `aips publish diagnose --worktree <root> --command '<literal command>'`. Report the stable reason code, phase, safe next step and Required Checks state (unconfigured, fail, pending, missing, cancelled or unavailable); never expose raw GitHub output or infer success from missing evidence. Diagnostics do not execute merge, consume grants or change repository policy. Retry safe read-only observations only; policy/admin changes and merges remain under native Human Authority and host confirmation.

Distinguish AIPS Hook denials from Claude Host Auto Mode denials (e.g. Merge Without Review) and GitHub checks. A Host classifier can reject even a read-only diagnostic before AIPS executes; never claim that a Host error was returned by AIPS or retry with disguised commands. In a user-controlled session, the read-only prepare command can report an independently observed denial using `--host-denied --host-denial-class merge-without-review` (or `read-only-diagnostic`); this does not grant permission.

A verified merge command needs a literal PR number, exactly one enabled merge method, and `--match-head-commit <full-sha>`. `--admin` and `--delete-branch` are forbidden on the protected merge path. Re-run read-only doctor/diagnose after candidate or checks change. The `recovery` field is advisory only: it never triggers native mutation, consumes grants, weakens Required Checks or satisfies Human confirmation. UNAVAILABLE protection evidence is not PENDING. Separate branch cleanup from merging.
