# Plan25 Phase 1 Evidence

Date: 2026-10-09
Base: Phase 0 candidate `fb0d63789e696e08cb65296b7e254b58c2d7171d`
Scope: stable release readiness, available-host Runtime acceptance, Project Intelligence recovery guidance, and Doctor consistency.

## Results

| Area | Evidence | Result and limit |
|---|---|---|
| Stable release | `scripts/check_release_readiness.py` with `tests/fixtures/release-readiness-ready.yaml` and `tests/fixtures/release-readiness-blocked.yaml`; `tests/evidence/release_channel_lifecycle.py` | Expected READY and blocked decisions passed. No version tag or Release was created; this verifies readiness policy, not publication or installation from a published stable artifact. |
| Native Runtime | `tests/evidence/opencode_native_acceptance.py --binary /opt/homebrew/bin/opencode` on OpenCode v2.0.24 | PASS: 27 Skills and 3 Commands discovered; MCP connected; plugin setup, native CLI model execution through a loopback mock, Context delivery, permission hook and native ALLOW/DENY decisions verified. `generation_executed` was false. Global instruction model delivery remains UNVERIFIED; governance remains ADVISORY. |
| Other hosts | Local runtime inventory and `tests/scenarios/235-opencode-native-context-guard.md` | No native acceptance was collected for Codex, Claude Code or Gemini CLI. Claude Code and Gemini CLI binaries were unavailable; the Codex CLI is installed, but its host acceptance was not run. Static adapter configuration and fixture simulations are not host execution evidence. |
| Project Intelligence | `tests/evidence/project_diagnostics_lifecycle.py`; read-only `aips project diagnose` and Intelligence status | Lifecycle PASS for missing, partial, stale and blocked recovery guidance, privacy and no-write behavior. This project reported technical READY/CURRENT; human review status remains separate. |
| Doctor consistency | `tests/evidence/harness_runtime_lifecycle.py`; read-only `aips doctor` and `aips project diagnose` | Lifecycle PASS when run with the prepared Python 3.12 environment. The live diagnostic reported NEEDS_ATTENTION because Doctor found this local checkout has no installed AIPS venv and the user's global OpenCode projections are stale; Doctor's non-zero result and Project Diagnostics' warning agree. No repair was applied to user configuration. |

## Local validation

- `project_diagnostics_lifecycle.py`: PASS.
- `release_channel_lifecycle.py`: PASS.
- `harness_runtime_lifecycle.py`: PASS with the prepared Python 3.12 environment on `PATH`.
- Release readiness fixtures: READY fixture passed; blocked fixture returned the expected `not_ready` result.
- Phase 0 exact-candidate Core Integration Gate: PASS for `fb0d63789e696e08cb65296b7e254b58c2d7171d` against `a657b544b2431e55f7deec350e875a9c94ad293a`; strict candidate secret scan passed. The report is kept outside the repository at `/private/tmp/plan25-phase0-gate-report.yaml`.

## Decision

Existing owners and recovery paths already provide the intended behavior. This phase adds no parallel release, Runtime, Project Intelligence or Doctor implementation. The verified local OpenCode result closes the available-host acceptance point for v2.0.24 only. Other host versions, production-provider behavior, real creative generation, and a published stable artifact remain unverified or explicitly out of scope.
