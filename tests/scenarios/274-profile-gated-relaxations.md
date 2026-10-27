# Scenario 274 — Profile-Gated Relaxations (Claude Co-Author Trailer, Post-Merge Refresh)

## Given

- A temporary AIPS config home and temporary stores; the real `~/.config/aips` is never read or written.
- The PR10 switch allow-list with two entries, `claude_coauthor_trailer` and `post_merge_refresh`, both defaulting to off.
- The publication identity policy in `config/git-publication.yaml` with a `profile_trailer_identities` entry for the Claude co-author trailer.

## When

- The commit-message PII scan runs over a message whose final trailer block holds the exact Claude co-author trailer, with the switch off and on.
- The trailer uses another domain, another name, another key, extra characters or a second address, or an address appears in the message body or outside the final trailer block.
- The Turn Context hook sees READY but STALE Intelligence whose task-relevant topics are affected, with `post_merge_refresh` off and on, repeatedly and for a new HEAD.

## Then

- With the switch off, behaviour is identical to before: the trailer is blocked by `pii.email.v2` and the hook starts nothing.
- With `claude_coauthor_trailer` on, only a final-block line `Co-Authored-By: Claude <words, digits, dots> <the Anthropic noreply address>` is masked for the scan. Any other address, a body address, a different key or name, a second address on the line and every secret finding still block.
- A malformed `profile_trailer_identities` entry fails closed as an invalid identity policy.
- With `post_merge_refresh` on, the hook starts one detached `aips intelligence refresh` per store per HEAD, guarded by an exclusive lock file inside the store, and never waits for it or fails the turn. READY-only or non-affected cases start nothing.
- Turn Context lists enabled switches in the existing `aips_profile_non_default=` line.

## Evidence

- `scripts/aips_profile.py`
- `scripts/publish_preflight.py`
- `config/git-publication.yaml`
- `scripts/turn_context_hook.py`
- `tests/test_pr11_profile_relaxations.py`
- `tests/test_profile_switch.py`

## Limits

- Switches are enabled only by a person through `aips profile set`; the PR3 guard denies the agent's Bash form and file writes.
- The background step runs the existing `aips intelligence refresh`, which refreshes revision metadata only when the committed tree equals the verified tree and the worktree is clean; otherwise it reports that a semantic refresh is required. It does not enrich topics and cannot target individual topics.
- Importing a user-supplied ComfyUI workflow with an unaudited topology (D5) is not part of this scenario: the existing opt-in `dynamic_local` mode already admits core nodes only, so no new switch is added here.
- The commit-time Claude Code guard already masks co-author trailers for its own scan; this scenario covers the publication gate scan.
