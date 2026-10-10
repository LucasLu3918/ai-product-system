"""One owning invocation for Plan27 regression evidence."""
from __future__ import annotations

import subprocess
import sys

from .static_contracts import ROOT, errors

result = subprocess.run([sys.executable, str(ROOT / "tests/evidence/plan27_lifecycle.py")],
                        cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
if result.returncode:
    errors.append(f"Plan27 lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
