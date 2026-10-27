# Scenario 235: OpenCode Native Context and Action Guard

## Given

- a Traditional Chinese or English request to inspect, discuss, create, or modify an SVG/image asset;
- an OpenCode V2 runtime with the AIPS managed plugin, or a V1/unknown runtime;
- a Git project with READY/CURRENT Project Intelligence, a stale/partial project, or a non-Git playground.

## When

- AIPS resolves prompt `domain`, `intent`, `effect`, and L0-L3 readiness;
- OpenCode dispatches a primary model request or evaluates a native file permission;
- the Harness installs, diagnoses, upgrades, or removes the runtime projection.

## Then

- Existing `classify_prompt()` and Context Manifest fields remain compatible, with additive dimensions and creative-asset routing;
- every primary model dispatch receives transient compact AIPS Context when the CLI succeeds;
- a new confined creative asset in a non-Git workspace may use L1 without full project Intelligence;
- a supported project write requires READY/CURRENT Intelligence, a confined target, and no unresolved authority conflict; missing/error/stale context denies that action;
- L3 external actions retain the existing Human approval gate;
- Shell permits only the bounded read-only allowlist and rejects operators, writes, and unsupported commands;
- V2-only plugin ownership is digest-bound and preserves unowned, edited, or unknown-version files; V1 gets no V2 plugin;
- each Context and native file decision resolves the active Session directory; plugin setup location is not reused across sessions;
- Context delivery remains within a 12,000-byte UTF-8 budget, and permission decisions refresh the Context for the active target;
- if the compact Context projection still exceeds 12,000 bytes, delivery remains unavailable and reports stable `context_compaction_over_budget`, source/projection byte counts and up to three fixed section names with serialized sizes; supported native file writes also deny before manifest policy evaluation; no section values, prompt, path or raw CLI output enter the user diagnostic or trace;
- the over-budget message gives read-only Context inspection and refresh-plan commands, preserves project-write denial, and the trace reader rejects unknown section names, excessive entries and oversized byte values;
- non-Git EPHEMERAL creative sessions receive a read-only asset/profile index from an external private cache; version suggestions never create or overwrite files or create `.ai/`;
- installation diagnostics distinguish supported major, unknown version, projection integrity, host discovery, and Hook execution, with a restart/new-session remediation;
- `aips harness trace` returns only allowlisted event fields and never prompt, credential, asset content, full path, or model reasoning;
- the optional V2 native acceptance sends actual Context through a local loopback mock model, performs one new creative write (ALLOW), and confirms one existing-asset edit is denied (DENY);
- the version/platform/source-bound acceptance report explicitly marks arbitrary Shell process effects, MCP/custom-tool effects, and out-of-process writes as UNSUPPORTED; a legacy report without this field leaves each category UNVERIFIED;
- the Shell policy rejects known command, argument, and path effects but is not represented as a complete process sandbox;
- MCP/custom tools and out-of-process writes are explicitly outside the guard;
- overall governance remains ADVISORY because arbitrary Shell effects, MCP/custom tools and out-of-process writes remain outside the guard, even when native hooks pass acceptance.

## Evidence boundaries

Classification, direct-action decisions, path/symlink handling, Shell argument policy, private creative cache, bounded performance/privacy trace, and install/update/doctor/uninstall lifecycle use deterministic local evidence. OpenCode v2.0.24 native acceptance verifies plugin registry discovery, Skills, Commands, MCP connection, loopback mock model Context delivery, session-root binding, and actual native file Allow/Deny decisions. It runs only when a compatible binary is supplied; a skipped/unavailable binary remains UNVERIFIED and overall governance stays ADVISORY. Linux/WSL, V1, production-provider behavior, MCP/custom-tool writes, arbitrary Shell effects and writes outside OpenCode remain unverified or out of scope.
