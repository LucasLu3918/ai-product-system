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

## Override reconciliation

`PROJECT_OVERRIDES.yaml` version 2 gives approved decisions a stable `subject`, `scope` and `value`.
Later discovery is reconciled through a separate candidate file rather than writing directly over approved state:

~~~yaml
version: 1
discoveries:
  - id: discovery-orders-persistence
    subject: architecture.orders.persistence
    scope: project
    value: repository
    type: OBSERVED_CONVENTION
    confidence: high
    evidence:
      - internal/orders/repository.py
~~~

Run:

~~~bash
aips intelligence reconcile --project /path/to/project --discoveries /path/to/discoveries.yaml
~~~

Reconciliation is deterministic and non-destructive:

- approved inferences, additional rules, exceptions and exclusions are preserved;
- matching values are reported as aligned;
- discoveries without an applicable override remain derived candidates;
- contradictory discoveries create stable `DISCOVERY_OVERRIDE_CONFLICT` records in both Project Intelligence and `PROJECT_OVERRIDES.yaml`;
- exclusion matches are conflicts rather than silently reintroduced inferences;
- conflict records persist hashes/pointers/evidence metadata, not duplicate raw discovered values;
- generated Human Review HTML surfaces the conflict;
- legacy unkeyed override entries are preserved but are not guessed into reconciliation semantics.

A later reconciliation can clear AIPS-managed conflicts when the candidate evidence no longer contradicts approved state. Manually maintained conflicts are preserved.

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

Project identity follows `orchestration/PROJECT_IDENTITY.md`: repository_id represents lineage while workspace_id represents the active worktree. Stable repository-level understanding may be reused, but freshness is evaluated against the active workspace.

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


## Semantic enrichment and READY

Deterministic bootstrap intentionally stops at `PARTIAL`.

The Agent uses `DISCOVERY.yaml`, authoritative sources and targeted repository evidence to enrich applicable semantic topics.

Required baseline topics for a non-trivial existing project:

- architecture;
- data-flow;
- modules;
- conventions;
- testing;
- security.

Operations is evaluated when applicable; N/A requires a reason.

A topic is not complete merely because a Markdown file exists. Derived topics require type, evidence, and confidence where applicable.

After enrichment:

~~~bash
aips intelligence finalize --project /path/to/project
~~~

`finalize` validates semantic coverage and moves readiness to `READY` only when required topics are sufficiently represented.

Do not claim the project has been initialized merely from directory/file-name inventory.

## Existing-project automatic behavior

The user should not need to run initialization commands during normal Agent use.

For a material existing-project mutation:

~~~text
Turn Context says Intelligence MISSING/PARTIAL
→ Agent performs bootstrap
→ targeted semantic enrichment
→ finalize
→ Change Impact
→ mutation
~~~

The CLI commands are deterministic building blocks used by the Agent/Harness and remain available for debugging.

## Change-impact artifacts

Project Intelligence provides the reusable graph. Per-change impact remains a run artifact rather than permanent project policy.

Attached:

~~~text
.ai/runs/<change-id>/CHANGE_IMPACT.yaml
~~~

Ephemeral:

~~~text
~/.config/aips/projects/<project-id>/changes/<change-id>.yaml
~~~

Use:

~~~bash
aips intelligence impact-init --project /path/to/project --prompt "<task>"
~~~

The generated draft must be semantically completed before mutation when impact is material.

## Attach / detach migration

A project can switch storage modes without losing Intelligence.

~~~text
EPHEMERAL External Cache
→ aips attach
→ validated migrate into .ai/intelligence/
→ External copy removed after successful migration

ATTACHED .ai/intelligence/
→ aips detach
→ validated sync to External Cache
→ then archive .ai/
~~~

Never maintain two silently diverging canonical copies.

## Monorepo

For a monorepo, prefer:

~~~text
system-level Intelligence
+
component/topic Intelligence
+
shared contract/data/event relationships
~~~

A task against one component loads the system summary, that component's relevant topics, and shared dependencies from the Impact Graph. It does not preload unrelated applications.

## Review changes

Regenerate Human Review HTML when:

- initial bootstrap/enrichment completes;
- architecture/data-flow/module relationships materially change;
- Impact Graph changes materially;
- PROJECT_OVERRIDES changes;
- an Intelligence schema migration changes represented information.

Ordinary narrow fixes with no Intelligence change do not require HTML regeneration.
