# Scenario 240 — Personal Publication Default and High-Assurance Opt-In

Context: an individual asks an Agent to implement and deliver a software change. No administrator publication trust-root is installed.

Expected:

- after the candidate is clean and required content/quality checks pass, the Agent defaults to pushing its own engineering branch and creating/updating a PR without a separate per-operation confirmation or external issuer, unless the user explicitly says local-only/no-publication;
- personal publication does not create an `APPROVED` record, signature, or claim of isolated Human authorization;
- an explicit local-only/no-publication instruction prevents remote delivery;
- personal-mode PR merge is available only as a standalone, explicit PR-number command with the exact candidate `--match-head-commit` SHA; the PR must be open, non-draft, mergeable, target the live remote default branch, and use the current allowlisted engineering branch;
- `feat/` is an allowlisted engineering branch prefix alongside the existing prefixes;
- before an ordinary merge, Claude Code's native `PreToolUse` permission asks the user and shows the PR, base/head SHAs, and required-check names; Gemini CLI's extension Policy Engine uses interactive `ask_user` in `default`, `autoEdit`, and `yolo` modes, paired with the AIPS hook's PR details;
- required PR checks must be reported, complete, and passing before the confirmation prompt; an empty, malformed, pending, or failing required-check result blocks merge; GitHub pins the head SHA at merge, while the base SHA is a pre-execution observation;
- `gh pr merge --auto` is accepted only with the same exact PR/head/base binding and a non-empty passing required-check observation; when the task explicitly authorizes merge, Claude Code may enable GitHub auto-merge without a second Claude prompt, while GitHub still enforces its checks and repository rules; Gemini CLI retains native `ask_user`; this path never uses `--admin` or skips GitHub policy;
- PR creation targets only the remote live default branch and an allowlisted engineering branch;
- personal pushes use only the single matching fetch/push `origin` URL; additional remotes are denied;
- the selected personal-mode trust model accepts the currently configured origin and explicitly does not claim protection if an Agent rewrites `.git/config` to another repository;
- direct default/protected-branch pushes, branch deletion, tag/release creation, admin merge, unsafe or unknown command forms, dirty candidates and blocked content remain denied;
- if the fixed administrator trust-root exists, high-assurance mode is selected; only a valid external single-use grant permits protected publication;
- an invalid or unreadable present trust-root fails closed and never falls back to personal mode;
- Claude and Gemini native controls provide the per-call confirmation described above; Codex remains `ADVISORY`, cannot guarantee interception of direct `gh pr merge`, and must not claim host enforcement. Human accepts this Codex limitation for personal mode.

Publication planning acceptance (Plan30):

- `prepare` binds explicit worktree identity, full HEAD/base, origin, remote head, PR state and body/policy digests; it returns literal cwd/argv without executing or issuing approval.
- `diagnose` exposes fixed safe failure codes for source/ref/cwd/base/content/metadata problems. Raw exception text and credentials are omitted.
- retry re-observes live evidence, reuses an OPEN PR, blocks ambiguous/CLOSED exact candidates and verifies a MERGED candidate through its integrated merge commit, including squash merges.
- changed inputs reject the old fingerprint; host-denied operations stop without alternate commands; high-assurance never falls back or consumes a grant during planning.
- real bare-Git and native hook fixtures are separate from actual Claude/Gemini Host permission and GitHub REST acceptance.
- staged index/blob inspection failures return fixed cause codes and safe remediation without echoing exception text, local paths, or staged content.
- task-scoped user authorization is evidence for the current requested delivery only; agent-authored files cannot create a general Human grant, and the existing high-assurance issuer remains authoritative.
