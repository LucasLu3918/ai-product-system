# Runtime Context

`scripts/runtime_context.py` is the shared source for runtime path and validation interpreter resolution. Keep it free of credentials and external-service side effects.

## Interpreter resolution

The order is `AIPS_VALIDATION_PYTHON`, `AIPS_VALIDATION_VENV`, project `.venv`, the project-hashed temporary validation venv, the installed AIPS venv, and the current Python. Full validation requires Python 3.12 and the pinned Gate modules. The base runtime only requires PyYAML. `bin/aips` is the thin public launcher; `scripts/aips_cli.sh` keeps the minimal bootstrap selection, then asks Runtime Context to resolve the requested capability level.

`bin/prepare-local-validation` uses the same project-hashed venv path. `scripts/package_install.py` continues to accept an explicit interpreter from its caller and does not choose one itself.

## Context contract

The publication environment report may include invocation mode, project/system roots, selected interpreter, capability readiness, config/cache paths, the GitHub CLI config path, and offline mode. Runtime Context reports Playwright package availability and leaves browser launch state unverified; the publication environment probe reports the actual browser launch result. It does not claim sandbox support without provider verification. Never serialize environment values, tokens, credential files, or secret-bearing command output.

Explicit `XDG_CACHE_HOME` remains authoritative. Without it, existing private fallback validation and write checks apply. Context collection must not create directories or modify permissions.

## Verification

`config/runtime-invariants.yaml` declares the supported invariant dimensions and high-risk combinations. `scripts/runtime_invariant_matrix.py --check` deterministically verifies exhaustive pair coverage, uniqueness, high-risk membership, and the configured case bound. Scenario 198 and its lifecycle evidence are registered in the repository conformance map.


The public `bin/aips` launcher resolves symlinks and forwards arguments to `scripts/aips_cli.sh`. Keep the shared resolver call and capability selection in the implementation layer while preserving the launcher contract.
