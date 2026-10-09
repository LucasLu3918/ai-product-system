# OpenCode compatibility and acceptance

The adapter uses native global AGENTS, canonical Skill/Command projections, a managed V2 plugin, and review-only MCP config. It does not select models, change user JSONC, download OpenCode or register MCP automatically. The plugin injects compact AIPS context before each primary model dispatch, uses the permission hook for supported native file actions, and registers one scoped `creative_execution` tool for local EPHEMERAL bundles. Isolated macOS OpenCode v2.0.24 acceptance verifies native hooks; overall governance remains **ADVISORY** because arbitrary Shell effects, other MCP/custom tools and out-of-process writes remain outside the guard.

## Contract profiles

| Interface | V1 profile | V2 profile |
|---|---|---|
| Global instructions | config root `AGENTS.md` | config root `AGENTS.md` |
| Skills | `skills/<id>/SKILL.md`, aligned name/description | same path; ID is path-derived, name is a label |
| Commands | `commands/aips-*.md`, `$ARGUMENTS` | same native Markdown projection |
| MCP preview | `mcp.aips`, local command + environment + enabled | `mcp.servers.aips`, local command + environment |
| Installation | detect executable; parsed major 1/2 required | unknown/probe-failed version preserves files and reports conflict |

The owned `plugins/aips-opencode.ts` projection is installed only for a positively detected V2 runtime. V1 retains its instruction/Skill/Command projections. The V2 plugin exports the documented `id`/`setup` shape directly so a global projection does not depend on resolving a package from the user’s plugin directory; install/status/doctor/uninstall share digest-bound ownership and conflict behavior.

## Readiness and enforcement boundary

The creative `review-assist` schema is a separate bounded action. The adapter requires a current-user review grant and active Session root, while the tool reports advisory results without changing execution review or acceptance state.

Creative continuation uses only in-memory state bound to the active Session root, a short TTL, finite turns and remaining outputs. Host-version discovery is not native acceptance evidence, and the synthetic lifecycle does not claim real model inference.

The cross-runtime `aips project diagnose` command reports configured status and static MCP capability only. It cannot establish that this OpenCode version loaded Context, invoked a Hook or executed a Tool; retain UNVERIFIED until the version-bound native acceptance evidence proves each effect.

Native v2.0.24 creative preparation is verified through Code Mode execute calling the catalog-provided tools.creative_execution. The V2 prompt-admission hook derives the mutation grant from the current user prompt before it is admitted, binds it to the Session root and bounded output count, and stores only a prompt digest; a new prompt revokes the prior grant. Model-dispatch Context remains for advisory routing and cannot grant creative authority. No real model inference is part of this acceptance.

Creative actions now include discover and configure. Context supports array/messages/data envelopes; only user messages can authorize mutations. A native-tool callback fixture covers action routing, while real OpenCode hook acceptance remains separately version-bound. Raster requests cannot silently become SVG; no local weights or real inference are implied by discovery.

Prompt classification returns independent `domain`, `intent`, and `effect` dimensions while preserving the legacy category/mutation/topics tuple. L0 is chat-only; L1 allows a new local creative asset in a non-Git workspace when the target is confined and absent; L2 requires current, READY Project Intelligence for supported project writes; L3 external actions remain subject to the existing Human approval gate. Prompt classification selects context; the native action hook makes a second decision from the operation and target.

Every Context and native write decision resolves the directory from `ctx.session.get({ sessionID })`; plugin `ctx.location` is not treated as the active Session root. Context is capped at 12,000 UTF-8 bytes. Permission decisions refresh Context against the current target immediately before evaluation. AIPS CLI and guard children use asynchronous bounded subprocesses with cancellation, output limits, and termination escalation. Session Context is deduplicated only while in flight and reused for at most one second; permission checks always refresh it. The bounded trace records prompt admission, Context, permission and Shell hook durations separately. These timings are observational; no latency improvement is claimed without host measurements.

The plugin reports three distinct runtime facts: hook delivery is configured, supported native permission checks are active in the plugin, and host-version acceptance remains `UNVERIFIED` unless the exact version passes the isolated native acceptance procedure below. `OPENCODE_VERSION` is recorded only as a reported version and never upgrades acceptance status by itself.

For EPHEMERAL creative sessions, the plugin runs a read-only scan of supported image/SVG metadata. At most 24 relative asset paths enter Context. The external cache is under `XDG_CACHE_HOME/aips/creative-workspaces/`, mode 0600, and does not store prompt or asset contents. Use `aips creative scan --project PATH` to refresh it and `aips creative next-version --project PATH --target RELATIVE_ASSET` to suggest an unoccupied versioned output path; the command never creates or overwrites the suggested file. EPHEMERAL remains the existing project mode and no `.ai/` folder is created.

The Shell policy parses a small command subset and rejects known execution, file-output, redirection, configuration, and path-escape options. Its AIPS allowlist contains only fixed read-only diagnostics and path-confined Creative Preflight; it does not allow generic Python, Shell, or arbitrary AIPS subcommands. Unsupported commands are replaced with a failing command. This string-level command check is not a complete process sandbox and cannot cover effects initiated outside the parsed command. Other MCP/custom tools and out-of-process writes remain outside this guard. External actions stay within existing Human approval authority; the plugin itself does not grant them.

