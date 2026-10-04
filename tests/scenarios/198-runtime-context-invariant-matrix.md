# Scenario 198 — Runtime Context and invariant matrix

## Given

AIPS may run from a source checkout, linked worktree, or installed system with different Python capabilities, cache locations, network access, and operating systems.

## When

The CLI resolves a validation interpreter or the publication preflight reports runtime readiness.

## Then

- Interpreter precedence is shared by the CLI and local validation setup.
- Runtime Context reports paths and capabilities without exposing environment values or credentials.
- Explicit cache configuration remains authoritative; fallback cache safety checks remain enforced.
- The deterministic runtime matrix covers every pair of declared dimension values and all listed high-risk cases.
- The matrix stays within its declared maximum and produces stable output.
