# Scenario 099 — Git Publication Tool Guard

Expected:
- ordinary shell commands pass without approval lookup;
- git push/tag and gh pr/release create require active APPROVED binding;
- common direct executable/path/global-option/shell-wrapper forms resolve to the same protected operation;
- a compound command containing multiple protected publication operations requires every detected operation to be approved;
- operation/candidate/branch/file mismatch blocks;
- the guard never creates Human approval.
