#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "tests/evidence/project_intelligence_reconciliation_lifecycle.py"
text = path.read_text(encoding="utf-8")
old_a = '                "source": "AGENTS.md",\n                "authority": "project_instruction",\n                "scope": "services/payments",\n                "material": True,\n            },\n            {\n                "id": "deploy-b",\n                "key": "deployment.mode",\n                "value": "automatic",\n                "source": "runtime-native",'
new_a = '                "source": "policy-a",\n                "authority": "project_instruction",\n                "scope": "services/payments",\n                "material": True,\n            },\n            {\n                "id": "deploy-b",\n                "key": "deployment.mode",\n                "value": "automatic",\n                "source": "policy-b",'
if old_a not in text:
    raise RuntimeError("deployment conflict fixture marker missing")
path.write_text(text.replace(old_a, new_a, 1), encoding="utf-8")
print("v0.18.0 reconciliation fixture correction: APPLIED")
