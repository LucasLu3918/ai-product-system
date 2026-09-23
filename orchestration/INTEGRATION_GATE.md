# Integration Gate (Janitor Gate)

Use before merge/publication of an integration candidate when deterministic validation can prove candidate fitness.

`Janitor` is the informal name. The canonical AIPS contract is **Integration Gate**.

The Gate is deterministic code. It has no Human approval, merge or release authority.

## Exact-candidate binding

~~~text
base SHA + head SHA
→ changed-file set/hash
→ Validation Profile hash
→ optional Core Change Test Matrix hash
→ Candidate Fingerprint
→ deterministic checks
→ PASS / FAIL / BLOCKED evidence
~~~

The checked-out `HEAD` must equal the declared head SHA. A stale/mismatched checkout is BLOCKED before checks execute.

Changing code, base revision, Validation Profile or required Test Matrix changes the candidate fingerprint and invalidates prior evidence.

## Validation Profile

Checks may declare `expected_test_count` when a command reports a standard unittest summary. The Gate fails if the expected count is absent or different, preventing a successful no-op command from being treated as test evidence.

Use `templates/automation/VALIDATION_PROFILE.yaml`.

Each project declares native validation as argv arrays, never arbitrary model judgment:

- lint/static checks;
- type checks;
- unit/integration/contract/E2E tests as applicable;
- security/secret checks;
- repository/schema/documentation checks;
- other deterministic commands justified by the project.

AIPS Core must not hard-code one language toolchain as the universal project contract. Go/PHP/JS/Python projects keep their own appropriate commands.

Path filters may skip checks that provably do not apply. Required applicable failures block the candidate.

## Core Change Test Matrix reuse

For Large/Core changes, the Gate reuses `templates/review/CORE_CHANGE_TEST_MATRIX.yaml`; it does not introduce a parallel Janitor matrix.

When a Validation Profile marks `matrix_required: true`, missing/unready matrix, blockers or unreconciled actual diff BLOCK execution.

The Matrix decides what evidence is applicable. The Gate executes/verifies deterministic commands and binds the resulting evidence to the candidate.

## GitHub required-check compatibility

AIPS keeps the existing protected-main required context `repository`.

The validation workflow runs the `janitor` job first. The required `repository` job is a compatibility aggregate that can succeed only when Janitor succeeds. Therefore existing branch protection continues to block a failing candidate without requiring a branch-protection migration.

~~~text
PR/main candidate
→ janitor: exact candidate + lint/type/tests/contracts
→ repository required aggregate
   ├─ janitor success → SUCCESS
   └─ janitor fail/block → FAILURE
→ merge remains Human/GitHub governed
~~~

## Report

Validation checks may declare `expected_test_count`; the Gate requires the standard unittest summary to report that exact number. This prevents zero-test commands from producing a false PASS.

Core candidates may include `trajectory-quality-gate-lifecycle`. Its PASS proves deterministic trajectory evidence and privacy-safe evaluation only; the report must retain `human_authority_preserved: true` and cannot authorize merge, release or publication.

Use `templates/review/INTEGRATION_GATE_REPORT.yaml`.

Local reports may store bounded command output tails plus fingerprints/status. CI uses `--omit-output-tail` so uploaded reports and workflow summaries contain check IDs, status, exit codes and output hashes without command output. A missing report is shown as `REPORT_UNAVAILABLE`; a skipped Gate is `NOT_RUN`. Neither state is PASS. Reports must not persist secrets or private model reasoning.

PASS means deterministic validation evidence is green. It does **not** authorize merge, publication, release, scope expansion or risk acceptance.

## PR base freshness

Local maintainers and GitHub Actions MUST enter the Gate through `scripts/publish_preflight.py` for publication candidates. The shared resolver binds the same base/head, PR-label change class, canonical `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`, `AIPS_DOCS_DIFF_BASE` and fast repository preflight before expensive lifecycle checks.

The preflight also requires a clean exact candidate checkout and validates the Matrix changed-files hash before the Gate starts. Browser-dependent evidence uses a versioned Playwright managed browser when available; a failed isolated launch probe is `ENVIRONMENT_BLOCKED`, not a product regression.

For pull-request validation, the caller should provide `--base-tip <fresh-target-ref>` after freshly fetching the target branch.

The Gate resolves both the declared base and current target tip. If they differ, the candidate is BLOCKED before validation commands execute:

~~~text
declared PR base SHA
↔ freshly fetched target branch tip
→ equal: continue exact-candidate validation
→ different: BLOCKED / regenerate and revalidate
~~~

When provided, `base_tip_sha` is included in candidate evidence/fingerprinting. This complements the existing exact-head checkout check and Human/GitHub merge preflight.

## Conditional Core Matrix enforcement

Validation Profiles may declare `matrix_required_change_classes` plus a narrow `matrix_required_paths` safety net. Standard changes are Matrix-optional by default; `aips:large-change` and `aips:core-change` resolve to required Matrix evidence. Known governance-core Integration Gate surfaces may also require the Matrix when labels are absent.

When required, the Matrix must bind the exact base SHA and deterministic changed-files hash, be reconciled to the actual diff, contain no blockers and have executable status. PASS remains evidence only.

Versioned review matrices may preserve history, but CI consumes only the canonical matrix path. A required matrix at any other path is a blocked publication candidate.


## v0.51 runtime-resource isolation interaction

Parallel Runtime Port Isolation does not change Integration Gate authority or candidate semantics. Runtime port lifecycle evidence is executed by repository validation for the exact candidate, while Scheduler-focused validation continues to check deterministic Task Graph metadata. A port lease is ephemeral execution coordination evidence and is not included as a merge/release authorization token.
## Content Safety Gate

The Integration Gate runs the content-safety lifecycle for affected candidates and requires the canonical sink manifest. Durable/public content safety failures are blocking; diagnostic redaction remains a safe degraded path.
