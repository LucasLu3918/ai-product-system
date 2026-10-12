# AIPS Global Turn Harness

For software/product/project work, use the AIPS Turn Context supplied by the UserPromptSubmit hook when available.

If hook context is unavailable, resolve before analysis/mutation:

`aips intelligence context --runtime claude-code --project "$PWD" --prompt "<current user request>"`

Preserve existing Claude/project memory. Existing-project mutations require Intelligence initialization/targeted refresh plus Change Impact before editing.

For publication blocks, use the read-only `aips publish doctor` and `aips publish diagnose --worktree <root> --command '<literal command>'`. Report the stable reason code, phase, safe next step and Required Checks state (unconfigured, fail, pending, missing, cancelled or unavailable); never expose raw GitHub output or infer success from missing evidence. Diagnostics do not execute merge, consume grants or change repository policy. Retry safe read-only observations only; policy/admin changes and merges remain under native Human Authority and host confirmation.
