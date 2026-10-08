"""Single owning invocation of the OpenCode integration lifecycle."""
import subprocess
import sys

from .static_contracts import ROOT, errors

result = subprocess.run([sys.executable, str(ROOT / "tests/evidence/opencode_integration_lifecycle.py")], capture_output=True, text=True, check=False)
if result.returncode:
    errors.append("OpenCode integration lifecycle failed: " + result.stdout + result.stderr)
else:
    print(result.stdout.strip())
