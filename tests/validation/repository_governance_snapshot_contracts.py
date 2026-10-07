from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
script = ROOT / "scripts/repository_governance_snapshot.py"
evidence = ROOT / "tests/evidence/repository_governance_snapshot_lifecycle.py"
for path in (script, evidence):
    result = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True, check=False)
    if result.returncode:
        raise SystemExit(result.stderr)
source = script.read_text(encoding="utf-8")
for required in ('["gh", "api", endpoint]', '"--paginate"', '"--slurp"', '"api_write_performed": False'):
    if required not in source:
        raise SystemExit(f"governance snapshot contract missing: {required}")
result = subprocess.run([sys.executable, str(evidence)], capture_output=True, text=True, check=False)
if result.returncode:
    raise SystemExit(result.stdout + result.stderr)
print(result.stdout.strip())
