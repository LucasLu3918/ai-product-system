# Scenario 058 — Existing User Agent File Is Preserved by Managed Composition

Claude Code is installed and `~/.claude/CLAUDE.md` already contains user instructions.

Expected:
- existing user instructions remain unchanged outside the AIPS-delimited managed block;
- AIPS may add/update only its managed block and namespaced Claude hooks when this can be verified safely;
- verified UserPromptSubmit capability is TURN_NATIVE, with CONTEXT_ALWAYS fallback when only the managed memory block is available;
- unrelated Claude settings/hooks remain intact;
- uninstall removes only unchanged AIPS-owned managed content/hooks and restores the original user file content;
- modified AIPS-owned content is preserved and reported as conflict rather than force-removed.
