# Runtime Policy Enforcement

Claude publication Hook remote failures fail closed without synchronous Doctor work. Safe denial context includes a manual read-only Doctor command; Prepare timeout reports stable redacted diagnostics without exception text or the command that timed out.

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

## Shell publication command inspection

The literal `git -C <path> push` form is accepted only after resolving its explicit target worktree; candidate inspection, scan evidence and operation checks all use that target.

The managed Claude publication Hook has an eight-second internal deadline. Timeout diagnostics include only a stable reason, safe phase and elapsed time; they fail closed and do not trigger a retry or synchronous Doctor request. Fresh Prepare evidence may skip the duplicate Hook scan while live command, candidate, remote and authority validation still runs.

The Claude/Gemini publication guard parses supported Bash input with the existing bounded AST parser. It recursively classifies command substitutions in arguments and in unquoted heredoc bodies without executing them. Quoted or escaped heredoc text stays literal. The parser locates Git and GitHub CLI subcommands after supported global options; dynamic executables, subcommands and Git context-option values remain denied. Unsupported syntax fails closed with a stable reason code and a short, sanitized recovery hint. This improves command classification only: protected publication still requires explicit literal arguments and the existing candidate, content-safety and approval checks.
The Claude PostToolUseFailure event reports bounded evidence after a Bash command starts; it is not a policy decision, does not replay the command and excludes raw Host error text.

The Claude/Gemini publication guard denies only command forms that could commit or publish: read-only commands with a dynamic directory or repository option, a dynamic path to a literal non-Git executable, `gh api` GET requests, local `git lfs` subcommands and repository-defined read-only Git aliases pass, while dynamic git/gh/shell executables, dynamic `-c`/`--config-env`/`--exec-path` values, API writes, publishing LFS subcommands and aliases that expand to commit or publication still fail closed (Scenario 099). Aliases are resolved only for plain `git <alias>`, because any global option can change which configuration defines them; shell aliases are classified by their body. Every command-classification denial carries the same stable reason code in its text and diagnostic.

Task write authorization is not a substitute for the Runtime Action PEP. `aips run owner` records the task's write set and truthful enforcement capability; `ADVISORY` must never be promoted to `TOOL_GUARDED` based on the presence of a lease alone.

## Runtime Action Envelope

Qwen Edit Plus reference injection is evaluated within the existing Creative execution boundary; adding per-port bindings does not grant an external network destination, new node class, or additional submission.

ComfyUI model registry data selects only already-reviewed executor topology families and validated bounded sampler values; it does not create a Runtime action, resource grant or new mutation authority. Dynamic edit reference slots are ordered and capped at eight, with local staged-byte verification before the authorized workflow submission. Audited topology templates are checked by the generic validator and create no Runtime action authority.

The commit-time font metadata scanner does not evaluate or broaden Runtime Action Envelope permissions; its ALLOW result remains separate from tool authorization.

`orchestration/schemas/runtime-action.yaml` defines version 1. The action binds actor/task/runtime, tool/operation/arguments, resource, destination/trust, effective SAL, Change Boundary, data classes, protected assets, Resource Authorization profile, credential reference and required enforcement. SAL is not data classification. The action digest includes the normalized arguments, destination, risk/data labels, boundary and the Resource Authorization profile fingerprint; it excludes the approval ID.

The current native hooks do not attest a separate trusted Runtime Action channel. They therefore rebuild direct `curl`/`wget` observations from the actual Hook tool name and command, bind the host and request metadata to that command, and read the Profile path only from the trusted `AIPS_RESOURCE_AUTHORIZATION_PROFILE` process environment. A top-level model-supplied `aips_runtime_action` cannot replace or widen observed host facts. Missing, unreadable, malformed or scope-mismatched Profiles produce distinct structured fail-closed diagnostics. Indirect scripts, child processes, SDK calls and hidden sockets require sandbox/network enforcement.

