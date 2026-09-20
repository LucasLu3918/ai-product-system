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

## Codex post-execution evidence hook

Codex may have an AIPS-managed `PostToolUse` hook in the user-level hooks configuration.

The hook is a separate observability lane, not a Turn Context or authorization mechanism:

~~~text
apply_patch completes
→ Codex PostToolUse
→ AIPS sanitizer
→ bounded canonical event spool
→ later evidence analysis
~~~

Requirements:

- default disabled unless an explicit AIPS capture config enables it;
- async and bounded;
- matcher limited to apply-patch aliases;
- actual hook payload must report canonical `tool_name=apply_patch`;
- persist no raw tool input/output, transcript/session/turn content, private reasoning or secret-like values;
- unresolved outcome or sensitive input degrades/drops evidence and returns success to the completed tool path;
- preserve unrelated user hooks during install/uninstall;
- do not bypass Codex hook trust review;
- do not report `live_capture_verified=true` until a real trusted Codex session is exercised.

This lane cannot grant, revoke or widen Resource Authorization and cannot automatically remediate.

