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
freshness: CURRENT | STALE | UNKNOWN
~~~

A project may be technically READY/CURRENT while human review remains UNREVIEWED.
Git filename discovery uses NUL-delimited paths. Freshness examines the complete dirty-path set; only the returned display list is shortened. If the Git path scan fails, times out or reaches its output limit, freshness is UNKNOWN and mutation context fails closed rather than claiming CURRENT.

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

`aips intelligence refresh` is a narrow revision-only operation for an equivalent Git tree after squash/rebase reconciliation. It requires a clean worktree and identical old/current tree objects. A changed tree returns `SEMANTIC_REFRESH_REQUIRED`; it never rewrites semantic topics automatically.

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

### Override reconciliation

Later semantic discovery may emit structured `DISCOVERY.yaml` inferences with an `id`, `value`, and evidence. Run `aips intelligence reconcile-overrides` after such enrichment. The deterministic reconciler compares matching structured assertions in `approved_inferences`, `additional_rules`, `exceptions`, and `excluded_inferences`. It never replaces an approved override. A contradictory value is appended as an idempotent `OPEN` conflict in `PROJECT_OVERRIDES.yaml`.

Active authority conflicts are included in the Turn Context Manifest. Material mutation fails closed with `unresolved_authority_conflict` until a human resolves or dismisses the conflict. This mechanism surfaces registered semantic contradictions; it does not guess conflicts by keyword-matching arbitrary Markdown.

## Context loading

Every turn resolves the Intelligence index, but does not reload every topic.

~~~text
Current task
→ Turn Context Manifest
→ relevant authoritative sources
→ relevant stable Intelligence topics
→ bounded Retrieval Intelligence evidence
→ optional evidence only when required
~~~

## Retrieval Intelligence

Project Intelligence is the stable understanding and authority/provenance layer. Retrieval Intelligence is a rebuildable, non-canonical cache used to assemble just-in-time repository evidence for the current task.

The two layers are complementary:

~~~text
Stable Project Intelligence
  PROJECT_INTELLIGENCE / SOURCE_REGISTRY / IMPACT_GRAPH / OVERRIDES
                         +
Rebuildable Retrieval Intelligence
  source chunks / symbols / tests / Impact Graph boosts / Git history
                         ↓
                   bounded Turn Context
~~~

The retrieval database MUST NOT become a source of truth and may be deleted/rebuilt at any time. Canonical facts, approved overrides and authority precedence continue to live in Project Intelligence and project-native sources.

Default local retrieval uses multiple lanes rather than treating vector similarity as sufficient:

1. lexical repository search;
2. symbol-definition matching;
3. bounded exact-identifier structural relationship expansion;
4. related test evidence;
5. Impact Graph path boosts;
6. relevant Git commit/diff history.

An optional future semantic/embedding provider is an enhancement lane, not a dependency. If no semantic provider is configured, metadata reports `NOT_CONFIGURED` and deterministic/local retrieval remains available.

The rebuildable SQLite cache is workspace-scoped under the AIPS cache home. `RETRIEVAL_INDEX.yaml` beside Project Intelligence contains only metadata/provenance and explicitly marks the database as non-canonical.

Before indexing or returning snippets:

- respect Git ignore/exclusion behavior;
- exclude credential/secret path families;
- redact secret-like values;
- bind results to current Git HEAD and dirty-workspace fingerprint;
- incrementally refresh committed or dirty changed paths;
- return path/line or commit provenance plus content hash;
- enforce a token budget and bounded result count.

Use:

~~~bash
aips intelligence index --project /path/to/project
aips intelligence retrieve --project /path/to/project --prompt "<task>" --token-budget 6000
~~~

The Human normally does not need to run these commands. When the Turn Context reports `retrieval_index_required=true`, the Agent should build the index as an engineering preparation step. Missing/unavailable Retrieval Intelligence degrades to existing stable Project Intelligence; it does not silently claim semantic evidence and does not by itself change authority.

## Retrieval Quality Evaluation

Do not add a semantic provider, new parser/index dependency or ranking complexity merely because it is available. Measure the current retrieval layer first with a repository-specific evaluation suite.

~~~text
Declared task cases + expected source evidence
              │
              ├─ v0.20-style static topic context baseline
              │
              └─ current local hybrid Retrieval Intelligence
                              │
                              ▼
Precision@K / Recall@K / F1@K / MRR
history recall / irrelevant-context rate
token usage / observed latency
                              │
                              ▼
                   Evidence-only report
                              │
                    Human review of gaps
                              │
                decide next optimization
~~~

The baseline is explicitly a controlled v0.20-style static-topic comparison, not a claim that every historical v0.20 turn behaved identically. Evaluation scope is limited to task-specific repository evidence retrieval. It does not measure overall Agent task completion, stable Intelligence semantic correctness, model/provider quality or a production latency SLO.

