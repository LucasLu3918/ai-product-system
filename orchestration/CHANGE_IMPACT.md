# Change Impact Guard

CI workflow seeds are included in deterministic discovery while global graph coverage remains partial. Review runtime routing, required-check consumers, registry/hash persistence and offline-dependency behavior explicitly; a discovered seed does not prove a compiler-resolved relationship.

Retrieval extractions preserve the legacy `retrieval_intelligence.py` facade and output contracts. Treat index-derived relation edges as lexical candidates; incomplete traversal remains explicit and cannot support repository-wide completeness claims.

The Project Intelligence facade now delegates filesystem-backed cache operations to `project_intelligence_storage.py`; preserve public imports, cache paths and recovery behavior when changing either module.

Use before mutating an existing project.

## Purpose

For cache recovery, review implicit fallback versus explicit XDG settings, directory ownership/symlink rejection, orphan metadata and rebuild behavior. Include gh child cache environments, package diagnostic consumers and installed-checkout synchronization in the boundary; do not widen sandbox permissions or count CLI fixtures as real REST acceptance. Traversal reports must record the policy-required consumer depth whenever consumers are requested, so generated evidence remains compatible with the unchanged validator minimum.

A local code edit may change contracts, persistence, events or consumers outside the directly edited file. Resolve impact before implementation and compare declared impact against the resulting diff.

Retrieval storage extraction keeps the disposable SQLite schema, read-only snapshot/WAL safeguards and facade exports unchanged. Review storage/cache consumers and preserve the exact `retrieval_intelligence.py` API boundary.

## Flow

~~~text
Mutation request
→ relevant Project Intelligence
→ Change Boundary
→ IMPACT_GRAPH traversal
→ CHANGE_IMPACT contract
→ IMPLEMENTATION_APPROVED
→ implementation in valid project-native style
→ tests / verification
→ actual Git base/head + binary diff digest + changed-file set vs declared impact
→ `aips intelligence impact-validate --project <repo> --path <CHANGE_IMPACT.yaml>`
   ├─ exact, clean, reconciled → READY
   └─ mismatch / unverifiable → BLOCKED
→ unexpected impact?
   ├─ yes → review / fix / expand approved boundary when needed
   └─ no  → refresh affected Intelligence
~~~

## Required dimensions

Assess when applicable:

- inbound API/request/event/input;
- outbound response/event/file/message;
- database/schema/storage/cache;
- downstream consumer/caller;
- authorization/security boundary;
- business invariant;
- migration/backward compatibility;
- tests/fixtures;
- observability;
- documentation/contracts.

N/A is allowed with reason.

## Project-native style

Preserve valid native conventions in this order:

~~~text
Explicit project rule
→ formatter/linter/schema/contract
→ shared abstraction
→ repeated majority convention
→ approved Project Intelligence
→ language/framework best practice
→ generic AIPS default
~~~

Do not perpetuate unsafe/broken patterns. When deviating for correctness/security, explain the compatibility impact and use the smallest compatible safer change.

## Fail policy

- read-only/explanation task + Intelligence unavailable → fail soft; continue with disclosed limitation when safe.
- mutation + required project/instruction/impact context unavailable → fail closed for the affected edit until resolved.


## Persistence

Create a per-change artifact using `templates/intelligence/CHANGE_IMPACT.yaml`.

Preferred locations:

~~~text
ATTACHED:
.ai/runs/<change-id>/CHANGE_IMPACT.yaml

EPHEMERAL:
~/.config/aips/projects/<project-id>/changes/<change-id>.yaml
~~~

`aips intelligence impact-init` creates a DRAFT. Resolve semantic impact, required dimensions, graph scope and unknowns, then record the user's scope authorization as `scope_review.status: APPROVED`, including an approval reference and timestamp. This permits implementation only; it does not assert that the eventual diff or graph has been reconciled. The workflow state may advance to `IMPLEMENTATION_APPROVED` before implementation.

`unknowns` may retain legacy strings; every such string stays unresolved and blocks implementation approval. New entries use `id`, `description`, `disposition`, `resolution`, `evidence` and `review`. Allowed dispositions are `OPEN`, `RESOLVED`, `MITIGATED` and `ACCEPTED_LIMITATION`; `OPEN` blocks approval. A closed disposition requires a substantive resolution, at least one verifiable evidence item and explicit Human review (`status: APPROVED`, `reviewer: human`, `approval_reference`, `reviewed_at`). Repository-file evidence uses a repository-relative `path` and SHA-256 of current file bytes; absolute paths, parent traversal, symlinks escaping the repo, missing files and stale hashes fail validation. Traversal evidence uses `kind: traversal`, the SHA-256 of the recorded traversal mapping encoded as canonical UTF-8 JSON (sorted keys, compact separators), and an optional `scope_id`. Traversal must be COMPLETE, non-truncated and unresolved-free. A scope ID must appear in the same report's `architecture_graph.coverage_scope_ids`; without a scope ID, all repository-wide API / data / events / consumers coverage dimensions must be complete. Scoped evidence never upgrades global coverage.

