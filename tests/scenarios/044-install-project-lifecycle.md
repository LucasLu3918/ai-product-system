# Scenario 044 — Install / External Project State / Uninstall Lifecycle

Expected:
- bootstrap.sh remains the install wrapper;
- uninstall.sh is the symmetric uninstall wrapper;
- `aips attach` explicitly bootstraps or imports Project Intelligence into external user state;
- attach, detach and preflight do not create or rewrite project `.ai/`, `.aips/`, `.git/info/exclude`, or `.gitignore`;
- existing `.ai/` files are preserved as legacy data; validated Intelligence migration copies to external state without deleting the source;
- new clones and non-Git projects receive no AIPS files or Git metadata;
- preflight keeps a project without `.ai/` EPHEMERAL internally while the CLI reports EXTERNAL storage;
- repeated attach/detach is safe and leaves project Git status unchanged;
- `aips status` reports the external storage mode and optional governance mode;
- detach is a compatibility command that preserves external state and legacy project files;
- `aips uninstall` removes AIPS-owned CLI/runtime integration state only; `--remove-venv` additionally removes the system venv;
- normal uninstall preserves legacy project `.ai` data and External Project Intelligence unless `--remove-cache` is explicitly requested;
- System repo and product repositories are not automatically deleted.
