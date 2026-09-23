# Portable Command Protocol

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
```

`render` is preview-only. `install` and `upgrade` write only AIPS-owned projections under `~/.config/aips/commands/`. Modified files are preserved and reported as `CONFLICT`; uninstall never removes a modified projection.

Portable Commands are an advisory access plane. They do not provide runtime-native tool enforcement, Git publish, merge, release, production, or Human approval authority. Host-native adapters remain separate.

Host placement and invocation claims must be verified before adding native integration. Unsupported or hosted-only surfaces use MCP or the generic renderer.
