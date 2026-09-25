# Runtime Policy Enforcement

## Purpose

Runtime Policy Enforcement provides deterministic, provider-neutral decisions for supported tool actions at the pre-execution boundary. It extends Resource Authorization and existing native hooks; it does not grant Human, publication, merge or release authority.

## Flow and authority

~~~text
Runtime hook payload
→ trusted adapter normalization to Runtime Action Envelope
→ Resource Authorization profile (default DENY)
→ deterministic runtime policy (deny-overrides)
→ optional semantic signal may DENY / ESCALATE only
→ exact scoped Approval Record when required
→ verified sandbox egress when policy requires it
→ native PEP allows the exact evaluated action or blocks
~~~

The policy evaluator is the Policy Decision Point. Claude `PreToolUse` and Gemini CLI `BeforeTool` are Policy Enforcement Points only for the operations their verified native hooks can actually block. Codex remains `ADVISORY`; generic runtimes remain `UNSUPPORTED` until a concrete verified PEP exists.

## Runtime Action Envelope

`orchestration/schemas/runtime-action.yaml` defines version 1. The action binds actor/task/runtime, tool/operation/arguments, resource, destination/trust, effective SAL, Change Boundary, data classes, protected assets, Resource Authorization profile, credential reference and required enforcement. SAL is not data classification. The action digest includes the normalized arguments, destination, risk/data labels, boundary and the Resource Authorization profile fingerprint; it excludes the approval ID.

Only a trusted host adapter may supply a top-level `aips_runtime_action`. User/model-controlled `tool_input` fields are not accepted as authority metadata. The current hooks conservatively identify direct `curl`/`wget` URLs and block them when policy context is missing. Indirect scripts, child processes, SDK calls and hidden sockets require sandbox/network enforcement.

## Policy and decisions

`config/runtime-policy.yaml` defaults to `DENY`. External destinations must be explicitly allowlisted. Built-in SAL3/4 and confidential/restricted external actions require exact approval, `TOOL_GUARDED`, and a current verified sandbox egress receipt. The checked-in sandbox registry currently has no verified allowlist egress provider, so those actions resolve to `BLOCKED` even when a hook can intercept them. This is the truthful current capability.

Decisions:

- `ALLOW` — explicit policy and Resource Authorization allow the action, and every required capability is verified.
- `DENY` — a hard policy or resource rule forbids the action. Deny overrides all allows.
- `REQUIRE_APPROVAL` — an otherwise eligible action needs a current exact scope-bound human Approval Record.
- `BLOCKED` — required evidence, policy, SAL, enforcement, sandbox or valid configuration is unavailable or stale.

The active Approval Record must bind operation `external_data_egress`, action digest, policy digest, exact destination, data classes, protected assets and Change Boundary. It must be APPROVED and unexpired. A missing record yields `REQUIRE_APPROVAL`; a present stale/invalid record yields `BLOCKED`.

## Audit and semantic providers

When `AIPS_GOVERNANCE_AUDIT_LEDGER` is configured, the hook appends a sanitized event through the existing Governance Audit implementation. Events include only action/policy digests, decision, destination hostname and rule IDs; raw arguments and secrets are omitted. An audit append failure blocks an otherwise allowed action. The hook observes pre-execution authorization; it does not claim that a tool actually completed.

`scripts/semantic_guard.py` validates the optional provider signal contract and binds it to the action digest. Only `ALLOW`, `DENY` and `ESCALATE` are accepted. Semantic `DENY` or `ESCALATE` can tighten an otherwise allowed deterministic decision; a semantic signal cannot override deterministic `DENY` or independently grant access. No external model call or mandatory provider dependency is part of the enforcement path.

NeMo Guardrails remains a possible optional trial adapter. Its current experimental IORails tool-call validation supports OpenAI Chat Completions engines `openai` and `nim`, not Anthropic, Gemini or OpenAI Responses; it also validates tool traffic rather than executing tools. It is therefore not the AIPS authorization engine or cross-runtime PEP.

## CLI

~~~bash
aips runtime-policy evaluate --action ACTION.yaml \
  --policy config/runtime-policy.yaml \
  --runtime-capability TOOL_GUARDED \
  --project-root /path/to/project
~~~

An `ALLOW` from the standalone evaluator is a decision result. It is not proof a runtime actually enforces it; only a verified native hook or sandbox can provide that evidence.
