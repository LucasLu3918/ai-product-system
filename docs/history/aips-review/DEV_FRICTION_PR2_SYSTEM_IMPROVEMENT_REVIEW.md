# System Improvement Review — Dev Friction PR2: Task-Scoped Intelligence Preparation

- **Appropriateness:** Suitable. The code already treats READY+STALE as advisory; the remaining friction came from instruction text that asked for refresh and indexing on nearly every turn.
- **User problem:** Agents refreshed Intelligence or rebuilt the Retrieval index before unrelated work, which slowed development without improving safety. Orphaned stores from deleted worktrees also accumulated in the user config directory (a dry run on the developer machine listed 167 orphaned stores against 27 live ones).
- **Proposed solution:** Compute task-scoped `refresh_required`/`targeted_refresh` from the existing `task_freshness` result, set `retrieval_index_required` only when the task needs retrieval, render only the steps the turn needs, and add a dry-run-by-default `aips intelligence gc`.
- **Reuse / lower-layer alternative:** Reuses the existing `task_freshness` irrelevance proof and the task classifier's topic selection; no new mode, data store, dependency or runtime component.
- **Security / reliability:** Fail-closed reasons, Change Impact, readiness and freshness reporting are unchanged. When topic relevance cannot be proven, refresh stays required. `gc` never deletes without `--yes`, never deletes a store whose project path exists (including a broken symlink at that path), refuses symlinks and unverifiable roots, stays confined to `projects/`, re-checks before removal and preserves non-Intelligence workspace data.
- **Compatibility:** Additive manifest fields; legacy manifests still render `targeted_refresh`. Adapter templates in the repo are updated so a reinstall writes accurate wording; installed user files are not touched.
- **Constitution impact:** NO. No authority, Human approval, privacy or publication rule changes.
- **Recommendation:** Adopt as PR2 of the approved plan; default on.
- **Additional optimization candidates:** Garbage-collecting the retrieval cache (`<cache>/aips/projects`) and sharing Intelligence across worktrees (PR8) are left out of this PR.
