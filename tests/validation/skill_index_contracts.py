"""One owning invocation of the Skill registry lifecycle in repository validation."""

import subprocess
import sys

from .static_contracts import ROOT, errors

result = subprocess.run(
    [sys.executable, str(ROOT / "tests/evidence/skill_index_lifecycle.py")],
    capture_output=True,
    check=False,
    text=True,
)
if result.returncode:
    errors.append("Skill index lifecycle failed: " + result.stdout + result.stderr)
else:
    print(result.stdout.strip())
