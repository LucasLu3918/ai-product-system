# Scenario 062 — Explicit Project State Uses External Persistence

User explicitly runs `aips attach`.

Expected:
- Project Intelligence is initialized in external user state;
- project root, Git config, hooks and ignore files remain unchanged;
- existing legacy `.ai` content is copied only when needed and remains byte-identical;
- legacy `.ai/intelligence/` remains in place after validated external copy;
- new run and Change Impact state remain outside the repository;
- uninstalling the Global Harness preserves external state and legacy project data.
