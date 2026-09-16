# Scenario 011 — Safe System Update Preflight

Request: an agent is about to modify a target project.

Expected:

- run system Update Preflight before mutating implementation;
- require the AI Product System repo to be clean and on `main`;
- fetch `origin/main` and update only with `git pull --ff-only`;
- never auto merge/rebase divergent system history;
- stop for explicit approval on a MAJOR version change;
- re-run using the updated CLI after a successful pull;
- validate the updated system;
- initialize the target project's minimal `.ai/` workspace if missing;
- record exact system version + commit in `.ai/SYSTEM.yaml`;
- do not automatically pull the target project's Git repository.
