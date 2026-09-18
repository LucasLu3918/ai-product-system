# Scenario 127 — Human Documentation Namespace

Request: Human-only AIPS documentation must remain clearly separated from Agent/machine-facing contracts and must not drift back into ambiguous locations.

Expected:

- permanent Human-only documentation lives under `docs/human/`;
- `docs/ARCHITECTURE.md` may remain a shared canonical Human/Agent architecture reference;
- repository-convention files such as root `README.md`, `CHANGELOG.md`, `SECURITY.md` and the short root `USER_GUIDE.md` redirect may remain outside `docs/human/` through an explicit allowlist;
- a repository-persisted standalone Human-only artifact outside `docs/human/` must be explicitly registered and use the `HUMAN_` filename prefix;
- Human HTML pages declare `aips-audience=human` and must not live outside the Human namespace unless registered as a standalone Human artifact;
- Agent execution contracts remain in existing canonical locations such as `orchestration/`, `harness/`, `roles/` and `skills/`; do not create a duplicate `docs/agent/` source of truth;
- Human and Agent documents may link to each other, but execution authority remains canonical in Agent/governance protocols;
- legacy `docs/<human-file>` references are rejected after migration;
- documentation audience placement is deterministically validated as part of repository validation.
