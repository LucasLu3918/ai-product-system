# Creative task authorization and multi-item execution

Given an explicitly admitted Creative prompt for a local EPHEMERAL project, when the native OpenCode tool requests mutation, then it uses the current prompt-admission grant and never derives authority from a truncated transcript.

Given a generation grant, when review assistance is requested without explicit current-user visual review intent, then the action is denied; a separate explicit review request may inspect only a bounded image through an installed local model and cannot complete Human review or user acceptance.

Given a job manifest containing multiple configured local Bundles, when one preflight or generation fails, then later items continue and the results identify each outcome without storing raw prompts.

Given a partially completed job is rerun, when prior output and manifest hashes still match, then completed items are skipped and failed items are retried without overwriting outputs.

Given local MFLUX commands are installed, when aips creative discover runs, then it performs bounded version-only probes and never starts image generation or model download.

Given the original Chinese request asks for two characters and the assistant requests role/style/output choices, when the user replies `哈利＋妙麗 A佈局＋B質感 獨立立繪`, then the current response receives a fresh grant limited to the active Session, original two-output cap and selected creative actions; the implementation does not reuse a prior prompt grant or raw transcript as authority.

Given a pending creative clarification, when the user cancels, switches to software work, changes Session root, requests more characters or exceeds the output count, then continuation is revoked or denied and no extra output is authorized.

Given local engine probing returns a timeout, nonzero version command, unrecognized version or missing executable, when diagnostics are reported, then command availability, process health and version parsing remain distinct; no diagnostic claims model inference or visual quality.

Evidence: scripts/creative_request_policy.py, scripts/creative_execution.py, harness/adapters/opencode/plugin.ts, tests/evidence/creative_request_policy_lifecycle.py, tests/evidence/creative_generate_set_lifecycle.py, tests/evidence/opencode_native_acceptance.py.

Given the output cap is exhausted, when the current native user asks `請按疤痕在額頭皮膚、不在頭髮上，重出一張哈利`, then derive a new single-output repair grant in the same Session; no raw transcript restores authority. Analysis, negation and feedback alone cannot grant generation.

Given explicit generation plus automatic correction, when a quality loop runs, then reserve one delivery and at most two repair attempts before inference, enforce the shared time ceiling, inspect every criterion and applicable expression at composition/detail scale, preserve machine/Human/user decisions, and stop on uncertainty, repeated defects or exhausted budget.

Given a user reports misplaced identity details, when feedback and repair are requested, then record version-bound defects, copy Profiles and Bundle, reverify source hashes, choose only installed edit capability of the selected model, and compare the exact parent/revision. Existing files stay intact. Duplicate native messages and concurrent tool calls cannot recharge or overspend the grant.

Repair evidence: tests/evidence/creative_repair_lifecycle.py and tests/evidence/creative_tool_harness.mjs. Synthetic evidence does not establish real local vision accuracy or native host acceptance.

The creative repair contract extends the existing executor: current explicit reconstruction intent, per-criterion local advisory checks, copied Profile/Bundle versions, hash-bound comparison and opt-in bounded repairs. Machine findings grant neither execution nor Human/user acceptance; no model download, cloud fallback or overwrite is introduced.
