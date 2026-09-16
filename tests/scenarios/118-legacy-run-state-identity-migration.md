# Scenario 118 — Legacy External Run State Migrates Safely

An EPHEMERAL v0.14 run exists under the old absolute-path-hash project namespace.

Expected:
- the run remains readable;
- first access migrates that run into the canonical workspace namespace when no conflict exists;
- matching clean legacy checkpoints remain resumable;
- migration does not create project-local `.ai/` state.
