# Scenario 215: Stable runtime dependency constraints

Given a stable AIPS install or managed-environment repair, when runtime dependencies are installed, then compatibility requirements are resolved through the exact tested constraints file. Optional test-only packages are not installed solely because they appear in constraints, and package diagnostics continue to redact raw index output.

Evidence: `scripts/package_install.py`, `scripts/aips_cli.sh`, `constraints/tested.txt`, and `tests/evidence/runtime_dependency_lock_lifecycle.py`.
