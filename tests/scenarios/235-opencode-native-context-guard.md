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
- MCP/custom tools, arbitrary Shell effects, and out-of-process writes are explicitly outside the guard;
- installation and plugin discovery do not upgrade governance beyond ADVISORY without executed context and permission-hook acceptance.

## Evidence boundaries

Classification, direct-action decisions, path/symlink handling, Shell allowlisting, and install/update/doctor/uninstall lifecycle use deterministic local evidence. OpenCode v2.0.24 native acceptance verifies plugin registry discovery, Skills, Commands and MCP discovery. Context injection and an actual permission decision remain UNVERIFIED without a provider/model action; governance stays ADVISORY. No claim covers MCP/custom-tool writes or files changed outside OpenCode.
