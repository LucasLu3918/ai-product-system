from __future__ import annotations

import sys
from pathlib import Path

from .static_contracts import ROOT, errors

sys.path.insert(0, str(ROOT))
from scripts.system_facts import read_yaml, validate_facts  # noqa: E402

fact_path = ROOT / "config/system-facts.yaml"
if fact_path.exists():
    errors.extend(validate_facts(ROOT))
    if (ROOT / "docs/human/SYSTEM_REFERENCE.md").is_file():
        import subprocess

        result = subprocess.run([sys.executable, str(ROOT / "scripts/system_facts.py"), "--check"], cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            errors.append("system facts generated reference is stale: " + (result.stdout + result.stderr).strip())
else:
    errors.append("config/system-facts.yaml is required")
