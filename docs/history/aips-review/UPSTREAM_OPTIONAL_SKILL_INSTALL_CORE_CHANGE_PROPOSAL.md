# Upstream Optional Native Skill Install / Uninstall

## System Improvement Review

- Appropriateness: APPROPRIATE WITH STATUS FILTERING.
- User problem: The upstream inventory is browseable, but there is no direct way to install and later selectively remove eligible upstream Skills as native Codex, Claude Code, or Gemini Skills.
- Proposed solution: Extend the existing `aips skills install|status|uninstall` commands with an explicit `--upstream` source selector. Batch operations inspect all 38 upstream records, install only `experimental_optional` and `adopted_optional` entries, and return a per-entry disposition for all other records.
- Existing coverage: Native Skill projection already validates ownership roots, records per-file digests, protects pre-existing Skills, shares Codex/Gemini references, and preserves modified files on uninstall. Upstream source records already carry disposition, local path, and reviewed source digest.
- Reuse / extension candidates: `scripts/skills_cli.py`, `scripts/native_skill_projection.py`, the existing `ownership.json` manifest, and `tests/evidence/skills_cli_lifecycle.py`.
- Lower-layer alternative: Manually copy files into Host directories; rejected because it bypasses ownership tracking and safe selective uninstall.
- Context / token cost: On-demand CLI only; no persistent prompt or automatic routing changes.
- Security / reliability: Copy only vendored files under the pinned upstream directory; verify the recorded `SKILL.md` digest; reject symlinks/path escape; never execute upstream scripts; do not overwrite unowned or modified Host files; uninstall only unchanged AIPS-owned `upstream` artifacts.
- Backward compatibility: Existing catalog `install`, `status`, and `uninstall` behavior stays the default. Manifest schema remains unchanged. Four optional upstream IDs already have canonical AIPS Skills and are skipped in favor of those canonical entries; six unique optional upstream Skills are installable.
- Scenario / test impact: Extend Scenario 259 and its existing public CLI lifecycle to cover batch/individual install, repeat installs, all three Hosts, workspace scope, mixed dispositions, duplicate IDs, modified files, unowned conflicts, and source-specific uninstall isolation.
- Human docs impact: Update Installation and User Guide with discovery, installation, status, and scoped removal examples; keep the required Harness, Maintenance, Technology Guide, Documentation Map/Sync, and Conformance placements aligned.
- Agent docs impact: CLI help describes source selection and eligibility.
- Architecture diagram impact: N/A — this extends an existing projection path and ownership manifest; no architecture boundary or runtime component changes.
- Constitution impact: NO — Human authority, project precedence, and existing authorization boundaries remain unchanged.
- Recommended AIPS solution: Add an explicit upstream source selector to the existing lifecycle, keep the active AIPS catalog as the default, and make upstream disposition and ownership visible in results.
- Additional optimization candidates: None included.
- Expected scope: Safe native installation/removal of optional vendored Skills only; integrated, workflow, and auto-routed source rows remain non-installable and are reported as skipped.
- Risks: An upstream Skill contains agent instructions. Installation copies its reviewed vendored source only after explicit user selection; it introduces no hooks, executable setup, or implicit routing.

## Core Change Proposal

### Purpose

Let users install and remove the optional, locally vendored upstream Skills through the same ownership-safe lifecycle used for AIPS Skills.

### Why this is a core change

The change expands the public AIPS CLI and modifies the shared native projection / ownership lifecycle used by Codex, Claude Code, and Gemini. A faulty source classification or uninstall filter could overwrite or delete another Skill, so the candidate requires exact lifecycle, negative-path, and cross-Host evidence.

### Proposed scope

#### In scope

