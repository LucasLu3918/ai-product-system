# Existing-Project Instruction Resolution

Load this only for brownfield work or when the user explicitly references project-local instructions.

## Resolution order

System safety/governance remains mandatory. Inside project execution:

```text
Current explicit user instruction / accepted current decision
→ nearest applicable scoped AGENTS.md
→ accepted project ADR / authoritative contract
→ broader project standards / root AGENTS.md
→ project-local skill/reference
→ global skill/reference
→ inference
```

## Scope

An instruction applies only to files/components inside its declared or directory scope. When multiple `AGENTS.md` files apply, the one nearest to the target path is more specific.

## Conflict handling

- equivalent/local conflicts: choose the more specific current instruction;
- material contract/architecture/security conflicts: surface impact and recommendation before implementation;
- after user approval, follow the user decision within its approved scope.

## Temporary vs permanent

A run-specific override is recorded under `.ai/runs/<run>/` and does not modify project policy. If the user approves a permanent change, update the authoritative project instruction/ADR/contract as part of the artifact contract.
