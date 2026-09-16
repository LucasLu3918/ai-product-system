# Scenario 058 — Existing User Agent File Is Preserved

Claude Code is installed and ~/.claude/CLAUDE.md already contains user instructions.

Expected:
- AIPS does not edit, append, import into or replace the file;
- claude-code adapter status becomes MANUAL;
- installation continues for other runtimes;
- uninstall leaves the original file byte-for-byte unchanged.
