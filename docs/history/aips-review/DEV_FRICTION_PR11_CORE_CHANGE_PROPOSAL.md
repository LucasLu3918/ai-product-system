# Core Change Proposal: Dev Friction PR11 — First Profile-Gated Relaxations

## Approved outcome

Add the first two relaxations behind the PR10 profile mechanism. Both switches default OFF and can only be enabled by a person through `aips profile set`. With no profile file, behaviour is identical to before.

Core Change Approval: the human user approved the full dev-friction plan scope including D2 and D5. This record applies that approval to exactly the PR11 scope below. The D5 item is intentionally not implemented (see Out of scope).

## Scope

- `scripts/aips_profile.py`: `SWITCHES` gains `claude_coauthor_trailer` and `post_merge_refresh`, each `default=False` with bilingual security implications. Enabled switches already appear in the Turn Context `aips_profile_non_default=` field through `turn_context_line`.
- `config/git-publication.yaml`, `scripts/publish_preflight.py` (D2): a new `identity.profile_trailer_identities` mapping keyed by switch id. `git_identity_policy` adds an entry to the masked-trailer list only when its switch is true; `mask_trailer_identities` masks that line for the PII scan. The existing Dependabot sign-off entries are unchanged.
  - Match: the final trailer block only, every line a trailer; key exactly `Co-Authored-By`; name `Claude` followed by one to four words of letters, digits and dots; address exactly the Anthropic noreply address (case-sensitive, nothing else on the line). Anything else stays unmasked and is blocked by `pii.email.v2`.
  - The `@` character is written as `\x40` in YAML patterns; tests build it at runtime.
  - A malformed entry raises the existing identity-policy error and fails closed. If the profile cannot be loaded, the switch is treated as off.
- `scripts/turn_context_hook.py`: `maybe_start_post_merge_refresh`. When `post_merge_refresh` is true, Intelligence is READY and STALE, and PR2 `task_refresh_requirement` reports `task_topics_affected`, start one detached `aips intelligence refresh --project <root>` (new session, no pipes). An exclusive lock file `.post-merge-refresh-<HEAD>.lock` inside the Intelligence store limits it to once per store per HEAD; lock files of older HEADs are removed. The hook never waits and swallows every error. One status line is appended only when a refresh started.
- Tests: `tests/test_pr11_profile_relaxations.py` (new) and `tests/test_profile_switch.py` (assertions that assumed an empty allow-list now use a patched empty allow-list).
- Scenario 274 (`tests/scenarios/274-profile-gated-relaxations.md`), `tests/scenario_coverage.yaml`, regenerated `docs/human/CONFORMANCE_CURRENT.md`, one localized sentence each in `docs/human/USER_GUIDE.md`, `docs/human/MAINTENANCE.md`, `docs/human/CONFORMANCE.md` and `orchestration/CONFORMANCE.md`.
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` is intentionally not edited; entries are reported to the integration owner.

## Why the security floor is not weakened

- Both switches are off by default and agents cannot enable them (PR3 and PR10 guard).
- D2 relaxes one exact line shape in one scanner. Secret scanning, every other PII rule, body-text addresses, other trailers and other domains stay blocked. The commit author and committer identity checks are unchanged. Publication authority, merge confirmation and Required Checks are untouched.
- `post_merge_refresh` runs the existing `aips intelligence refresh`, which writes only the Intelligence store, refuses a dirty worktree and refuses to claim currency when the committed tree changed. It does not edit project files, publish or contact the network.
- The background step runs as the same user with the same permissions as the hook; it takes no prompt or repository text as arguments.

## Compatibility

- Switches off: no behavioural change. `config/git-publication.yaml` gains an additive key that older loaders ignore. `aips --help` is unchanged.

## Out of scope

- D5 import of unaudited topology workflows: the existing opt-in `dynamic_local` ComfyUI mode (Scenario 268) already admits any topology whose every node passes `comfyui_workflow_policy`. A default-off switch would remove a shipped capability for existing bundles and tests, and adding an `UNVERIFIED` manifest field only under a switch changes nothing in practice. Left for a separate proposal that decides the intended gate.
- Semantic topic enrichment in the background and per-topic refresh targeting: `aips intelligence refresh` has no topic argument and cannot enrich topics.

## Verification

Recorded in the final report of the PR11 implementation: ruff, focused tests, `python -m pytest -q tests`, `python scripts/capability_registry.py check`, `python scripts/conformance_summary.py current --check`, `python tests/validate_repository.py`.

## Human approval

- Core Change Approval: the human user approved the full dev-friction plan scope including D2 and D5; this record applies it to the PR11 scope above (D5 not implemented).
- Publication: not requested; no push, PR or merge.
