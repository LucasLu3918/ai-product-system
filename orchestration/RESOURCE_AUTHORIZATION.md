# Resource-Scoped Agent Authorization

## Purpose

Add deterministic least-privilege evidence to the existing Execution Profile without creating a new Role, Skill or Human approval gate.

The contract answers one narrow pre-execution question:

> Is this subject explicitly granted this operation on this declared resource under the current execution constraints?

It does not infer intent, discover permissions from prose, or grant protected publication/destructive authority.

## Contract

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
- missing operation grant → DENY;
- mutating operation with a required but absent Change Boundary → DENY;
- duplicate/unknown grants or operations → profile BLOCKED;
- secret values are forbidden; only a credential reference may appear;
- merge/release/Human/protected-operation authority MUST remain false.

Protected operations such as publication, administration and destructive deletion are intentionally outside this profile. They continue through normal Governance / Approval Binding / Git Publish / safety challenge paths.

## Enforcement truth

`scripts/resource_authorization.py` produces **PRE_EXECUTION_EVIDENCE**. It does not claim that every runtime can mechanically intercept every tool call.

A runtime with a verified pre-tool guard may consume this evidence as an additional deny condition. A runtime without such a guard remains advisory and must not be represented as runtime-enforced.

Resource Authorization can tighten an operation but never widens Change Boundary, Execution Isolation, Role/Skill responsibility or Human authority.

For supported runtime tool actions, Resource Authorization is one input to `orchestration/RUNTIME_POLICY_ENFORCEMENT.md`. It remains default-DENY evidence and is evaluated before policy ALLOW; an action cannot use a policy allow rule to bypass a missing resource grant.

## CLI

~~~bash
aips authorization validate --profile RESOURCE_AUTHORIZATION_PROFILE.yaml

aips authorization check \
  --profile RESOURCE_AUTHORIZATION_PROFILE.yaml \
  --resource-id application-source \
  --operation update \
  --change-boundary orders
~~~

An ALLOW means only that the declared ordinary resource operation is within the deterministic profile. All other applicable governance/testing/publication gates still apply.
