# Progressive Requirement Clarification

Use when a request is not yet specific enough for reliable implementation.

## Goal

Turn user intent into an implementation-ready goal without forcing the user to design the solution for the Agent.

## Status

Use only:

- READY — enough is known to implement safely.
- NEEDS_CLARIFICATION — a material user/product decision is still required.
- BLOCKED — implementation cannot continue because a required dependency/context/decision is unavailable or contradictory.

## Decision rule

Ambiguity alone is not a reason to ask.

If a competent professional default can safely resolve the ambiguity without materially changing product direction, use the default and record it when useful.

Ask only when the answer can materially change:
- product behavior;
- scope;
- public contract;
- architecture;
- security/privacy;
- data model;
- cost;
- irreversible/recovery behavior;
- brand/visual direction when mismatch would be costly.

## Flow

~~~text
User Request
→ Can the goal be implemented safely as stated?
  ├─ yes → READY
  └─ no
      ↓
   Can a safe professional default resolve it?
      ├─ yes → apply default → READY
      └─ no
          ↓
      NEEDS_CLARIFICATION
          ↓
      Ask the smallest useful question
          ↓
      Offer examples/options + recommendation when helpful
          ↓
      Update goal
          ↓
      READY / NEEDS_CLARIFICATION / BLOCKED
~~~

Do not send long questionnaires. Ask the next blocking question or a small batch of tightly related questions.

## Implementation-ready goal

Before broad implementation, ensure enough clarity exists for:

- objective;
- target user / actor when relevant;
- expected output/behavior;
- in-scope / out-of-scope boundary;
- required inputs/assets;
- material constraints;
- testable success criteria;
- no unresolved blocking unknowns.

Use `templates/requirements/IMPLEMENTATION_GOAL.yaml` when persistence is useful.

## Guidance style

Prefer:
- plain-language choices;
- 2–4 concrete options;
- a recommended default;
- examples the user can react to.

Avoid asking non-expert users to choose low-level architecture, schema, spacing values or other professional details the system can derive safely.
