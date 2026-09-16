# Scenario 044 — Install / Attach / Detach / Uninstall Lifecycle

Expected:
- bootstrap.sh remains the install wrapper;
- uninstall.sh is the symmetric uninstall wrapper;
- aips attach creates/updates .ai workspace;
- aips status reports attachment/system provenance;
- aips detach archives .ai as .ai.detached-<timestamp> without deleting product source;
- attach stops when a detached workspace exists instead of silently creating a second workspace;
- documented restore returns the archived workspace to .ai;
- aips uninstall removes CLI/config only; --remove-venv additionally removes system venv;
- System repo and product repositories are not automatically deleted.