An existing change ID is never silently reinitialized. Use a new `--change-id` for a new run. If an intentional restart is required, pass `--reset`; the command copies the previous YAML to a timestamped sibling backup before writing the new DRAFT and returns `backup_path`.

`READY` is reserved for the post-implementation state. It requires full commit SHAs for base/head, a clean worktree, an ancestor relationship from base to head, `head_revision` equal to checked-out `HEAD`, `diff_digest` equal to `sha256:` plus the SHA-256 of `git diff --binary --no-ext-diff <base> <head> --`, and `reconciliation.changed_files` equal to the exact sorted Git path set. Every actual changed path must also appear in `change.target_paths`. Keep semantic Impact Graph review and human evidence explicit; a matching digest does not prove semantic completeness. Unresolved or newly discovered material impact keeps the artifact out of READY and requires impact review; material boundary expansion also requires scope reapproval. Never use `READY` as a pre-implementation approval state.

Run `aips intelligence impact-validate --project <repo> --path <CHANGE_IMPACT.yaml>` before treating an artifact as implementation-approved or READY. Validation fails closed when either the user-authorized scope record or the post-diff Git reconciliation is missing, dirty, unverifiable or mismatched. DRAFT and IMPLEMENTATION_APPROVED validation does not require a Git diff.

For publication-tool changes, include the selected checkout, installed CLI routing, local validation environment and retrieval-cache consumers in the declared impact. Reconcile every documentation path required by the working-tree impact preview before marking the artifact READY.

For retrieval-cache recovery, distinguish read-only access from stale-index refresh writes, as well as connection establishment from the first SQLite query. Preserve live-WAL refusal, source-stability comparison and snapshot integrity as explicit data boundaries in the impact review. A sandbox write denial must identify the configured cache/sidecar write requirement, retain stale status and avoid suggesting a forced rebuild for an otherwise valid index.

When traversal validation reports `affected node lacks a final disposition`, inspect that node's callers and consumers and explicitly choose `reviewed_safe`, `requires_change` or `unknown`. Do not infer a disposition from the absence of a diff. `requires_change` must be included in the approved `target_paths`; high-risk `unknown` nodes remain blocking until the relationship is reviewed or the impact boundary is expanded. Rerun `aips intelligence impact-validate` after resolving each finding.

## Diff reconciliation

Changes to extracted Project Intelligence promotion helpers preserve the facade and approval boundary; governance snapshots are read-only and report UNKNOWN for inaccessible surfaces.

Plan17 regression evidence covers numeric diff headers, four browser/OpenAPI combinations, mandatory aggregates, reusable caller keys/permissions, explicit Python and isolated children, recursive placement, signed identity/immutable proposal rejection and atomic deletion races. Missing or malformed capability plans retain the full profile. A latest cancelled check stays INCOMPLETE; replaced old checks are reported as SUPERSEDED.

For shared Python bootstrap changes, reconcile every composite-action caller, each declared import profile, dependency constraints, and lifecycle evidence.

For shell CLI changes, include the stable launcher and facade, module load paths, installed/source-checkout consumers and lifecycle tests. The lexical graph does not resolve shell calls; preserve any accepted partial-coverage limitation and review direct dispatch/source consumers explicitly.

Project Intelligence 的 temporal query 可逐步抽至內部 adapter，但必須保留 `project_intelligence.py` 的同一函式物件、CLI dispatch 與結果契約；Scenario 204 提供回歸證據。

Scoped traversal evidence may be complete for directly inspected callers while retrieval-index freshness or repository-wide graph coverage remains incomplete. Record the limitation and keep global coverage claims partial.

Validation-scope hints remain conservative: unknown paths and validator/governance paths retain the full validator set, while the shadow report records proposed omissions without skipping execution.

Architecture Impact Graph traversal is extracted behind `project_intelligence.py` while preserving the public facade and result contract. Structural retrieval graph building follows the same compatibility pattern; neither extraction changes risk policy, index authority, evidence status or consumer-facing CLI behavior.

