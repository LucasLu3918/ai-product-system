# Scenario 262: ComfyUI Resource Authorization and Diagnostics

Given a Resource Authorization profile is absent, missing, unreadable, malformed, or schema-invalid, when Runtime Policy evaluates an action, then it returns a distinct stable reason and a safe Traditional Chinese recovery action; every case remains blocked.

Given a grant with a specific resource kind, selector, operation, destination and constraints, when any observed field does not match (including network, port, HTTP method, path or redirect), then the action is denied before policy ALLOW and the result retains `status`, `phase`, `reason_code`, `source`, `retryable`, `trace_id` and `recovery.action`.

Given a native Hook includes model-supplied Runtime Action metadata, when the action does not bind to the actual tool and directly observed URL, then the adapter rebuilds or denies it from the host event; the Resource Authorization profile path comes only from the trusted process environment.

Given `aips creative discover` runs, when the fixed ComfyUI service is available, then it performs only bounded GET requests to fixed allowlisted loopback paths and reports capped model filenames without submitting a generation job. An unknown port, method, path, external address, redirect, oversized response, 4xx, 5xx, malformed response, or missing model remains unavailable or incomplete with safe diagnostics and no raw body.

Given a Creative Bundle selects one registered character, background, texture or UI ornament preset, when prompt compilation occurs, then only that static guidance is added and its registry hash is recorded in provenance. It does not select a provider, authorize generation, or bypass workflow validation.

Given Apple Silicon or model precision metadata is observed, when preflight reports MPS compatibility, then the result identifies static evidence and `INFERENCE_UNVERIFIED`; only an actually observed local inference can establish backend compatibility.

Evidence: `tests/test_runtime_policy.py`, `tests/evidence/resource_authorization_lifecycle.py`, `tests/evidence/runtime_policy_lifecycle.py`, `tests/evidence/creative_execution_lifecycle.py`, and `tests/validation/creative_execution_contracts.py`.
