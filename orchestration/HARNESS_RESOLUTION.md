# Harness Resolution

Use when AIPS is installed through the Global Harness or when an Agent needs to resolve runtime/project context without replaying setup instructions.

## Goal

Resolve deterministic environment facts before loading reasoning context.

~~~text
Agent Session
→ Minimal Runtime Adapter Bootstrap
→ aips harness resolve
→ Runtime + Project + Mode + Instruction pointers
→ AIPS applicable?
   ├─ no  → normal conversation
   └─ yes → minimal AIPS routing/context
~~~

## Applicability

The Global Harness is always available, but full AIPS orchestration is not mandatory for unrelated conversation.

AIPS orchestration is normally applicable to:

- software/product/project planning;
- implementation/refactoring/debugging;
- architecture/API/data/security/quality work;
- visual/product delivery work;
- repository/documentation changes;
- deployment/operations/release work.

A general knowledge question with no active project/work product may proceed normally.

## Deterministic resolver

Use:

~~~bash
aips harness resolve --cwd "$PWD"
~~~

When the runtime is known:

~~~bash
aips harness resolve --runtime codex --cwd "$PWD"
aips harness resolve --runtime claude-code --cwd "$PWD"
aips harness resolve --runtime gemini-cli --cwd "$PWD"
~~~

For an explicit project outside cwd:

~~~bash
aips harness resolve --project /path/to/project
~~~

Do not infer an attached workspace when the resolver reports EPHEMERAL.

## Project modes

### EPHEMERAL

- use AIPS governance/planning/review as applicable;
- read project/runtime-native instructions;
- inspect source when needed;
- do not create `.ai/` automatically;
- do not persist Project Knowledge/State unless the user explicitly attaches the project.

### ATTACHED

The user explicitly enabled persistence with `aips attach <project>`.

AIPS may use:

- `.ai/STATE.yaml`;
- `.ai/MANIFEST.yaml`;
- `.ai/knowledge/`;
- run/decision/event persistence.

## Instruction composition

AIPS does not replace runtime-native instructions.

Resolve all applicable sources with their actual scope and native precedence, while keeping AIPS constitutional/governance rules mandatory within the AIPS workflow.

Typical effective order:

~~~text
External platform / safety constraints
→ AIPS Constitution / Governance
→ Current explicit user decision
→ Runtime-native instructions in their native scope / precedence
→ Nearest project AGENTS / accepted ADR / contracts
→ Official project docs
→ Project Knowledge
→ Project-local Skills
→ AIPS Skills
→ Generic inference
~~~

If native runtime rules force a different precedence, do not falsely claim enforcement. Surface material conflicts and follow the runtime/platform constraints.

## Minimal loading

The resolver returns pointers, not a request to open every source.

Load only:

1. Minimal AIPS entry/router when applicable;
2. relevant runtime/project instructions;
3. relevant Project Knowledge topics;
4. selected protocol/Role/Skill leaves.

## Runtime coverage

`aips harness status` reports machine-specific integration state.

- AUTOMATIC — runtime loads an AIPS-owned bootstrap automatically.
- MANUAL — runtime detected but a user-owned integration resource prevents safe automatic installation.
- NOT_DETECTED — runtime not present.
- CONFLICT — namespace/registration collision.
- ERROR — installation/verification failed.

MANUAL is intentional safety behavior, not a reason to patch existing user configuration.

## Update / uninstall

Adapters are AIPS-owned and independently removable. Uninstall does not remove project `.ai/`, user/project instructions, custom Skills or source code.
