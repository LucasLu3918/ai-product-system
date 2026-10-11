# Creative repair validation and change inventory

Scope authorization: user approved the preceding P0/P1/P2 implementation and requested locally verified PR merge into main.

## Focused evidence

- Pillow 12.3.0 is a runtime dependency so ordinary installed AIPS can decode/crop images; it is not limited to the test-only visual environment.
- PASS: Ruff on changed creative modules, fixtures and validator consumers.
- PASS: mypy on creative_repair, creative_execution, creative_request_policy and turn_intent.
- PASS: original recreation/read-only/negated prompt policy and bounded repair lifecycle.
- PASS: versioned feedback/profile copies, source hashes, lineage comparison, finite repair/uncertainty/repeated-defect/time stops.
- PASS: projected native tool fixture, including scope, current-message replay, concurrent reservations and overlapping prompt epoch.
- Independent distinct-role semantic review: no remaining material blockers after two correction rounds. Runtime attestation remains unavailable; this is not a VERIFIED attestation claim.
- Credential-free native host acceptance: OpenCode v2.0.24 on darwin; prepare, revocation, Context and supported native permission hooks observed. New repair execution is covered by the projected tool fixture.
- Real local image generation and vision accuracy: UNVERIFIED in this change; fixtures never establish artwork quality.
- Initial complete Gate caught the CLI help golden contract drift; both help aliases were synchronized and focused baseline rerun passed.
- Ordinary generation now grants only bounded quality checks of its own produced manifests; this cannot grant repair/acceptance authority.
- Exact-candidate full Core Gate and required remote checks: executed separately before publication/merge, report kept in task-local temporary evidence.

## Actual file changes

- modified: `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`
- added: `.aips/review/CREATIVE_REPAIR_CORE_CHANGE_PROPOSAL.md`
- added: `.aips/review/CREATIVE_REPAIR_VALIDATION.md`
- modified: `CHANGELOG.md`
- modified: `config/documentation-placement.yaml`
- modified: `config/documentation-sync.yaml`
- modified: `constraints/tested.txt`
- modified: `docs/ARCHITECTURE.md`
- modified: `docs/human/ARCHITECTURE_OVERVIEW.md`
- modified: `docs/human/CONFORMANCE.md`
- modified: `docs/human/DOCUMENTATION_MAP.md`
- modified: `docs/human/DOCUMENTATION_SYNC.md`
- modified: `docs/human/EVOLUTION_RADAR.md`
- modified: `docs/human/EVOLUTION_RADAR_OVERVIEW.md`
- modified: `docs/human/GETTING_STARTED.md`
- modified: `docs/human/HARNESS.md`
- modified: `docs/human/INSTALLATION.md`
- modified: `docs/human/MAINTENANCE.md`
- modified: `docs/human/PROJECT_INTELLIGENCE.md`
- modified: `docs/human/SECURITY_ASSURANCE.md`
- modified: `docs/human/TECHNOLOGY_GUIDE.md`
- modified: `docs/human/USER_GUIDE.md`
- modified: `docs/human/index.md`
- modified: `harness/HARNESS_PROTOCOL.md`
- modified: `harness/adapters/opencode/AGENTS.md`
- modified: `harness/adapters/opencode/COMPATIBILITY.md`
- modified: `harness/adapters/opencode/plugin.ts`
- modified: `orchestration/CHANGE_IMPACT.md`
- modified: `orchestration/CONFORMANCE.md`
- modified: `orchestration/CORE_CHANGE_TESTING.md`
- modified: `orchestration/CREATIVE_DIRECTION.md`
- modified: `orchestration/DETERMINISTIC_SCHEDULER.md`
- modified: `orchestration/DOCUMENTATION_SYNC.md`
- modified: `orchestration/EVOLUTION_RADAR.md`
- modified: `orchestration/EXECUTION_ISOLATION.md`
- modified: `orchestration/GITHUB_RULESET_POLICY.md`
- modified: `orchestration/INTEGRATION_GATE.md`
- modified: `orchestration/ORCHESTRATOR.md`
- modified: `orchestration/PROJECT_INTELLIGENCE.md`
- modified: `orchestration/RELEASE_READINESS.md`
- modified: `orchestration/RUNTIME_CONTEXT.md`
- modified: `requirements.txt`
- modified: `scripts/aips_cli/help.sh`
- modified: `scripts/creative_execution.py`
- added: `scripts/creative_repair.py`
- modified: `scripts/creative_request_policy.py`
- modified: `scripts/turn_intent.py`
- modified: `templates/creative/VISUAL_REVIEW_REPORT.schema.json`
- added: `tests/evidence/creative_repair_lifecycle.py`
- modified: `tests/evidence/creative_tool_harness.mjs`
- modified: `tests/scenarios/238-creative-task-authorization-and-multi-item-execution.md`
- modified: `tests/validation/creative_quality_contracts.py`
- modified: `tests/validation/registry.py`

- modified: `tests/fixtures/plan21-contract-golden-vectors.yaml`
