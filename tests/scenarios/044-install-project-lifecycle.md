# Scenario 044 — Install / Attach / Detach / Uninstall Lifecycle

Expected:
- bootstrap.sh remains the install wrapper;
- uninstall.sh is the symmetric uninstall wrapper;
- `aips attach` explicitly creates/updates the `.ai` workspace;
- `aips status` reports attachment/system provenance;
- `aips detach` syncs reusable Intelligence externally, then archives `.ai` as `.ai.detached-<timestamp>` without deleting product source;
- attach stops when a detached workspace exists instead of silently creating a second workspace;
- preflight keeps a project without `.ai/` EPHEMERAL and does not auto-attach it;
- documented restore returns the archived workspace to `.ai`;
- `aips uninstall` removes AIPS-owned CLI/runtime integration state only; `--remove-venv` additionally removes the system venv;
- normal uninstall preserves project `.ai` workspaces and External Project Intelligence unless `--remove-cache` is explicitly requested;
- System repo and product repositories are not automatically deleted.
