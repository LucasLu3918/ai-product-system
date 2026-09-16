# Project Intelligence

Project Intelligence is the reusable, evidence-grounded understanding layer for existing projects.

It replaces Project Knowledge as the long-term cache model. Existing `.ai/knowledge/` remains readable for migration compatibility, but new reusable discovery belongs in Project Intelligence.

## Goals

- understand an existing project once, then reuse that understanding across Agents and turns;
- preserve authoritative project instructions/docs instead of duplicating them;
- make architecture, data flow, module boundaries, contracts and change impact discoverable;
- keep mutation aligned with valid project-native conventions;
- refresh only affected knowledge when the project or AIPS intelligence schema changes.

## Storage

Attached project:

~~~text
.ai/intelligence/
├── PROJECT_INTELLIGENCE.yaml
├── SOURCE_REGISTRY.yaml
├── IMPACT_GRAPH.yaml
├── PROJECT_OVERRIDES.yaml
├── topics/
│   ├── architecture.md
│   ├── data-flow.md
│   ├── modules.md
│   ├── conventions.md
│   ├── testing.md
│   ├── security.md
│   └── operations.md
└── reviews/
    └── PROJECT_INTELLIGENCE_REVIEW.html
~~~

Ephemeral project:

~~~text
~/.config/aips/projects/<project-id>/intelligence/
└── same canonical structure
~~~

EPHEMERAL means no project-local persistent workspace. AIPS may keep an external cache without writing into the repository.

## Canonical machine-readable files

- `PROJECT_INTELLIGENCE.yaml` — status, project identity, revision/freshness, topic pointers, architecture summary, schema/version.
- `SOURCE_REGISTRY.yaml` — authoritative/native/project sources, scope, runtime auto-load coverage and hashes.
- `IMPACT_GRAPH.yaml` — machine-readable API/data/event/module/consumer relationships.
- `PROJECT_OVERRIDES.yaml` — user-approved additions, exceptions, exclusions and approved inferences.

Generated HTML is a review view, never a source of truth.

## Three-axis state

Keep these independent:

~~~yaml
readiness: READY | PARTIAL | BLOCKED
review: UNREVIEWED | REVIEWED | CHANGES_REQUESTED
freshness: CURRENT | STALE
~~~

A project may be technically READY/CURRENT while human review remains UNREVIEWED.

Human review blocks work only when a material unresolved interpretation affects the current change.

## Initial Intelligence Bootstrap

Initial bootstrap is read-only by default.

~~~text
Existing runtime/project instructions + official docs
→ repository topology
→ manifests / runtimes / frameworks
→ entry points
→ module / dependency boundaries
→ API / DB / events / external I/O
→ representative implementations
→ tests / security / operations
→ valid repeated conventions
→ Impact Graph
→ coverage/confidence check
→ persist Intelligence
→ deterministic HTML review
~~~

"Whole-project understanding" does not mean reading every file. Use breadth-first discovery followed by targeted depth until critical areas are sufficiently understood.

Do not run unknown project binaries, package installs, migrations, containers or arbitrary scripts merely to discover architecture. Runtime evidence requiring execution is marked pending and handled in an approved execution phase.

## Source registry and deduplication

Storage deduplication and runtime-context deduplication are different problems.

If `AGENTS.md` already contains an architecture rule, do not copy that rule into a topic. Register a pointer:

~~~yaml
path: AGENTS.md
authority: project_instruction
auto_loaded_by:
  - codex
~~~

A Runtime that does not auto-load that source may still be instructed to load the relevant file for the turn.

Never assume a source is visible to every Runtime merely because it exists.

## Authority

Project Intelligence is below:

1. external platform/safety requirements;
2. AIPS Constitution/governance;
3. current explicit user decision;
4. applicable runtime-native/project instructions;
5. accepted ADR/contracts/official docs;
6. approved canonical Product/Brand/Visual/Quality artifacts.

`PROJECT_OVERRIDES.yaml` records explicit user/project authority decisions about derived Intelligence. A later scan must not silently delete or override them.

If new evidence conflicts with an override, mark a conflict for human review.

## Intelligence types

Derived statements remain classified as:

- FACT;
- INTERPRETATION;
- OBSERVED_CONVENTION.

Only valid conventions should be preserved during implementation. Unsafe or demonstrably broken patterns are not copied merely because they are common.

## Freshness

Freshness is not "HEAD changed".

Track relevant evidence:

- Git HEAD / branch / worktree identity;
- uncommitted changed paths;
- watched source paths/globs;
- selected instruction/config/schema hashes;
- intelligence schema version;
- relevant AIPS version requirements.

Targeted refresh only affected topics.

AIPS schema upgrade order:

~~~text
Schema current?
├─ yes → no action
└─ no
   → deterministic migration possible?
      ├─ yes → migrate
      └─ no → discover only missing evidence
~~~

## Branch / worktree

Project identity distinguishes repository lineage and active worktree/revision. Stable repository-level knowledge may be reused, but freshness is evaluated against the active workspace.

## Concurrency

Project Intelligence has one writer per project intelligence store.

Writers use:

~~~text
lock
→ write temporary generation
→ validate
→ atomic replace
→ release lock
~~~

Readers continue using the last valid generation.

## Sensitive data

Do not persist secret values or sensitive payload bodies in Intelligence or HTML.

Never persist:

- credentials;
- API tokens;
- private keys;
- passwords;
- secret environment values;
- unnecessary personal/customer payload data.

It is acceptable to record structural facts such as "database credentials are required" without copying the credential.

## Human review

Generate `PROJECT_INTELLIGENCE_REVIEW.html` deterministically from canonical Intelligence.

The review should show:

- overview / identity / freshness;
- architecture and data flow;
- modules and dependencies;
- APIs/contracts/data/events;
- conventions;
- security/testing/operations;
- impact graph;
- provenance/confidence;
- authoritative pointers;
- unknowns;
- overrides/exceptions/exclusions.

The HTML is self-contained and must not require CDN/network access.

User corrections persist in `PROJECT_OVERRIDES.yaml`, not by editing generated HTML.

## Context loading

Every turn resolves the Intelligence index, but does not reload every topic.

~~~text
Current task
→ Turn Context Manifest
→ relevant authoritative sources
→ relevant Intelligence topics
→ optional evidence only when required
~~~

## Migration from v0.8 Project Knowledge

If `.ai/knowledge/KNOWLEDGE_INDEX.yaml` exists and no Intelligence exists:

1. preserve the old files;
2. register them as migration sources;
3. map authoritative pointers into SOURCE_REGISTRY;
4. map stable derived topics into Intelligence topics;
5. do not duplicate existing canonical Visual/Quality/Brand/Product artifacts;
6. mark migration provenance;
7. stop using `.ai/knowledge/` as the primary write target.
