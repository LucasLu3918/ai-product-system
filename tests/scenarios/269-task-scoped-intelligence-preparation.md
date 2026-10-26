# Scenario 269: Task-Scoped Intelligence Preparation

## Given

- A local Git project has Project Intelligence readiness `READY` and freshness `STALE`.
- Only the `testing` topic is affected; the Retrieval index has not been built.
- The user config `projects/` directory also contains a store whose recorded project root was deleted.

## When

- A mutation prompt selects only unaffected topics, a testing prompt selects the affected topic, and a read-only prompt selects no topics.
- `aips intelligence gc` runs first without and then with `--yes`.

## Then

- The unaffected mutation reports `refresh_required=false`, an advisory reason and no `targeted_refresh`, while Change Impact stays required and the fail policy stays soft.
- The testing task reports `refresh_required=true` with `targeted_refresh=[testing]` only.
- The read-only turn reports `retrieval_index_status=MISSING` without `retrieval_index_required`, and the Turn Context hook gives no refresh, index or Change Impact instruction.
- Non-READY, UNKNOWN, instruction-conflict, path-escape, creative and external controls are unchanged.
- The `gc` dry run lists only the orphaned store and deletes nothing; `--yes` removes only that store, never a store whose project path exists, symlinked entries or stores with an unverifiable root.

## Evidence

- `tests/evidence/intelligence_context_lifecycle.py`
- `tests/test_intelligence_task_freshness.py`
