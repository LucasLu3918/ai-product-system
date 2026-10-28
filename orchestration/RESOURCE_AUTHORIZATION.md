# Resource-Scoped Agent Authorization

Publication Doctor remains a separately invoked read-only observation. A Claude Hook timeout or retryable remote failure stays denied until a fresh Prepare and the existing authority checks succeed.

## Purpose

Add deterministic least-privilege evidence to the existing Execution Profile without creating a new Role, Skill or Human approval gate.

The contract answers one narrow pre-execution question:

> Is this subject explicitly granted this operation on this declared resource under the current execution constraints?

It does not infer intent, discover permissions from prose, or grant protected publication/destructive authority.

## Contract

Publication resource binding resolves literal `git -C <path>` from invocation cwd and binds authorization checks to the resulting target worktree and candidate; dynamic or missing paths are denied.

ComfyUI creative reference bindings remain constrained by the existing local-project resource scope. Qwen Image Edit Plus maps no more than three contiguous staged references and does not widen the authorization grant.

Publication scan evidence is not a Resource Authorization grant: it describes one successful scanner result and cannot authorize a Git operation or expand a declared resource scope.

A recipe in a publication denial and PR-bound scan evidence are not Resource Authorization grants; they never authorize a Git operation.

Creative's dynamic ComfyUI workflow mode applies the same least-privilege intent locally: schema discovery is read-only, workflow import is an explicit project-path write, and generation is a distinct execution action. Fixed FLUX 3 Klein also validates the live `TextGenerate` schema and final serialized payload; neither validation grants permission to submit a job.

Creative model profile declarations do not create Resource Authorization grants or expand the fixed loopback ComfyUI destination, method or path allowlist. FLUX 3 Klein Base/Distilled profiles share the audited topology; bounded ordered reference slots for dynamic edit remain subject to the same local schema, file-size and staged-byte checks. Local profile drafts and approvals create no grants and open no endpoint or download.

Media-format and EXIF/XMP checks are content-safety decisions; they do not create a Resource Authorization profile or grant provider, filesystem or network access.

Commit font metadata inspection is a content-safety decision; it cannot authorize a tool action, push, merge, or release.

Publication diagnostic bindings and audit records are observational data, not resource grants. They do not infer a selector or operation permission and cannot authorize push, PR creation, merge, or any Creative action.
Plan44 command detail and native failure fields remain observation-only; neither creates nor satisfies a Resource Authorization grant.

Each execution may reference a Resource Authorization Profile:

~~~yaml
version: 1
default_effect: DENY
subject:
  id: implementation-agent
  role: backend-engineer
grants:
  - id: application-source
    kind: repository_path
    selector: "src/**"
    operations: [read, search, update]
    constraints:
      change_boundary_required: true
      network_allowed: false
      allowed_destinations: ["git.example.com"] # Optional exact destination hosts.
      allowed_ports: [443]
      allowed_methods: [GET, POST]
      allowed_paths: ["/v1/**"]
      redirects_allowed: false
authority:
  human_approval_granted: false
  merge_authorized: false
  release_authorized: false
  protected_operation_authorized: false
~~~

Supported resource kinds are repository paths, workspaces, runtime tools, connectors and external services. Supported ordinary operations are read, search, create, update and execute.

The evaluator is fail-closed:

- default effect MUST be `DENY`;
- missing resource grant → DENY;
- mismatched resource kind or selector → DENY;
- missing operation grant → DENY;
- mutating operation with a required but absent Change Boundary → DENY;
- network use requires `network_allowed: true`; missing is treated as false;
- supplied destination, port, method, path or redirect evidence must meet every declared constraint;
- duplicate/unknown grants or operations → profile BLOCKED;
- secret values are forbidden; only a credential reference may appear;
- merge/release/Human/protected-operation authority MUST remain false.

Protected operations such as publication, administration and destructive deletion are intentionally outside this profile. They continue through normal Governance / Approval Binding / Git Publish / safety challenge paths.

## Enforcement truth

Resource authorization is checked at the consuming runtime boundary; a valid profile or diagnostic report alone does not execute a workflow or confer broader host permission.

Shared publication guard 的非預期授權例外會拒絕操作，輸出只包含 allowlist 例外類別與診斷 ID；這不改變任何資源 grant。
Commit Content Safety is a separate content boundary, not a Resource Authorization profile or grant. Plan41 adds only read-only diagnostics and preserves all existing Human Authority, Required Checks and Git Publish Approval decisions.
Scenario 266 further records versioned injection signals and exact expiring exceptions in that content boundary; neither changes Resource grants, Human approval, or publication decisions.

Publication guard command classification is not a Resource Authorization decision and cannot create a grant.

Resource Authorization emits `status`, `phase`, `reason_code`, `source`, `retryable`, `trace_id` and `recovery.action` alongside its decision evidence. Profile absence, missing/unreadable files, malformed YAML/schema, and grant-scope mismatches retain separate stable reason codes. Local filesystem paths and raw parser errors are not emitted.

`scripts/resource_authorization.py` produces **PRE_EXECUTION_EVIDENCE**. It does not claim that every runtime can mechanically intercept every tool call.

A runtime with a verified pre-tool guard may consume this evidence as an additional deny condition. A runtime without such a guard remains advisory and must not be represented as runtime-enforced.

Resource Authorization can tighten an operation but never widens Change Boundary, Execution Isolation, Role/Skill responsibility or Human authority.

For scheduled repository work, `aips run owner claim` derives a task-scoped authorization record from the canonical Task Graph `write_set` and `change_boundary`. Paths outside the write set remain denied at the contract level, and final task completion independently checks the actual Git diff. This record is advisory evidence: it is not a filesystem sandbox and cannot intercept arbitrary runtime writes. Report `TOOL_GUARDED` only when a verified native write guard enforces the exact task record.

For supported runtime tool actions, Resource Authorization is one input to `orchestration/RUNTIME_POLICY_ENFORCEMENT.md`. It remains default-DENY evidence and is evaluated before policy ALLOW; an action cannot use a policy allow rule to bypass a missing resource grant.

## CLI

~~~bash
aips authorization validate --profile RESOURCE_AUTHORIZATION_PROFILE.yaml

aips authorization check \
  --profile RESOURCE_AUTHORIZATION_PROFILE.yaml \
  --resource-id application-source \
  --kind repository_path \
  --selector src/app.py \
  --operation update \
  --change-boundary orders
~~~

An ALLOW means only that the declared ordinary resource operation is within the deterministic profile. All other applicable governance/testing/publication gates still apply.

For external services, the runtime binds the grant selector to the observed destination host and passes explicit port/method/path and redirect evidence when available. A model-provided Runtime Action cannot replace the host-observed tool, URL or trusted `AIPS_RESOURCE_AUTHORIZATION_PROFILE` environment setting.

Git publication remains subject to explicit Human task intent and exact-candidate validation. AIPS Required Checks enforcement is opt-in via `AIPS_ENFORCE_REQUIRED_CHECKS=1`; GitHub native protection remains effective.
