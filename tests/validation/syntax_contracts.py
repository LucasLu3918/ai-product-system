import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from scripts.github_workflow_validation import validate_workflows

from .static_contracts import ROOT, errors, load_yaml, roles, scenarios, skills, version

errors.extend(validate_workflows(ROOT))

shell_paths = ["bin/aips", "scripts/aips_cli.sh", "scripts/bootstrap.sh", "scripts/uninstall.sh", "harness/adapters/gemini-cli/hooks/aips-turn-context.sh", "harness/adapters/gemini-cli/hooks/aips-governance-guard.sh"]
shell_paths.extend(str(path.relative_to(ROOT)) for path in sorted((ROOT / "scripts/aips_cli").glob("*.sh")))
for shell in shell_paths:
    p = ROOT / shell
    if p.exists():
        result = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"Shell syntax failed: {shell}: {result.stderr.strip()}")
