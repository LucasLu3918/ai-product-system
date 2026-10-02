# Scenario 196 — Explicit OpenAPI client generator adapter

## Given

- An existing project has a structurally valid, READY Implementation Profile.
- Its canonical OpenAPI source has current Phase 2 validation evidence bound to the current Git revision and exact spec digest.
- A local executable, exact version, argv, optional tool inputs, output directory and output allowlist are declared and pinned by hash.

## When

- The agent previews the adapter, then the Human explicitly invokes local execution with `--execute`.

## Then

- Preview runs no generator; the Integration Gate also remains inspection-only.
- Execution uses argv without a shell, staged read-only inputs, minimal environment, a bounded timeout and output limits.
- The adapter checks deterministic output, rejects unexpected files, symlinks and unknown or manually edited existing output.
- Successful apply updates generated ownership and Phase 3 hash/input/tool/version records together with the output directory; a failed replacement restores the prior state.
- Reports bind the candidate revision and exact inputs/output hashes, persist no raw process output, and do not claim OS sandboxing or semantic client correctness.

## Evidence

- `tests/validation/implementation_profile_contracts.py`
- `tests/evidence/openapi_generator_adapter_lifecycle.py`
- `templates/implementation/GENERATOR_ADAPTER_REPORT.schema.json`
