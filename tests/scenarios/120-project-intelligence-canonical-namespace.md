# Scenario 120 — Project Intelligence Uses Canonical Workspace Namespace

An existing project bootstraps Project Intelligence in EPHEMERAL mode.

Expected:
- external Intelligence is stored under the canonical `workspace_id`;
- authoritative source and freshness behavior remain unchanged;
- legacy Project Intelligence namespace is migrated only when the canonical destination is absent;
- no project-local `.ai/` workspace is created merely for migration/bootstrap.
