# Plan28: Git Publication Reliability and Security

Direction approved by Human in the current task: external Ed25519 issuer; AIPS only,
local validation followed by feature PR and merge to main. Constitutional semantics
are unchanged: enforce existing Human authority instead of introducing Agent authority.

## Boundary

Extend the existing governance guard, Approval Record and CLI. Add a publication
authority adapter, exact-operation proposals, externally signed receipts and atomic
consumption through a separately administered HTTPS service. Production trust
configuration is administrator-owned and cannot be supplied by repository content
or an Agent-controlled environment variable. No private keys are provisioned by AIPS.

Bind common Git directory, worktree Git directory, branch, HEAD, explicit base,
complete NUL-delimited changed files and diff digest, remote push URL, exact argv,
target ref, observed remote tip, force/delete semantics, expiration and grant ID.
Unsupported/ambiguous publication commands fail closed. Verification is read-only;
the PreToolUse gate consumes a grant before allowing execution. A failed execution
requires a new grant. Legacy unsigned Git grants require reissuance; existing
non-publication runtime policy verification retains its API and semantics.

Use shell AST command nodes, including executable substitutions, rather than
searching heredoc/string text. Only syntactically valid Co-Authored-By trailers in
commit messages receive the email exemption; staged blobs still receive complete
content safety scanning. Read-only tag queries need no publication grant.

## Acceptance / tests

Positive signed verification and consume; unsigned/tampered/expired/wrong-key
rejection; stale remote/ref/force/delete/base/candidate/worktree/diff; no upstream;
service outage, replay and racing consume; malformed/unsupported shell; quoted
heredoc, executable substitutions, nested commands, tag reads; legal trailer,
ordinary email and staged secret rejection; CLI/Harness and runtime-policy
compatibility; full repository validator, strict candidate tree/history secret scan,
documentation closure and exact-candidate Integration Gate.

## Compatibility / operations

Reuse current protected-publication vocabulary and extend it to PR merge. New
records are version 2. Missing external issuer denies protected Git operations.
Codex/OpenCode advisory capability remains advisory: no universal sandbox claim.
The HTTPS issuer must be deployed separately, with its signing key and transactional
grant store inaccessible to Agents. Fixture signatures prove protocol behavior,
not a production trust root. Protected trust configuration and service deployment
are documented operational prerequisites.

## Impact and review

Inputs: shell commands, Git metadata, v2 records, external trust policy and service.
Outputs: proposals, redacted deny reasons, signed status/consume assertions.
Consumers: Claude/Gemini hooks, CLI, runtime policy, validators and Human docs.
Repository-wide Impact Graph remains partial; manually reviewed direct consumer
references are bounded evidence, not global completeness. Architecture Mermaid and
Human overview gain the issuer boundary; SVGs remain N/A (no product deployment unit).
No new Role, Skill, Capability, constitutional amendment or unrelated optimization.

## Final file boundary

Paths are repository-relative; new modules/proposal/test are additions, other paths are modifications.

- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`
- `.aips/review/PLAN28_CORE_CHANGE_PROPOSAL.md`
- `CHANGELOG.md`
- `config/documentation-placement.yaml`
- `constraints/tested.txt`
- `docs/ARCHITECTURE.md`
- `docs/human/ARCHITECTURE_OVERVIEW.md`
- `docs/human/CONFORMANCE.md`
- `docs/human/DOCUMENTATION_MAP.md`
- `docs/human/DOCUMENTATION_SYNC.md`
- `docs/human/EVOLUTION_RADAR.md`
- `docs/human/HARNESS.md`
- `docs/human/INSTALLATION.md`
- `docs/human/MAINTENANCE.md`
- `docs/human/PROJECT_INTELLIGENCE.md`
- `docs/human/SECURITY_ASSURANCE.md`
- `docs/human/TECHNOLOGY_GUIDE.md`
- `docs/human/USER_GUIDE.md`
- `docs/human/index.md`
- `harness/HARNESS_PROTOCOL.md`
- `harness/adapters/opencode/AGENTS.md`
- `harness/adapters/opencode/COMPATIBILITY.md`
- `orchestration/CHANGE_IMPACT.md`
- `orchestration/CONFORMANCE.md`
- `orchestration/CREATIVE_DIRECTION.md`
- `orchestration/DETERMINISTIC_SCHEDULER.md`
- `orchestration/DOCUMENTATION_SYNC.md`
- `orchestration/EXECUTION_ISOLATION.md`
- `orchestration/GITHUB_RULESET_POLICY.md`
- `orchestration/INTEGRATION_GATE.md`
- `orchestration/ORCHESTRATOR.md`
- `orchestration/PROJECT_INTELLIGENCE.md`
- `orchestration/RELEASE_READINESS.md`
- `orchestration/RUNTIME_CONTEXT.md`
- `requirements.txt`
- `scripts/aips_cli/dispatch.sh`
- `scripts/aips_cli/help.sh`
- `scripts/governance_guard.py`
- `scripts/publication_authority.py`
- `scripts/publication_commands.py`
- `scripts/publication_issuer.py`
- `templates/governance/APPROVAL_RECORD.yaml`
- `tests/fixtures/plan21-contract-golden-vectors.yaml`
- `tests/scenarios/018-git-publish-approval.md`
- `tests/scenarios/096-approval-fingerprint-determinism.md`
- `tests/scenarios/097-approval-scope-drift-stops-protected-action.md`
- `tests/test_publication_authority.py`
- `tests/validation/governance_resume.py`
