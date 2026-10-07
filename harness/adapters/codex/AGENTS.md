# AIPS Global Turn Harness

For every user turn involving software/product/project work, resolve the current AIPS Turn Context before analysis or mutation:

`aips intelligence context --runtime codex --project "$PWD" --prompt "<current user request>"`

Use returned pointers progressively. Preserve all existing user/project-native instructions.
The fixed AIPS system layer is `harness/BOOTSTRAP.md` plus `SYSTEM_CORE.md`; follow only the canonical protocol paths selected in `context.system_protocol_routes`. `SYSTEM.md` remains a compatibility index.

For an existing-project mutation:
1. initialize Project Intelligence when missing;
2. targeted-refresh it when stale;
3. resolve Change Impact before editing;
4. preserve valid project-native conventions;
5. verify input/output/data/event/consumer impact after the diff.

General conversation does not require heavy project initialization.

The runtime/user-selected primary implementation model remains the default unless policy or capability requires another route. Skill tiers must not silently downshift it. Prefer bounded primary execution; delegate only for material evidence, specialty, isolation or independent-review value.
