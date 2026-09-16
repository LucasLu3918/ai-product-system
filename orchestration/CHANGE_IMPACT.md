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
→ implementation in valid project-native style
→ tests / verification
→ actual diff vs declared impact
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
