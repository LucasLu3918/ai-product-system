# Runtime Context

Runtime Context is the bounded, deterministic view of the active AIPS runtime, target project, task intent, scoped instructions, and currently available Project Intelligence. It is an advisory context contract; it does not replace host-agent judgment or grant write authority.

## Interpreter resolution

Publication shell classification uses pinned bashlex and signature verification uses pinned cryptography in the runtime. Missing parser or trust configuration returns a normal fail-closed Hook envelope; no environment-provided signing root is accepted.

Explicit validation Python/venv selection cannot silently fall back. Verify coverage, Hypothesis, mandatory JSON Schema and pip consistency before full validation; telemetry requires loopback even without browser. Child executors preserve HOME/credential lookup while removing inherited plan/import overrides and binding PATH to the selected Python.

The shared CI bootstrap uses the caller-selected pinned Python version, declared requirement files, tested constraints, and explicit import modules.

The public shell CLI remains a thin `bin/aips` launcher into `scripts/aips_cli.sh`. The facade resolves its real checkout and sources the implementation modules from `scripts/aips_cli/` before command dispatch, so installed symlinks and unrelated caller working directories use the matching runtime implementation.

The tested runtime installs from the repository's bounded constraints file through the existing bootstrap path. The resolver uses the same supported Python floor for CLI, validation and publication preflight.

Installed AIPS update selection follows the channel recorded in Git metadata: verified stable tags by default, explicit development branch when requested, and a documented `main` bootstrap only while no stable tag exists. Keep interpreter floor resolution independent from the update channel.

Resolve the Python interpreter from the target system/project configuration using the existing runtime path helper. Prefer a prepared, complete validation environment; report the selected executable and missing capabilities. Do not infer compatibility from a Python executable name alone.

Managed AIPS CLI runtimes require Python >=3.12. An explicit `AIPS_PYTHON` is authoritative and must satisfy the floor; automatic selection checks supported versioned executables before the generic `python3` fallback. Repository validation's compatibility smoke matrix is sourced from `config/system-facts.yaml`.

## Context contract

The additive `impact-candidates` command is read-only and its output does not alter Context freshness, project readiness or mutation authorization.

Creative prompt compilation and model guidance consume approved Profile facts as advisory input; only the active user's explicit action grant authorizes local execution or visual review.

For OpenCode Creative mutations, Runtime Context is advisory routing input; only the current native prompt-admission hook creates the transient, session-bound action grant.

OpenCode resolves project context from the active Session's directory rather than the plugin's setup location, enforces its compact UTF-8 budget and records only bounded privacy-safe timing metadata.

OpenCode's creative `prepare` action also binds its requested output to the active EPHEMERAL project scope and requires explicit create intent; it does not inherit the plugin installation directory as a write root.

OpenCode native projections use the existing resolved Python runtime. Version probing and file integrity remain distinct from native runtime verification; no model or provider configuration is selected by the adapter.

For project work, context identifies project mode and stable instruction sources, then loads only relevant Intelligence topics. Missing/stale Intelligence and Retrieval remain explicit. A non-Git or no-HEAD workspace still receives basic context; Git-dependent history is reported unavailable. Turn Context does not persist prompts, tool arguments, secrets, or private reasoning.

## Verification

Facade extraction keeps same function/exception identity under the supported interpreter. Validate source CLI and existing installed entrypoints with the complete Python 3.12 environment; missing observations stay UNKNOWN and do not bypass Gate requirements.

Creative preflight may report host OS/architecture, backend, runtime, model and discovered dtype. This metadata is diagnostic only; report compatibility as unverified until a supported inference smoke establishes it, without downloads or silent backend fallback.

Project Diagnostics reports allowlisted Runtime capability status and may leave effects UNVERIFIED. Only version-bound native lifecycle evidence can establish Context delivery or Hook/Tool execution.

Creative native-tool callback evidence normalizes array/messages/data Context envelopes and exercises user-only authority without provider credentials. The loopback native-host check remains a separate version-bound result; command discovery does not prove model readiness or image quality.

The creative CLI resolves the standard AIPS runtime; preflight checks local engine availability without launching generation, while execution is a separate explicit command.

Runtime Context validation remains bound to exact selected sources; shared hash helpers preserve the existing raw digest representation and do not alter routing.

Operator-only repository governance evidence is outside runtime context and does not alter adapter selection, project intelligence resolution, or runtime capability claims.

Use `aips intelligence context --runtime <id> --project <path> --prompt <task>` to inspect the resolved view and `aips publish environment` / the repository validator to inspect local Gate prerequisites. Runtime lifecycle evidence binds results to exact project/runtime inputs; diagnostics do not substitute for the final candidate Integration Gate.

- The release-readiness evaluator fails closed when the changelog is unavailable or its canonical Unreleased section is missing, duplicated, malformed, or non-empty.
