#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.system_facts import read_yaml, validate_facts  # noqa: E402

facts = read_yaml(ROOT / "config/system-facts.yaml")
assert not validate_facts(ROOT, facts)
broken = deepcopy(facts)
broken["commands"].append(deepcopy(broken["commands"][0]))
assert any("unique" in error for error in validate_facts(ROOT, broken))
broken = deepcopy(facts)
broken["commands"][0]["surfaces"] = ["missing-surface"]
assert any("known architecture surfaces" in error for error in validate_facts(ROOT, broken))
first = subprocess.run([sys.executable, str(ROOT / "scripts/system_facts.py"), "--check"], cwd=ROOT, capture_output=True, text=True)
second = subprocess.run([sys.executable, str(ROOT / "scripts/system_facts.py"), "--check"], cwd=ROOT, capture_output=True, text=True)
assert first.returncode == second.returncode == 0, first.stdout + first.stderr + second.stdout + second.stderr
print("system facts lifecycle: PASS")
