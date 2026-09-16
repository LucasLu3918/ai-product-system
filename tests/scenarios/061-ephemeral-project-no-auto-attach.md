# Scenario 061 — Ephemeral Project Does Not Auto-Attach

A project has no .ai/ workspace.

Expected:
- harness resolve reports EPHEMERAL;
- preflight does not create .ai/;
- AIPS may still guide project work and read project instructions;
- persistence requires explicit aips attach.
