# Deterministic Automation

Use deterministic code before AI reasoning when a step can be reliably produced from explicit rules.

## Principle

~~~text
Existing deterministic tool
→ simple Shell / script
→ structured output
→ AI reasoning only on the useful result
~~~

Do not send large raw data to an AI merely to perform counting, filtering, extraction, format conversion or other deterministic work.

## Good candidates

- repository/file inventory;
- Git changed-file statistics;
- duplicate Role/Skill IDs;
- YAML/JSON/schema validation;
- test/log summarization;
- dependency/version extraction;
- pattern search;
- CSV/JSON transformation;
- checksum/hash;
- documentation link checks;
- repeatable report generation.

## Keep AI for reasoning

Do not automate subjective or genuinely reasoning-heavy decisions merely to save tokens. Examples: architecture tradeoffs, threat modeling, visual taste, requirement conflicts and product decisions.

## Automation value check

Prefer a helper when the expected benefit from reuse, input size, token reduction, consistency and verifiability outweighs creation/maintenance cost.

Do not build a large tool for a trivial one-off input.

## Tool lifetime

~~~text
run-local
→ project reusable
→ system reusable
~~~

- Run-local: `.ai/runs/<run-id>/tools/`
- Project reusable: `.ai/tools/`
- System reusable: `ai-product-system/scripts/` only after repeated cross-project value is proven.

Promotion requires evidence; do not place every helper in the global system.

## Output contract

Prefer JSON or YAML summaries with raw evidence stored separately.

Example:

~~~yaml
status: success
summary:
  files_scanned: 128
  failures: 2
findings:
  - id: duplicate-skill
    evidence: skills/INDEX.yaml
raw_evidence:
  path: .ai/runs/run-123/evidence/output.log
~~~

AI reads the summary first and opens raw evidence only when needed.

## Safety

- default to read-only analysis;
- use least privilege;
- never persist secrets into output;
- bounded inputs/outputs;
- destructive operations still require normal governance/approval;
- high-risk helpers require review;
- generated code must be simple enough to inspect and reproduce.

## Shell vs Python

Prefer Shell for short filesystem/process/Git composition.

Prefer Python when parsing structured data, applying non-trivial transformations or producing structured reports.

Use the language already available in the project when that materially reduces setup or maintenance.


## Scheduling after planning

When a Human-approved/planned change is already decomposed into bounded tasks, do not spend model turns repeatedly deciding which ready task runs next.

Use `orchestration/DETERMINISTIC_SCHEDULER.md` and a Structured Task Graph. The LLM/Orchestrator owns semantic planning; deterministic code owns dependency readiness, stable ordering, parallel capacity and Change Boundary locks.

A blocked graph returns to planning/governance only when semantic change is actually required. The Scheduler must not silently invent a workaround.

## Merge-candidate validation

Use `orchestration/INTEGRATION_GATE.md` for exact-candidate deterministic validation. Validation Profiles are project-native argv contracts; Core Change Test Matrix evidence is reused rather than duplicated.
