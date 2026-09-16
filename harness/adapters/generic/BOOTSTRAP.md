# AIPS Generic Manual Bootstrap

Use this only when the current Agent runtime has no safe automatic AIPS Adapter.

For product/project/software engineering work:

1. run or ask the environment to run `aips harness resolve --cwd "$PWD"`;
2. follow the returned `harness.bootstrap`, `system.entry` and `system.router` pointers;
3. preserve the runtime's native instructions and the target project's instructions;
4. load only relevant AIPS protocols/Project Knowledge;
5. do not create `.ai/` unless the project is explicitly attached;
6. for unrelated conversation, continue normally.

This is a manual fallback. It does not grant AIPS authority over runtime/platform rules.
