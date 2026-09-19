# Documentation Consistency Contract

## Purpose

Keep Human-facing and Agent-facing documentation synchronized with behavior-bearing AIPS changes.

Documentation completeness is part of implementation completeness. A change is not complete merely because code and tests pass while affected guidance, terminology or architecture descriptions remain stale.

## Authority

This contract does not create a new Human Approval Gate. It strengthens the existing Documentation Impact Gate with deterministic changed-path checks.

Canonical configuration: `config/documentation-sync.yaml`.
Validator: `scripts/documentation_sync.py`.
Human explanation: `docs/human/DOCUMENTATION_SYNC.md`.
Human technology inventory: `docs/human/TECHNOLOGY_GUIDE.html`.

## Audience synchronization

When a configured behavior-bearing source path changes, the same change MUST update the mapped documentation surfaces:

- Human docs explain behavior, workflows, terminology and operational use in Traditional Chinese;
- Agent docs define concise execution contracts and authority boundaries in English;
- the Human Technology Guide is reviewed whenever configured technical implementation/contract surfaces change.

The mapping is explicit and deterministic. Do not guess from file names during validation.

Project Intelligence documentation mapping includes the stable intelligence implementation, rebuildable Retrieval Intelligence implementation, Retrieval Quality Evaluation harness, Structural Retrieval trial/adoption harness and provider-neutral local-first embedding Trial / optional remote operator-summary surfaces, including the dedicated semantic Trial dependency, so changes to indexing/ranking/context assembly/evaluation metrics, structural retrieval behavior or embedding Trial provider/privacy/operator-handoff contracts require the Human Project Intelligence guide, Agent protocol and Technology Guide to be reviewed together.

## Technology Guide rule

`docs/human/TECHNOLOGY_GUIDE.html` is a maintained Human inventory of important AIPS techniques and terms. A configured technical change requires the guide to be updated in the same diff, even when the update only clarifies that the technology inventory is unchanged and records the reviewed behavior.

This deliberately favors documentation freshness over minimizing documentation diffs.

## Validation behavior

`documentation_sync.py`:

1. validates `config/documentation-sync.yaml`;
2. receives changed files explicitly or resolves them from a Git comparison base;
3. matches changed behavior-bearing paths against configured rules;
4. requires every mapped Human and Agent document in the same change;
5. requires the Technology Guide when a configured technical path changed;
6. fails repository validation if a required documentation surface is missing from the diff.

CI sets `AIPS_DOCS_DIFF_BASE` from the GitHub event base revision. Local validation without a known base still validates the contract/configuration, while focused checks may pass `--base-ref` or `--files` explicitly.

## Scope discipline

Do not edit unrelated documentation merely to satisfy the validator. If a mapping becomes systematically noisy or inaccurate, change the mapping through normal AIPS maintenance review rather than bypassing the check.

The deterministic check proves that required documentation surfaces were reviewed in the same change. It cannot prove semantic correctness of prose. Semantic accuracy remains part of Author/Reviewer responsibility.

## Cross-document navigation

Human pages should link to relevant Human detail pages and, when useful for maintainers, canonical Agent protocols. Agent protocols may point to Human explanations but must keep canonical execution rules in Agent-facing protocol files rather than duplicating large Human guides.


## Human Documentation Namespace

Permanent Human-only documentation MUST live under `docs/human/`. The detailed audience policy is deterministic:

- config: `config/documentation-audience.yaml`;
- validator: `scripts/documentation_audience.py`;
- Human-only root: `docs/human/`;
- shared canonical docs under `docs/` require explicit allowlisting;
- standalone Human artifacts outside the Human root MUST be listed in `standalone_human_documents` and use the `HUMAN_` prefix.

Do not create a parallel `docs/agent/` tree. Existing `orchestration/`, `harness/`, Roles, Skills, templates and schemas remain canonical Agent/machine surfaces.


## Deterministic execution mapping

The `deterministic-execution` rule binds Scheduler / Integration Gate implementation, Task Graph / Validation Profile contracts, validation dependencies and the GitHub validation workflow to their Human architecture/user guidance and Agent orchestration protocols.

This keeps the runtime implementation, exact-candidate CI behavior and authority boundaries synchronized when future changes touch scheduling or Janitor behavior.


## Resource authorization mapping

The `resource-authorization` rule binds the deterministic evaluator, Resource Authorization Profile schema/template and Execution Profile reference to Human Architecture/User guidance plus Agent Execution Isolation/Orchestrator protocols. Any behavior change must keep default-DENY semantics, protected-authority boundaries and runtime-enforcement truth synchronized across those surfaces.


## Agent Runtime Assurance mapping

The `agent-runtime-assurance` documentation rule binds the provider-neutral intent/anomaly evaluator and Agent protocol to Human Architecture/User guidance plus Resource Authorization / Execution Isolation contracts.

When the same change updates `references/evolution/CAPABILITY_MAP.yaml`, the Evolution Radar mapping also applies. This intentionally keeps semantic capability discovery synchronized with the implemented evidence contract and prevents future duplicate subsystem recommendations.
