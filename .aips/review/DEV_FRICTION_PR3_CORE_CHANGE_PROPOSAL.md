# Core Change Proposal: Installed System and Profile Write Protection, Preflight Degradation (Dev Friction PR3)

## Approval

Core Change Approval: the human user approved the full plan scope (`aips-dev-friction-plan.md`, PR3 row, D8). This record covers exactly the PR3 scope below and no other PR.

## Purpose

Stop an agent session from editing the installed AIPS system checkout (`~/.local/share/aips/system`) or AIPS profile settings in place, which made `aips system preflight` and `aips update` refuse with "System repo has local changes" and stalled unrelated creative work. When the installed checkout is dirty, preflight should continue on the installed version instead of stopping.

## Why this is a core/large change

It changes the shared PreToolUse guard (now also invoked for file-edit tools), the Claude Code hook registration written by the installer, and the preflight path of the CLI. A false deny blocks ordinary development; a false allow lets an agent change the installed system.

## Measured Baseline

- The Claude hook matcher was `Bash` only, so `Edit`, `Write`, `NotebookEdit` and `MultiEdit` on the installed system or profile files were never classified.
- `update_system` died on any local change in the installed checkout, including during `aips system preflight`.

## Proposed Scope

### In scope

- New module `scripts/protected_paths.py`:
  - Protected install roots: `$XDG_DATA_HOME/aips/system` (default `~/.local/share/aips/system`), the literal `~/.local/share/aips/system`, and `AIPS_INSTALL_DIR` when set. The recorded `system-dir` file is not used, because a development checkout may be recorded there and must stay writable.
  - Protected profile settings under the config home (`$XDG_CONFIG_HOME/aips`, default `~/.config/aips`): the directory itself, `profile*` files directly inside it, and `profiles/`. `profile_settings_path()` defines the PR10 file `profile.yaml` now.
  - File tools (`Edit`, `Write`, `MultiEdit` via `file_path`; `NotebookEdit` via `notebook_path`): targets resolved with `~` expansion, `realpath` (symlinks and `..`), relative to the hook payload `cwd`. Resolution failure denies only when the raw path mentions `aips`.
  - Bash, best-effort: redirections (`>`, `>>`, `>|`, `&>`, `>&`), `tee`, `rm`, `unlink`, `touch`, `mkdir`, `rmdir`, `truncate`, `chmod`, `chown`, `chgrp`, `shred`, `cp`/`install`/`ln`/`rsync` destinations (including `-t` and `-d`), `mv`, `sed -i`, `dd of=`, `git -C`/`--git-dir`/`--work-tree`/`GIT_DIR` with any verb outside a read-only allowlist (status, log, diff, show, rev-parse, ls-files, ls-tree, cat-file, grep, blame, describe, shortlog, rev-list, for-each-ref, show-ref, help, version), `cd` tracking, `bash|sh|zsh -c` and `eval` recursion (depth limit 3, then fail closed), wrapper commands (`env`, `sudo`, `command`, `nohup`, `time`, `exec`, `xargs`, ...). Shell-quoted `$HOME` and `~` are expanded; other runtime expansions are not classified.
- Hook integration in `scripts/governance_guard.py`: the check runs after runtime policy and before publication classification. Denial reason `PROTECTED_PATH_WRITE`; an unexpected exception in the check denies with `PROTECTED_PATH_GUARD_UNAVAILABLE` (fail closed). The diagnostic is static and input-free: it never echoes the path or command, and the next step is bilingual.
- Installer `scripts/manage_runtime_adapter.py`: the managed Claude guard group uses matcher `Bash|Edit|Write|NotebookEdit|MultiEdit`. The `onFailure: block` version logic is unchanged. The `PostToolUseFailure` group stays `Bash`.
- Preflight degradation in `scripts/aips_cli/maintenance.sh`: `update_system` takes an optional `dirty_mode`. `aips system preflight` and `aips preflight` pass `skip`: on local changes they warn with the installed version and commit, print read-only and human clean-up steps, skip the update and continue to `_preflight-after-update`. Explicit `aips update` keeps `refuse` and still dies without touching the tree. Doctor wording updated.
- Tests: `tests/test_protected_path_guard.py` (unit and real hook subprocess tests for allow and deny) and `tests/test_system_preflight_degradation.py` (CLI in a temporary system copy with a stub `bin/aips`).
- Documentation sync: one sentence each in `harness/adapters/claude-code/CLAUDE.md`, `harness/HARNESS_PROTOCOL.md`, `docs/human/HARNESS.md`, `docs/human/SECURITY_ASSURANCE.md`, `docs/human/INSTALLATION.md`.

