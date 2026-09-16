from pathlib import Path
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import yaml

from .static_contracts import ROOT, errors, load_yaml, roles, skills, scenarios, version

for shell in ("bin/aips", "scripts/bootstrap.sh", "scripts/uninstall.sh", "harness/adapters/gemini-cli/hooks/aips-turn-context.sh", "harness/adapters/gemini-cli/hooks/aips-governance-guard.sh"):
    p = ROOT / shell
    if p.exists():
        result = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"Shell syntax failed: {shell}: {result.stderr.strip()}")
