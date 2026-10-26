# Core Change Proposal — Dev Friction PR2: Task-Scoped Intelligence Preparation

## Purpose

Align Turn Context instructions with the policy the code already enforces. Since the READY Stale Advisory change, READY+STALE Intelligence does not block a confined local L2 write, but the hook still told agents to "satisfy Intelligence initialization/refresh/readiness" and to build the Retrieval index on almost every turn. That made agents refresh or index before unrelated work. This change makes the preparation steps task-scoped and adds a safe cleanup command for orphaned external stores.

## Why this is a Core Change

The change touches the Turn Context manifest requirements, the Claude Code / Gemini prompt hook, the Global Harness adapter templates and Project Intelligence policy text. Wrong wording could hide a required refresh or weaken a hard stop, so the boundary needs explicit evidence.

## Approved Scope

Status: APPROVED. The Human approved the full AIPS dev-friction plan (`aips-dev-friction-plan.md`, direction C). This proposal covers exactly PR2 of that plan and does not expand it:

1. READY+STALE: state staleness as advisory; require refresh only when task-relevant topics are affected (from the existing `task_freshness` computation). Unaffected or topic-free turns get no refresh instruction.
2. `retrieval_index_required` is true only when the current task needs retrieval; otherwise report index status without an instruction.
3. Hard stops unchanged: MISSING/UNKNOWN Intelligence, insufficient readiness, instruction conflicts, path escapes, Change Impact for mutation, creative and external/high-risk controls.
4. Sync policy text in the Harness protocol, Turn Harness, Project Intelligence docs and the Global Harness adapter templates in the repo (never `~/.claude` itself).
5. Add `aips intelligence gc`: dry run by default, deletion only with `--yes`, confined to the user config `projects/` directory.

### Out of scope

- Fail policy changes (`fail_closed_reasons` logic is untouched), OpenCode guard, Change Impact, readiness rules, `.ai` persistence, retrieval ranking, worktree sharing (PR8), profiles (PR10), the retrieval cache directory, Constitution and publication authority.

## Design

- `retrieval_needed_for_task(prompt, mutation, desired_topics)`: true for a non-empty prompt that is a likely mutation or selects Intelligence topics. `retrieval_index_required = retrieval_needed and store initialized and index MISSING`. `retrieval_index_status` is always reported.
- `task_refresh_requirement(freshness, readiness, selected, task_freshness)` returns `refresh_required`, task-scoped `targeted_refresh`, `freshness_advisory` and `refresh_reason`:
  - not STALE → no refresh;
  - STALE and not READY → store-wide refresh (unchanged; the fail policy still closes for mutation);
  - READY+STALE with no task-relevant topics → advisory, no refresh;
  - READY+STALE and `task_freshness=CURRENT` (irrelevance proven) → advisory, no refresh;
  - otherwise → refresh the affected selected topics, or all affected topics when relevance cannot be proven.
- `turn_context_hook.py` renders `freshness_advisory=...` and lists `targeted_refresh` only when refresh is required, reports a missing index without an instruction when not needed, and replaces the fixed closing sentence with the steps this turn needs. Mutation turns always include "resolve Change Impact"; a closed fail policy is named with its reasons. Legacy manifests without the new fields keep the previous `targeted_refresh` rendering.
- `scripts/project_intelligence_gc.py`: for each `<config>/projects/<workspace>/intelligence`, read `project.root` from `PROJECT_INTELLIGENCE.yaml`. Orphan only when the root is absolute and `lstat` reports nothing there. Refuse a symlinked `projects/`, skip symlinked workspace/store entries, require resolved confinement to `projects/`, skip missing/unreadable manifests and unverifiable roots, re-check before `rmtree`, remove only the `intelligence` store and keep other workspace data (runs, changes).

## Impact and compatibility

Additive manifest fields (`retrieval_needed`, `retrieval_index_status`, `refresh_required`, `refresh_reason`, `freshness_advisory`); `targeted_refresh` keeps its type and is now task-scoped. `freshness.affected_topics` still exposes the store-wide list. The only consumers of `targeted_refresh` are the hook and lifecycle evidence. No schema version, persistent data or migration change. `gc` is a new opt-in command.

## Architecture Diagram Impact

N/A — no component topology, deployment unit or data-flow topology changes.

## Validation

- Unit: `tests/test_intelligence_task_freshness.py`.
- Lifecycle: `tests/evidence/intelligence_context_lifecycle.py` (related vs unrelated READY+STALE task, read-only index status, hook output, gc dry run and `--yes` in temp config) and `tests/evidence/layered_context_memory_lifecycle.py`.
- Scenario 269, `capability_registry.py check`, repository preflight.

## Approval

Status: APPROVED for the PR2 scope above, as part of the Human-approved dev-friction plan.
