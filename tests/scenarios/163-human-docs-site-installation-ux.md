# Scenario 163 — Human Documentation Site & Canonical Placement

Expected:
- docs/human is the single canonical Human source and VitePress renders it without duplicating content;
- current-behavior docs have one H1 and no release/scenario-style H2 append stream;
- subsystem changes map to allowed canonical topic sections through deterministic placement config;
- legacy standalone Technology/Evolution HTML cannot receive new appended sections;
- README and Getting Started no longer teach mkdir/cd/git clone/bootstrap as public install flow;
- macOS/Linux use one public installer that manages the AIPS checkout;
- Windows documentation truthfully uses a PowerShell launcher into WSL and does not claim native Windows runtime;
- bootstrap.sh remains backward-compatible only;
- pull requests build the docs site; only main can deploy the Pages artifact;
- an unconfigured repository Pages setting is reported as SKIPPED_NOT_CONFIGURED rather than a false docs build failure, and no one-time placement bypass remains after the migration;
- no new Role, Skill, Approval Gate, model/provider credential or product production authority is introduced.
