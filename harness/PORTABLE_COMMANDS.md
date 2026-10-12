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

`render` is preview-only. OpenCode installs commands into its native `commands/` directory. Codex, Claude Code, and Gemini CLI install Portable Commands as native Agent Skills: Codex and Gemini share `~/.agents/skills/<name>/SKILL.md`, while Claude Code uses `~/.claude/skills/<name>/SKILL.md`. Other Hosts keep managed reference projections under `~/.config/aips/commands/projections/<host>/`. Modified files are preserved and reported as `CONFLICT`; uninstall never removes a modified projection.

For OpenCode, `aips commands install aips.grill-me --host opencode` writes the native command projection. Invoke `/grill-me` or `/aips-grill-me`; `aips commands uninstall --host opencode` removes only unchanged, ownership-recorded AIPS commands. For Codex, Claude Code, and Gemini CLI, `aips commands install aips.grill-me --host <host>` writes a host-compatible `SKILL.md` with `name: grill-me` and `description` frontmatter. Invoke `$grill-me` in Codex and `/grill-me` in Claude Code or Gemini CLI. Codex and Gemini references share one host-neutral projection; removing one host keeps the files while another host still uses them. Other Hosts' renderer output remains a managed reference artifact, not an automatically registered native command.

`aips commands status --host <host>` checks native Skill ownership and drift for Codex, Claude Code, or Gemini CLI. `aips commands uninstall <command-id> --host <host>` removes only that command's recorded native Skill association or command projection. `aips commands uninstall --host <host>` removes all commands for one Host; `aips commands uninstall --all` removes all recorded command projections across Hosts. Unchanged generated files are removed. If a file was edited, it is kept and reported as `CONFLICT`, with ownership retained for a later safe retry. A same-name file that existed before AIPS recorded ownership is treated as a conflict and is never adopted or deleted.

Portable Commands are an advisory access plane. They do not provide runtime-native tool enforcement, Git publish, merge, release, production, or Human approval authority. Host-native adapters remain separate.

`aips.grill-me` is an explicit requirement-clarification wrapper. It asks one decision-focused question per turn, checks available evidence first and stops when material decisions are resolved. It reuses `orchestration/REQUIREMENT_CLARIFICATION.md`; it does not activate during ordinary requests.

Host placement and invocation claims must be verified before adding native integration. Codex, Claude Code, and Gemini CLI discovery paths use their native Agent Skills conventions; unsupported or hosted-only surfaces use MCP or the generic renderer.
