# Dev Friction PR5 System Improvement Review

## Recommendation

**Appropriateness: appropriate, with a documented race window.** A timed-out AIPS ComfyUI job kept occupying the local queue and required manual clearing; after a restart a job could still appear as running with no record of ownership. The fix records AIPS-submitted prompt_ids in a private ledger and interrupts only ledger-owned jobs that the live queue reports as running.

**Verified contract:** the locally installed ComfyUI 0.42.5 `/interrupt` honors a targeted `prompt_id` and skips the interrupt otherwise; `GET /queue` exposes running and pending ids; `POST /queue` deletes by id. The verification was by reading `server.py` and `execution.py`, not by a live run. No real ComfyUI job was started or interrupted.

**Lower-layer alternative:** reusing the existing trace directory and allowlisted request helper instead of a new service or runtime. The ledger is a bounded JSON file, not a database.

**Residual limitations:**
- Check-then-interrupt race: ComfyUI provides no compare-and-interrupt. A job can finish between the queue read and the interrupt, and the server's own running-id check is not atomic with the flag set. The residual window is documented and reported through the per-id re-check (`STILL_RUNNING` / `CLEARED` / `NOT_PRESENT`).
- Older ComfyUI builds that ignore the `prompt_id` body would perform a global interrupt. AIPS cannot detect this from the response. Only ComfyUI versions with the targeted handler should be relied on; the 0.42.5 source is the reviewed reference.
- Ownership is per endpoint binding and per local user state; a ledger deleted by the user loses ownership knowledge, and such jobs are then left for manual inspection (no interrupt).

**Security and reliability:** loopback-only, no egress, node trust policy untouched, no downloads, no model switching, no automatic resubmission, no global interrupt. Diagnostics are privacy-bounded.

**Compatibility:** successful runs are unchanged apart from a ledger write and release. Existing fixtures were updated for the queue read; the real user state directory was not written by tests (state directory isolated in the affected lifecycle tests).

**Documentation impact:** `orchestration/CREATIVE_DIRECTION.md`, `orchestration/CORE_CHANGE_TESTING.md`, `docs/human/CONFORMANCE.md`, `docs/human/USER_GUIDE.md`, `tests/scenarios/236-local-creative-execution.md`. The `aips creative recover` command is in the CLI help. Repository-wide documentation placement and sync closure is left to the integration branch.

**Architecture diagrams:** no dataflow change beyond the local recovery path; no trust-boundary change.

**Constitution impact: NO.**

**Deferred:** restart-time automatic recovery (only the explicit command ships), calibrated timeouts, and any check for the global-interrupt behavior of older ComfyUI builds.
