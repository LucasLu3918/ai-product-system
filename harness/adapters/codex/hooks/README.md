# Codex PreToolUse Probe

This is an isolated, repository-local experiment for one exact harmless `Bash` command:

```sh
printf 'AIPS_PLAN19_HOOK_PROBE'
```

The hook returns Codex's documented `PreToolUse` denial shape for that command. It does not deny other commands, install itself into `CODEX_HOME`, trust itself, or change project/user configuration. `hooks.json` is an example configuration for manual review and is not loaded by this repository's normal Codex session.

Run the provider-neutral contract probe with:

```sh
python tests/evidence/codex_hooks_lifecycle.py
```

That test sends synthetic hook-event JSON directly to the callback; it does **not** claim that a live Codex process dispatched the event. The configured timeout is three seconds. Hook failure, timeout, malformed output and unsupported/specialized tool paths must remain treated as potentially unguarded unless verified in a separate runtime-specific probe. Hosted tools such as web search are outside the local function-tool hook path, and later `write_stdin` input does not trigger a second `PreToolUse` check. Overall Codex governance therefore remains `ADVISORY`.

The event and denial fields follow the official [Codex Hooks documentation](https://developers.openai.com/codex/hooks). The hook contract allows denial for supported calls, but it is not a complete enforcement boundary.
