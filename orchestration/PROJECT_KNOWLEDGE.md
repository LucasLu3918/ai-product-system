# Project Knowledge — v0.8 Compatibility

Project Knowledge was the v0.7/v0.8 reusable discovery cache.

From v0.9 onward, the canonical model is `orchestration/PROJECT_INTELLIGENCE.md`.

## Compatibility rule

If an existing project contains:

~~~text
.ai/knowledge/KNOWLEDGE_INDEX.yaml
.ai/knowledge/*.md
~~~

do not delete or rewrite it automatically.

Treat it as migration evidence:

~~~text
Legacy Project Knowledge
→ migration source
→ SOURCE_REGISTRY / Project Intelligence topic mapping
→ canonical Project Intelligence
~~~

New reusable project understanding MUST NOT be written back into `.ai/knowledge/`.

## No duplication

Visual / Quality / Brand / Product canonical artifacts remain canonical and are referenced by Project Intelligence rather than copied.

Existing authoritative AGENTS/ADR/contracts/docs remain pointers, not duplicated content.

## Migration safety

- preserve the old knowledge directory;
- do not promote legacy interpretations to authoritative facts automatically;
- keep prior evidence/confidence where still supported;
- refresh only affected/missing information;
- explicit user/project overrides remain higher than derived Intelligence.

For all new behavior, read `orchestration/PROJECT_INTELLIGENCE.md`.
