# Scenario 233: Public CLI Help and Error Contracts

## Given

- AIPS exposes grouped shell, harness, MCP, project, system, evolution and skills commands.

## When

- A user requests group help or supplies an unsupported subcommand.

## Then

- Supported group `--help` routes return status 0 and a concise usage line.
- Unknown subcommands return nonzero with a group-specific diagnostic.
- Help routing remains in the existing thin shell facade; library modules are not converted into CLI parsers.
- `aips skills list` reads canonical Skill frontmatter, supports exact capability/trigger filters, and emits text or JSON without modifying the generated index.
- Unknown list arguments fail; filters with no matches return a successful empty list.

## Evidence

- `scripts/aips_cli/dispatch.sh`
- `scripts/aips_cli/commands.sh`
- `scripts/skills_cli.py`
- `scripts/skill_index.py`
- `tests/evidence/skills_cli_lifecycle.py`
- `tests/validation/skills_cli_contracts.py`
- `tests/validation/registry.py`
