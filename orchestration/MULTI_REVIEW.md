# Multi-Perspective Review

Use for large/core/high-risk changes when one generic reviewer is insufficient.

## Trigger

Resolve a Review Panel from semantic impact, risk, complexity and Change Boundary — not LOC alone.

Typical triggers:
- Core Change;
- Auth/Authz;
- payment/stored-value/high-value business logic;
- schema/migration;
- public API/contract;
- concurrency/distributed consistency;
- cross-component change;
- broad refactor;
- production topology;
- SAL 3–4;
- high Reliability Impact.

## Reviewer resolution

Choose only needed perspectives.

Examples:
- Quality Reviewer — correctness, regression, tests, maintainability, contracts.
- Software Architect — boundaries, dependency direction, coupling, architecture drift.
- Security Engineer — trust/auth/authz/data/abuse/business invariants, credential handling and secret leakage when applicable.
- Database Engineer — schema/migration/query/transaction/locking/consistency.
- Performance Engineer — hot paths, allocation, N+1, caching, concurrency/resource use.
- Product Designer / Frontend — UX/visual implementation when affected.
- SRE / Cloud Architect — operability, deployment, recovery, production topology.

Do not create reviewers merely for panel size.

## Bounded parallel review

Each reviewer receives:
- exact objective/perspective;
- affected files/contracts;
- relevant tests/evidence;
- read-only permissions;
- expected finding format.

Do not ask every reviewer to “review everything”.

## Finding format

Use `templates/review/REVIEW_FINDING.yaml`.

Every material finding must include:
- severity;
- location/scope;
- category;
- concrete finding;
- impact;
- evidence;
- recommendation;
- reviewer perspective;
- status.

## Consolidation

Before sending findings to the Author:
1. normalize severity/category;
2. merge duplicates/shared root causes;
3. preserve contributing reviewer perspectives;
4. separate blockers from optional comments;
5. detect reviewer conflicts.

Use `templates/review/REVIEW_REPORT.md`.

## Author fix loop

Reviewer identifies; original Author writes.

~~~text
Review Panel
→ Consolidated Findings
→ Original Author Fix
→ Tests
→ Targeted Re-review
→ PASS / remaining findings
~~~

Reviewers do not silently rewrite the implementation unless explicitly assigned as the writer for a separately approved boundary.

If a recommendation materially expands scope, route it through the applicable Core Change/approval process.

## Re-review

After fixes, default to targeted re-review using:
- original finding;
- fix diff;
- affected tests/evidence.

Repeat full broad review only when the fix materially expands/change the boundary.

## Convergence

Avoid endless reviewer loops.

If reviewers materially disagree:
- summarize the conflict/evidence;
- use the appropriate authority (often Architect, Security governance or Human decision);
- do not oscillate implementation indefinitely.

Continue additional rounds only for unresolved material findings or newly introduced material risk.

## Learning extraction

After material review completion, use `templates/review/LESSONS.yaml`.

Classify lessons:
- run lesson — specific to this task/run;
- project lesson — recurring project invariant/convention worth persisting;
- system capability lesson — cross-project, repeated, generalizable capability gap.

Do not automatically modify permanent Role/Skill/System behavior from one review.

For a system capability lesson:
1. show evidence and recurrence;
2. recommend the smallest target (existing Skill before Role);
3. ask the user whether to start System Improvement;
4. if approved, use Capability Incubation + System Self-Improvement.


## Test evidence review

For Large/Core changes, reviewers compare the Impact-derived Test Matrix with the final Change Boundary and actual diff.

A green subset is insufficient if a materially affected boundary lacks applicable evidence.

If implementation scope expands, recompute required tests before PASS.
