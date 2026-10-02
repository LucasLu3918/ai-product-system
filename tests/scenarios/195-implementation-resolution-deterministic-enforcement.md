# Scenario 195 — Implementation Resolution deterministic enforcement

## Purpose

Bind an applicable REST/OpenAPI Implementation Profile to an exact Git candidate and verify ownership, generated-output provenance, selected language, required project checks and Phase 2 contract evidence before an existing Integration Gate claims PASS.

## Cases

- Existing Phase 1/2 Profiles without the optional `enforcement` section stay structurally readable; unrelated Gate paths are skipped.
- A selected language Profile must validate and name the language recorded by the Implementation Profile. The Profile fingerprint and exact base/head are reported reproducibly.
- Changed in-scope paths with unknown or unresolved ownership are blocked. A changed generated file requires a matching generation record; output and input hashes must still match. This verifies record integrity, not that a generator was rerun.
- Mandatory, project-required and risk-triggered checks require fresh command evidence linked to the Profile, source file, argv and Git revision. A missing, failed, timed-out, truncated or non-reproducible result cannot pass.
- Explicit local command collection uses argv without a shell, a timeout and a capped digest-only output report. The Integration Gate verifies evidence and does not execute Profile-supplied commands.
- OpenAPI validation, compatibility and conformance reports retain Phase 2 status, kind, path, digest and revision checks. Stale or mismatched reports block enforcement.
- Report mode surfaces findings without blocking the Gate. Enforce mode fails when evidence is not PASS, including when the Profile's own scope excludes a path selected by the Gate policy.

## Limits

The Profile and unsigned command report are local evidence, not proof of semantic test quality or generator execution. CI should collect command evidence in the current run; committed command reports are rejected. Human review remains responsible for contract authority, breaking changes and business correctness.
