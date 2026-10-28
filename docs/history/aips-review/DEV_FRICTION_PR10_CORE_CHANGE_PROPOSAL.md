# Core Change Proposal: Dev Friction PR10 — Profile Switch Mechanism (Default Strict)

## Approved outcome

Add the mechanism by which a person, and only a person, switches AIPS profile relaxations: `aips profile show` and `aips profile set`. Every switch defaults OFF and no relaxation is enabled in this PR. The switch allow-list is fixed in code, so PR11 adds relaxations by adding entries rather than by changing the mechanism (D8). The active profile is visible in Turn Context and as field names in publication diagnostics.

Core Change Approval: the human user approved the full dev-friction plan scope including D8. This record applies that approval to exactly the PR10 scope below.

## Scope

- `scripts/aips_profile.py` (new): switch allow-list (`SWITCHES`, empty), bounded loader (`load_profile`), Turn Context line (`turn_context_line`), publication field summary (`diagnostic_fields`), `show` (text or stable JSON) and `set` (interactive confirmation, atomic private write) with a CLI entry point.
- `scripts/aips_cli/dispatch.sh`, `scripts/aips_cli/help.sh`: route and document `aips profile show|set`.
- `scripts/protected_paths.py`: the PR3 guard additionally denies an agent Bash invocation of `aips profile set` (verb `aips` with arguments `profile set`). The existing profile-file and profile-directory categories are unchanged.
- `scripts/turn_context_hook.py`: one line, `aips_profile=strict` plus `aips_profile_non_default=` and `aips_profile_status=INVALID reason=` when applicable; a fallback line when the profile module cannot be imported.
- `scripts/publication_diagnostics.py`: `profile` block in the `doctor` result with `name`, `status`, `non_default_fields` and `reason_code` only.
- `tests/test_profile_switch.py` (new, 35 tests), `tests/test_protected_path_guard.py` (one subprocess guard test for `aips profile set` and profile reads).
- `tests/fixtures/plan21-contract-golden-vectors.yaml`: the pinned stdout digest of `aips --help` and `aips help` is updated for the two additive usage lines (the same procedure PR6 used).
- `tests/scenarios/272-profile-switch-mechanism.md` (new) and `tests/scenario_coverage.yaml`; `docs/human/CONFORMANCE_CURRENT.md` regenerated.
- Docs (one localized sentence each): `docs/human/USER_GUIDE.md` (Security section, Traditional Chinese) and `harness/HARNESS_PROTOCOL.md` (Mutation safety section, English).
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` is intentionally not edited; matrix entries are reported to the integration owner.

## Profile file format (version 1)

Path: `$XDG_CONFIG_HOME/aips/profile.yaml`, or `~/.config/aips/profile.yaml` when `XDG_CONFIG_HOME` is unset. The file is reported only with the fixed label `~/.config/aips/profile.yaml`.

```yaml
version: 1
settings:
  <switch-id>: true | false
