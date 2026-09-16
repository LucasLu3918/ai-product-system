# Capability Incubation

Use before creating or materially expanding a Role, Capability or Skill.

## Goal

Keep the system small, clear and reusable. Prefer extending existing capability over creating near-duplicates.

## Reuse Check

Before proposing a new Role/Skill/Capability:

1. search roles/INDEX.yaml, capabilities/INDEX.yaml and skills/INDEX.yaml;
2. compare existing candidates by:
   - responsibility;
   - trigger;
   - inputs;
   - outputs;
   - authority;
   - review obligation;
   - reusable method/knowledge;
3. classify overlap:
   - HIGH → reuse existing;
   - PARTIAL → extend existing when coherent;
   - LOW → consider a minimal new skill/capability;
4. explain why a new item is still necessary.

## Creation preference

~~~text
Reuse existing
→ Extend existing
→ New narrow Skill
→ New Capability only for a useful routing group
→ New Role only for distinct responsibility + authority + review obligation
~~~

A new style, framework, artifact type or trend is normally data/reference/skill knowledge, not a Role.

## Progressive incubation

For a genuinely new capability:

1. define user goal and common scenarios;
2. define input/output/boundary/trigger;
3. create the smallest trial skill or extension;
4. add scenarios;
5. use it on real work;
6. collect gaps;
7. refine;
8. promote to a Role only after repeated evidence of independent responsibility.

## Role promotion test

Create/promote a Role only if all are true:

- responsibility is materially different from existing roles;
- it needs independent decision authority or ownership;
- it has distinct review obligations;
- combining it with an existing role causes persistent ambiguity.

Otherwise keep it as Skill/Capability knowledge.

## Maintenance

When extending an existing item, update its index metadata and body rather than duplicating similar text elsewhere.


## New Skill admission contract

A new system Skill is justified only after the Reuse Check demonstrates a real reusable capability gap.

Before adding a Skill:

1. search Skill/Capability indexes and the most relevant existing Skill bodies;
2. document closest candidates and why reuse/extension is insufficient;
3. define one narrow responsibility;
4. define positive triggers and important non-triggers;
5. define inputs, outputs and boundaries;
6. state expected context/token cost and model requirements;
7. keep provider/framework/version-specific details as reference data unless they form a stable reusable method;
8. add scenario evidence for routing and expected behavior;
9. register the Skill exactly once and validate unique ID/path;
10. update Human/Agent docs only when user-visible behavior changes.

Reject a new Skill when it is merely:

- a synonym/variant of an existing Skill;
- one product/style/framework name with no distinct reusable method;
- a temporary project convention that belongs in Project Intelligence;
- a one-off helper that belongs in run/project automation;
- a policy that belongs in governance/orchestration.

A Skill must not embed secrets, credentials or environment-specific private configuration.

If later evidence shows substantial overlap, prefer merge/deprecation over permanent Skill proliferation.