Turn Context intent and `--target-path` narrow instruction selection before mutation analysis. This routing is advisory: the declared Change Boundary and post-diff reconciliation remain authoritative, and non-Git directories retain basic context without historical assertions.

For runtime-floor or installer-recovery changes, include explicit interpreter selection, managed venv install/update repair, `doctor`, canonical facts, scheduled compatibility CI and documentation consumers. If shell call relationships are missing or traversal is truncated, preserve that limitation and manually review the installer, workflow, tests and docs; do not claim global graph completeness.

After implementation compare:

~~~text
Declared Change Impact
↔ Actual changed files/contracts/schema/events/tests
~~~

If actual material impact falls outside the declared Change Boundary:

1. stop affected continuation;
2. update impact analysis;
3. re-run required review/testing;
4. obtain scope reapproval when the approved boundary materially expanded.

- For release-readiness policy changes, include the changelog parser, exact candidate consumers, negative lifecycle cases, Scenario 208, and all canonical documentation placements in the final reconciled boundary.
## Impact Graph maintenance

Update reusable `IMPACT_GRAPH.yaml` only when the change reveals/stably changes cross-component relationships.

A one-off run artifact does not automatically become permanent Intelligence.

### Seed-scoped coverage

When repository-wide graph coverage is incomplete but a bounded architectural area has been reviewed, record an optional `coverage_scopes` entry with its exact `seed_ids`, per-dimension `coverage`, and source `evidence`. Traversal may use that entry only when every matched graph seed is included. This establishes completeness only for those seeds; it never upgrades the graph's repository-wide `coverage`. Missing evidence or an unmatched seed falls back to repository-wide coverage and remains unresolved when that coverage is partial.

## Temporal Change Impact

When a change depends on architecture evolution, resolve the temporal state before traversing the graph:

~~~text
target revision or merge-base/HEAD
→ active temporal assertions
→ temporal-filtered Impact Graph
→ Change Boundary
→ CHANGE_IMPACT.yaml
~~~

Historical Change Impact MUST NOT use a rule whose `from_revision` is not an ancestor of the target revision. Assertions with unknown historical starts may be used for current-state context only and must be reported as `PARTIAL` or `UNKNOWN`. Between two revisions, report added, ended, superseded and conflicting assertions rather than silently selecting a winner.

## Risk-adaptive bounded traversal

Use `aips intelligence impact-traverse` to find likely code callers and consumers before implementation. The command combines rebuildable lexical relationships from the local Retrieval Intelligence index with exact relationships in canonical `IMPACT_GRAPH.yaml`; lexical matches are candidates, not compiler-resolved references.

Example: `aips intelligence impact-traverse --project . --seed get_products --seed-path src/api.py --risk-class api_contract --direction callers --direction consumers --max-depth 3 --max-nodes 100 --max-edges 250`. Repeat `--seed` alongside optional same-index `--seed-path`/`--seed-line`, and pass `--graph-seed` to identify an exact canonical Impact Graph node when symbol/path matching is ambiguous. Use `--changed-path` for each path in the implementation diff when recording node status.

Risk policy is intentionally shallow for documentation/style-only changes and private leaves. Public signatures/return shapes, shared DTOs/libraries, API contracts, database or event schemas, security boundaries and payment paths require at least two caller hops (capped at four). Consumers are traversed in the requested direction. High-risk classes that require depth two or more require complete graph coverage and no unresolved relationships before READY.

Traversal records its policy version, required/reached depth, visited nodes/edges, truncation, unresolved evidence, node dispositions and whether each affected path changed in the actual diff. Node and edge budgets are hard bounds; hitting one is reported as `TRUNCATED` and cannot establish completeness. Dynamic string dispatch, missing graph coverage, stale indexes and unmapped graph paths remain explicit unknowns. For high-risk changes, use bounded relevant Git history to resolve temporal or ownership uncertainty; do not scan history for low-risk leaves by default.

Before READY, review each affected-but-unchanged node and record `reviewed_safe`, `requires_change` or `unknown`. Required changes must be in the approved target path set and match the actual diff. Unknown or incomplete evidence blocks high-risk READY. The exact diff digest and changed-path reconciliation remain mandatory; traversal evidence supplements rather than replaces semantic review.

For a multi-perspective review, include the seeds, risk policy, budgets, index freshness, graph coverage, exact versus inferred edges, unresolved/truncated evidence and affected-but-unchanged dispositions. Reviewers assess whether the evidence supports the implementation and diff; traversal does not prove compiler-resolved completeness.
