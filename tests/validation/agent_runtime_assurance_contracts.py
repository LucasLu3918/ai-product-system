from pathlib import Path
import subprocess
import sys

from .static_contracts import ROOT, errors

required = (
    ROOT / "scripts/agent_assurance.py",
    ROOT / "orchestration/AGENT_RUNTIME_ASSURANCE.md",
    ROOT / "tests/evidence/agent_runtime_assurance_lifecycle.py",
    ROOT / "tests/scenarios/139-agent-runtime-anomaly-evidence.md",
    ROOT / "tests/scenarios/140-semantic-intent-governance.md",
)
for path in required:
    if not path.exists():
        errors.append(f"Missing Agent Runtime Assurance artifact: {path.relative_to(ROOT)}")

for path in (ROOT / "scripts/agent_assurance.py", ROOT / "tests/evidence/agent_runtime_assurance_lifecycle.py"):
    if path.exists():
        compiled = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True)
        if compiled.returncode != 0:
            errors.append(f"Agent Runtime Assurance syntax failed: {path.relative_to(ROOT)}: {compiled.stderr.strip()}")

evidence = ROOT / "tests/evidence/agent_runtime_assurance_lifecycle.py"
if evidence.exists():
    result = subprocess.run([sys.executable, str(evidence)], capture_output=True, text=True)
    if result.returncode != 0:
        errors.append(f"Agent Runtime Assurance lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")

doc = (ROOT / "orchestration/AGENT_RUNTIME_ASSURANCE.md").read_text(encoding="utf-8") if (ROOT / "orchestration/AGENT_RUNTIME_ASSURANCE.md").exists() else ""
for phrase in ("can only narrow existing permission", "automatic_remediation=false", "POST_EXECUTION_EVIDENCE"):
    if phrase not in doc:
        errors.append(f"Agent Runtime Assurance contract missing phrase: {phrase}")

script_doc = (ROOT / "scripts/agent_assurance.py").read_text(encoding="utf-8") if (ROOT / "scripts/agent_assurance.py").exists() else ""
for phrase in ('secret_findings(declared_intent)', '"events_fingerprint": digest(events_doc)', '"runtime_enforced": False'):
    if phrase not in script_doc:
        errors.append(f"Agent Runtime Assurance implementation contract missing phrase: {phrase}")
