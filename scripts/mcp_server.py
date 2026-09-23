#!/usr/bin/env python3
"""AIPS MCP interoperability gateway (local stdio, provider-neutral)."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import deterministic_scheduler
import yaml
from mcp.server import MCPServer
from mcp.types import ToolAnnotations

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_VERSION = "2026-07-28"
AUTHORITY = {
    "human_approval": False,
    "git_publish": False,
    "merge": False,
    "release": False,
    "production": False,
    "host_native_tool_enforcement": False,
}
SERVER_INSTRUCTIONS = (
    "AIPS MCP is a portable ADVISORY access plane for canonical AIPS Roles, Skills, "
    "orchestration context and deterministic helpers. The host model performs semantic "
    "reasoning. This server does not grant Human approval, Git publish, merge, release, "
    "production, or host-native tool enforcement authority. Load only task-relevant "
    "resources. Verified runtime-native adapters remain required for TURN_NATIVE or "
    "TOOL_GUARDED behavior."
)

PROTOCOL_RESOURCES = {
    "system-router": "SYSTEM.md",
    "planning-package": "orchestration/PLANNING_PACKAGE.md",
    "product-delivery": "orchestration/PRODUCT_DELIVERY.md",
    "quality-planning": "orchestration/QUALITY_PLANNING.md",
    "change-impact": "orchestration/CHANGE_IMPACT.md",
    "execution-isolation": "orchestration/EXECUTION_ISOLATION.md",
    "deterministic-scheduler": "orchestration/DETERMINISTIC_SCHEDULER.md",
    "secret-handling": "orchestration/SECRET_HANDLING.md",
    "release-readiness": "orchestration/RELEASE_READINESS.md",
    "multi-review": "orchestration/MULTI_REVIEW.md",
}
WORKFLOWS = {
    "security-review": {
        "role": "security-engineer",
        "skills": ["secure-design", "threat-modeling", "authorization-security", "security-testing"],
        "protocols": ["change-impact", "secret-handling"],
    },
    "architecture-review": {
        "role": "software-architect",
        "skills": ["clean-architecture", "domain-driven-design"],
        "protocols": ["change-impact", "multi-review"],
    },
    "code-review": {
        "role": "quality-reviewer",
        "skills": ["code-review", "tdd"],
        "protocols": ["change-impact", "multi-review"],
    },
    "delivery-plan": {
        "role": "delivery-planner",
        "skills": ["delivery-planning", "requirements-definition"],
        "protocols": ["planning-package", "product-delivery", "quality-planning"],
    },
}
READ_ONLY_TOOL = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)
HOST_COMPATIBILITY = {
    "cursor": {
        "surface": "editor-and-cli",
        "transport": "stdio",
        "tool_only_facade_available": True,
        "native_guard_included": False,
        "verification": "official-config-contract-and-mcp-protocol",
    },
    "windsurf": {
        "surface": "cascade",
        "transport": "stdio",
        "tool_only_facade_available": True,
        "native_guard_included": False,
        "verification": "official-config-contract-and-mcp-protocol",
    },
    "copilot": {
        "surface": "github-copilot-cli",
        "transport": "stdio",
        "tool_only_facade_available": True,
        "native_guard_included": False,
        "verification": "official-config-contract-and-mcp-protocol",
        "limitation": "hosted-agent-and-code-review-surfaces-are-tool-only",
    },
    "amp": {
        "surface": "cli",
        "transport": "stdio",
        "tool_only_facade_available": True,
        "native_guard_included": False,
        "verification": "official-config-contract-and-mcp-protocol",
    },
    "codex": {
        "surface": "cli",
        "transport": "stdio",
        "tool_only_facade_available": True,
        "native_guard_included": False,
        "verification": "pinned-cli-registration-and-mcp-protocol",
    },
    "generic": {
        "surface": "mcp-host",
        "transport": "stdio",
        "tool_only_facade_available": True,
        "native_guard_included": False,
        "verification": "mcp-protocol",
    },
}


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"expected mapping: {path}")
    return data


ROLE_INDEX = _load_yaml(ROOT / "roles" / "INDEX.yaml").get("roles") or {}
SKILL_INDEX = _load_yaml(ROOT / "skills" / "INDEX.yaml").get("skills") or {}


def _canonical_file(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("resource path escapes AIPS root") from exc
    if not path.is_file():
        raise ValueError(f"canonical resource is missing: {relative}")
    return path


def _role_path(role_id: str) -> Path:
    item = ROLE_INDEX.get(role_id)
    if not isinstance(item, dict):
        raise ValueError(f"unknown AIPS role: {role_id}")
    return _canonical_file("roles/" + str(item["path"]))


def _skill_path(skill_id: str) -> Path:
    item = SKILL_INDEX.get(skill_id)
    if not isinstance(item, dict):
        raise ValueError(f"unknown AIPS skill: {skill_id}")
    return _canonical_file("skills/" + str(item["path"]))


def _capability_path(kind: str, capability_id: str) -> tuple[Path, str]:
    if kind == "role":
        return _role_path(capability_id), f"aips://roles/{capability_id}"
    if kind == "skill":
        return _skill_path(capability_id), f"aips://skills/{capability_id}"
    if kind == "protocol":
        relative = PROTOCOL_RESOURCES.get(capability_id)
        if relative is None:
            raise ValueError(f"unknown AIPS protocol: {capability_id}")
        return _canonical_file(relative), f"aips://protocol/{capability_id}"
    raise ValueError("kind must be role, skill, or protocol")


def _workspace_root() -> Path:
    raw = os.environ.get("AIPS_MCP_WORKSPACE")
    return Path(raw).expanduser().resolve() if raw else Path.cwd().resolve()


def _resolve_project(raw: str) -> tuple[Path | None, str | None]:
    workspace = _workspace_root()
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = workspace / candidate
    candidate = candidate.resolve()
    if not candidate.is_dir():
        return None, f"project path does not exist: {candidate}"
    try:
        candidate.relative_to(workspace)
    except ValueError:
        return None, "project path is outside AIPS_MCP_WORKSPACE"
    return candidate, None


def _run_json(script: str, args: list[str], *, cwd: Path | None = None) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        return {"status": "BLOCKED", "reason": (result.stderr or result.stdout).strip()}
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "BLOCKED", "reason": "deterministic helper returned non-JSON output"}
    if not isinstance(value, dict):
        return {"status": "BLOCKED", "reason": "deterministic helper returned unexpected shape"}
    return value


def _catalog(kind: str) -> str:
    if kind == "roles":
        value = {"version": 1, "roles": ROLE_INDEX}
    elif kind == "skills":
        value = {"version": 1, "skills": SKILL_INDEX}
    else:
        value = {"version": 1, "protocols": PROTOCOL_RESOURCES}
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True)


def _prompt_text(name: str, objective: str, role: str, skills: list[str], protocols: list[str]) -> str:
    resources = [
        f"aips://roles/{role}",
        *[f"aips://skills/{item}" for item in skills],
        *[f"aips://protocol/{item}" for item in protocols],
    ]
    return (
        f"AIPS prompt: {name}\n"
        f"Objective: {objective}\n\n"
        "Read only these task-relevant canonical AIPS resources before reasoning:\n- "
        + "\n- ".join(resources)
        + "\n\nThe host model performs the semantic analysis. Preserve Protected Human Authority and "
        "current project/runtime instructions. Do not claim private chain-of-thought. "
        "Return observable findings, evidence, assumptions, risks, and next actions. "
        "This prompt grants no Git publish, merge, release, production, or approval authority."
    )


def _workflow_text(name: str, objective: str) -> str:
    workflow = WORKFLOWS.get(name)
    if workflow is None:
        raise ValueError(f"unknown AIPS workflow: {name}")
    return _prompt_text(
        name,
        objective,
        str(workflow["role"]),
        list(workflow["skills"]),
        list(workflow["protocols"]),
    )


mcp = MCPServer("AIPS", instructions=SERVER_INSTRUCTIONS)


@mcp.resource("aips://catalog/roles")
def role_catalog() -> str:
    """Canonical AIPS Role index; read Role bodies only after selection."""
    return _catalog("roles")


@mcp.resource("aips://catalog/skills")
def skill_catalog() -> str:
    """Canonical AIPS Skill index; read Skill bodies only after selection."""
    return _catalog("skills")


@mcp.resource("aips://catalog/protocols")
def protocol_catalog() -> str:
    """Allowlisted orchestration resources exposed by this gateway."""
    return _catalog("protocols")


@mcp.resource("aips://roles/{role_id}")
def role_resource(role_id: str) -> str:
    """Read one canonical Role body after an explicit role id is known."""
    return _role_path(role_id).read_text(encoding="utf-8")


@mcp.resource("aips://skills/{skill_id}")
def skill_resource(skill_id: str) -> str:
    """Read one canonical Skill body after an explicit skill id is known."""
    return _skill_path(skill_id).read_text(encoding="utf-8")


@mcp.resource("aips://protocol/{protocol_id}")
def protocol_resource(protocol_id: str) -> str:
    """Read one allowlisted AIPS orchestration protocol."""
    relative = PROTOCOL_RESOURCES.get(protocol_id)
    if relative is None:
        raise ValueError(f"unknown AIPS protocol resource: {protocol_id}")
    return _canonical_file(relative).read_text(encoding="utf-8")


@mcp.prompt()
def security_review(objective: str) -> str:
    """Prepare a host-model security review using canonical AIPS security context."""
    return _workflow_text("security-review", objective)


@mcp.prompt()
def architecture_review(objective: str) -> str:
    """Prepare a host-model architecture review using canonical AIPS architecture context."""
    return _workflow_text("architecture-review", objective)


@mcp.prompt()
def code_review(objective: str) -> str:
    """Prepare a host-model code review using canonical AIPS quality context."""
    return _workflow_text("code-review", objective)


@mcp.prompt()
def delivery_plan(objective: str) -> str:
    """Prepare a host-model delivery plan using canonical AIPS planning context."""
    return _workflow_text("delivery-plan", objective)


@mcp.tool(annotations=READ_ONLY_TOOL)
def aips_system_info() -> dict[str, Any]:
    """Return AIPS/MCP identity and explicit authority boundaries."""
    return {
        "status": "AVAILABLE",
        "gateway": "mcp-interoperability",
        "transport": "stdio",
        "protocol_revision": PROTOCOL_VERSION,
        "aips_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "roles": len(ROLE_INDEX),
        "skills": len(SKILL_INDEX),
        "external_provider_credential_required": False,
        "semantic_reasoning_location": "host_model",
        "client_registration_managed": False,
        "authority": dict(AUTHORITY),
    }


@mcp.tool(annotations=READ_ONLY_TOOL)
def aips_project_identity(project: str = ".") -> dict[str, Any]:
    """Resolve canonical project/workspace identity inside the configured MCP workspace."""
    path, error = _resolve_project(project)
    if error:
        return {"status": "BLOCKED", "reason": error, "authority": dict(AUTHORITY)}
    value = _run_json("aips_identity.py", ["show", "--project", str(path), "--format", "json"], cwd=path)
    value["authority"] = dict(AUTHORITY)
    return value


@mcp.tool(annotations=READ_ONLY_TOOL)
def aips_harness_context(project: str = ".") -> dict[str, Any]:
    """Resolve compact AIPS project context for an MCP host without claiming native hooks."""
    path, error = _resolve_project(project)
    if error:
        return {"status": "BLOCKED", "reason": error, "authority": dict(AUTHORITY)}
    value = _run_json(
        "harness_resolve.py",
        ["--runtime", "unknown", "--cwd", str(path), "--project", str(path), "--format", "json"],
        cwd=path,
    )
    if value.get("status") == "BLOCKED":
        value["authority"] = dict(AUTHORITY)
        return value
    value["runtime"] = {
        "id": "mcp-host",
        "detected": True,
        "adapter_status": "MCP_GATEWAY",
        "capability": "MCP_STANDARD",
        "governance_enforcement": "ADVISORY",
        "native_instructions": [],
    }
    value["mcp"] = {
        "transport": "stdio",
        "protocol_revision": PROTOCOL_VERSION,
        "native_adapter_replacement": False,
    }
    value["authority"] = dict(AUTHORITY)
    return value


@mcp.tool(annotations=READ_ONLY_TOOL)
def aips_role_skill_bundle(role_ids: list[str], skill_ids: list[str], objective: str = "") -> dict[str, Any]:
    """Validate explicit Role/Skill ids and return resource URIs; no semantic selection is performed."""
    unknown_roles = sorted({item for item in role_ids if item not in ROLE_INDEX})
    unknown_skills = sorted({item for item in skill_ids if item not in SKILL_INDEX})
    if unknown_roles or unknown_skills:
        return {
            "status": "BLOCKED",
            "unknown_roles": unknown_roles,
            "unknown_skills": unknown_skills,
            "semantic_selection_performed": False,
            "authority": dict(AUTHORITY),
        }
    return {
        "status": "READY",
        "objective": objective,
        "roles": [f"aips://roles/{item}" for item in sorted(set(role_ids))],
        "skills": [f"aips://skills/{item}" for item in sorted(set(skill_ids))],
        "semantic_selection_performed": False,
        "selection_owner": "host_model_or_existing_aips_orchestration",
        "authority": dict(AUTHORITY),
    }


@mcp.tool(annotations=READ_ONLY_TOOL)
def aips_capability_catalog(kind: str) -> dict[str, Any]:
    """List canonical AIPS role, skill, or allowlisted protocol metadata for tool-only MCP hosts."""
    if kind == "role":
        items = ROLE_INDEX
    elif kind == "skill":
        items = SKILL_INDEX
    elif kind == "protocol":
        items = {item: {"path": path} for item, path in PROTOCOL_RESOURCES.items()}
    else:
        return {
            "status": "BLOCKED",
            "reason": "kind must be role, skill, or protocol",
            "authority": dict(AUTHORITY),
        }
    return {
        "status": "READY",
        "kind": kind,
        "items": items,
        "semantic_selection_performed": False,
        "authority": dict(AUTHORITY),
    }


@mcp.tool(annotations=READ_ONLY_TOOL)
def aips_capability_read(kind: str, capability_id: str) -> dict[str, Any]:
    """Read one canonical Role, Skill, or allowlisted protocol for a tool-only MCP host."""
    try:
        path, uri = _capability_path(kind, capability_id)
    except ValueError as exc:
        return {"status": "BLOCKED", "reason": str(exc), "authority": dict(AUTHORITY)}
    return {
        "status": "READY",
        "kind": kind,
        "id": capability_id,
        "uri": uri,
        "content": path.read_text(encoding="utf-8"),
        "authority": dict(AUTHORITY),
    }


@mcp.tool(annotations=READ_ONLY_TOOL)
def aips_workflow_context(workflow: str, objective: str) -> dict[str, Any]:
    """Render an AIPS review/planning workflow for hosts that do not expose MCP Prompts."""
    item = WORKFLOWS.get(workflow)
    if item is None:
        return {
            "status": "BLOCKED",
            "reason": f"unknown AIPS workflow: {workflow}",
            "available_workflows": sorted(WORKFLOWS),
            "authority": dict(AUTHORITY),
        }
    resources = [
        f"aips://roles/{item['role']}",
        *[f"aips://skills/{value}" for value in item["skills"]],
        *[f"aips://protocol/{value}" for value in item["protocols"]],
    ]
    return {
        "status": "READY",
        "workflow": workflow,
        "objective": objective,
        "resources": resources,
        "prompt": _workflow_text(workflow, objective),
        "semantic_reasoning_location": "host_model",
        "authority": dict(AUTHORITY),
    }


@mcp.tool(annotations=READ_ONLY_TOOL)
def aips_schedule(graph: dict[str, Any], state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the existing deterministic AIPS scheduler; this cannot invent tasks or grant authority."""
    try:
        result = deterministic_scheduler.schedule(
            graph,
            state or {"plan_id": graph.get("plan_id"), "tasks": {}},
        )
    except deterministic_scheduler.SchedulerError as exc:
        return {"status": "BLOCKED", "reason": str(exc), "authority": dict(AUTHORITY)}
    result["authority"] = dict(AUTHORITY)
    return result


