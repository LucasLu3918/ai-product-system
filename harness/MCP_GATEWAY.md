# MCP Interoperability Gateway

AIPS MCP is a portable access plane over existing AIPS canonical Roles, Skills, orchestration protocols and deterministic helpers. It is not a second orchestration system and it does not replace runtime-native Harness adapters.

## Boundary

~~~text
MCP-compatible Host
→ local stdio MCP client
→ AIPS MCP Gateway
   ├─ Resources → canonical Role / Skill / selected protocol files
   ├─ Prompts   → reusable host-model review/planning templates
   └─ Tools     → bounded deterministic AIPS helpers

Native Runtime Adapter (when available)
→ per-turn hooks / pre-tool governance enforcement
~~~

MCP access and native adapter enforcement are separate capabilities. A host that only connects through MCP is ADVISORY. Do not report TURN_NATIVE, TOOL_GUARDED or ENFORCED unless a separately verified runtime-native integration provides it.

## Transport

v0.52 supports local stdio only:

~~~bash
aips mcp serve
~~~

No remote HTTP service, OAuth server, hosted AIPS control plane or external Agent/provider credential is required.

## Progressive disclosure

- list Role / Skill catalogs first;
- read one Role or Skill body only after the host has selected it;
- selected orchestration protocols are allowlisted;
- do not expose arbitrary repository paths through MCP Resources;
- project tools are restricted to AIPS_MCP_WORKSPACE (default: server current working directory).

Roles/Skills remain single-source-of-truth files. The gateway does not copy them into another registry.

## Semantic reasoning

The MCP server does not call an LLM. Prompts provide bounded reusable context, while semantic selection/review/planning remains owned by the host model or existing AIPS orchestration. aips_role_skill_bundle validates explicit IDs; it does not pretend to perform semantic routing.

## Authority

Every AIPS MCP tool preserves false authority for Human approval, Git publication, merge, release, production and host-native tool enforcement unless an existing separately governed path proves otherwise.

MCP cannot generally intercept a host's own shell/file/git tools. Verified native hooks remain the mechanism for runtime-specific pre-tool guarding.

## Client configuration

~~~bash
aips mcp inspect
aips mcp config --client cursor
aips mcp config --client codex
aips mcp config --client generic
~~~

Configuration output is review-only. v0.52 never silently edits client-owned MCP configuration.

## Verification

Scenario 162 uses the official MCP Python Client against the real AIPS stdio subprocess and checks Resources / Resource Templates / Prompts / Tools / authority boundaries / workspace confinement. CI also installs a pinned Codex CLI, registers AIPS with codex mcp add, and verifies it is discoverable with codex mcp list without provider inference.
