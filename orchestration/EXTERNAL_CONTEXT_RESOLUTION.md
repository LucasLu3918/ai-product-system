# External Context Resolution

Use when the user provides a URL, ticket, document or external-system reference that the task depends on.

## Goal

Resolve the exact user-provided source with the least user effort. Do not ask the user to manually copy content until supported connection/public-access options have been exhausted.

## Resolution order

~~~text
User-provided source
→ Identify provider/source type
→ Connected connector / MCP / app
→ If connection exists but authorization is required:
     guide connect/authorize
     preserve current task + pending source
     resume after authorization
→ Exact public URL / public web access
→ Other supported provider/API path
→ User-provided export/upload/text/screenshot as last fallback
~~~

Exact connected/public source evidence has priority over search results and inference.

## Authorization

Distinguish:
- connector exists but is not authorized;
- connector is unavailable;
- connector is authorized but access to the specific resource is denied;
- provider/source is publicly accessible.

When authorization is needed:
1. explain the minimum connection action;
2. keep the current task objective and source reference;
3. after authorization, resume from the pending retrieval step rather than asking the user to restate the task.

## Fallback

Only ask the user to provide content when:
- no suitable connector/provider path exists or it cannot access the resource;
- public access is unavailable;
- another supported retrieval path is unavailable.

Useful fallbacks:
- paste relevant text;
- upload/export the ticket/document;
- provide screenshots;
- provide a PDF/CSV/JSON export.

Ask for only the portion required by the task.

## Source provenance

Record:
- original user-provided URL/reference;
- provider/source type;
- retrieval path;
- authorization/access state;
- retrieved resource identity/version/date when available.

Do not replace exact source content with generic web search when the user supplied an authoritative private source.

## Version-aware implementation knowledge

For OpenAPI validation, use the pinned local validator and declared specification version; never resolve `$ref` through the network. Any external contract authority must be separately retrieved, identified and recorded before it is treated as a baseline.

For a selected framework or runtime, use official documentation matching the project version when a material implementation question is not answered by current project evidence or a stable language profile. Record the exact source, applicable version and retrieved/reviewed date. Do not copy a framework's entire documentation set into AIPS. If official context is unavailable or conflicting, preserve the gap in the Implementation Profile and block only the decision-dependent work. Repeated, stable gaps may be proposed for Capability Incubation; they do not automatically create a Skill or Framework Profile.

Phase 3 enforcement binds the selected stable language Profile by path and digest to the exact implementation candidate. External framework documentation remains contextual evidence with source/version provenance; a Profile hash cannot establish that remote documentation or a framework recommendation is semantically correct.

## Safety / permissions

Connections and actions still follow provider permissions, privacy, least privilege and existing tool/governance rules.