def inspect_payload() -> dict[str, Any]:
    return {
        "server": {"name": "AIPS", "transport": "stdio", "protocol_revision": PROTOCOL_VERSION},
        "capabilities": {"tools": True, "resources": True, "prompts": True},
        "tools": [
            "aips_system_info",
            "aips_project_identity",
            "aips_harness_context",
            "aips_role_skill_bundle",
            "aips_capability_catalog",
            "aips_capability_read",
            "aips_workflow_context",
            "aips_schedule",
        ],
        "resources": {
            "catalogs": [
                "aips://catalog/roles",
                "aips://catalog/skills",
                "aips://catalog/protocols",
            ],
            "templates": [
                "aips://roles/{role_id}",
                "aips://skills/{skill_id}",
                "aips://protocol/{protocol_id}",
            ],
        },
        "prompts": ["security_review", "architecture_review", "code_review", "delivery_plan"],
        "tool_only_compatibility": {
            "catalog": "aips_capability_catalog",
            "read": "aips_capability_read",
            "workflows": "aips_workflow_context",
            "all_tools_read_only": True,
        },
        "clients": list(HOST_COMPATIBILITY),
        "client_compatibility": HOST_COMPATIBILITY,
        "client_registration_managed": False,
        "external_provider_credential_required": False,
        "authority": dict(AUTHORITY),
    }


