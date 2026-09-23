# Scenario 166 — Temporal Project Intelligence

An existing project must answer current and historical architecture questions without applying future rules to an older revision or inventing unknown history.

Required behavior:

- `CURRENT` returns active current assertions;
- `AS_OF` filters by Git revision ancestry;
- `BETWEEN` reports added, ended and superseded assertions;
- `WHY` returns provenance and supersession context;
- unknown historical starts are excluded from explicit historical queries;
- malformed intervals and dangling supersession references fail closed;
- temporal SQLite tables are rebuildable from canonical YAML;
- current Project Intelligence remains the fast default.