Runtime decisions expose `status`, `phase`, `reason_code`, `source`, `retryable`, `trace_id` and `recovery.action`. Destination evidence can include port, HTTP method, path and redirect status; Resource Authorization compares these to the exact grant kind, selector and constraints before policy evaluation.

## Policy and decisions

Runtime policy decisions consume the explicit action envelope and verified native enforcement capability; project mode is advisory input and cannot override global policy.

ComfyUI workflow schema and final serialized-payload validation are application-level checks rather than native tool authorization. They do not bypass Runtime Action policy or OpenCode prompt admission; only the separately requested Creative execution action can submit to the configured loopback service. Passing the fixed FLUX 3 Klein `TextGenerate` check does not establish MPS inference.

AVIF metadata findings remain in the content-safety scanner and are not Runtime Action Envelope decisions or execution permissions.

Publication authorization 的未預期內部例外一律轉為 deny；診斷僅回報安全類別與識別資料。Claude Code `onFailure: block` 僅對 v2.1.295+ managed publication PreToolUse 設定。
Plan41 commit findings are produced by the existing Content Safety policy, not the Runtime Policy decision envelope. Its read-only CLI shares the Hook scanner and cannot create an allow decision, mutate Git or grant publication authority.
Scenario 266 records added-line injection classification and safe recovery for this scanner; full-blob secret/PII scanning and Runtime Policy decisions remain independent.

Publication diagnostics share safe failure classifications with native policy reporting but remain read-only. A diagnostic lookup or trace write cannot change a policy decision, create a grant, or claim the Host executed an action.

## Per-project optional governance modes

The project mode layer is an opt-in AIPS policy after the independent runtime policy and protected-path checks. A missing project record is `off`. `observe` reports bounded local action metadata only; `assist` may report a failed AIPS check as advice; neither mode returns a Host allow/deny decision. `enforce` requires a validated non-empty action scope and may deny only a failed in-scope action. Passing AIPS checks never grant Host permission in project `assist` or `enforce` mode.

The global administrator high-assurance publication trust root remains separate and is evaluated for every content-sensitive operation before a project mode can relax AIPS checks. Project YAML cannot replace that trust root. GitHub branch protection, required checks, and native Host confirmation remain effective in every project mode.

`config/runtime-policy.yaml` defaults to `DENY`. External destinations must be explicitly allowlisted. Built-in SAL3/4 and confidential/restricted external actions require exact approval, `TOOL_GUARDED`, and a current verified sandbox egress receipt. The checked-in sandbox registry currently has no verified allowlist egress provider, so those actions resolve to `BLOCKED` even when a hook can intercept them. This is the truthful current capability.

Decisions:

- `ALLOW` — explicit policy and Resource Authorization allow the action, and every required capability is verified.
- `DENY` — a hard policy or resource rule forbids the action. Deny overrides all allows.
- `REQUIRE_APPROVAL` — an otherwise eligible action needs a current exact scope-bound human Approval Record.
- `BLOCKED` — required evidence, policy, SAL, enforcement, sandbox or valid configuration is unavailable or stale.

The active Approval Record must bind operation `external_data_egress`, action digest, policy digest, exact destination, data classes, protected assets and Change Boundary. It must be APPROVED and unexpired. A missing record yields `REQUIRE_APPROVAL`; a present stale/invalid record yields `BLOCKED`.

In personal mode the publication guard parses command words with NUL-marked expansions: quoted-heredoc or single-quoted `gh pr create` text, including literal `$` and backticks, is data for content safety, while `$VAR`, backticks, `$"..."`, command substitution and unquoted heredocs deny with `PUBLICATION_ARGUMENT_DYNAMIC`. Denials carry a static recipe in `next_step`/`next_step_zh`; multiple protected operations deny as `MULTI_COMMAND_UNSUPPORTED`.

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

Personal PR merge checks are independently enforced by AIPS only when `AIPS_ENFORCE_REQUIRED_CHECKS=1`. This runtime setting does not mutate or bypass GitHub's native branch protection and rulesets.
