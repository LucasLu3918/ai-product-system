"""Single owning invocation of the OpenCode integration lifecycle."""
import subprocess
import sys

from .static_contracts import ROOT, errors

plugin = (ROOT / "harness/adapters/opencode/plugin.ts").read_text(encoding="utf-8")
guard = (ROOT / "scripts/opencode_native_guard.py").read_text(encoding="utf-8")
compatibility = (ROOT / "harness/adapters/opencode/COMPATIBILITY.md").read_text(encoding="utf-8")
registry = (ROOT / "harness/adapters/REGISTRY.yaml").read_text(encoding="utf-8")
projection = (ROOT / "scripts/opencode_skill_projection.py").read_text(encoding="utf-8")
diagnostics = (ROOT / "harness/adapters/opencode/context_diagnostics.mjs").read_text(encoding="utf-8")
for marker in ('export default {', 'ctx.session.hook("prompt"', 'ctx.session.hook("context"', 'creativeAdmissions', 'creative_admission_grant_missing', 'ctx.permission.hook("evaluate"', 'ctx.shell.hook("create.before"', 'ctx.session.get({ sessionID })', 'MAX_CONTEXT_BYTES', 'creative_workspace_profile.py', 'generate-set'):
    if marker not in plugin:
        errors.append(f"OpenCode V2 plugin is missing documented hook contract: {marker}")
if "spawnSync" in plugin or "const result = await invokeAsync" not in plugin or "contextCacheTtlMs" not in plugin or "signal?.aborted" not in plugin or 'host_version_acceptance: "UNVERIFIED"' not in plugin:
    errors.append("OpenCode native subprocesses must be asynchronous, bounded, cancellable, short-cache scoped and explicit about host-version acceptance")
for marker in ('duration_ms:', 'host_capability', 'permission_enforcement:', 'host_version_acceptance:'):
    if marker not in plugin:
        errors.append(f"OpenCode bounded latency/host evidence is missing: {marker}")
for marker in ('evaluate_write', 'evaluate_shell', 'Project Intelligence readiness is not READY', 'READY Project Intelligence is stale but advisory', 'target escapes project root'):
    if marker not in guard:
        errors.append(f"OpenCode native guard is missing decision boundary: {marker}")
if 'hook_execution": "UNVERIFIED"' not in projection or 'pre_tool_guard: AVAILABLE_UNVERIFIED' not in registry or 'remains **ADVISORY**' not in compatibility or 'MCP/custom tools' not in compatibility:
    errors.append("OpenCode guard verification truth or advisory governance was overstated")
for marker in ("context_compaction_over_budget", "context_original_bytes", "context_projection_bytes", "context_largest_sections", "formatContextFailure"):
    if marker not in plugin and marker not in diagnostics:
        errors.append(f"OpenCode over-budget context diagnosis is missing: {marker}")
if "harness/adapters/opencode/context_diagnostics.mjs" not in plugin or "const contextDiagnostics = await import(pathToFileURL" not in plugin or "const contextBudget = entry.manifest ? compactManifest(entry.manifest) : null" not in plugin or "contextBudget?.reasonCode" not in plugin or plugin.index("contextBudget?.reasonCode") > plugin.index('await invokeGuard(python, guard, "write"'):
    errors.append("OpenCode native file permissions must deny irreducible Context projection overflow before evaluating the manifest")

result = subprocess.run([sys.executable, str(ROOT / "tests/evidence/opencode_integration_lifecycle.py")], capture_output=True, text=True, check=False)
if result.returncode:
    errors.append("OpenCode integration lifecycle failed: " + result.stdout + result.stderr)
else:
    print(result.stdout.strip())