```

- Missing file: every switch keeps its code default (strict).
- Malformed YAML, a non-mapping document, a `version` other than integer 1, a non-mapping `settings`, an unknown top-level key, an unknown switch key, a non-boolean value, a symlink, a non-regular path, an unreadable file or a file over 16 KiB: fail closed. All switches revert to defaults, the whole file is ignored, and a bounded diagnostic is reported (reason code, up to eight field names matching `^[a-z][a-z0-9_]{0,63}$`, otherwise `<invalid-key>`).
- Allow-list: `SWITCHES` in `scripts/aips_profile.py`. It is empty in PR10. Each entry carries a default (must be `False`), a bilingual security implication and nothing else. Keys outside the allow-list are never accepted from the file or from `set`.

## Command contract

- `aips profile show [--format text|json]`: JSON has sorted keys and includes `schema_version`, `profile` (`strict`), `status` (`DEFAULT`, `LOADED` or `INVALID`), `profile_file`, `switches` (value, default and source per switch), `non_default_fields` and `diagnostic`.
- `aips profile set <key> <true|false>`:
  1. Refuse with `PROFILE_SET_REQUIRES_TTY` unless stdin and stderr are both terminals. Nothing is written.
  2. Refuse `PROFILE_KEY_NOT_ALLOWED` for a key outside the allow-list, and `PROFILE_VALUE_INVALID` for a value other than `true` or `false`.
  3. Refuse `PROFILE_FILE_INVALID` when the existing file is invalid, so that a person repairs it instead of having it overwritten, and `PROFILE_VALUE_UNCHANGED` when the value does not change.
  4. Print the file label, key, old value, new value and the security implication to stderr. Require the exact phrase `SET <key> <value>`; anything else declines with `PROFILE_SET_DECLINED` and no write.
  5. Write atomically (temporary file, fsync, `os.replace`) with mode 0600 in a directory set to mode 0700, preserving the other settings in the file. Verify by reloading.
- No flag skips confirmation. The argument parser has no such option, and a test asserts that `--yes`, `--force` and `--no-confirm` are rejected.
- Refusals print a stable JSON payload with `status: BLOCKED`, `phase: profile_set`, `reason_code`, `profile_file` and a Traditional Chinese recovery sentence. The payload never echoes the submitted key or any path.

## Agent-write guard evidence

PR3 already denies Edit, Write, MultiEdit and NotebookEdit writes to `profile.yaml` and to `profiles/` under the config home, and Bash writes such as redirection, `tee`, `mv`, `cp`, `rm`, `sed -i` and `dd of=`. Existing tests cover these cases through the real hook subprocess. PR10 adds:

- `aips profile set` (and `/path/to/aips profile set`, including after `&&`, `;`, `bash -c` and `cd`) is denied with `PROTECTED_PATH_WRITE`, so an agent cannot reach the terminal gate through its own Bash tool. Reads (`aips profile show`) are allowed.
- The Edit and Write denial for `profile.yaml` is exercised by the new test module and remains covered by the existing tests.

Nothing in PR3 was weakened: the new branch only adds a denial, and every previous denial and allowance is unchanged.

## Why the security floor is not weakened

- No switch is enabled, and the allow-list is empty. Every future switch must default to `False` (test `test_every_switch_defaults_off`).
- Secret, PII and content scanning, publication authority, merge confirmation, node trust policy and loopback-only ComfyUI are untouched. The publication change is a read-only `profile` block in the doctor result.
- The mechanism only reads and writes the user's own AIPS config file. It makes no network request and never reads the install directory.
- Diagnostics report switch names, status and reason codes only. Neither switch values nor paths appear in Turn Context or the doctor result.
- The TTY gate and the typed phrase are local guards. The agent guard blocks the agent's Bash form of `aips profile set`. The host confirmation remains the authority for the change.

## Compatibility

- With no `profile.yaml`, existing behaviour is unchanged: all protections and publication decisions are identical; Turn Context gains one line (`aips_profile=strict`) and the doctor result gains one additive `profile` key. The unit test `test_missing_file_is_strict_defaults` and the Turn Context test assert this.
- `aips --help` and `aips help` gain two additive usage lines; the plan21 golden digest is updated accordingly.

## Out of scope

- Any relaxation switch (PR11): Claude co-author trailer exact-match allowance (D2), restricted import of new topology workflows (D5), background targeted refresh after merge.
- Blocking `python -c` or other interpreter-based writes to `profile.yaml`; the PR3 guard continues to label Bash write detection as best-effort.

## Verification

Recorded in the final report of the PR10 implementation: ruff on changed Python files, the focused unit tests, the full `python -m pytest -q tests`, `python tests/validate_repository.py`, `python scripts/capability_registry.py check`, `python tests/evidence/plan21_contract_baseline.py` and the repository preflight after commit.

## Human approval

- Core Change Approval: the human user approved the full dev-friction plan scope including D8; this record applies it to exactly the PR10 scope above.
- Publication: not requested; no push, PR or merge.
