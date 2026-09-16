# Scenario 076 — Source Registry Runtime-aware Dedup

AGENTS / CLAUDE / GEMINI / official docs are authoritative pointers, not copied derived content.

Expected:
- `SOURCE_REGISTRY.yaml` records each source as a pointer with `content_duplicated: false`;
- runtime visibility records only the Runtime that natively auto-loads the corresponding instruction file;
- Turn Context does not reinject a source already native to the current Runtime;
- applicable authoritative sources not natively loaded remain available as targeted-load project pointers;
- deterministic bootstrap does not copy authoritative source content into derived Project Intelligence topics.
