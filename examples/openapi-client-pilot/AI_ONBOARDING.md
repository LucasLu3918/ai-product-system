# AI onboarding checklist: REST/OpenAPI product

Use this checklist when a product asks for an API change or a generated client.
Keep the product contract, implementation Profile, generated files and acceptance
evidence in that product's repository. This Widgets project is a workflow example,
not evidence that another product's behavior is correct.

## 1. Inspect the product before proposing changes

- Read the repository's `AGENTS.md` / equivalent instructions and current project
  architecture, build, test and CI conventions.
- Find the API contract, consumers, existing generated files, generator config and
  project-native quality commands. Record their repository-relative paths.
- Resolve contract authority as `canonical`, `descriptive`, `proposed` or
  `unresolved`. Do not call a spec canonical just because it is named `openapi.yaml`.
- Identify material decisions that need the product owner. Keep unresolved
  decisions explicit; do not infer approval for breaking API behavior.

## 2. Validate the contract and plan

From the product repository, run the installed AIPS OpenAPI validator against the
local contract. Resolve only repository-local references; remote references and
paths escaping the product root must stay blocked.

```bash
aips openapi validate api/openapi.yaml --repo-root . \
  --output /tmp/openapi-validation.json
```

If comparing compatibility, choose the product's approved canonical baseline and
name that authority explicitly. `BREAKING`, `UNKNOWN` and `BLOCKED` results need
resolution before treating the change as implementation-ready. Preserve the
product's own requirements, operation IDs, authorization rules, errors, retry and
idempotency behavior as applicable.

Create or update the product's `IMPLEMENTATION_PROFILE.yaml` only after material
choices are resolved. Inspect the Profile with Phase 3 `--mode report`, classify
generated, scaffolded, project-owned and unresolved files, and keep the product's
existing lint/test commands. Do not use the AIPS example's toolchain as the default
for another product.

## 3. Preview generation before executing it

Enable an adapter only when the product has an approved canonical contract, current
Phase 2 evidence, a repository-local pinned generator and reviewed output ownership.
Run the adapter without `--execute` first and inspect its version, argv, input
hashes and allowed output paths:

```bash
aips openapi generator IMPLEMENTATION_PROFILE.yaml \
  --repo-root . --adapter-id <adapter-id>
```

The preview must not start the generator. Run with `--execute` only after the
product owner has explicitly requested local generation. The adapter is a bounded
local subprocess, not an OS sandbox; use only a trusted pinned executable. Never
replace hand-edited or ownership-mismatched output. Keep business decisions in
product-owned code.

## 4. Verify the product behavior and evidence

- Run the product's documented unit, contract, integration and security checks
  that apply to the changed boundary.
- Run contract tests with argv JSON and JUnit output; require coverage for every
  applicable operation ID. Test success and relevant error/authorization paths
  against the product's actual service or an approved local test service.
- Generate current Phase 2, Phase 3 and (if enabled) Phase 4 reports on the exact
  candidate revision. Re-run them after contract, test, generator input/output,
  Profile or candidate revision changes.
- Inspect Phase 3 with `--mode enforce` only after required evidence is current.
  Missing, changed, stale, `FAIL`, `BLOCKED` or `UNVERIFIED` evidence is not PASS.
- Confirm generated and handwritten ownership, the exact changed-file set, and
  that the PR contains no unrelated product changes.
- During development, run the affected product checks. After the candidate stops
  changing, run its complete required local validation once; it should include the
  repository-wide checks, so do not immediately repeat those same checks separately.
  Keep PR and main CI because they validate different candidate revisions. Reuse
  prepared environments and read their timing reports to find measured bottlenecks;
  never shorten the required gate by omitting checks.

Useful freshness check:

```bash
aips openapi verify-evidence <report.json> --repo-root .
```

## 5. Stop conditions and recovery

| Finding | Action |
|---|---|
| Contract authority is `unresolved` or a breaking change lacks a decision | Stop the affected implementation and get the product owner's decision. |
| Remote `$ref`, escaping path or missing validator dependency | Keep validation blocked; resolve the local reference or install the pinned dependency through the product's approved setup. |
| Adapter preview is not READY, inputs/version/hash differ, or output is outside the allowlist | Do not execute; correct the Profile/tool pin or keep generation out of scope. |
| Existing generated file was hand-edited or ownership is unresolved | Preserve the file and resolve ownership; never force replacement. |
| Evidence reports `STALE` | Re-run the affected validation/test on the current candidate and verify the new report. |
| Tests or operation coverage are missing | Add or repair product-owned assertions; structural coverage alone does not prove assertion quality. |
| Local environment is `ENVIRONMENT_BLOCKED` | Follow the named environment remediation, then rerun the same check; do not misreport it as a product failure. |

## Completion record

Record the product repository and candidate revision, contract authority and
baseline, Profile digest, generator ID/version if used, generated-file ownership,
operation coverage, project-native checks, evidence freshness, known limitations
and unresolved decisions. Never copy secrets, raw prompts, private reasoning or
unnecessary payloads into the record.

For the runnable synthetic workflow, see [README.md](README.md). It proves the
tool chain against a local fixture; only the product's own service and tests can
complete a real product acceptance.
