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
