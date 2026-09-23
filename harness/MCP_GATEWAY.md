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

## Host capability compatibility

Full MCP hosts may use Resources, Prompts and Tools directly. Tool-only hosts use `aips_capability_catalog`, `aips_capability_read` and `aips_workflow_context` to obtain the same canonical Role / Skill / allowlisted protocol and review/planning context without creating a copied registry or a second reasoning engine.

Every AIPS MCP Tool is side-effect-free and declares read-only, non-destructive, idempotent and closed-world hints. These annotations describe the current AIPS gateway contract; they do not grant authority or make an untrusted third-party server safe.

Use MCP as the default integration for a new compatible Host. Add a runtime-native adapter only when the Host exposes a verifiable per-turn hook, pre-tool guard or runtime-specific event source that MCP cannot provide. A Host name alone does not justify another adapter.

`aips mcp inspect` returns the machine-readable compatibility matrix. Current validation scope is:

| Client | Surface | Validation | Native guard included |
|---|---|---|---|
| Cursor | Editor / CLI, local stdio | official config contract + MCP protocol | no |
| Windsurf | Cascade, local stdio | official config contract + MCP protocol | no |
| GitHub Copilot | CLI local stdio; hosted agent/code review are tool-only | official config contract + MCP protocol | no |
| Amp | CLI local stdio | official config contract + MCP protocol | no |
| Codex | CLI local stdio | pinned CLI registration + MCP protocol | no |
| Generic | local stdio MCP Host | MCP protocol | no |

Config/protocol validation is not a claim that an unavailable third-party GUI binary was executed. Every row remains ADVISORY unless a separate native integration is verified.

## Transport

The current gateway supports local stdio only:

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
aips mcp config --client windsurf
aips mcp config --client copilot
aips mcp config --client amp
aips mcp config --client codex
aips mcp config --client generic
~~~

Configuration output is review-only. AIPS never silently edits client-owned MCP configuration.

`copilot` targets GitHub Copilot CLI local stdio configuration. GitHub-hosted Copilot agent/code-review environments are tool-only and can use AIPS only when that environment can execute the configured AIPS command and resolve the declared workspace. Do not present a local absolute path as a hosted deployment.

## Verification

Scenario 162 uses the official MCP Python Client against the real AIPS stdio subprocess and checks Resources / Resource Templates / Prompts / Tools / authority boundaries / workspace confinement. CI also installs a pinned Codex CLI, registers AIPS with codex mcp add, and verifies it is discoverable with codex mcp list without provider inference.
