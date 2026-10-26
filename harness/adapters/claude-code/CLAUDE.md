# AIPS Global Turn Harness

For software/product/project work, use the AIPS Turn Context supplied by the UserPromptSubmit hook when available.

If hook context is unavailable, resolve before analysis/mutation:

`aips intelligence context --runtime claude-code --project "$PWD" --prompt "<current user request>"`

Preserve existing Claude/project memory. Existing-project mutations require initialized READY Intelligence plus Change Impact before editing. READY+STALE freshness is advisory: refresh only the topics listed in `targeted_refresh` when the Turn Context sets `refresh_required=true`, and build the Retrieval index only when `retrieval_index_required=true`.

For publication blocks, use the read-only `aips publish doctor` and `aips publish diagnose --worktree <root> --command '<literal command>'`. Doctor observes the remote default policy branch separately from the candidate/source branch; `--branch` explicitly overrides the policy target. Report the stable reason code, phase, blocker source/rule, safe endpoint/status category, Traditional Chinese recovery step and Required Checks state; never expose raw GitHub output or infer success from missing evidence. Prepare and Hook may expose matching hashed worktree ID, candidate SHA, target ref, publication mode and AIPS runtime version/revision. These observations do not authorize a command. `PLANNED` and `next_step: PUSH` are not permission; Hook `AUTHORIZED` means only that AIPS allowed the tool, while the Host may still deny and execution has not started. Only verified action results can be `EXECUTED`.

Claude Code denial context may contain a bounded Diagnostic ID, reason code, phase, category, allowlisted exception class, retryability and safe binding, excluding raw commands, arguments, prompts, exception messages and credentials. When `AIPS_GOVERNANCE_AUDIT_LEDGER` is already configured, a redacted allowlisted event can be looked up with `aips publish diagnose --diagnostic-id <UUID> --format json`; lookup verifies the existing ledger chain. If it is unset, the result is `NOT_CONFIGURED`, and no default ledger is created. Append failure never changes Hook allow/deny. Diagnostics are observational and cannot consume grants or change repository policy. A retryable network, rate-limit or GitHub server denial may trigger one read-only Doctor. Policy/admin changes and merges remain under native Human Authority and host confirmation.

The managed Claude Code `PreToolUse:Bash` guard uses `onFailure: "block"` only when the detected host version is v2.1.295 or later. AIPS returns a structured fail-closed denial within its eight-second Hook deadline, with a safe phase, reason code and elapsed time. Older or unknown host versions retain compatible hook settings and cannot guarantee blocking on an unexpected process crash; upgrade Claude Code before relying on host-level failure blocking. The prompt-context hook does not use this policy.

The managed `PostToolUseFailure:Bash` hook reports only that native execution failed, its bounded error category, and a parsed exit code when available. It never echoes the host error, command or paths. This event fires after the tool has started; it does not authorize, retry, or roll back the command. A PreToolUse denial is reported separately as `NOT_EXECUTED`.

Distinguish AIPS Hook denials from Claude Host Auto Mode denials (e.g. Merge Without Review) and GitHub checks. A Host classifier can reject even a read-only diagnostic before AIPS executes; never claim that a Host error was returned by AIPS or retry with disguised commands. In a user-controlled session, the read-only prepare command can report an independently observed denial using `--host-denied --host-denial-class merge-without-review` (or `read-only-diagnostic`); this does not grant permission.

A verified merge command needs a literal PR number, exactly one enabled merge method, and `--match-head-commit <full-sha>`. `--admin` and `--delete-branch` are forbidden on the protected merge path. Re-run read-only doctor/diagnose after candidate or checks change. The `recovery` field is advisory only: it never triggers native mutation, consumes grants, weakens Required Checks or satisfies Human confirmation. UNAVAILABLE protection evidence is not PENDING. Separate branch cleanup from merging.

## Standard Publication Recipe

Run one publication command per Bash call; never chain a push with a PR command.

1. Commit: `git commit -m "$(cat <<'EOF'` … `EOF` `)"` with a quoted delimiter, `git commit -m '<text>'`, or `git commit -F <file>`; literal `git add <paths> &&` may precede it. Unquoted heredocs, `$VAR` and backticks are denied.
2. Write the PR body to a file outside the worktree, then run `aips publish prepare --worktree <root> --title <title> --body-file <file> --runtime claude-code --format json`.
3. Run the emitted invocation `argv` exactly: `git push origin <full-candidate-sha>:refs/heads/<branch>` (`-u` allowed). A bare branch name or `HEAD` is denied.
4. Re-run the same Prepare and run its emitted `gh pr create --repo <owner/repo> --head <branch> --base <default> --title <title> --body-file <file>`. A literal `--body` (including a quoted `<<'EOF'` heredoc) is also accepted; `--repo`, `--head` and `--base` are required.

Prepare scan evidence is bound to the exact candidate, operation, target and policy digest and expires after 30 minutes. A denial names the supported form in `next_step`/`next_step_zh`; follow it instead of trying command variants.

## Publication Diagnostics and Recovery

Before continuing a blocked publication, run `aips publish doctor --worktree <candidate-root> --worktree-details` and inspect its phase, reason code, source HTTP status, endpoint, and sanitized error summary. A `403` is an access/evidence failure. A `404` from classic branch protection means no classic rule only after the branch itself is verified; active rules still come from the effective-rules observation. If `branch.protected` is true and classic policy is permission-hidden, Required Checks policy is `UNKNOWN_PERMISSION`.

Treat `WORKTREE_DIRTY` paths as review evidence. Preserve files whose delivery scope is unclear; do not automatically stash, delete, ignore, or commit them. Push, PR, required-check, and merge blockers belong to separate phases. `ALREADY_MERGED` means stop publication retries and continue with post-merge reconciliation for the exact PR head and merge commit.

Use diagnostics for safe observation and local validation only. Retry a read-only observation when the diagnostic marks the evidence retryable. Host denial, missing Human approval, stale scope, missing/failing required checks, or a changed candidate requires the named approval, review, or revalidation step; diagnostic output never supplies permission to publish or merge.