The `creative_execution` tool binds to the active Session root and requires a non-Git EPHEMERAL workspace. Its `prepare` action creates versioned character/style Profiles and an unconfigured Bundle under an explicit relative scope without overwriting; `preflight` reads an existing Bundle without starting generation; `execute` requires an explicit action and writes only create-only PNG/JPEG/WEBP outputs plus a provenance manifest under the Bundle output scope. MFLUX model/operation pairs map to fixed CLI executables and argument shapes; FLUX.1 edit accepts one reference, while FLUX.2/Qwen `--image-paths` edit accepts up to eight staged references. The bounded ComfyUI workflow accepts exactly one hash-checked reference. The local helper blocks model downloads, non-loopback ComfyUI endpoints, redirects, proxies and custom ComfyUI nodes. Its trace excludes prompts, raw images and filesystem paths. This boundary applies only to this AIPS-owned tool; it does not extend to user-installed MCP tools.

`aips harness trace [--limit 1..100]` reads bounded events from `$XDG_STATE_HOME/aips/opencode/events.jsonl` (default `~/.local/state/aips/opencode/events.jsonl`). Trace records contain plugin setup, coarse task classification, readiness/decision, duration, byte count, and one-way session/project identifiers. They exclude prompts, credentials, asset contents, full paths, and model reasoning. The file is capped at 512 KiB; a full file is cleared before another event is appended.

`AVAILABLE_UNVERIFIED` describes installations without a matching native acceptance result; it does not prove plugin host discovery, model Context delivery or permission execution on that machine. `aips harness doctor` reports these boundaries separately and gives install/restart/new-session repair steps. The verified result is limited to the listed macOS/OpenCode version and mock-provider actions; it does not make the overall adapter TOOL_GUARDED.

MCP config defaults to V2; select `--opencode-version 1` for an explicit V1 preview. Both profiles bind `AIPS_MCP_WORKSPACE` to the configuration generation directory. Copying a preview into another project requires regenerating it there.

## Evidence (2026-10-08)

| Boundary | macOS / OpenCode v2.0.24 | Linux / WSL | V1 native |
|---|---|---|---|
| 27 canonical Skill descriptions/projection integrity | PASS lifecycle | deterministic lifecycle can run in CI | native UNVERIFIED |
| Skill native discovery and `tdd` body load | VERIFIED | UNVERIFIED | UNVERIFIED |
| Three native AIPS Commands discovered | VERIFIED | UNVERIFIED | UNVERIFIED |
| AIPS MCP server connected | VERIFIED, isolated stdio server | UNVERIFIED | UNVERIFIED |
| Global AGENTS delivery to model | official contract; model delivery UNVERIFIED | UNVERIFIED | UNVERIFIED |
| Automatic Skill selection / production-provider behavior | UNVERIFIED (mock only) | UNVERIFIED | UNVERIFIED |
| V2 AIPS plugin setup/discovery | VERIFIED on local 2.0.24 registry | UNVERIFIED | NOT_INSTALLED |
| Context injection hook execution | VERIFIED with loopback mock model | UNVERIFIED | NOT_INSTALLED |
| Permission hook execution | VERIFIED: new creative write ALLOW; existing asset edit DENY | UNVERIFIED | NOT_INSTALLED |
| Direct-action helper decisions | lifecycle and native permission propagation VERIFIED | deterministic only | NOT_INSTALLED |
| Shell read-only allowlist | helper lifecycle VERIFIED; native replacement UNVERIFIED | deterministic only | NOT_INSTALLED |
| MCP/custom-tool write protection | OUT OF SCOPE / UNVERIFIED | UNVERIFIED | UNVERIFIED |

Reproduce deterministic ownership, conflict, corruption, symlink, interruption, drift, Shell side-effect, creative cache, trace privacy and removal checks with `python3 tests/evidence/opencode_integration_lifecycle.py`. Optional native acceptance uses an explicitly supplied installed V2 binary and a local loopback OpenAI-compatible mock model. It verifies the actual provider request contains AIPS Context, the native file tool allows a new EPHEMERAL creative asset, and it denies modification of an existing asset with incomplete Project Intelligence:

```sh
python3 tests/evidence/opencode_native_acceptance.py --binary /absolute/path/to/opencode
```

The native check uses temporary HOME/XDG/config/data, a non-Git session workspace, private loopback servers and transient server authentication. It loads a Skill with `resume: false`, verifies session-root binding, connects local MCP, and sends model requests only to the local mock. Plugin initialization is asynchronous, so discovery uses bounded polling. Test secrets and raw server logs are never emitted. When no OpenCode V2 executable is supplied, native model and permission acceptance remain UNVERIFIED; deterministic lifecycle tests do not substitute for it.

Installation/doctor report file integrity and version probing separately; merely detecting v2.0.24 on another machine cannot confer this acceptance result. Modified or unowned same-name files are preserved, damaged manifests/path escapes/symlinks block writes, and changing config roots requires reconciling the previous ownership state first. Interrupted checkpoints keep conservative ownership and may need manual review before retry.

Official contracts: [V2 Skills](https://opencode.ai/v2/docs/skills/), [V2 Commands](https://opencode.ai/v2/docs/commands/), [V2 Instructions](https://opencode.ai/v2/docs/instructions/), [V2 MCP](https://opencode.ai/v2/docs/mcp/). V1 compatibility follows the explicitly selected [V1 documentation](https://opencode.ai/docs/).

The local creative executor registers Z-Image Turbo generate via the dedicated MFLUX command or the fixed ComfyUI split-loader API workflow. ComfyUI verifies the local UNET, Qwen `lumina2` CLIP and VAE inventories and remains generate-only. Existing native request authority and configure/preflight/execute contracts apply without a new permission surface.

The OpenCode configure schema exposes the registered `model_profile`, `unet_name`, `clip_name` and `vae_name` fields. Read-only discovery checks only `127.0.0.1:8188`; FP8 compatibility remains advisory and real inference remains unverified.

The optional generate-set action accepts a bounded project-relative job manifest and maps only to the current prompt's explicit execute grant. Its shared CLI validates every Bundle, runs per-item preflight, continues after failures, and records hash-bound results for safe resume.
