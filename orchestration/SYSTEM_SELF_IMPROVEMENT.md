# System Self-Improvement Protocol

Load this protocol whenever the user proposes changing, extending, simplifying, optimizing or governing the AI Product System itself.

## Goal

The system must not blindly accept every proposed improvement. It first evaluates whether the idea is appropriate, redundant, overly complex, unsafe or better solved at a lower layer.

## Self-Improvement Review

Before implementation, evaluate:

- What concrete problem does the suggestion solve?
- Is the behavior already covered by an existing principle, gate, role, skill, workflow or template?
- Can the goal be achieved with less complexity or less context/token overhead?
- Will it create Role/Skill/Gate proliferation?
- If it proposes a Role/Skill/Capability, what existing items overlap and can be reused or extended?
- Is it backward compatible?
- What existing scenarios or projects could change behavior?
- Does it affect security, reliability, human authority, project precedence, persistence or Git/release behavior?
- Does it need a new abstraction, or can an existing abstraction be extended?
- Which documents, diagrams, templates and tests would need updates?
- Does it touch the Constitution semantically, even if the file itself is not directly edited?

## Required response before implementation

Present a concise System Improvement Review:

~~~text
Appropriateness:
Problem addressed:
Overlap with existing design:
Possible simplification:
Additional optimization:
Recommended direction:
Expected scope:
Risks:
Backward compatibility:
Constitution impact: NO / YES
Why:
~~~

If the recommendation materially differs from the user's original suggestion, explain the alternative and wait for the user to choose.

Implementation begins only after the user confirms the direction.

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

## Integration with other gates

After self-improvement direction is approved:

- run Capability Incubation before adding or materially expanding Roles/Skills/Capabilities;

- use Core Change Approval for large/core changes;
- implement within approved scope;
- run scenario/validation/review;
- run Documentation Impact Gate;
- prepare Git Publish Proposal;
- wait for publication approval before changing a remote branch/ref.

If implementation materially drifts from the approved System Improvement Review or Core Change Proposal, stop and request approval again.