Keep evaluation control data outside the indexed product source (or under the attached AIPS `.ai/` workspace, which Retrieval Intelligence excludes) so expected answers cannot contaminate retrieval results.

A suite declares:

- task query;
- expected relevant source paths;
- optional expected Git-history terms;
- baseline context files;
- top-K / result / token budgets;
- deterministic thresholds;
- case enforcement: `required` or `diagnostic`;
- dimensions such as language, monorepo/shared-module, low-lexical-overlap, synonymy or cross-file-call-chain.

`required` cases are release regressions: any threshold failure fails the evaluation suite. `diagnostic` cases are intentionally harder probes of capability boundaries: they still compute the same thresholds and retain explicit `FAIL` status, but their failure is aggregated as diagnostic gap evidence instead of blocking the suite. Diagnostic gaps must never be rewritten as PASS merely to keep CI green.

A report records Precision@K, Recall@K, F1@K, MRR, history recall, irrelevant-context rate, direct-source-recall delta and token use. It also records required pass/fail counts plus diagnostic gap IDs, dimension aggregation and failed-check aggregation so repeated structural gaps can justify a later retrieval-architecture review. Wall-clock latency is recorded only as an observation because shared CI timing is not a reliable pass/fail SLO. The result fingerprint binds the suite, repository revision/dirty state, deterministic metrics/checks and authority boundary; observed latency, machine-local paths and index timestamps are deliberately excluded from the fingerprint.

Use:

~~~bash
aips intelligence evaluate \
  --project /path/to/project \
  --suite retrieval-evaluation.yaml \
  --output retrieval-evaluation-report.json
~~~

Evaluation is non-authoritative. PASS or FAIL never enables embeddings, changes ranking weights, selects Tree-sitter/LSP/Sourcegraph, modifies code or grants publication authority. A material retrieval architecture change still requires normal System Self-Improvement / Core Change / Git Publish governance.

## Structural Retrieval

AIPS now adopts the bounded exact-identifier two-hop relation graph as part of normal Retrieval Intelligence after the controlled candidate passed the full corpus and Human Adoption Decision.

The adopted lane remains local, deterministic, provider-neutral and dependency-free:

~~~text
exact query symbol definition
        ↓
lexical-index bridge discovery
        ↓
bridge chunk referencing the exact seed
        ↓
other exact identifiers in the bridge
        ↓
indexed target symbol definitions
        ↓
optional companion test boost
~~~

The implementation is bounded by hard limits on bridge chunks, identifiers per bridge, target definitions and companion-test scans. Retrieval output reports structural status, whether the lane was enabled by default or explicitly, and traversal telemetry including truncation.

Normal `query_repository` / Turn Context retrieval enables the structural lane by default. Diagnostic callers can explicitly disable it; the CLI exposes `aips intelligence retrieve ... --no-structural` for regression/debug comparison.

Adoption constraints remain:

- source/test/history token budgets and provenance rules are unchanged;
- secret-path exclusion/redaction remains mandatory;
- no Tree-sitter/LSP/Sourcegraph dependency is introduced;
- semantic provider status remains independent and truthful;
- exact structural traversal does not claim compiler-grade semantic resolution;
- the retained Scenario 130 Trial harness can replay explicit OFF/ON comparison;
- Retrieval Quality Evaluation measures the adopted default behavior.

The earlier candidate passed with no required-case regression and recovered complete Recall@K for the cross-file structural diagnostic. This adoption does not create a new Role, Skill, Human Approval Gate or publication authority.

## Semantic Alias Expansion Candidate Trial — HOLD

After Structural Retrieval adoption, AIPS tested a dependency-free deterministic alias-expansion bridge before adding embeddings or a remote semantic provider.

The candidate uses transparent source-controlled software-engineering alias groups and cross-group coherence scoring. It remains useful as a reproducible research artifact, but the committed full-corpus Trial outcome is **FAIL / HOLD**:

- `auth-token-expiry`, `go-receipt-reconciliation` and `typescript-session-refresh` regress under the candidate;
- the already-covered registration diagnostic drops below its baseline source recall;
- the unresolved `synonym-access-rotation` diagnostic does not improve source recall;
- the actual semantic provider remains truthfully `NOT_CONFIGURED`.

Therefore alias expansion stays disabled by default and is not an adoption candidate. Scenario 132 intentionally replays the failing candidate and expects recommendation `HOLD`; this prevents ranking tweaks from silently rewriting negative evidence into a PASS.

This result narrows the next research question: if AIPS continues semantic retrieval work, it should evaluate a materially different candidate (for example a real embedding/semantic provider) under a separate Human-reviewed Trial, with source-code transfer/privacy, provider configuration, cost, cache and fallback boundaries explicitly approved first. No provider is enabled by Scenario 132.

## Remote Embedding Retrieval Trial Readiness

Scenario 133 prepares that materially different candidate without changing production Retrieval Intelligence.

