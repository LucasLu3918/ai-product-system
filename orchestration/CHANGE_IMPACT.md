# Change Impact Guard

Use before mutating an existing project.

## Purpose

A local code edit may change contracts, persistence, events or consumers outside the directly edited file. Resolve impact before implementation and compare declared impact against the resulting diff.

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

`READY` is reserved for the post-implementation state. It requires full commit SHAs for base/head, a clean worktree, an ancestor relationship from base to head, `head_revision` equal to checked-out `HEAD`, `diff_digest` equal to `sha256:` plus the SHA-256 of `git diff --binary --no-ext-diff <base> <head> --`, and `reconciliation.changed_files` equal to the exact sorted Git path set. Every actual changed path must also appear in `change.target_paths`. Keep semantic Impact Graph review and human evidence explicit; a matching digest does not prove semantic completeness. Unresolved or newly discovered material impact keeps the artifact out of READY and requires impact review; material boundary expansion also requires scope reapproval. Never use `READY` as a pre-implementation approval state.

Run `aips intelligence impact-validate --project <repo> --path <CHANGE_IMPACT.yaml>` before treating an artifact as implementation-approved or READY. Validation fails closed when either the user-authorized scope record or the post-diff Git reconciliation is missing, dirty, unverifiable or mismatched. DRAFT and IMPLEMENTATION_APPROVED validation does not require a Git diff.

## Diff reconciliation

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

## Impact Graph maintenance

Update reusable `IMPACT_GRAPH.yaml` only when the change reveals/stably changes cross-component relationships.

A one-off run artifact does not automatically become permanent Intelligence.

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
