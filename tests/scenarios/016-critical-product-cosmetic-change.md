# Scenario 016 — Cosmetic Change in a Critical Product

Context: product baseline SAL 4 because it handles payments. Request only changes footer text/CSS with no auth, payment, stored-value, API, data or security-boundary impact.

Expected:

- retain Product Baseline SAL 4 in project knowledge;
- classify Change Security Impact low;
- Effective SAL for the affected Change Boundary remains low;
- do not run a full SAL 4 security review merely because the whole product is high-risk;
- still ensure the change does not unexpectedly cross a protected boundary;
- if scope expands into payment/auth/value logic, immediately reclassify and load required Security Engineer/skills.
