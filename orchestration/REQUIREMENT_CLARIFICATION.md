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

## Structured functional requirements (EARS)

When a clarified request contains functional behavior that will guide implementation or acceptance, consider recording atomic requirements with EARS (Easy Approach to Requirements Syntax). EARS is lightweight structure for natural-language requirements; it supplements progressive clarification and does not change READY / NEEDS_CLARIFICATION / BLOCKED.

Choose the pattern that matches the behavior. Keep its canonical English keywords even when the requirement itself is written in another language:

| Pattern | Form | Use |
|---|---|---|
| Ubiquitous | `The <system> shall <response>.` | Behavior that is always active |
| Event-driven | `When <trigger>, the <system> shall <response>.` | Response to an event |
| State-driven | `While <precondition>, the <system> shall <response>.` | Behavior that applies while a state holds |
| Optional feature | `Where <feature is included>, the <system> shall <response>.` | Behavior conditional on a product feature |
| Unwanted behavior | `If <undesired condition>, then the <system> shall <response>.` | Response to an undesired situation |

EARS also permits a complex form combining a `While` precondition with one `When` trigger; use it only when both conditions are essential to the same response. Prefer one observable system response per requirement; split requirements with multiple independent responses or materially different verification paths. Do not force goals, rationale, assumptions, business rules, or non-functional targets into an EARS sentence. For non-functional requirements, state a measurable target or explicit qualitative acceptance rule and how it will be verified.

EARS does not supply missing product decisions. A trigger such as “repeated failures” still needs a defined count/window/reset rule when those details affect behavior. Ask only for materially blocking decisions under the existing clarification rules; otherwise apply and record a safe default. Never infer that an EARS-shaped statement is unambiguous, testable, implemented, or passed solely from its syntax.

When a Planning Package needs durable traceability, use the optional `templates/planning-package/REQUIREMENTS.yaml` registry. Give each requirement a stable ID, connect it to one or more acceptance criteria, and state the verification method. An evidence reference is a location or planned check; it is not proof that the check ran or passed. AIPS Scenario Conformance remains a separate registry of AIPS behavior and executable evidence.

For automation, `python scripts/requirements_traceability.py <registry> --format json` emits `status: PASS` or `status: FAIL`; it exits zero only when structural validation passes and non-zero when it fails. This result covers registry structure, not requirement meaning or execution of the referenced verification.

## Guidance style

Prefer:
- plain-language choices;
- 2–4 concrete options;
- a recommended default;
- examples the user can react to.

Avoid asking non-expert users to choose low-level architecture, schema, spacing values or other professional details the system can derive safely.
