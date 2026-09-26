# Scenario 180 — External Eval / Red-Team Interoperability

## Given

- AIPS Agent Eval Case/Result is the canonical deterministic contract.
- Promptfoo and PyRIT are optional, untrusted evidence producers.
- External formats may contain executable configuration, secrets, private reasoning, malformed YAML, stale files or stochastic scores.

## When

- The user imports bounded Promptfoo config plus JSONL observations, imports a versioned PyRIT bridge, selects a risk profile, or promotes a finding.
- The user attempts to promote a finding that is not confirmed or lacks explicit Human approval.
- The user attempts to verify an edited evidence artifact or mismatched source file.

## Then

- Parsing rejects duplicate YAML keys, aliases, explicit tags, unknown/executable fields, unsupported providers/assertions, secret-like values, private reasoning and inputs outside byte/depth/node/item limits.
- The adapter records source hashes and a canonical evidence fingerprint, and verifies exact source hashes when requested.
- Promptfoo/PyRIT results remain `SIGNAL` or `REVIEW` and advisory; they cannot provide a Gate PASS/BLOCK or release authority.
- A confirmed finding requires Human review and a minimal deterministic rubric before it becomes an AIPS canonical Case; the existing Agent Eval scorer verifies a recorded result.
- AIPS never runs Promptfoo/PyRIT, contacts an external provider, requires credentials, or changes Runtime Policy / Content Safety enforcement.

## Evidence

- `tests/test_eval_interop.py`
- `tests/evidence/eval_interop_lifecycle.py`
- `tests/validation/eval_interop_contracts.py`
- `scripts/eval_interop.py`
