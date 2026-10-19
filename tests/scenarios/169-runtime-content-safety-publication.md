# Scenario 169 — Runtime and Publication Content Safety

Commit, push, PR and release content paths, including `--body-file` and `git commit -F`, are scanned before publication and durable content fails closed.

The commit guard also inspects quoted-delimiter heredoc messages, literal `git add` commands joined by `&&` before the commit, `-a`/`-am` and `--amend`: content the commit would include is scanned from the worktree when it is not yet staged. A heredoc that would end early, follow a comment or use an unquoted delimiter is never treated as literal. Secret, PII and ambiguous injection (`REVIEW`) findings still block at commit, because publication-time candidate scanning covers secrets only.
