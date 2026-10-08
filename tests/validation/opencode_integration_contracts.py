"""Single owning invocation of the OpenCode integration lifecycle."""
import subprocess
import sys

from .static_contracts import ROOT, errors

plugin = (ROOT / "harness/adapters/opencode/plugin.ts").read_text(encoding="utf-8")
guard = (ROOT / "scripts/opencode_native_guard.py").read_text(encoding="utf-8")
compatibility = (ROOT / "harness/adapters/opencode/COMPATIBILITY.md").read_text(encoding="utf-8")
registry = (ROOT / "harness/adapters/REGISTRY.yaml").read_text(encoding="utf-8")
for marker in ('Plugin.define', 'ctx.session.hook("context"', 'ctx.permission.hook("evaluate"', 'ctx.shell.hook("create.before"'):
    if marker not in plugin:
        errors.append(f"OpenCode V2 plugin is missing documented hook contract: {marker}")
for marker in ('evaluate_write', 'evaluate_shell', 'Project Intelligence readiness is not READY', 'target escapes project root'):
    if marker not in guard:
        errors.append(f"OpenCode native guard is missing decision boundary: {marker}")
if 'pre_tool_guard: AVAILABLE_UNVERIFIED' not in registry or 'remains **ADVISORY**' not in compatibility:
    errors.append("OpenCode guard verification truth or advisory governance was overstated")

result = subprocess.run([sys.executable, str(ROOT / "tests/evidence/opencode_integration_lifecycle.py")], capture_output=True, text=True, check=False)
if result.returncode:
    errors.append("OpenCode integration lifecycle failed: " + result.stdout + result.stderr)
else:
    print(result.stdout.strip())
