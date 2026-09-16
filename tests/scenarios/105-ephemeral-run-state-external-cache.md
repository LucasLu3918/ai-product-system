# Scenario 105 — EPHEMERAL Run State Uses External Cache

Expected:
- checkpoint/event/resume work without attaching the project;
- no .ai directory is created;
- run artifacts live under the external AIPS project cache;
- attaching later does not require duplicate canonical run state.
