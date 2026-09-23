from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from .static_contracts import ROOT, errors
except ImportError:
    from static_contracts import ROOT, errors

registry = ROOT / "harness/commands/REGISTRY.yaml"
script = ROOT / "scripts/portable_commands.py"
doc = ROOT / "harness/PORTABLE_COMMANDS.md"
for path in (registry, script, doc):
    if not path.is_file():
        errors.append(f"Portable Command artifact missing: {path.relative_to(ROOT)}")

if script.is_file():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(script)], cwd=ROOT, capture_output=True, text=True)
    if compiled.returncode:
        errors.append(f"portable_commands.py syntax failed: {compiled.stderr.strip()}")
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, XDG_CONFIG_HOME=tmp)
        listed = subprocess.run([sys.executable, str(script), "list", "--format", "json"], cwd=ROOT, env=env, capture_output=True, text=True)
        if listed.returncode or "aips.plan" not in listed.stdout:
            errors.append(f"portable command list failed: {listed.stdout} {listed.stderr}")
        installed = subprocess.run([sys.executable, str(script), "install", "aips.plan", "--host", "generic", "--format", "json"], cwd=ROOT, env=env, capture_output=True, text=True)
        if installed.returncode:
            errors.append(f"portable command install failed: {installed.stdout} {installed.stderr}")
        path = Path(tmp) / "aips" / "commands" / "projections" / "generic" / "aips-plan.md"
        if not path.is_file():
            errors.append("portable command install did not create an owned projection")
        else:
            path.write_text(path.read_text(encoding="utf-8") + "\nuser edit\n", encoding="utf-8")
            status = subprocess.run([sys.executable, str(script), "status", "--format", "json"], cwd=ROOT, env=env, capture_output=True, text=True)
            if status.returncode or "CONFLICT" not in status.stdout:
                errors.append("modified portable projection was not detected as CONFLICT")
