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

