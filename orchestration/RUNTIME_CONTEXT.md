# Runtime Context

Runtime Context is the bounded, deterministic view of the active AIPS runtime, target project, task intent, scoped instructions, and currently available Project Intelligence. It is an advisory context contract; it does not replace host-agent judgment or grant write authority.

## Interpreter resolution

Resolve the Python interpreter from the target system/project configuration using the existing runtime path helper. Prefer a prepared, complete validation environment; report the selected executable and missing capabilities. Do not infer compatibility from a Python executable name alone.

## Context contract

For project work, context identifies project mode and stable instruction sources, then loads only relevant Intelligence topics. Missing/stale Intelligence and Retrieval remain explicit. A non-Git or no-HEAD workspace still receives basic context; Git-dependent history is reported unavailable. Turn Context does not persist prompts, tool arguments, secrets, or private reasoning.

## Verification

Use `aips intelligence context --runtime <id> --project <path> --prompt <task>` to inspect the resolved view and `aips publish environment` / the repository validator to inspect local Gate prerequisites. Runtime lifecycle evidence binds results to exact project/runtime inputs; diagnostics do not substitute for the final candidate Integration Gate.
