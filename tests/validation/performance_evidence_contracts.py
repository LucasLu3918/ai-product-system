import subprocess
import sys

from .static_contracts import ROOT, errors

performance_helper = ROOT / "scripts/performance_evidence.py"
performance_evidence = ROOT / "tests/evidence/performance_evidence_lifecycle.py"
performance_template = ROOT / "templates/performance/PERFORMANCE_EVIDENCE.yaml"

for required in (performance_helper, performance_evidence, performance_template):
    if not required.exists():
        errors.append(f"Missing performance evidence artifact: {required.relative_to(ROOT)}")
        continue
    if required.suffix == ".py":
        compiled = subprocess.run(
            [sys.executable, "-m", "py_compile", str(required)],
            capture_output=True,
            text=True,
        )
        if compiled.returncode != 0:
            errors.append(
                f"Performance evidence syntax failed: {required.relative_to(ROOT)}: {compiled.stderr.strip()}"
            )

if performance_evidence.exists():
    try:
        focused = subprocess.run(
            [sys.executable, str(performance_evidence)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        errors.append("Performance evidence lifecycle timed out after 30 seconds")
    else:
        if focused.returncode != 0:
            errors.append(
                f"Performance evidence lifecycle failed: {focused.stdout.strip()} {focused.stderr.strip()}"
            )
