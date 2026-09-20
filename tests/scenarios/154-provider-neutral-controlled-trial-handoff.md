# Scenario 154 — Provider-neutral Controlled Trial Handoff

## Intent

A Human-approved Evolution TRIAL MUST remain executable as a bounded contract even when the optional OpenAI executor credential is unavailable, without allowing an external executor to self-assert PASS or gain publication authority.

## Expected behavior

- preserve the existing explicit Human TRIAL Decision, exact baseline revision, decision fingerprint, approved scope, approved paths, forbidden paths and change limits;
- resolve Trial provider deterministically from `auto / openai-codex-action / handoff`;
- prefer the existing pinned Codex executor only when explicitly selected/resolved and its credential is available;
- fall back from `auto` to a credential-free `TRIAL_HANDOFF_READY` artifact when `OPENAI_API_KEY` is unavailable;
- bind the handoff to the exact Trial fingerprint, Human Decision fingerprint and repository baseline;
- carry the same worktree-isolation requirement and repository validation command into the handoff;
- permit a Human-selected compatible Agent to consume the handoff without granting repository publication credentials;
- explicitly set `external_executor_may_claim_pass=false`;
- require AIPS deterministic scope/diff/repository validation before any Trial may become PASS/FAIL evidence;
- do not emit a BLOCKED Trial merely because the optional OpenAI credential is absent when handoff is available;
- preserve Codex execution failure/isolation failure as fail-closed BLOCKED results when that provider is actually selected;
- keep contents read + issues write workflow permissions and never grant PR, merge, release or publication authority;
- require a separate Human Adoption Decision after any eventual validated PASS Trial.

## Rationale

Provider choice is an execution detail, not a governance authority. The handoff makes the existing Trial contract portable while keeping AIPS deterministic validation and Protected Human Authority as the source of truth.
