# Scenario 062 — Attached Project Enables Persistence

User explicitly runs `aips attach`.

Expected:
- project mode becomes ATTACHED;
- `.ai` state/manifest/system provenance are available;
- Project Intelligence persists under `.ai/intelligence/` according to policy;
- existing External Project Intelligence is validated/migrated when applicable;
- uninstalling the Global Harness does not remove the project `.ai` workspace.
