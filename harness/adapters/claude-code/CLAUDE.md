# AIPS Global Turn Harness

For software/product/project work, use the AIPS Turn Context supplied by the UserPromptSubmit hook when available.

If hook context is unavailable, resolve before analysis/mutation:

`aips intelligence context --runtime claude-code --project "$PWD" --prompt "<current user request>"`

Preserve existing Claude/project memory. Existing-project mutations require Intelligence initialization/targeted refresh plus Change Impact before editing.
