# Scenario 044 — Install / Attach / Detach / Uninstall Lifecycle

Expected:
- bootstrap.sh remains the install wrapper;
- uninstall.sh is the symmetric uninstall wrapper;
- `aips attach` explicitly creates/updates the `.ai` workspace;
- in Git worktrees, attach/detach add anchored `.ai/` and `.ai.detached-*/` patterns to repository-local `info/exclude`, preserve existing entries, and leave `.gitignore` unchanged;
- normal Git staging omits new AIPS-local state; already tracked paths are not silently untracked;
- nested project attachment scopes local exclude patterns to the nested project path, while non-Git projects do not gain Git metadata;
- `aips status` reports attachment/system provenance;
- `aips detach` syncs reusable Intelligence externally, then archives `.ai` as `.ai.detached-<timestamp>` without deleting product source;
- attach stops when a detached workspace exists instead of silently creating a second workspace;
- preflight keeps a project without `.ai/` EPHEMERAL and does not auto-attach it;
- documented restore returns the archived workspace to `.ai`;
- `aips uninstall` removes AIPS-owned CLI/runtime integration state only; `--remove-venv` additionally removes the system venv;
- normal uninstall preserves project `.ai` workspaces and External Project Intelligence unless `--remove-cache` is explicitly requested;
- System repo and product repositories are not automatically deleted.
