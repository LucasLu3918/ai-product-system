# Scenario 067 — Failed Adapter Uninstall Preserves Ownership

An AIPS-owned runtime registration cannot be safely removed during uninstall.

Expected:
- uninstall reports failure instead of claiming complete removal;
- Ownership state is preserved for retry;
- AIPS does not lose track of the remaining registration;
- after the runtime problem is resolved, uninstall can be retried safely.
