# Scenario 237: Read-only Project Diagnostics and Recovery Guidance

## Given

- AIPS already exposes `doctor`, Project Intelligence status, Harness resolution and MCP static inspection commands.
- A project may have missing, partial, stale or unavailable Project Intelligence.

## When

- A user runs `aips project diagnose <project-path>` in text, YAML or JSON format.

## Then

- The additive command returns an aggregate status with stable reason codes, safe messages, advisory next actions and verification commands.
- Missing, partial and stale Project Intelligence map to bounded recovery guidance; the command does not bootstrap, refresh, index, attach or repair anything.
- Child command errors and timeouts are reported without raw subprocess output, prompts, environment content, credentials or project source excerpts.
- Project files remain unchanged; an invalid project path is rejected.
- Harness configuration and MCP static capability do not claim successful native Hook, tool or live Host execution; unverified effects remain `UNVERIFIED`.

## Evidence

- `scripts/project_diagnostics.py`
- `scripts/aips_cli/project.sh`
- `tests/evidence/project_diagnostics_lifecycle.py`
- `tests/validation/static_contracts.py`
