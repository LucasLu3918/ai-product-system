#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import tempfile

import anyio
from mcp import Client, StdioServerParameters
from mcp.types import TextContent, TextResourceContents

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "scripts" / "mcp_server.py"


def structured(result):
    if result.is_error:
        raise AssertionError(f"MCP tool returned error: {result.content}")
    if result.structured_content is None:
        raise AssertionError("MCP tool did not return structured_content")
    return result.structured_content


async def exercise() -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER), "serve"],
        env={"AIPS_MCP_WORKSPACE": str(ROOT)},
    )
    async with Client(params) as client:
        assert client.protocol_version == "2026-07-28", client.protocol_version
        assert client.instructions and "Human approval" in client.instructions
        assert "host-native tool enforcement" in client.instructions

        tools = await client.list_tools()
        tool_names = {item.name for item in tools.tools}
        required_tools = {
            "aips_system_info",
            "aips_project_identity",
            "aips_harness_context",
            "aips_role_skill_bundle",
            "aips_schedule",
        }
        assert required_tools <= tool_names, tool_names

        resources = await client.list_resources()
        resource_uris = {str(item.uri) for item in resources.resources}
        assert {
            "aips://catalog/roles",
            "aips://catalog/skills",
            "aips://catalog/protocols",
        } <= resource_uris

        templates = await client.list_resource_templates()
        template_uris = {item.uri_template for item in templates.resource_templates}
        assert "aips://roles/{role_id}" in template_uris
        assert "aips://skills/{skill_id}" in template_uris
        assert "aips://protocol/{protocol_id}" in template_uris

        prompts = await client.list_prompts()
        prompt_names = {item.name for item in prompts.prompts}
        assert {"security_review", "architecture_review", "code_review", "delivery_plan"} <= prompt_names

        role = await client.read_resource("aips://roles/security-engineer")
        assert any(isinstance(item, TextResourceContents) and "Security" in item.text for item in role.contents)
        skill = await client.read_resource("aips://skills/threat-modeling")
        assert any(isinstance(item, TextResourceContents) and "threat" in item.text.lower() for item in skill.contents)

        prompt = await client.get_prompt("security_review", {"objective": "Review checkout authorization"})
        texts = [item.content.text for item in prompt.messages if isinstance(item.content, TextContent)]
        rendered = "\n".join(texts)
        assert "aips://roles/security-engineer" in rendered
        assert "private chain-of-thought" in rendered
        assert "grants no Git publish" in rendered

        info = structured(await client.call_tool("aips_system_info", {}))
        assert info["protocol_revision"] == "2026-07-28"
        assert info["external_provider_credential_required"] is False
        assert all(value is False for value in info["authority"].values())

        bundle = structured(
            await client.call_tool(
                "aips_role_skill_bundle",
                {
                    "role_ids": ["security-engineer"],
                    "skill_ids": ["threat-modeling"],
                    "objective": "review",
                },
            )
        )
        assert bundle["status"] == "READY"
        assert bundle["semantic_selection_performed"] is False

        blocked_bundle = structured(
            await client.call_tool(
                "aips_role_skill_bundle",
                {"role_ids": ["../secrets"], "skill_ids": [], "objective": "escape"},
            )
        )
        assert blocked_bundle["status"] == "BLOCKED"

        graph = {
            "version": 1,
            "plan_id": "mcp-lifecycle",
            "base_revision": "fixture",
            "max_parallel": 2,
            "tasks": [
                {"id": "read-a", "read_only": True, "dependencies": [], "order": 10},
                {"id": "read-b", "read_only": True, "dependencies": [], "order": 20},
            ],
        }
        scheduled = structured(await client.call_tool("aips_schedule", {"graph": graph}))
        assert scheduled["dispatch"] == ["read-a", "read-b"]
        assert scheduled["authority"]["merge"] is False

        identity = structured(await client.call_tool("aips_project_identity", {"project": "."}))
        assert identity["identity"]["repository_id"]

        context = structured(await client.call_tool("aips_harness_context", {"project": "."}))
        assert context["runtime"]["id"] == "mcp-host"
        assert context["runtime"]["governance_enforcement"] == "ADVISORY"

        with tempfile.TemporaryDirectory() as outside:
            escaped = structured(await client.call_tool("aips_project_identity", {"project": outside}))
            assert escaped["status"] == "BLOCKED"
            assert "outside AIPS_MCP_WORKSPACE" in escaped["reason"]


if __name__ == "__main__":
    anyio.run(exercise)
    print("MCP INTEROPERABILITY LIFECYCLE PASSED")
