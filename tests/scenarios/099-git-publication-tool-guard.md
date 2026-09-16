# Scenario 099 — Git Publication Tool Guard

Expected:
- ordinary shell commands pass without approval lookup;
- git push/tag and gh pr/release create require active APPROVED binding;
- operation/candidate/branch/file mismatch blocks;
- the guard never creates Human approval.
