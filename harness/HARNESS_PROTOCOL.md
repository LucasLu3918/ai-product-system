# Global Agent Harness Protocol

AIPS Global Harness makes AIPS available to supported Agent runtimes while preserving the user's existing Agent ecosystem.

## Turn-aware flow

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

## Non-invasive invariant

AIPS does not replace or delete user-owned Agent instructions, Skills, project source or unrelated runtime settings.

Shared instruction files use reversible delimited managed blocks. Structured settings files receive only an AIPS namespaced hook entry.

## Capability

Report TURN_NATIVE / CONTEXT_ALWAYS / SESSION_ONLY / MANUAL / UNSUPPORTED separately from installation status.

## Project persistence

ATTACHED projects use `.ai/intelligence/`. EPHEMERAL projects remain source-clean but may reuse external Intelligence at `~/.config/aips/projects/<project-id>/intelligence/`.

## Context budget

Load minimal Harness rules, critical native/project instructions, task-relevant Intelligence, then optional evidence on demand.

## Mutation safety

Existing-project mutations require current enough Intelligence, relevant native rules, Change Impact, valid project-native style preservation, and verification of declared inputs/outputs/data/events/consumers.

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

Runtime adapter source-contract verification is not the same as executing the actual runtime binary.

Scenario 143 pins Gemini CLI v0.60.0 and executes the bundled CLI, built-in file tools and linked AIPS extension on the exact PR head. Gemini CLI's official `--fake-responses` interface replaces provider inference only; it does not replace CLI/tool/hook execution.

A runtime may claim `live_capture_verified=true` for this bounded Gemini CLI integration only after that exact-head workflow succeeds. Provider/model session verification remains a separate state.

## Live provider-session verification boundary

Real runtime execution and live provider/model execution are distinct claims.

After Scenario 143, Gemini CLI may truthfully report runtime-specific `live_capture_verified=true`, but provider/model verification remains false until a trusted protected-main session executes with a protected credential.

Provider credentials must not be injected into unmerged PR code. A secure provider-session verification may only persist redacted/boolean evidence and must preserve the existing non-enforcing AfterTool semantics.

## MCP interoperability access plane

Use `harness/MCP_GATEWAY.md` when a compatible host can connect through MCP.

MCP is a standard access plane, not a native-adapter replacement. Resources provide progressive disclosure over canonical AIPS sources; Prompts provide reusable host-model context; Tools expose bounded deterministic helpers. Tool-only Hosts use the read-only capability catalog/read/workflow Tools over the same canonical sources. MCP-only clients report governance enforcement as ADVISORY because the server cannot generally intercept host-native tools. Existing Runtime adapters remain responsible for verified TURN_NATIVE / TOOL_GUARDED behavior.

For a new MCP-compatible Host, start with the MCP access plane. Add a runtime-native adapter only after a verified per-turn hook, pre-tool guard or runtime-specific event source demonstrates an enforcement/evidence requirement that MCP cannot satisfy.

The gateway is local stdio, provider-neutral and credential-free. It emits review-only Cursor, Windsurf, GitHub Copilot CLI, Amp, Codex and generic configuration payloads, and does not silently register itself into client-owned configuration.
