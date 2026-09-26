# Eval / Red-Team Interoperability

## Authority and data flow

AIPS Agent Eval Case / Result remain canonical. Promptfoo and PyRIT are optional evidence producers behind `scripts/eval_interop.py`; their status, score, or discovery finding never becomes an Integration Gate result.

Scenario 181 adds an independent operational telemetry lane; it does not change external-evaluation evidence, score interpretation or finding-promotion authority.

~~~text
Promptfoo config + JSONL observations ─┐
PyRIT v1 bridge observations ──────────┴→ bounded static parser → normalized, fingerprinted evidence
                                                              ↓
                                            review / minimal reproduction
                                                              ↓
                                      Human-confirmed AIPS Agent Eval Case
                                                              ↓
                                   local deterministic score + existing Gate
~~~

No Promptfoo or PyRIT command is executed by AIPS. No provider credential, remote generation, upload, sharing, or telemetry is required or enabled by this adapter. Users may run an external producer separately and explicitly choose which local evidence to import.

## Supported commands

- `aips eval export-promptfoo --case CASE.yaml --provider openai:MODEL --output promptfooconfig.yaml` emits one inline prompt, one explicit built-in OpenAI provider, and one variables-only test. It does not convert the AIPS rubric into external executable assertions; AIPS remains the scorer.
- `aips eval import-promptfoo --config CONFIG.yaml --results RESULTS.jsonl --output EVIDENCE.yaml` accepts one inline prompt, one built-in OpenAI provider, up to 100 inline tests, and the deterministic `equals`, `contains`, `not-contains`, and `is-json` assertion subset. Result rows must align with configured variables and expose only a response string/output.
- `aips eval verify-evidence --evidence EVIDENCE.yaml [--config CONFIG.yaml --results RESULTS.jsonl] [--bridge BRIDGE.yaml]` checks the normalized evidence fingerprint and, when source files are provided, source digests.
- `aips eval import-pyrit --bridge BRIDGE.yaml --output EVIDENCE.yaml` accepts the versioned AIPS bridge envelope; it does not claim to parse PyRIT's native evolving storage format.
- `aips eval profile --change-class CLASS [--area CLASS] [--deep-pyrit]` selects the strongest requested risk profile. Deep external scanning is opt-in and advisory.
- `aips eval promote-finding --finding FINDING.yaml --output CASE.yaml` requires a `CONFIRMED` finding and explicit Human approval metadata, then writes a minimal canonical Case with a deterministic rubric.

## Input and persistence boundary

All imported YAML is UTF-8 and bounded to 1 MB, 20 levels, 10,000 nodes, and 100 cases. Duplicate keys, aliases, explicit tags, unknown fields, file/path-backed providers, generators, hooks, custom code, model-graded assertions, and unsupported result shapes fail closed. Each JSONL row is a bounded mapping with optional scalar `vars`, required `response` (text or `{output: text}`), and optional boolean `success` / numeric `score`; only response text is scored, and external status/score values are discarded. No `eval`, shell, plugin, provider, scorer, or callback is invoked.

Private reasoning fields and recognizable secret material are rejected before output. Diagnostics expose categories only. Evidence contains source digests and a SHA-256 fingerprint over canonical JSON; `verify-evidence` detects edits to evidence or imported source files. Imported observations can contain sensitive prompts and responses, so output stays at the caller-selected local path and must follow the repository's existing data handling policy.

External evaluations map to `SIGNAL` or `REVIEW`. They are not eligible to hard-block or pass publication. A Human may confirm a finding and define a minimal reproduction. Only the resulting canonical Case, when independently run and deterministically scored with a current matching Result, can become regression evidence for an existing policy or Gate.

## Risk profiles

The versioned profiles in `config/eval-profiles.yaml` cover ordinary changes, prompt/system changes, routing/tool policy, RAG, MCP/tool permissions, credential/SAL3-4, provider migration, release candidates, and optional deep PyRIT scans. A higher-risk requested area wins. Profiles recommend evidence; they do not change Runtime Policy, Content Safety, Integration Gate applicability, or Human authority.

## Format references

The adapter intentionally supports a small static subset because Promptfoo accepts file-backed and executable configuration in addition to inline cases ([Promptfoo configuration guide](https://www.promptfoo.dev/docs/configuration/guide/), [reference](https://www.promptfoo.dev/docs/configuration/reference/)). PyRIT is an evolving framework with modular scenarios, attacks, converters, targets, scorers and memory; AIPS therefore accepts a versioned bridge envelope instead of claiming native-format compatibility ([PyRIT framework](https://github.com/microsoft/PyRIT/blob/main/doc/code/framework.md)).
