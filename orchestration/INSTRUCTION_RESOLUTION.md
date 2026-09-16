# Existing-Project Instruction Resolution

Use for brownfield work and Turn Harness context composition.

## Resolution order

~~~text
External platform / safety constraints
→ AIPS Constitution / Governance
→ current explicit user decision
→ runtime-native instructions in native precedence
→ nearest scoped project instructions
→ accepted ADR / authoritative contracts
→ broader official project docs
→ PROJECT_OVERRIDES
→ Project Intelligence (derived, non-governing)
→ project-local Skills
→ AIPS Skills
→ inference
~~~

Material conflicts are surfaced; a runtime's mandatory native precedence is never falsely overridden.

## Source Registry

Use `SOURCE_REGISTRY.yaml` to record authoritative/native sources and runtime visibility.

Do not copy source content into Intelligence merely to normalize formats.

Storage deduplication and runtime-context deduplication are separate:

- if a Runtime already auto-loads a source, Turn Context can point to it without reinjecting content;
- if a Runtime does not auto-load an applicable authoritative source, include a pointer for targeted load.

## Scope

Directory-scoped instructions apply only to targets inside their scope. Nearest applicable project instruction wins over broader project instruction when otherwise equivalent.

## Temporary vs permanent

A task-specific override is temporary. A permanent user/project decision belongs in the appropriate authoritative project record or `PROJECT_OVERRIDES.yaml` when it specifically confirms/excepts derived Intelligence.

## Adapter rule

Runtime Adapters are transport/integration mechanisms, not new instruction authorities.
