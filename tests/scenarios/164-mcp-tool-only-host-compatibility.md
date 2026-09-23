# Scenario 164 — MCP Tool-Only Host Compatibility

MCP hosts with different capability subsets need truthful access to AIPS without duplicating canonical Roles, Skills, protocols, or review workflows.

Expected:
- every AIPS MCP Tool declares read-only, non-destructive, idempotent, closed-world annotations;
- tool-only hosts can list and read canonical Role / Skill / allowlisted protocol content through bounded Tools;
- tool-only hosts can render Security Review, Architecture Review, Code Review, and Delivery Plan context without a second model call;
- invalid kinds, ids, path-like escapes, and workflows fail closed;
- Cursor, Windsurf, GitHub Copilot CLI, Amp, Codex, and generic review-only configuration payloads are deterministic JSON and never mutate client-owned settings;
- Copilot configuration allowlists the AIPS tool facade because Copilot cloud/code-review surfaces do not consume MCP Resources or Prompts;
- host capability guidance distinguishes MCP ADVISORY access from runtime-native hook enforcement;
- existing Resources, Prompts, Tools, workspace confinement, authority boundaries, and native adapters remain backward compatible;
- lifecycle verification uses the official MCP Python Client against the real local stdio subprocess.
