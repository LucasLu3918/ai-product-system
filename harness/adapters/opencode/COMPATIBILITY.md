# OpenCode compatibility and acceptance

The adapter uses native global AGENTS, canonical Skill/Command projections and review-only MCP config. It does not select models, change user JSONC, download OpenCode or install a plugin. Native discovery/load plus existing MCP support meet this integration's access requirements; a native hook plugin is not required. Governance remains **ADVISORY**, with **UNSUPPORTED** pre-tool enforcement.

## Contract profiles

| Interface | V1 profile | V2 profile |
|---|---|---|
| Global instructions | config root `AGENTS.md` | config root `AGENTS.md` |
| Skills | `skills/<id>/SKILL.md`, aligned name/description | same path; ID is path-derived, name is a label |
| Commands | `commands/aips-*.md`, `$ARGUMENTS` | same native Markdown projection |
| MCP preview | `mcp.aips`, local command + environment + enabled | `mcp.servers.aips`, local command + environment |
| Installation | detect executable; parsed major 1/2 required | unknown/probe-failed version preserves files and reports conflict |

MCP config defaults to V2; select `--opencode-version 1` for an explicit V1 preview. Both profiles bind `AIPS_MCP_WORKSPACE` to the configuration generation directory. Copying a preview into another project requires regenerating it there.

## Evidence (2026-10-08)

| Boundary | macOS / OpenCode v2.0.24 | Linux / WSL | V1 native |
|---|---|---|---|
| 27 canonical Skill descriptions/projection integrity | PASS lifecycle | deterministic lifecycle can run in CI | native UNVERIFIED |
| Skill native discovery and `tdd` body load | VERIFIED | UNVERIFIED | UNVERIFIED |
| Three native AIPS Commands discovered | VERIFIED | UNVERIFIED | UNVERIFIED |
| AIPS MCP server connected | VERIFIED, isolated stdio server | UNVERIFIED | UNVERIFIED |
| Global AGENTS delivery to model | official contract; model delivery UNVERIFIED | UNVERIFIED | UNVERIFIED |
| Automatic Skill selection / model execution | UNVERIFIED (no provider calls) | UNVERIFIED | UNVERIFIED |
| Native pre-tool governance guard | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED |

Reproduce deterministic ownership, conflict, corruption, symlink, interruption, drift and removal checks with `python3 tests/evidence/opencode_integration_lifecycle.py`. Optional native acceptance uses an explicitly supplied installed V2 binary:

```sh
python3 tests/evidence/opencode_native_acceptance.py --binary /absolute/path/to/opencode
```

The native check uses temporary HOME/XDG/config/data, a private loopback server and transient server authentication. It loads a Skill with `resume: false`, inspects session evidence and connects local MCP without model execution. Plugin initialization is asynchronous, so discovery uses bounded polling. Test secrets and raw server logs are never emitted.

Installation/doctor report file integrity and version probing separately; merely detecting v2.0.24 on another machine cannot confer this acceptance result. Modified or unowned same-name files are preserved, damaged manifests/path escapes/symlinks block writes, and changing config roots requires reconciling the previous ownership state first. Interrupted checkpoints keep conservative ownership and may need manual review before retry.

Official contracts: [V2 Skills](https://opencode.ai/v2/docs/skills/), [V2 Commands](https://opencode.ai/v2/docs/commands/), [V2 Instructions](https://opencode.ai/v2/docs/instructions/), [V2 MCP](https://opencode.ai/v2/docs/mcp/). V1 compatibility follows the explicitly selected [V1 documentation](https://opencode.ai/docs/).
