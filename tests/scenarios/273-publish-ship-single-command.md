# Scenario 273: Publish Ship Single Command

## Given

- A personal-mode engineering branch has a clean candidate commit on an allowlisted branch, and the remote default branch is an ancestor of it.
- The remote branch is absent or points at an earlier commit; no PR exists for the candidate.
- Remote and PR observations come from a local bare remote and mocked GitHub responses; no live GitHub call is made.

## When

- The agent runs `aips publish ship --title <title> --body-file <file> --base <default-branch>` as one Bash command.
- The same command is run with extra options, a dynamic value, a second protected command in the same Bash call, or in high-assurance mode.
- The candidate changes, the remote tip moves, or the push or PR create child fails between steps.
- A Prepare run precedes a standalone `gh pr merge` for the same PR head.

## Then

- The Hook classifies the invocation as one protected operation `publish_ship`, validates the exact candidate, the push scope and the remote tip, and records a single scan for the candidate.
- The chain performs one scan, then `git push origin <full-candidate-sha>:refs/heads/<branch>`, then `gh pr create --repo --head --base`; a failed step stops the chain with a bilingual recovery message that names the single supported command.
- A rerun after a failed PR create skips the completed push and creates only the PR; a candidate that already has an open PR reports it without creating another.
- Forged evidence for another candidate, a changed candidate, a moved remote tip or a changed body never reach a child command.
- Extra options, dynamic values, a chained `git push`, or high-assurance mode are denied with the supported form in `next_step` and `next_step_zh`.
- `aips publish prepare` stores merge-bound evidence for the PR head; the Hook accepts the standalone merge only with that evidence, and still requires human confirmation.

## Evidence

- `tests/test_publication_ship.py`
- `tests/test_publication_planning.py`
- `tests/evidence/governance_command_guard.py`
- `scripts/publication_ship.py`
- `scripts/governance_guard.py`
- `scripts/publication_planning.py`
