# Scenario 162 — MCP Interoperability Gateway

An MCP-compatible host needs portable access to AIPS without a new full runtime-specific adapter.

Expected:
- AIPS exposes a local stdio MCP server using the stable MCP 2026-07-28 protocol through the official Python SDK v2;
- Tools, Resources and Prompts are all discoverable through a real MCP client connection;
- Roles and Skills remain canonical files under roles/ and skills/ and are loaded through resource indexes/templates only on demand;
- reusable prompts reference canonical Role/Skill/Orchestration resources and leave semantic reasoning in the host model;
- deterministic tools expose project identity, compact Harness context, explicit Role/Skill bundle validation and the existing deterministic Scheduler;
- project-oriented tools are bounded to AIPS_MCP_WORKSPACE and reject outside paths;
- MCP access reports governance enforcement as ADVISORY and never claims Human approval, Git publish, merge, release, production or host-native tool interception authority;
- existing Claude Code / Gemini CLI / Codex native Harness behavior is preserved; MCP does not replace verified native hooks;
- the baseline server requires no external Agent/provider credential and v0.52 uses local stdio only;
- client configuration output is review-only and does not silently edit Cursor, Codex or other client-owned settings;
- CI validates an exact-candidate real stdio protocol session and registers/lists AIPS through a pinned Codex CLI without provider inference.
