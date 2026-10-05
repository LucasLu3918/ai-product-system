#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.system_facts import read_yaml, validate_facts

facts = read_yaml(ROOT / "config/system-facts.yaml")
assert not validate_facts(ROOT, facts)
broken = deepcopy(facts)
broken["commands"].append(deepcopy(broken["commands"][0]))
assert any("unique" in error for error in validate_facts(ROOT, broken))
broken = deepcopy(facts)
broken["commands"][0]["surfaces"] = ["missing-surface"]
assert any("known architecture surfaces" in error for error in validate_facts(ROOT, broken))
broken = deepcopy(facts)
broken["python"]["ci_compatibility_tested"] = ["3.12", "3.12"]
assert any("unique Python versions" in error for error in validate_facts(ROOT, broken))
broken = deepcopy(facts)
broken["python"]["ci_compatibility_tested"] = ["3.11", "3.12"]
assert any("below python.supported" in error for error in validate_facts(ROOT, broken))
first = subprocess.run([sys.executable, str(ROOT / "scripts/system_facts.py"), "--check"], cwd=ROOT, capture_output=True, text=True, check=False)
second = subprocess.run([sys.executable, str(ROOT / "scripts/system_facts.py"), "--check"], cwd=ROOT, capture_output=True, text=True, check=False)
assert first.returncode == second.returncode == 0, first.stdout + first.stderr + second.stdout + second.stderr
print("system facts lifecycle: PASS")
