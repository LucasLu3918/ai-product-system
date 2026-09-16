# Scenario 068 — v0.7 to v0.8 Harness Migration

An existing installed v0.7 system is upgraded through preflight.

Expected:
- old preflight updates AIPS then re-execs the new CLI;
- v0.8 detects the existing AIPS installation and safely installs/refreshes Global Harness;
- existing user-owned instruction files still force MANUAL rather than overwrite;
- a plain repository checkout without AIPS installation does not register global adapters implicitly.
