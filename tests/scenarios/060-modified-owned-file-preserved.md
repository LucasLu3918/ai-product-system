# Scenario 060 — Modified AIPS-owned Integration Is Preserved

After AIPS installed a managed instruction block or namespaced runtime integration, the AIPS-owned portion is manually modified.

Expected:
- uninstall detects that the owned content no longer matches its recorded snapshot;
- uninstall preserves the live integration and reports CONFLICT/failure for safe retry;
- it does not delete possible user modifications merely because the integration was originally AIPS-owned;
- unrelated user content/settings remain untouched.