The first adapter uses the approved OpenAI embeddings endpoint with a bounded configuration contract and reuses the protected CI secret reference already used by Evolution Radar. The Trial is synthetic-only: it may transmit the committed Retrieval Quality fixture, but MUST NOT transmit AIPS repository/product source.

~~~text
9-case synthetic corpus
        ↓
current Retrieval baseline
        ↓
remote embedding candidate (bounded)
        ↓
in-memory cosine merge
        ↓
same Recall / Precision / MRR / history / purity checks
        ↓
PASS / FAIL / PENDING / BLOCKED evidence
        ↓
Human review before adoption
~~~

Safety / authority boundaries:

- normal Pull Request and main validation do not call the embedding provider;
- the remote Trial runs only on the dedicated Trial branch or explicit workflow dispatch;
- missing credentials produce `TRIAL_PENDING`;
- provider/network/runtime failure produces `TRIAL_BLOCKED`;
- request count, candidate chunk count and remote input characters are bounded;
- no Vector DB is introduced; candidate vectors are ephemeral/in-memory Trial data;
- provider/model metadata and usage tokens are recorded, but secret values never enter payloads or reports;
- normal Turn Context does not enable any embedding lane;
- production source transfer remains forbidden;
- PASS does not grant provider enablement, adoption, publication, merge or release authority.

The initial adapter defaults to `text-embedding-3-small`, with model override through repository variable only. A different provider can be introduced later through the same Trial contract rather than becoming a hard dependency.

### Remote Trial operator handoff

The dedicated workflow MUST publish a GitHub Job Summary from the machine-readable Trial report. Workflow-level `SUCCESS` is not equivalent to Trial `PASS`.

Status handling is fixed:

- `TRIAL_PENDING`: configure the repository Actions secret `OPENAI_API_KEY`, then re-run `retrieval-semantic-trial`;
- `TRIAL_BLOCKED`: inspect provider/network/config evidence and keep HOLD until corrected;
- `FAIL`: preserve negative evidence and keep remote embedding disabled;
- `PASS`: stop at Human review; a separate Human Adoption Decision is required.

The summary may report provider/model identifiers, credential availability as a boolean, privacy scope, request/token counts and authority flags. It MUST NOT print credential values.

## Provider-Neutral Local-First Embedding Trial

Scenario 134 removes the remote credential as the default semantic-retrieval research blocker while preserving Scenario 133 as historical remote-readiness evidence.

Provider selection is explicit and bounded:

~~~text
synthetic corpus
      ↓
current Retrieval baseline
      ↓
provider selector
   ├─ local (default): pinned sentence-transformers + pinned BGE revision
   └─ remote (optional): existing OpenAI-compatible adapter
      ↓
ephemeral in-memory cosine merge
      ↓
same quality/regression checks
      ↓
PASS / FAIL / PENDING / BLOCKED
      ↓
Human review before adoption
~~~

Local-mode contracts:

- local mode is the default and requires no credential;
- the model identifier and exact model revision are pinned in configuration;
- model artifact download may use network on the dedicated Trial runner, but synthetic query/chunk inference remains runner-local;
- Hugging Face telemetry is disabled by workflow environment;
- model dependency/download/load/inference failure is `TRIAL_BLOCKED / HOLD`;
- normal PR/main validation does not install the semantic Trial dependency or execute the model.

Remote-mode contracts remain available only when `AIPS_RETRIEVAL_EMBEDDING_PROVIDER=remote` is explicitly selected. That path retains protected `OPENAI_API_KEY` injection and truthful `TRIAL_PENDING` when the credential is unavailable.

Both modes preserve `synthetic_fixture_only`, repository/product source-transfer=false, bounded candidate/input/batch limits, ephemeral vectors, no Vector DB, default enablement=false, provider auto-enablement=false and mandatory Human Adoption Decision after PASS.

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
→ ensure Retrieval Intelligence index
→ retrieve bounded task evidence
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

## Temporal Project Intelligence

Project Intelligence may include `TEMPORAL_ASSERTIONS.yaml` as its canonical temporal assertion ledger. It records facts and architecture decisions with explicit provenance, supersession and history quality. Git revision ancestry is the authoritative validity axis; wall-clock timestamps are observation metadata only.

The current materialized view remains the default path. Historical work uses bounded, just-in-time queries:

~~~text
CURRENT
AS_OF <revision>
BETWEEN <base> <head>
WHY <assertion>
~~~

Use `aips intelligence temporal --project <path> --mode as-of --revision <sha>` for a deterministic historical query. `UNKNOWN` history must remain unknown; migration and reconstruction MUST NOT invent a validity start revision. `VERIFIED`, `INFERRED`, `PARTIAL` and `UNKNOWN` history quality must remain visible in output.

`IMPACT_GRAPH.yaml` v2 may add optional revision validity and provenance to nodes or edges while v1 data remains readable. Retrieval SQLite may project temporal assertions, supersession links and ancestry cache, but it is rebuildable and never canonical.
