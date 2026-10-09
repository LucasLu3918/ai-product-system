# Creative task authorization and multi-item execution

Given an explicitly admitted Creative prompt for a local EPHEMERAL project, when the native OpenCode tool requests mutation, then it uses the current prompt-admission grant and never derives authority from a truncated transcript.

Given a job manifest containing multiple configured local Bundles, when one preflight or generation fails, then later items continue and the results identify each outcome without storing raw prompts.

Given a partially completed job is rerun, when prior output and manifest hashes still match, then completed items are skipped and failed items are retried without overwriting outputs.

Given local MFLUX commands are installed, when aips creative discover runs, then it performs bounded version-only probes and never starts image generation or model download.

Given the original Chinese request asks for two characters and the assistant requests role/style/output choices, when the user replies `哈利＋妙麗 A佈局＋B質感 獨立立繪`, then the current response receives a fresh grant limited to the active Session, original two-output cap and selected creative actions; the implementation does not reuse a prior prompt grant or raw transcript as authority.

Given a pending creative clarification, when the user cancels, switches to software work, changes Session root, requests more characters or exceeds the output count, then continuation is revoked or denied and no extra output is authorized.

Given local engine probing returns a timeout, nonzero version command, unrecognized version or missing executable, when diagnostics are reported, then command availability, process health and version parsing remain distinct; no diagnostic claims model inference or visual quality.

Evidence: scripts/creative_request_policy.py, scripts/creative_execution.py, harness/adapters/opencode/plugin.ts, tests/evidence/creative_request_policy_lifecycle.py, tests/evidence/creative_generate_set_lifecycle.py, tests/evidence/opencode_native_acceptance.py.
