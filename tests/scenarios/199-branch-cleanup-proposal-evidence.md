# Scenario 199 — Branch cleanup proposal evidence

## Intent

Produce deterministic, reviewable cleanup proposals while keeping routine reports read-only and deletion explicitly Human-authorized.

## Expected behavior

- classify supported short-lived branch prefixes and preserve unclassified branches;
- report branch SHA, PR merge status, age, target integration and recommendation;
- treat missing, open, closed-unmerged and moved-head PR evidence distinctly;
- keep report authority false and never delete during report generation;
- permit cleanup only through explicit protected-main workflow dispatch and exact one-time manifest;
- preflight every manifest entry before the first delete.

## Evidence

`tests/evidence/branch_hygiene_lifecycle.py` checks all supported prefix families, deterministic report fields, PR evidence and temporary-repository cleanup behavior.
