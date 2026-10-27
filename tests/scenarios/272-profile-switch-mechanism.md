# Scenario 272 — Profile Switch Mechanism (Default Strict)

## Given

- A temporary AIPS config home and temporary HOME; the real `~/.config/aips` is never read or written.
- The fixed switch allow-list in code. PR10 defines the mechanism with no relaxation enabled.
- The PR3 Claude Code guard hook running as a subprocess with a temporary HOME.

## When

- No `profile.yaml` exists, and `aips profile show` or Turn Context is rendered.
- A `profile.yaml` is malformed, contains an unknown key or a non-boolean value, is a symlink, or is oversized.
- A person runs `aips profile set` without an interactive terminal, with a wrong confirmation phrase, or with the exact phrase.
- An agent attempts Edit, Write or Bash writes to `profile.yaml`, the profile directory, or `aips profile set`.

## Then

- With no profile file, every switch keeps its strict default, Turn Context shows `aips_profile=strict` only, and publication diagnostics report the strict name with an empty non-default field list.
- A malformed file, an unknown key or a wrong type fails closed to all defaults and reports only a reason code and bounded field names. Unknown keys reject the whole file; no relaxation is accepted from it.
- `aips profile set` refuses without an interactive stdin and stderr, with the stable reason code `PROFILE_SET_REQUIRES_TTY`, and writes nothing. No flag skips confirmation.
- In a terminal, the command prints the old value, the new value and the security implication, then requires the exact phrase `SET <key> <value>`. Any other input declines and writes nothing.
- A confirmed change is written atomically as a 0600 file inside a 0700 directory. A failed replace leaves the previous file and no temporary file.
- The PR3 guard denies agent writes to `profile.yaml` and to `aips profile set` and still allows `aips profile show` and unrelated commands.

## Evidence

- `scripts/aips_profile.py`
- `scripts/protected_paths.py`
- `scripts/turn_context_hook.py`
- `scripts/publication_diagnostics.py`
- `scripts/aips_cli/dispatch.sh`
- `tests/test_profile_switch.py`
- `tests/test_protected_path_guard.py`
- `tests/fixtures/plan21-contract-golden-vectors.yaml`

## Limits

- The terminal gate is a local check, not an operating-system boundary. A process that can allocate a pseudo-terminal could imitate one; the agent-side guard blocks the agent's Bash form of `aips profile set`, and the host confirmation remains the authority.
- The guard is best-effort for Bash writes; interpreters such as `python -c` are not classified. Profile writes by other tools are not proven outside the covered forms.
- No relaxation is enabled in this scenario. Relaxation switches and their implications belong to the later PR that adds them to the allow-list.
