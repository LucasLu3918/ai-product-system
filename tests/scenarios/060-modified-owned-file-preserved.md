# Scenario 060 — Modified AIPS-owned File Is Preserved

After AIPS created a runtime bootstrap, the file was manually modified.

Expected:
- uninstall detects that it no longer matches the installed AIPS copy;
- uninstall preserves the live file and warns;
- it does not delete possible user content merely because the file was originally AIPS-created.
