# Scenario 099 — Git Publication Tool Guard

Expected:
- ordinary shell commands pass without approval lookup;
- git push/tag and gh pr/release create require active APPROVED binding;
- common direct executable/path/global-option/shell-wrapper forms resolve to the same protected operation;
- a compound command containing multiple protected publication operations requires every detected operation to be approved;
- operation/candidate/branch/file mismatch blocks;
- read-only commands with a dynamic directory/repository option, a dynamic path prefix to a literal non-Git executable, a `gh api` GET request, a `git lfs` local subcommand or a repository-defined read-only Git alias pass without approval lookup;
- dynamic executables named git/gh/shell, dynamic `-c`/`--config-env`/`--exec-path` values, dynamic context on a publication verb, API writes, publishing LFS subcommands and aliases that expand to commit or publication fail closed with stable reason codes;
- every command-classification denial reports the same reason code in the denial text and its diagnostic;
- the guard never creates Human approval.
