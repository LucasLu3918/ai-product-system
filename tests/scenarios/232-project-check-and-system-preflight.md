# Scenario 232: Project Check and System Preflight CLI

## Given

- AIPS supports EPHEMERAL and ATTACHED Projects with optional Project Intelligence.
- Existing users may invoke the top-level `aips preflight` command from scripts.

## When

- A user checks a valid Project or runs system preflight before implementation.

## Then

- `aips project check <path>` reports the Project mode and Intelligence freshness without writing, refreshing, or attaching the Project.
- Missing or stale Intelligence is reported as `UNKNOWN` or `STALE`; only an invalid project path makes project check fail.
- `aips system preflight <path>` routes through the established system update and validation lifecycle.
- `aips preflight <path>` remains behavior-compatible as a supported alias.

## Evidence

- `scripts/aips_cli/project.sh`
- `scripts/aips_cli/dispatch.sh`
- `tests/evidence/install_preflight_lifecycle.py`
- `tests/validation/static_contracts.py`
