# Portable Command Protocol

The OpenCode renderer places canonical command projections in its native `commands/` directory, includes description frontmatter and forwards `$ARGUMENTS`. Its digest-bound ownership preserves collisions and user edits during upgrade/uninstall; model selection stays with the user.

AIPS Portable Commands expose one canonical workflow through host-native renderers. The canonical ID is stable (`aips.plan`), while a host may present it as `/aips.plan`, `/aips-plan`, `$aips-plan`, MCP, or a generic bootstrap.

The registry is `harness/commands/REGISTRY.yaml`; generated projections are thin wrappers and never replace `core/CONSTITUTION.md`, `SYSTEM.md`, or orchestration protocols.

## CLI

```bash
aips commands list
aips commands inspect aips.plan
aips commands render aips.plan --host cursor
aips commands install --host cursor
aips commands status
aips commands upgrade --host cursor
aips commands uninstall --host cursor
aips commands render aips.grill-me --host codex
aips commands install aips.grill-me --host opencode
```

`render` is preview-only. OpenCode installs commands into its native `commands/` directory; other Hosts store managed reference projections under `~/.config/aips/commands/projections/<host>/`. Modified files are preserved and reported as `CONFLICT`; uninstall never removes a modified projection.

For OpenCode, `aips commands install aips.grill-me --host opencode` writes the native command projection. Invoke `/grill-me` or `/aips-grill-me`; `aips commands uninstall --host opencode` removes only unchanged, ownership-recorded AIPS commands. For other Hosts, renderer output under `~/.config/aips/commands/projections/<host>/` is a managed reference artifact, not an automatically registered native command. Use MCP where supported, or inspect/render the command and invoke its declared `$...`/slash form through that Host's own supported mechanism. Install/uninstall projections with the same `--host`; do not copy over a Host's native command or Skill directory.

`aips commands uninstall --host <host>` removes only that Host's recorded command projections; omit `--host` to remove all recorded command projections. Unchanged generated files are removed. If a file was edited, it is kept and reported as `CONFLICT`, with ownership retained for a later safe retry. A same-name file that existed before AIPS recorded ownership is treated as a conflict and is never adopted or deleted.

Portable Commands are an advisory access plane. They do not provide runtime-native tool enforcement, Git publish, merge, release, production, or Human approval authority. Host-native adapters remain separate.

`aips.grill-me` is an explicit requirement-clarification wrapper. It asks one decision-focused question per turn, checks available evidence first and stops when material decisions are resolved. It reuses `orchestration/REQUIREMENT_CLARIFICATION.md`; it does not activate during ordinary requests.

Host placement and invocation claims must be verified before adding native integration. Unsupported or hosted-only surfaces use MCP or the generic renderer.
