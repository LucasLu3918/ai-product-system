# Global Agent Harness Protocol

OpenCode composes a managed global instruction block and digest-owned native Skill/Command projections. Adapter Registry drives Host status and ownership; runtime verification remains separate from file integrity. Basic installation keeps MCP client configuration review-only and governance ADVISORY.

AIPS Global Harness makes AIPS available to supported Agent runtimes while preserving the user's existing Agent ecosystem.

## Turn-aware flow

OpenCode V2 installs an owned plugin that injects compact Context before primary dispatch and evaluates supported direct file permissions. Plugin setup remains distinct from verified action-level enforcement.

~~~text
User Prompt
→ runtime-native Turn/Context mechanism
→ compact AIPS Turn Context
→ runtime + project instructions
→ relevant Project Intelligence
→ AIPS orchestration when applicable
→ execution / verification / targeted refresh
~~~

Every turn may resolve current context. Every turn must not rescan the repository.

Adapter-facing machine-readable output stays on stdout and diagnostics stay on stderr. Invalid state and unavailable subprocesses use explicit failure status/reason codes; malformed hook input must fail closed rather than being treated as an empty valid request.

## Non-invasive invariant

AIPS does not replace or delete user-owned Agent instructions, Skills, project source or unrelated runtime settings.

Shared instruction files use reversible delimited managed blocks. Structured settings files receive only an AIPS namespaced hook entry.

## Capability

Report TURN_NATIVE / CONTEXT_ALWAYS / SESSION_ONLY / MANUAL / UNSUPPORTED separately from installation status.

## Project persistence

ATTACHED projects use `.ai/intelligence/`. EPHEMERAL projects remain source-clean but may reuse external Intelligence at `~/.config/aips/projects/<project-id>/intelligence/`.

Local Creative Bundle preparation is limited to an explicit project-relative scope in a non-Git EPHEMERAL project. It creates versioned Profile/Bundle files without overwrite and leaves engine/model/license provenance unconfigured; prepare never invokes a generator.

OpenCode creative discovery reports MFLUX command/version state and probes only `http://127.0.0.1:8188` for ComfyUI. Keep model, preflight and real-inference readiness separate, and preserve provider reason codes without local paths or credentials.

## Context budget

OpenCode V2 applies a 12,000-byte UTF-8 cap to its transient AIPS Context and uses a session/prompt/target cache; the bounded trace records duration and size without prompt text.

Load `SYSTEM_CORE.md` with minimal Harness rules and critical native/project instructions. Turn Context selects canonical task protocols by pointer; load only those protocols, then task-relevant Intelligence and optional evidence on demand. `SYSTEM.md` remains a compatibility router and is not part of the fixed system layer.

## Mutation safety

Optional creative `review-assist` is a separate current-user-authorized action bound to the active Session root; its local vision findings remain advisory and cannot grant write, generation or acceptance authority.

The OpenCode creative tool receives a fresh per-response grant; only bounded structured state tied to the same Session root can continue an active clarification. Cancellation, unrelated work, scope expansion, expiry and exhausted output budgets revoke continuation.

The creative tool normalizes native message envelopes and evaluates user-only requests independently of routing. Read-only discovery/preflight remain available without create intent. Configuration is an allowlisted create-only Bundle operation; revocation and requested-medium mismatch fail closed without generic YAML permission expansion.

Existing-project mutations require current enough Intelligence, relevant native rules, Change Impact, valid project-native style preservation, and verification of declared inputs/outputs/data/events/consumers.

The `impact-candidates` command is read-only discovery evidence. Candidate relationships remain unreviewed and cannot satisfy canonical graph coverage or mutation approval by themselves.

Missing required context fails closed for the affected mutation; general conversation fails soft.

## Uninstall

Remove only AIPS managed blocks/hooks/extensions. Preserve modified managed content with conflict warning. Preserve Project Intelligence cache unless the user explicitly requests cache removal.

## Resumable workflow state

For substantial multi-step engineering work, a Runtime may resume from AIPS run checkpoints rather than replaying conversation history.

Resume state never bypasses current Turn Context, Project Intelligence freshness, Change Impact, approval, security or verification rules. Revision drift makes the checkpoint STALE until affected evidence is refreshed.

## Optional post-execution evidence hooks

A runtime adapter may add a post-execution evidence hook only when the runtime exposes a native lifecycle point and the hook can remain narrower than the execution authority path.

