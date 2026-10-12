"""Own the public Skill-list CLI lifecycle contract."""

import subprocess
import sys

from .static_contracts import ROOT, errors

evidence = ROOT / "tests/evidence/skills_cli_lifecycle.py"
if not evidence.is_file():
    errors.append("Skill CLI lifecycle evidence is missing")
else:
    result = subprocess.run(
        [sys.executable, str(evidence)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        errors.append("Skill CLI lifecycle failed: " + result.stdout + result.stderr)
