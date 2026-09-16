# Existing-Project Instruction Resolution

Load this for brownfield work, Global Harness instruction composition, or when the user explicitly references runtime/project-local instructions.

## Resolution order

External platform/safety constraints and AIPS constitutional/governance rules remain mandatory. Do not replace runtime-native instructions. Inside project execution:

```text
Current explicit user instruction / accepted current decision
→ runtime-native instructions in their native scope/precedence
→ nearest applicable project instructions (including scoped AGENTS.md)
→ accepted project ADR / authoritative contract
→ broader official project standards/docs
→ Project Knowledge cache (derived, non-governing)
→ project-local skill/reference
→ global AIPS skill/reference
→ inference
```

If the runtime enforces a different native precedence, obey that runtime rule and surface material conflicts.

## Scope

An instruction applies only to files/components inside its declared or directory scope. When multiple `AGENTS.md` files apply, the one nearest to the target path is more specific.

## Conflict handling

- equivalent/local conflicts: choose the more specific current instruction;
- material contract/architecture/security conflicts: surface impact and recommendation before implementation;
- after user approval, follow the user decision within its approved scope.

## Temporary vs permanent

A run-specific override is recorded under `.ai/runs/<run>/` and does not modify project policy. If the user approves a permanent change, update the authoritative project instruction/ADR/contract as part of the artifact contract.


## Global Harness

Runtime Adapters are integration mechanisms, not new instruction authorities.

- Codex/Claude/Gemini native instruction files remain in their native locations.
- AIPS does not copy their content into project knowledge.
- Existing user-owned runtime instruction files block destructive automatic adapter installation and result in MANUAL coverage.
- Project-specific instructions are still resolved for the actual target path.
