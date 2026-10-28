# Plan44 Git Publish Proposal

## Target

- Remote: `origin` (`https://github.com/LucasLu3918/ai-product-system.git`)
- Branch: `codex/plan44-publication-recovery`
- Pull request: one Core Change PR targeting `main`; merge after exact candidate validation, mergeability, and the required `repository` check pass.
- Authorized actions: publish this approved candidate, create its PR, and merge that exact PR into `main` after all required gates pass.
- Excluded actions: direct protected-branch push, release/tag, policy change, unrelated PR merge, forced update, or branch deletion.

## Candidate and Scope

Base SHA and candidate SHA will be recorded after the final commit. The final file set and changed-files digest must match the active Core Change Matrix and this approved scope. No unrelated worktree content is included.

## Required Evidence

- Focused publication and Claude runtime contracts.
- Documentation-impact closure and Core Change Matrix validation.
- Credential-free secret scan of the exact final tree and base-to-head history.
- Complete local Integration Gate and exact remote required check `repository`.
- Live default-base, PR head, mergeability and check revalidation immediately before merge.

## Merge Method

Use a GitHub-supported merge method only after observing the exact PR and required checks. The repository currently disallows squash merge; select an enabled method from live repository metadata and pin the PR head SHA. Do not use admin bypass or delete the source branch as part of merge.

## Status

Proposal prepared for the approved task. Candidate-specific evidence and PR URL are pending final validation/publication.
