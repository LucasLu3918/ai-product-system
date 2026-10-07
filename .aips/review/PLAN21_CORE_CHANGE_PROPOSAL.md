# Plan21 Core Change Proposal

## Purpose

Implement the final Plan21 recommendations across shared deterministic primitives, failure semantics, CLI boundaries, quality gates, documentation/preflight, installer reliability, measured performance, and CI security coverage.

## Why this is a core/large change

The work changes security and install/update failure behavior, public CLI help/error contracts, CI enforcement, shared fingerprints, and cross-module conventions. It spans several consumers and must be delivered as reviewable phase candidates instead of one oversized PR.

## Proposed Scope

### In scope

- Phase 0: freeze digest golden vectors, public CLI output/exit behavior, installer recovery lifecycle, and validation timing baseline.
- Phase 1 (P0): make malformed governance inputs fail closed; replace silent exception fallbacks with explicit failure classification and useful diagnostics; add bounded download/Git retries, portable atomic install locking, and staged transactional clone promotion.
- Phase 2: introduce `scripts/aips_common` hashing/path/ignore primitives with compatibility wrappers; preserve governance-domain canonicalization; add deterministic contracts against duplicate core primitives.
- Phase 3: repair public command-group `--help` and error status behavior; retain library modules as libraries; extend existing Ruff/mypy/quality ratchets and add focused pytest unit coverage/CI jobs without a repository-wide coverage threshold.
- Phase 4: make `INSTALLATION.md` canonical for full setup, reduce duplicated onboarding blocks, add non-breaking `system preflight` / `project check` command routes and preserve `preflight` compatibility semantics; complete the `SYSTEM.md` compatibility migration without repeating the Plan20 core work.
- Phase 5: measure small/medium/large repository timings, batch documentation git diff/read operations, use bounded single-read snapshots and reuse existing retrieval index data; do not add a second fingerprint database or weaken authoritative hashes.
- Phase 6: verify CodeQL Default Setup through read-only governance evidence, add one weekly cross-ecosystem dependency inventory scan, and run Gitleaks in shadow/advisory parity mode before considering enforcement.
- Keep all eight accepted recommendation areas and the Failure Semantics Contract / Deterministic Golden Vectors in scope. Defer only mechanisms the final recommendations explicitly reject (repo-wide 70% coverage, `flock` as the sole lock, blanket `argparse` conversion, new fingerprint SQLite DB, or treating missing CodeQL YAML as disabled).

### Out of scope

- Constitution changes, breaking public CLI renames, automated release/tag creation, changing protected-branch policy, promoting advisory security tools to mandatory enforcement without parity evidence, or introducing an independent fingerprint cache.
- Changes to user projects, external services, credentials, or production deployment.

## Expected Files / Modules

- Python helpers and consumers: `scripts/aips_common/**`, `scripts/governance_guard.py`, `scripts/harness_resolve.py`, `scripts/aips_identity.py`, `scripts/execution_isolation.py`, `scripts/task_ownership.py`, `scripts/check_secret_leakage.py`, `scripts/deterministic_scheduler.py`, `scripts/repository_health.py`, `scripts/governance_audit.py`, `scripts/publish_preflight.py`, `scripts/documentation_placement.py`, `scripts/project_intelligence.py`, `scripts/retrieval_intelligence.py`, and focused tests/contracts.
- CLI/installers: `scripts/aips_cli/dispatch.sh`, `scripts/aips_cli/help.sh`, `scripts/install.sh`, `scripts/install.ps1`, installer lifecycle evidence and public CLI contracts.
- Quality/CI/config: `pyproject.toml`, existing quality ratchet configuration, requirements/test configuration, relevant `.github/workflows/**`, and dependency scanner configuration.
- Documentation and architecture: `README.md`, `docs/human/INSTALLATION.md`, `docs/human/GETTING_STARTED.md`, `SYSTEM.md`, canonical orchestration guidance, affected scenarios, and architecture diagrams only where the final boundary changes them.
- Review evidence: this proposal, per-phase Change Impact, and candidate-bound `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`.

Exact changed paths will be frozen and reconciled separately for each phase candidate.

## Impact

### Architecture / Contracts

Preserve canonical JSON bytes and existing digest representations; preserve public facade imports and CLI semantics except documented help/error corrections. Domain-specific governance canonicalization remains owned by its domain.

### Data / Migration

No persistent schema migration is planned. Installer staging/lock metadata must recover safely from interruption and preserve a prior valid installation.

### Security / Reliability

Malformed or unreadable policy input must not become an empty/allow-shaped success. Installer recovery must be serialized across macOS/WSL without relying on platform-specific `flock`; retries are bounded; promotion occurs only after verification. Advisory scanners cannot change allow/deny or publish status.

### Compatibility / Rollback

Compatibility wrappers and the `aips preflight` route remain. Each phase is independently revertible and separately validated. No fingerprint is accepted unless its authoritative hash is computed.

### Tests / Validation

Use golden digest vectors, negative malformed-input contracts, CLI stdout/exit snapshots, installer retry/lock/staging/recovery lifecycle tests, facade identity contracts, incremental lint/type/unit tests, documentation placement/sync, exact candidate secret scan, full local Integration Gate, PR checks, and post-merge main checks. Performance claims require measured before/after evidence. Matrix N/A entries require reasons.

### Secret / Credential Impact

Secrets required: NO. Candidate secret scans remain credential-free; diagnostics must not print payloads or secrets.

### Documentation / Diagrams

Update human and agent guidance for changed behavior. Update architecture diagrams only for real boundary/topology changes; otherwise record N/A in the phase matrix.

## Risks

- Digest refactoring can drift byte-level fingerprints; frozen vectors and wrappers mitigate this.
- Broad exception cleanup can change capability-probe behavior; classify each expected miss separately and keep policy failures fail-closed.
- Cross-platform installer locking and atomic promotion are interruption-sensitive; lifecycle coverage must include concurrency, stale locks, partial clone cleanup, and preserved existing installs.
- CI scanner action/version/network failures can create cost or false alarms; weekly OSV and Gitleaks remain advisory until parity is reviewed.
- The full scope is large; phase candidates must not silently expand, and each PR must pass its exact-candidate gates before merge.

## Recommendation

Proceed in the ordered phases above. Ship separate PRs for phase candidates so each change is independently reviewable and revertible; merge only after local exact-candidate validation and required remote checks pass.

## Proposed Implementation Order

1. Phase 0 contract freeze and measurement baseline.
2. Phase 1 P0 failure semantics and installer reliability.
3. Phase 2 common deterministic primitives.
4. Phase 3 CLI and quality contracts.
5. Phase 4 documentation and preflight semantics.
6. Phase 5 measured performance improvements.
7. Phase 6 CI security defense in depth.

## Approval

Status: APPROVED BY USER REQUEST
Approved by: User
Approved at: 2026-10-08 (user instruction to implement all final Plan21 recommendations)
Approval record: Current task request, following the final recommendations in the `plan21` conversation.
Proposal fingerprint: pending exact-scope hash
Scope fingerprint: pending phase file-set reconciliation
