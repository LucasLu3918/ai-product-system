# Scenario 233: Public CLI Help and Error Contracts

## Given

- AIPS exposes grouped shell, harness, MCP, project, system and evolution commands.

## When

- A user requests group help or supplies an unsupported subcommand.

## Then

- Supported group `--help` routes return status 0 and a concise usage line.
- Unknown subcommands return nonzero with a group-specific diagnostic.
- Help routing remains in the existing thin shell facade; library modules are not converted into CLI parsers.

## Evidence

- `scripts/aips_cli/dispatch.sh`
- `scripts/aips_cli/commands.sh`
- `tests/validation/static_contracts.py`