Scenario 142 adds the first implementation for Gemini CLI `AfterTool` with these invariants:

- disabled by default;
- bounded matcher scope (`read_file|write_file|replace`);
- metadata-only structural projection;
- explicit system-temporary sink;
- no raw tool input/response persistence;
- non-enforcing `decision=allow`; Gemini CLI still waits synchronously for the AfterTool command to return;
- explicit truth that `critical_path=false` refers only to authorization/result-flow enforcement, while `synchronous_hook=true` / `latency_path=synchronous`; 
- disabled fast path returns allow in the shell wrapper without launching Python;
- capture failure degrades observability only;
- no Resource Authorization widening, remediation or publication authority.

Runtime-native contract verification and actual runtime execution verification are distinct. Source-controlled CI may verify hook schema/wiring while `live_runtime_execution_verified=false`; only an exact-candidate real-runtime Trial may promote that runtime-specific verification state.

## Exact-candidate real-runtime verification

Internal creative prompt compiler extraction preserves the existing `creative_execution` facade and does not alter native Harness permissions or tool signatures; exact output parity is covered by the repository lifecycle evidence.

Native acceptance records setup, hook delivery, permission enforcement and exact host version as separate evidence. A passing host/version fixture does not establish behavior for another version, provider, Shell surface or model instruction path.

OpenCode V2 Creative mutation acceptance must exercise the native prompt-admission hook and prove that a later or cancelled prompt revokes the grant; transcript Context alone is not authorization.

Runtime adapter source-contract verification is not the same as executing the actual runtime binary.

Scenario 143 pins Gemini CLI v0.60.0 and executes the bundled CLI, built-in file tools and linked AIPS extension on the exact PR head. Gemini CLI's official `--fake-responses` interface replaces provider inference only; it does not replace CLI/tool/hook execution.

A runtime may claim `live_capture_verified=true` for this bounded Gemini CLI integration only after that exact-head workflow succeeds. Provider/model session verification remains a separate state.

## Live provider-session verification boundary

Real runtime execution and live provider/model execution are distinct claims.

After Scenario 143, Gemini CLI may truthfully report runtime-specific `live_capture_verified=true`, but provider/model verification remains false until a trusted protected-main session executes with a protected credential.

Provider credentials must not be injected into unmerged PR code. A secure provider-session verification may only persist redacted/boolean evidence and must preserve the existing non-enforcing AfterTool semantics.

## MCP interoperability access plane

The `aips project diagnose` projection may report MCP static inspection and allowlisted Runtime status. It does not execute MCP tools or prove native Host delivery; absent version-bound runtime evidence stays UNVERIFIED.

The OpenCode V2 adapter exposes local creative execution as an explicit, preflight-gated tool; this path does not grant MCP or arbitrary Shell write authority.

Use `harness/MCP_GATEWAY.md` when a compatible host can connect through MCP.

MCP is a standard access plane, not a native-adapter replacement. Resources provide progressive disclosure over canonical AIPS sources; Prompts provide reusable host-model context; Tools expose bounded deterministic helpers. Tool-only Hosts use the read-only capability catalog/read/workflow Tools over the same canonical sources. MCP-only clients report governance enforcement as ADVISORY because the server cannot generally intercept host-native tools. Existing Runtime adapters remain responsible for verified TURN_NATIVE / TOOL_GUARDED behavior.

For a new MCP-compatible Host, start with the MCP access plane. Add a runtime-native adapter only after a verified per-turn hook, pre-tool guard or runtime-specific event source demonstrates an enforcement/evidence requirement that MCP cannot satisfy.

The gateway is local stdio, provider-neutral and credential-free. It emits review-only Cursor, Windsurf, GitHub Copilot CLI, Amp, Codex and generic configuration payloads, and does not silently register itself into client-owned configuration.

The Codex managed block preserves eligible runtime primary model preference and bounded primary execution; it does not mutate host model settings or grant auxiliary permissions.

**Plan19 architecture and runtime closure.**

Codex PreToolUse support remains `EXPERIMENTAL` and `ADVISORY`: the local probe denies only its harmless synthetic command. Do not infer live runtime coverage or change user-global hook configuration from this evidence.

Creative adapters share the closed executor registry, including Z-Image Turbo generate only through fixed MFLUX argv or the built-in ComfyUI split-loader workflow; local model inventory checks do not grant broader generation authority or arbitrary command arguments.
