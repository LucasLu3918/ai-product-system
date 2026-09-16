# Global Agent Harness Protocol

AIPS Global Harness makes AIPS available automatically to supported Agent runtimes without taking ownership of the user's existing Agent ecosystem.

## Purpose

~~~text
Agent Runtime
→ Runtime Adapter
→ Minimal AIPS Bootstrap
→ Harness / Project Resolution
→ Runtime + Project Instruction Composition
→ AIPS Orchestration when applicable
→ Execution / Verification / Persistence
~~~

The harness is always available after installation. Full AIPS orchestration is activated only for applicable product/project/software work.

## Non-invasive invariant

AIPS MUST NOT overwrite, rewrite, delete or silently adopt user-owned:

- AGENTS.md / AGENTS.override.md;
- CLAUDE.md;
- GEMINI.md;
- runtime settings/configuration;
- user or project Skills;
- project source.

An Adapter may create an AIPS-owned runtime registration/file only when:

1. the runtime supports that integration;
2. no user-owned resource must be overwritten;
3. ownership can be recorded;
4. uninstall is reversible.

If safe automatic integration is not possible, mark the runtime `MANUAL`.

## Adapter preference

~~~text
Official Extension / Plugin
→ Official Hook / Context mechanism
→ Official namespaced registration
→ reversible AIPS-owned bootstrap file / wrapper
→ MANUAL
~~~

Do not patch an existing user file merely to achieve automatic coverage.

## Runtime coverage states

- `AUTOMATIC` — AIPS bootstrap is loaded automatically through an AIPS-owned integration.
- `MANUAL` — runtime detected, but safe automatic bootstrap is unavailable or blocked by an existing user-owned resource.
- `NOT_DETECTED` — runtime executable/config not detected.
- `CONFLICT` — a resource/name collision prevents safe installation.
- `ERROR` — integration attempted but verification failed.

Coverage is machine-specific. `aips harness status` is authoritative for the current machine.

## Ownership

Installation writes an Ownership Manifest under the AIPS config directory.

Only resources listed as AIPS-owned may be removed automatically.

For AIPS-owned plain files, keep a reference copy/checksum. If the live file no longer matches the installed AIPS copy, uninstall preserves it and reports the conflict rather than deleting possible user edits.

## Project resolution

Project selection order:

1. explicit project path supplied to the task/resolver;
2. current Git root, when present;
3. current working directory.

Then classify:

- `.ai/` exists → `ATTACHED`;
- no `.ai/` → `EPHEMERAL`.

Ephemeral Mode never creates `.ai/` implicitly.

## Instruction composition

Adapters expose runtime-native instructions; AIPS resolves project instructions and its own governance.

Do not copy runtime-native/project instructions into AIPS files just to normalize formats.

Material conflicts are surfaced through existing instruction-resolution rules.

## Update

AIPS system updates may change the Bootstrap/Adapter implementation. AIPS-owned adapters should either point to the system copy or be safely refreshable.

Never update an adapter by replacing a user-owned file.

## Uninstall

~~~text
Read Ownership Manifest
→ disable/unregister AIPS-owned adapters
→ remove only unchanged AIPS-owned bootstrap files
→ preserve modified/conflicting files
→ remove AIPS harness registry/config
→ preserve user/project instructions, skills, source and project .ai/
~~~

Repository and `.venv` lifecycle remain controlled by existing uninstall flags.

## Verification

A supported automatic adapter is healthy only when:

- runtime is detected;
- the AIPS-owned integration is present;
- Bootstrap target exists;
- ownership is recorded;
- uninstall path is known/reversible.

Use `aips harness doctor`.