- Add `--upstream` to `aips skills install`, `status`, and `uninstall`.
- Surface the source selector and batch forms in root and Skill-group help.
- Add `aips skills install --upstream --all --host <codex|claude|gemini>` and per-ID installation.
- Only `experimental_optional` and `adopted_optional` source records are install candidates. Other dispositions return a stable skipped result with the disposition as the reason.
- Skip upstream records whose ID is already in the canonical AIPS catalog; direct users to the canonical Skill instead of creating a name collision.
- Support repeatable `--host`, existing `user|workspace` scope, and the existing ownership manifest.
- Validate source containment, symlinks, source identity, and reviewed `SKILL.md` SHA-256 before copying the vendored package.
- Keep source-specific status and uninstall scoped to `source_kind=upstream`.
- Update CLI help, Installation/User Guide, Scenario 259 and its lifecycle evidence.

#### Out of scope

- Installing all 38 source Skills regardless of disposition.
- Changing AIPS auto-routing, the canonical Skill catalog, source pin, manifest schema, Host configuration, hooks, or agent-specific settings.
- Fetching or executing upstream content or setup scripts during install.
- Adding Hosts or changing the existing AIPS catalog install/uninstall defaults.

### Expected files / modules

- `scripts/native_skill_projection.py`
- `scripts/skills_cli.py`
- `scripts/aips_cli/dispatch.sh`
- `scripts/aips_cli/help.sh`
- `tests/evidence/skills_cli_lifecycle.py`
- `tests/fixtures/plan21-contract-golden-vectors.yaml`
- `tests/scenarios/259-matt-pocock-skill-integration.md`
- `docs/human/INSTALLATION.md`
- `docs/human/USER_GUIDE.md`
- `CHANGELOG.md`
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`
- `.aips/review/UPSTREAM_OPTIONAL_SKILL_INSTALL_CORE_CHANGE_PROPOSAL.md`
- `docs/human/index.md`
- `docs/human/HARNESS.md`
- `docs/human/MAINTENANCE.md`
- `docs/human/DOCUMENTATION_MAP.md`
- `docs/human/DOCUMENTATION_SYNC.md`
- `docs/human/TECHNOLOGY_GUIDE.md`
- `docs/human/CONFORMANCE.md`
- `orchestration/CONFORMANCE.md`
- `orchestration/DOCUMENTATION_SYNC.md`

### Impact

#### Architecture / Contracts

Additive CLI flags and structured result statuses; no new module, Host adapter, shared type, API, or native Skill format.

#### Data / Migration

Reuse the existing manifest. No migration. The new `source_kind` value is `upstream`; `source_id` is namespaced to the reviewed Matt Pocock source and Skill ID.

#### Security / Reliability

Keep fail-closed path and digest checks. Never claim or rewrite a pre-existing unowned Skill. Never delete a modified file or user-added resource. `--upstream` removal cannot select AIPS catalog or Portable Command records.

#### Compatibility / Rollback

Existing commands without `--upstream` retain current semantics. Rollback is selective `aips skills uninstall --upstream --all --host ...`; conflict-preserved data remains on disk and in the manifest for recovery.

#### Tests / Validation

Impact-derived matrix is maintained in `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` and bound to the exact final base/head and changed-file set.

#### Secret / Credential Impact

Secrets required: NO. No credentials are acquired or transmitted. No upstream script or hook executes.

#### Documentation / Diagrams

Update human CLI install/removal instructions. Architecture diagrams: N/A for the reasons above.

### Risks

- Source and canonical IDs can overlap; skip such upstream entries and preserve the canonical projection.
- A user may edit an installed source Skill; digest-bound uninstall must preserve it and report a conflict.
- Upstream instructions may be unsafe or stale; restrict the feature to reviewed, vendored optional records and do not execute package contents.

### Recommendation

Proceed with the scoped extension and existing ownership controls. User approved this boundary in the request: “請幫我依照建議實作所有事項，本地驗證完後需完成遠端pr合至main”.

### Proposed implementation order

1. Add source validation, package projection, and status-aware install/uninstall selection.
2. Extend the isolated CLI lifecycle and Scenario 259.
3. Update public command help and installation documentation.
4. Run focused checks, exact Core Change Integration Gate, and publication checks.
5. Publish a PR and merge the exact passing candidate to `main` under the user's explicit request.

### Approval

Status: APPROVED
Approved by: Human
Approved at: 2026-10-12
Approval record: Current user request in this Codex task.
