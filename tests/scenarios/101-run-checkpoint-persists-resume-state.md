# Scenario 101 — Run Checkpoint Persists Resume State

Expected:
- a material workflow step can persist a compact CHECKPOINT.yaml;
- checkpoint contains protocol/current step/status/completed steps/evidence/project revision;
- checkpoint and events persist in the external user-state store for every project;
- legacy project-local `.ai/` is never modified by checkpoint writes;
- chat transcript is not required for resume.
