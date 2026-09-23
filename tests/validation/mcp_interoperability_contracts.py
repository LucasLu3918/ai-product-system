import subprocess
import sys

from .static_contracts import ROOT, errors

required = [
    ROOT / "scripts/mcp_server.py",
    ROOT / "harness/MCP_GATEWAY.md",
    ROOT / "tests/scenarios/162-mcp-interoperability-gateway.md",
    ROOT / "tests/evidence/mcp_interoperability_lifecycle.py",
    ROOT / ".github/workflows/mcp-codex-interop.yml",
    ROOT / ".aips/review/V0.52.0_MCP_INTEROPERABILITY_GATEWAY.md",
]
for path in required:
    if not path.exists():
        errors.append(f"Missing v0.52 MCP interoperability artifact: {path.relative_to(ROOT)}")

server = ROOT / "scripts/mcp_server.py"
if server.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(server)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"mcp_server.py syntax failed: {compiled.stderr.strip()}")
    text = server.read_text(encoding="utf-8")
    for marker in (
        "from mcp.server import MCPServer",
        "from mcp.types import ToolAnnotations",
        'PROTOCOL_VERSION = "2026-07-28"',
        "mcp.run()",
        "aips://catalog/roles",
        "aips://roles/{role_id}",
        "aips://skills/{skill_id}",
        "security_review",
        "aips_project_identity",
        "aips_harness_context",
        "aips_role_skill_bundle",
        "aips_capability_catalog",
        "aips_capability_read",
        "aips_workflow_context",
        "aips_schedule",
        "HOST_COMPATIBILITY",
        "client_compatibility",
        "read_only_hint=True",
        "destructive_hint=False",
        "open_world_hint=False",
        "client_registration_managed",
        "host_native_tool_enforcement",
        "semantic_selection_performed",
        "AIPS_MCP_WORKSPACE",
    ):
        if marker not in text:
            errors.append(f"mcp_server.py missing v0.52 contract: {marker}")
    for forbidden in ("git push", "merge_pull_request", "production deploy"):
        if forbidden in text:
            errors.append(f"MCP gateway must not expose protected operation authority: {forbidden}")

requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
if "mcp>=2.0.0,<3" not in requirements:
    errors.append("requirements.txt must pin MCP Python SDK to stable v2 major")

cli = (ROOT / "bin/aips").read_text(encoding="utf-8")
for marker in (
    "aips mcp serve",
    "aips mcp inspect",
    "cursor|windsurf|copilot|amp|codex|generic",
    "mcp_cmd()",
    "mcp)",
):
    if marker not in cli:
        errors.append(f"bin/aips missing MCP CLI contract: {marker}")

adapter_registry = (ROOT / "harness/adapters/REGISTRY.yaml").read_text(encoding="utf-8")
if "mcp-interoperability" in adapter_registry:
    errors.append("MCP access plane must not be misrepresented as a runtime-native adapter")

capability_map = (ROOT / "references/evolution/CAPABILITY_MAP.yaml").read_text(encoding="utf-8")
if "id: mcp-interoperability-gateway" in capability_map:
    errors.append("MCP gateway must reuse turn-aware-global-harness instead of adding a Capability ID")

surfaces = (ROOT / "config/architecture-surfaces.yaml").read_text(encoding="utf-8")
if "harness/MCP_GATEWAY.md" not in surfaces or "scripts/mcp_server.py" not in surfaces or "tests/evidence/mcp_interoperability_lifecycle.py" not in surfaces:
    errors.append("Harness runtime architecture surface missing MCP gateway path/validation binding")

workflow_path = ROOT / ".github/workflows/mcp-codex-interop.yml"
workflow = workflow_path.read_text(encoding="utf-8") if workflow_path.exists() else ""
for marker in ("@openai/codex@0.155.1", "codex mcp add", "codex mcp list", "mcp_interoperability_lifecycle.py"):
    if marker not in workflow:
        errors.append(f"MCP/Codex interoperability workflow missing: {marker}")
for forbidden in ("OPENAI_API_KEY", "GEMINI_API_KEY", "secrets."):
    if forbidden in workflow:
        errors.append(f"MCP/Codex interoperability workflow must be credential-free: {forbidden}")

for client in ("cursor", "windsurf", "copilot", "amp", "codex", "generic"):
    result = subprocess.run(
        [sys.executable, str(server), "config", "--client", client],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        errors.append(f"MCP client configuration failed for {client}: {result.stderr.strip()}")
        continue
    try:
        payload = __import__("json").loads(result.stdout)
    except ValueError as exc:
        errors.append(f"MCP client configuration is not JSON for {client}: {exc}")
        continue
    if payload.get("client") != client or payload.get("automatic_change") is not False:
        errors.append(f"MCP client configuration boundary mismatch for {client}")

evidence = ROOT / "tests/evidence/mcp_interoperability_lifecycle.py"
if evidence.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(evidence)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"MCP interoperability lifecycle syntax failed: {compiled.stderr.strip()}")
    else:
        result = subprocess.run([sys.executable, str(evidence)], capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            errors.append(f"MCP interoperability lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
