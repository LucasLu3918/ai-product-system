# Scenario 069 — CLI Name Collision Is Non-destructive

`~/.local/bin/aips` already exists as a regular file or a symlink owned by something else.

Expected:
- AIPS install stops with a clear collision error;
- the existing file/symlink is not overwritten or deleted;
- no runtime Adapter installation is claimed complete;
- an existing symlink to this exact AIPS system may be safely reused.