### Out of scope

- Editing `~/.claude/settings.json` or any user-global hook configuration (the installer change applies only to newly installed or refreshed settings).
- Claiming complete Bash enforcement. Interpreters (`python -c`, `node -e`, `perl -i`), `patch`, pipelines that build paths at runtime, and unparsed syntax are not classified.
- Changing publication authority, secret or PII scanning, content safety, or merge confirmation. The guard only adds a deny before publication classification.
- Gemini tool names for file edits (the file-edit check applies to `claude-code` only; the Bash check applies to both runtimes as before).

## Human CLI Exemption

`aips update`, `aips install`, `aips preflight` and `aips system preflight` invoked by a human name no protected path, so the hook does not classify them as writes. The CLI keeps its own checks: `update` refuses on a dirty installed checkout, and `preflight` skips the update on a dirty checkout without discarding anything. A redirection or write command that names a protected path is still denied even when it accompanies a CLI command. A limitation is acknowledged: an agent could run `aips update` through Bash to fast-forward a clean installed checkout to the configured channel; this is the existing CLI behavior and is not widened by this change.

## Expected Files / Modules

- `scripts/protected_paths.py` (new), `scripts/governance_guard.py`, `scripts/manage_runtime_adapter.py`, `scripts/aips_cli/maintenance.sh`
- `tests/test_protected_path_guard.py` (new), `tests/test_system_preflight_degradation.py` (new)
- `harness/adapters/claude-code/CLAUDE.md`, `harness/HARNESS_PROTOCOL.md`, `docs/human/HARNESS.md`, `docs/human/SECURITY_ASSURANCE.md`, `docs/human/INSTALLATION.md`
- `.aips/review/DEV_FRICTION_PR3_CORE_CHANGE_PROPOSAL.md`, `.aips/review/DEV_FRICTION_PR3_SYSTEM_IMPROVEMENT_REVIEW.md`. The Core Change Test Matrix entries are consolidated by the integration branch owner.

## Impact

### Architecture / Contracts

No new trust boundary or authority path. The PreToolUse guard now also receives file-edit tool events from the managed Claude group. The deny envelope is unchanged except for the new reason code.

### Data / Migration

None. Existing settings files are updated by the installer on refresh; the old `Bash`-only matcher is replaced in the managed group only.

### Security / Reliability

Reads are never denied. Secret, PII and content scans, publication approval and Human merge confirmation are unchanged. The hook gains one earlier deny for protected writes and fails closed on an internal error. The preflight change narrows the update step only; it does not alter `update`'s refusal and never runs destructive Git commands.

### Compatibility / Rollback

Installed copies created before this change keep their old settings until `aips install` or harness refresh rewrites the managed group. Revert the candidate to restore the previous Bash-only matcher and the die-on-dirty preflight.

### Tests / Validation

Real hook subprocess tests (Edit family, Bash write forms, reads, CLI maintenance, git read/write verbs, symlink and traversal), shell preflight degradation with the installed copy cloned into a temporary directory, existing publication suites, governance command guard evidence, capability registry, repository validation and repository preflight.

### Secret / Credential Impact

Secrets required: NO. The guard reads no credentials; diagnostics contain no path or command text.

## Risks

- Bash coverage is incomplete by design. Documentation states the limit; the guard is not described as a boundary against a determined agent.
- A false deny is possible when a legitimate command writes under the installed system path from a development session; the diagnostic points to the development repository.
- Unparseable Bash that mentions `aips`, `.local/share` or `.config` is denied; this can block an unusual but harmless shell form, and the diagnostic says so.
