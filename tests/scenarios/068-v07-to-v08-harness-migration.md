# Scenario 068 — Legacy Installation to Managed Harness Migration

An older AIPS installation is upgraded through preflight into the current managed Harness model.

Expected:
- the old preflight updates AIPS then re-execs the new CLI;
- the new CLI detects the existing AIPS installation and safely installs/refreshes Global Harness integration;
- existing user-owned instruction content is preserved through managed composition where supported;
- an unsafe/colliding integration reports MANUAL/CONFLICT rather than overwriting user content;
- a plain repository checkout without AIPS installation does not register global adapters implicitly.
