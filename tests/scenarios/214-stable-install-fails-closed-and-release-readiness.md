# Scenario 214: Stable install fails closed and release readiness

Given a repository without a stable release tag, when the installer or updater uses the stable channel, then it stops without switching to mutable `main`; an explicit `--channel main` remains available for development. Given a verified `vX.Y.Z` tag, stable installation checks the exact remote commit and embedded `VERSION` before checking out the tag detached. A clean main-channel update fast-forwards to the exact remote main commit; a divergent update is rejected while preserving the installed commit and version, with no automatic rollback, merge or rebase. A manual release-readiness run on `main` records the exact candidate/version assessment with read-only permissions and never writes a tag or release.

Evidence: `tests/evidence/release_channel_lifecycle.py`, `tests/evidence/install_preflight_lifecycle.py`, `tests/evidence/version_policy_lifecycle.py`, and `.github/workflows/release-readiness.yml`.
