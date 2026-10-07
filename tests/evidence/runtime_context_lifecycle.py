#!/usr/bin/env python3
"""Exercise Runtime Context resolution and invariant matrix contracts."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import runtime_context


def main() -> None:
    assert runtime_context.default_validation_venv(ROOT).name.startswith("aips-validation-")
    cases = runtime_context.candidate_python_paths(ROOT, ROOT, {"AIPS_VALIDATION_PYTHON": "/explicit/python", "AIPS_VALIDATION_VENV": "/explicit/venv"})
    assert str(cases[0]) == "/explicit/python"
    assert len(cases) == 1, "explicit Python selection is authoritative; no venv fallback"
    assert str(runtime_context.candidate_python_paths(ROOT, ROOT, {"AIPS_VALIDATION_VENV": "/explicit/venv"})[0]) == "/explicit/venv/bin/python"
    context = runtime_context.collect_runtime_context(ROOT, ROOT, env={"HOME": "/private/home", "XDG_CACHE_HOME": "/private/cache", "XDG_CONFIG_HOME": "/private/config", "GITHUB_TOKEN": "must-not-be-returned"})
    serialized = json.dumps(context, sort_keys=True)
    assert "must-not-be-returned" not in serialized and "GITHUB_TOKEN" not in serialized
    assert context["paths"]["cache_home"] == "/private/cache"
    assert context["capabilities"]["offline"] is False
    assert context["capabilities"]["browser"]["launch_verified"] is False
    assert context["capabilities"]["sandbox"]["status"] == "NOT_PROBED"
    matrix = subprocess.run([sys.executable, str(ROOT / "scripts/runtime_invariant_matrix.py"), "--check"], cwd=ROOT, capture_output=True, text=True, check=True)
    assert "PASS cases=108" in matrix.stdout
    print("runtime_context_lifecycle evidence: PASS")


if __name__ == "__main__":
    main()
