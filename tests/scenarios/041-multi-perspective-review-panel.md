# Scenario 041 — Multi-Perspective Review Panel

Context: a large backend change affects public API, authorization and database transaction behavior.

Expected:
- trigger review from semantic impact/risk, not LOC alone;
- select only useful perspectives such as Quality Reviewer, Software Architect, Security Engineer and Database Engineer;
- give each reviewer bounded files/contracts/tests and read-only permissions;
- do not ask every reviewer to review the entire repository;
- normalize/deduplicate findings before returning them to the Author.
