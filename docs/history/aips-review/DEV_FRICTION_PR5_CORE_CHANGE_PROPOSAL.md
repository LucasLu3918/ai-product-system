# Core Change Proposal: Dev Friction PR5 — Interrupt Only AIPS-Owned ComfyUI Jobs on Timeout

## Approved outcome

After an accepted ComfyUI job times out or polling fails, AIPS may interrupt the job only when AIPS itself submitted it and ComfyUI reports it as running. AIPS records each accepted `prompt_id` in a private local ledger so ownership survives a process restart. An explicit `aips creative recover` command applies the same rule to owned jobs whose own timeout has elapsed. No automatic resubmission. Default ON (decision D11 of the approved dev-friction plan); no trust-boundary change.

Core Change Approval: the human user approved the full dev-friction plan scope including D11 ("after ownership is confirmed, automatically interrupt"). This record applies that approval to exactly the PR5 scope below.

## Scope

- `scripts/creative_execution.py`
  - Loopback allowlist: `GET /queue` (read-only, no query) and `POST /interrupt` (no query) are added. `POST /prompt` and `POST /queue` keep their existing behavior. No other path or method is opened.
  - Private owned-job ledger (`comfy-jobs.json`, see Ledger below), written under the existing AIPS state directory (`trace_path().parent`, 0700 directory, 0600 files, lock file alongside).
  - `reconcile_owned_comfy_jobs`: reads `/queue`; deletes owned queued jobs by exact id; sends `POST /interrupt {"prompt_id": id}` only for owned ids reported in `queue_running`; re-checks the queue (up to 10 times, 0.5 s apart) and reports a per-job state.
  - `comfy_execute`: records the owned prompt_id right after an accepted `/prompt`; releases it on completion or on a ComfyUI execution error; on timeout or polling failure it reconciles and raises `comfy_job_recovery_required` with privacy-bounded diagnostics.
  - `recover_comfy_jobs` and CLI `aips creative recover [--base-url]`.
- `scripts/creative_errors.py`: Traditional Chinese recovery text for `comfy_job_recovery_required`; allowlist for the bounded diagnostic keys `job_state`, `ownership`, `interrupt_requested`, `queued_delete_requested`, `other_jobs_running`, `automatic_resubmission`.
- `scripts/aips_cli/dispatch.sh`, `scripts/aips_cli/help.sh`: route and document `creative recover`.
- Tests: `tests/evidence/creative_execution_lifecycle.py` (stateful synthetic loopback queue fixture), `tests/evidence/plan27_lifecycle.py` and `tests/evidence/comfyui_dynamic_workflow_lifecycle.py` (existing timeout fixtures updated for the queue read; state directory isolated).
- Docs: `orchestration/CREATIVE_DIRECTION.md`, `orchestration/CORE_CHANGE_TESTING.md`, `docs/human/CONFORMANCE.md`, `docs/human/USER_GUIDE.md`, `tests/scenarios/236-local-creative-execution.md`.

## Verification of ComfyUI targeted interrupt

Verified from the locally installed ComfyUI source (version 0.42.5, `ComfyUI/server.py` and `execution.py`), not from memory:

- `POST /interrupt` accepts a JSON body `prompt_id`. If present, the server scans `prompt_queue.get_current_queue()` running items and calls `nodes.interrupt_processing()` only when an item's id matches. Otherwise it logs "skipping interrupt" and returns 200. Without `prompt_id` it performs a global interrupt, which AIPS never sends.
- `GET /queue` returns `queue_running` and `queue_pending`; each item's index 1 is the prompt_id. Items are trimmed to five fields, so the private workflow and extra data are not returned.
- `POST /queue` with `{"delete": [...]}` removes pending items by exact id.
- The interrupt flag is reset by `execution.py` (`interrupt_processing(False)`) before the next prompt.

## Race window (documented, not closed)

AIPS checks ownership with `GET /queue`, then sends `POST /interrupt`. Between the two calls the owned job may finish and a different job may start. ComfyUI re-checks the running id inside `/interrupt`, so a foreign job is only interrupted if it is the owned id at that moment. However, the server-side check and `interrupt_processing()` are separate steps, so a very small window remains in which the owned job could finish just before the flag is set. Consequences: the worst case is an interrupt that finds no running owned job or stops a job that has just started, which is not AIPS-owned — ComfyUI does not expose a compare-and-interrupt primitive. Mitigation: the re-check after interrupt reports `STILL_RUNNING`, `CLEARED` or `NOT_PRESENT` per id; `NOT_PRESENT` and `CLEARED` are the only states that release the ledger entry. The residual window is reported as a limitation in the final report. Older ComfyUI servers that ignore the body perform a global interrupt; AIPS cannot detect that from the response. The executor therefore interrupts only after `GET /queue` confirms the owned id is running, and this limitation is recorded in the system improvement review.

## Ledger

- Path: `$XDG_STATE_HOME/aips/creative-execution/comfy-jobs.json` (default `~/.local/state/aips/creative-execution/`), lock file `comfy-jobs.lock`, directory 0700, files 0600, atomic replace.
- Schema (version 1): `{"version": 1, "jobs": [{"prompt_id", "submitted_at", "profile_id", "timeout_seconds", "binding_sha256"}]}`. At most 64 entries and 64 KiB. Invalid or extra fields are discarded.
- No prompt text, workflow, path, client id, endpoint or raw response is stored. `binding_sha256` is a SHA-256 over the endpoint host:port, prompt_id, submission time, profile id and timeout. Entries whose binding does not verify for the current endpoint are never treated as owned, which blocks tampered or cross-endpoint entries.
- A ledger write failure never blocks or alters the Hook decision for the current run; the job still gets the owned-job recovery path within the process.

## Why the security floor is not weakened

- Loopback only; redirects, proxies and non-allowlisted paths remain refused. `/interrupt` and `GET /queue` are the only additions and both reject queries.
- Never interrupts a job not recorded as owned and reported running; never interrupts when the queue cannot be read; a global interrupt is never sent.
- Owned queued jobs are deleted by exact id, as before.
- No automatic resubmission; `automatic_resubmission` is always `false` in every result.
- Node trust policy, workflow validation, model profile selection and no-download rules are untouched. The agent cannot select a different model.
- Diagnostics pass the existing allowlist: bounded enums and counts only; prompt text, paths and provider bodies are never emitted.

## Defaults and compatibility

- Behavior change only on timeout, polling failure or an explicit `recover`. Successful runs record and release the ledger entry. Existing timeout tests were updated because the cleanup path now reads `/queue` before deleting.
- The Bundle `timeout_seconds` (or profile/default timeout) is recorded so recovery of an owned job waits for its own deadline, not for an unrelated caller's deadline.

## Out of scope

Automatic resubmission, global interrupt, interrupt of non-AIPS jobs, restart-time automatic recovery (only the explicit command), calibration of timeouts, edit models (D13), and any change to ComfyUI itself.

## Human approval

- Core Change Approval: the human user approved the full dev-friction plan scope including D11; this record applies it to exactly the PR5 scope above.
- Publication: not requested; no push, PR or merge.
