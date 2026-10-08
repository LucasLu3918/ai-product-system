# OpenCode compatibility and acceptance

The adapter uses native global AGENTS, canonical Skill/Command projections, a managed V2 plugin, and review-only MCP config. It does not select models, change user JSONC, download OpenCode or register MCP automatically. The plugin injects compact AIPS context before each primary model dispatch and uses the permission hook for supported native file actions. Runtime governance remains **ADVISORY** until action-level native acceptance proves enforcement.

## Contract profiles

| Interface | V1 profile | V2 profile |
|---|---|---|
| Global instructions | config root `AGENTS.md` | config root `AGENTS.md` |
| Skills | `skills/<id>/SKILL.md`, aligned name/description | same path; ID is path-derived, name is a label |
| Commands | `commands/aips-*.md`, `$ARGUMENTS` | same native Markdown projection |
| MCP preview | `mcp.aips`, local command + environment + enabled | `mcp.servers.aips`, local command + environment |
| Installation | detect executable; parsed major 1/2 required | unknown/probe-failed version preserves files and reports conflict |

The owned `plugins/aips-opencode.ts` projection is installed only for a positively detected V2 runtime. V1 retains its instruction/Skill/Command projections. The plugin uses `Plugin.define` from `@opencode/plugin`; install/status/doctor/uninstall share digest-bound ownership and conflict behavior.

## Readiness and enforcement boundary

Prompt classification returns independent `domain`, `intent`, and `effect` dimensions while preserving the legacy category/mutation/topics tuple. L0 is chat-only; L1 allows a new local creative asset in a non-Git workspace when the target is confined and absent; L2 requires current, READY Project Intelligence for supported project writes; L3 external actions remain subject to the existing Human approval gate. Prompt classification selects context; the native action hook makes a second decision from the operation and target.

The plugin checks native `edit`, `write`, and `patch` permission resources and limits Shell to a bounded read-only allowlist. Unknown Shell commands are replaced with a failing command. MCP/custom tools and writes outside OpenCode remain outside this guard. `AVAILABLE_UNVERIFIED` means the V2 plugin and helper are installed; it does not prove model context delivery or an executed permission decision. Do not describe the adapter as TOOL_GUARDED until runtime acceptance proves that boundary.

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
| V2 AIPS plugin setup/discovery | VERIFIED on local 2.0.24 registry | UNVERIFIED | NOT_INSTALLED |
| Context injection hook execution | UNVERIFIED (no model provider call) | UNVERIFIED | NOT_INSTALLED |
| Permission hook execution | UNVERIFIED (no native write attempted) | UNVERIFIED | NOT_INSTALLED |
| Direct-action helper decisions | lifecycle VERIFIED; native permission propagation UNVERIFIED | deterministic only | NOT_INSTALLED |
| Shell read-only allowlist | helper lifecycle VERIFIED; native replacement UNVERIFIED | deterministic only | NOT_INSTALLED |
| MCP/custom-tool write protection | OUT OF SCOPE / UNVERIFIED | UNVERIFIED | UNVERIFIED |

Reproduce deterministic ownership, conflict, corruption, symlink, interruption, drift and removal checks with `python3 tests/evidence/opencode_integration_lifecycle.py`. Optional native acceptance uses an explicitly supplied installed V2 binary:

```sh
python3 tests/evidence/opencode_native_acceptance.py --binary /absolute/path/to/opencode
```

The native check uses temporary HOME/XDG/config/data, a private loopback server and transient server authentication. It loads a Skill with `resume: false`, inspects session evidence and connects local MCP without model execution. Plugin initialization is asynchronous, so discovery uses bounded polling. Test secrets and raw server logs are never emitted.

Installation/doctor report file integrity and version probing separately; merely detecting v2.0.24 on another machine cannot confer this acceptance result. Modified or unowned same-name files are preserved, damaged manifests/path escapes/symlinks block writes, and changing config roots requires reconciling the previous ownership state first. Interrupted checkpoints keep conservative ownership and may need manual review before retry.

Official contracts: [V2 Skills](https://opencode.ai/v2/docs/skills/), [V2 Commands](https://opencode.ai/v2/docs/commands/), [V2 Instructions](https://opencode.ai/v2/docs/instructions/), [V2 MCP](https://opencode.ai/v2/docs/mcp/). V1 compatibility follows the explicitly selected [V1 documentation](https://opencode.ai/docs/).