def config_payload(client: str) -> dict[str, Any]:
    aips = str((ROOT / "bin" / "aips").resolve())
    if client == "cursor":
        return {
            "client": "cursor",
            "automatic_change": False,
            "config": {
                "mcpServers": {
                    "aips": {
                        "type": "stdio",
                        "command": aips,
                        "args": ["mcp", "serve"],
                        "env": {"AIPS_MCP_WORKSPACE": "${workspaceFolder}"},
                    }
                }
            },
            "note": "Review and add this entry to the client-owned MCP configuration; AIPS does not modify it automatically.",
        }
    if client == "windsurf":
        return {
            "client": "windsurf",
            "automatic_change": False,
            "config_path": "~/.codeium/windsurf/mcp_config.json",
            "config": {
                "mcpServers": {
                    "aips": {
                        "command": aips,
                        "args": ["mcp", "serve"],
                        "env": {"AIPS_MCP_WORKSPACE": "/absolute/project/workspace"},
                    }
                }
            },
            "note": "Review the absolute workspace path before adding this entry. MCP remains ADVISORY; use verified Windsurf hooks separately when native pre-tool enforcement is required.",
        }
    if client == "copilot":
        return {
            "client": "copilot",
            "surface": "github-copilot-cli",
            "automatic_change": False,
            "config_path": ".github/mcp.json or .mcp.json",
            "config": {
                "mcpServers": {
                    "aips": {
                        "type": "stdio",
                        "command": aips,
                        "args": ["mcp", "serve"],
                        "env": {"AIPS_MCP_WORKSPACE": "/absolute/project/workspace"},
                        "tools": [
                            "aips_system_info",
                            "aips_project_identity",
                            "aips_harness_context",
                            "aips_role_skill_bundle",
                            "aips_capability_catalog",
                            "aips_capability_read",
                            "aips_workflow_context",
                            "aips_schedule",
                        ],
                    }
                }
            },
            "note": "This local stdio payload targets GitHub Copilot CLI. Copilot cloud/code-review surfaces are tool-only and require an environment where the AIPS command and workspace path exist.",
        }
    if client == "amp":
        return {
            "client": "amp",
            "automatic_change": False,
            "config_path": ".amp/settings.json or ~/.config/amp/settings.json",
            "config": {
                "amp.mcpServers": {
                    "aips": {
                        "command": aips,
                        "args": ["mcp", "serve"],
                        "env": {"AIPS_MCP_WORKSPACE": "/absolute/project/workspace"},
                    }
                }
            },
            "note": "Review the absolute workspace path before adding this entry. Workspace MCP servers require Amp approval before execution.",
        }
    if client == "codex":
        return {
            "client": "codex",
            "automatic_change": False,
            "registration_command": ["codex", "mcp", "add", "aips", "--", aips, "mcp", "serve"],
            "note": "Run from the intended project workspace. Native Codex governance remains ADVISORY unless separately verified.",
        }
    return {
        "client": "generic",
        "automatic_change": False,
        "transport": "stdio",
        "command": aips,
        "args": ["mcp", "serve"],
        "environment": {"AIPS_MCP_WORKSPACE": "/absolute/project/workspace"},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("serve")
    sub.add_parser("inspect")
    config = sub.add_parser("config")
    config.add_argument(
        "--client",
        choices=["cursor", "windsurf", "copilot", "amp", "codex", "generic"],
        default="generic",
    )
    args = parser.parse_args()

    if args.command == "serve":
        mcp.run()
        return 0
    if args.command == "inspect":
        print(json.dumps(inspect_payload(), ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(config_payload(args.client), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
