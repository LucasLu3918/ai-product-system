# Project Knowledge

Use for existing projects to avoid repeatedly rediscovering stable project facts, architecture, conventions and design knowledge.

## Golden rule

**Discover once, persist only what is costly to rediscover, prefer pointers to authoritative sources, and refresh only affected knowledge.**

Project Knowledge is a cache/navigation layer, not a new governance authority.

## What to persist

Persist only knowledge that is:

- expensive to rediscover;
- useful across multiple future tasks;
- reasonably stable;
- not already expressed clearly in an authoritative project source.

Do not persist trivial observations or copy entire repository documentation.

## Authority / precedence

Project Knowledge never overrides:

1. current explicit user decision;
2. applicable scoped AGENTS.md;
3. accepted ADR / authoritative contract;
4. official project documentation;
5. approved Product/Brand/Visual/Quality artifacts.

Knowledge points to these sources when they already exist.

Derived knowledge is below authoritative sources and above fresh generic inference only as a discovery accelerator.

## Knowledge types

Classify derived entries:

- **FACT** — directly verifiable repository/config fact.
- **INTERPRETATION** — evidence-based architectural/design interpretation.
- **OBSERVED_CONVENTION** — repeated pattern that is not necessarily an official rule.

Do not turn an observed convention into a mandatory rule without promotion/approval.

## Status

Use:

- **AUTHORITATIVE** — pointer to an existing governing/official source.
- **DISCOVERED** — derived from repository evidence.
- **APPROVED** — discovered knowledge confirmed by the user/project authority.
- **STALE** — potentially invalid after a relevant change.

## Storage

Use:

~~~text
.ai/
└── knowledge/
    ├── KNOWLEDGE_INDEX.yaml
    ├── architecture.md
    ├── backend.md
    ├── frontend.md
    ├── data.md
    ├── testing.md
    ├── security.md
    ├── operations.md
    └── ...
~~~

Create only files with useful content.

Visual/product/quality/brand knowledge that already has a canonical artifact should remain there. The Knowledge Index stores a pointer instead of copying it.

Examples:

- visual → `docs/design/PROJECT_VISUAL_PROFILE.yaml`
- quality → `docs/quality/QUALITY_PROFILE.yaml`
- product → `PRODUCT.yaml`
- brand → `brand/BRAND_PROFILE.yaml`

## Initial Project Knowledge Discovery

Do not "full scan" every file.

Use progressive discovery:

~~~text
Existing AGENTS / ADR / Contracts / Docs
→ repository structure
→ manifests/config/entry points
→ representative modules
→ tests/contracts
→ identify knowledge gaps
→ targeted expansion
→ sufficient evidence?
   ├─ yes → persist/reuse
   └─ no  → expand only the uncertain area
~~~

Good triggers:

- no Knowledge Index exists and the task requires broad project understanding;
- user asks to understand the project;
- a core change cannot be done safely with current knowledge;
- a reusable knowledge gap is repeatedly rediscovered.

## Duplication check

Before writing a knowledge topic:

1. search applicable AGENTS.md;
2. check ADR/contracts;
3. check official docs;
4. check Product/Brand/Visual/Quality artifacts;
5. if an adequate source exists, add/update an AUTHORITATIVE pointer only;
6. otherwise persist concise derived knowledge.

## Evidence and confidence

INTERPRETATION / OBSERVED_CONVENTION entries require:

- confidence: low / medium / high;
- evidence summary;
- targeted evidence references;
- verified commit/ref when available.

Do not persist “DDD + Clean Architecture” from naming alone. Evidence may include dependency direction, repository interfaces, aggregate boundaries and infrastructure adapters.

Keep evidence concise; reference source paths rather than copying large source bodies.

## Staleness / invalidation

A new Git commit alone does not make all knowledge stale.

Each topic may define:

- watched paths/globs;
- watched signals/change categories;
- verified commit;
- last verification date.

When related paths/signals change, mark only the affected topic potentially STALE and perform targeted refresh.

Examples:

- README typo → architecture knowledge remains current.
- domain/application/infrastructure boundary rewrite → architecture knowledge refresh.
- shared design tokens/components changed → visual profile refresh.

## Targeted refresh

When a topic is stale:

1. load the previous conclusion/evidence;
2. inspect only relevant changed/current sources;
3. verify/update the conclusion;
4. update evidence/confidence/verified commit;
5. leave unrelated topics untouched.

## Promotion

Repeated/important derived knowledge may deserve authoritative status.

~~~text
DISCOVERED / APPROVED knowledge
→ repeated evidence / broad project importance
→ recommend promotion
→ user/project approval
→ AGENTS.md / ADR / contract / official docs
→ Knowledge Index becomes an AUTHORITATIVE pointer
~~~

Do not automatically promote or rewrite governing project documentation.

## Security limit

Cached security knowledge accelerates context discovery but never replaces current risk classification, authorization review, security testing or required independent Security Review.

An observed middleware pattern is not proof that a new endpoint is secure.

## Context loading

Agents should first read `KNOWLEDGE_INDEX.yaml`, then load only topics relevant to the current task.

Do not preload all topic files.
