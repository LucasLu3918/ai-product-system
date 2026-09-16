# System Self-Improvement Protocol

Load this protocol whenever the user proposes changing, extending, simplifying, optimizing or governing the AI Product System itself.

## Goal

The system must not blindly accept every proposed improvement. It first evaluates whether the idea is appropriate, redundant, overly complex, unsafe or better solved at a lower layer.

## Problem / Solution Separation

Treat these as separate concepts:

~~~text
User Problem
≠ Proposed Solution
≠ Recommended AIPS Solution
~~~

- **User Problem** — the concrete need, failure mode or desired outcome.
- **Proposed Solution** — the user's suggested mechanism, abstraction or implementation.
- **Recommended AIPS Solution** — the smallest coherent design that solves the problem while preserving AIPS principles and existing capabilities.

A proposed solution is a candidate design, not automatically the correct system architecture. Evaluate the underlying problem first.

If the user explicitly fixes a mechanism as a requirement, preserve that requirement inside its approved scope, but still disclose material duplication, risk, cost or a safer/simpler alternative before implementation.

## Self-Improvement Review

Before implementation, evaluate:

- What concrete problem does the suggestion solve?
- What solution did the user propose, if any?
- Is the behavior already covered by an existing principle, gate, role, skill, capability, workflow, work mode, template or deterministic automation?
- Which existing items are the closest reuse or extension candidates?
- Can the goal be achieved at a lower-authority layer or with less complexity?
- What ongoing context/token cost does the change add at bootstrap, per-turn or on-demand execution?
- Will it create Role/Skill/Capability/Gate proliferation?
- If it proposes a Role/Skill/Capability, what existing items overlap and can be reused or extended?
- Does it affect security or reliability boundaries, failure behavior, secrets, persistence, concurrency or recovery?
- Is it backward compatible? Does it require migration or behavior changes for existing projects/runtimes?
- What existing scenarios or projects could change behavior?
- What tests/scenarios are required by the final Change Boundary?
- Which Human-facing docs and Agent-facing docs would need updates?
- Which architecture diagrams are affected, and why is each affected diagram updated or explicitly N/A?
- Does it affect human authority, project precedence, Git/release behavior or other governance semantics?
- Does it need a new abstraction, or can an existing abstraction be extended?
- Does it touch the Constitution semantically, even if the file itself is not directly edited?

Prefer evidence from the current repository over assumptions about existing coverage.

## Recommendation Rule

After evaluating the problem and the proposed solution:

1. reuse existing behavior when it already solves the problem;
2. extend the narrowest coherent existing abstraction when reuse is insufficient;
3. use a lower-layer solution when it avoids unnecessary global/system cost;
4. introduce a new abstraction only when a real reusable gap remains;
5. explicitly state when the recommended AIPS solution differs from the proposed solution.

Do not create a new Role, Skill, Capability or Approval Gate merely to mirror the wording of a request.

## Additional Optimization Confirmation

During review or implementation planning, the Agent may discover optimizations beyond the currently approved request. These are optional candidates, not implicit scope.

For each material additional optimization:

1. describe the optimization and the concrete benefit;
2. disclose its scope impact and affected files/components when known;
3. classify the recommended timing as `NOW`, `LATER` or `REJECT`;
4. keep it separate from the already approved implementation scope;
5. request explicit Human confirmation before adding a `NOW` candidate to implementation.

~~~text
discover optimization
→ disclose separately
→ recommend NOW / LATER / REJECT
→ Human confirms inclusion when NOW
→ only then expand Implementation Scope
~~~

A `LATER` candidate remains deferred. A `REJECT` candidate is recorded only when useful for explaining why it should not be pursued.

Do not implement an unapproved optimization merely because it is adjacent, convenient or beneficial. If including it would materially expand an already approved Change Boundary, update the review/proposal and obtain the applicable scope re-approval before proceeding.

## Required response before implementation

Present a concise System Improvement Review:

~~~text
Appropriateness:
User problem:
Proposed solution:
Existing coverage:
Reuse / extension candidates:
Lower-layer alternative:
Context / token cost:
Security / reliability:
Backward compatibility:
Scenario / test impact:
Human docs impact:
Agent docs impact:
Architecture diagram impact:
Constitution impact: NO / YES
Why:
Recommended AIPS solution:
Additional optimization candidates:
Expected scope:
Risks:
~~~

If the recommendation materially differs from the user's original suggestion, explain the alternative and wait for the user to choose.

If any material additional optimization is recommended for `NOW`, keep it outside the implementation scope until the user explicitly confirms inclusion.

Implementation begins only after the user confirms the direction and any additional optimizations that are included in scope.

## Constitution Impact Check

Constitution impact is based on semantics, not file path alone.

Potential constitutional impact includes changes to:

- Protected Human Authority;
- Truth / No Silent Assumptions;
- Protected Safety Boundary;
- Stop-the-Line;
- Scope Integrity;
- explicit high-risk approval;
- constitutional authority/amendment rules.

If impact = YES:

1. stop ordinary system-change execution;
2. run the Constitutional Change Gate;
3. explain affected Article(s), proposed change and risks;
4. explain whether a lower-layer alternative exists;
5. request a second, explicit Constitutional Approval;
6. do not implement the amendment until that approval is received.

## Lower-layer preference

Prefer the least-authoritative layer that solves the problem:

~~~text
Skill / Template
→ Workflow / Work Mode
→ System / Orchestration
→ Governance
→ Constitution
~~~

Project-specific knowledge belongs in Project Intelligence. One-off deterministic behavior belongs in project/run automation when it does not justify a global reusable capability.

## Integration with other gates

After self-improvement direction is approved:

- run Capability Incubation before adding or materially expanding Roles/Skills/Capabilities;
- use Core Change Approval for large/core changes;
- implement within approved scope;
- derive tests from the final Change Boundary for Large/Core changes;
- run scenario/validation/review;
- run Documentation Impact Gate;
- run Architecture Diagram Impact Check for Large/Core changes;
- prepare Git Publish Proposal;
- wait for publication approval before changing a remote branch/ref.

If implementation materially drifts from the approved System Improvement Review or Core Change Proposal, including an unapproved additional optimization, stop and request approval again.
