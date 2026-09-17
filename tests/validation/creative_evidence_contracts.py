import subprocess
import sys

from .static_contracts import ROOT, errors

creative_helper = ROOT / "scripts/creative_evidence.py"
creative_lifecycle = ROOT / "tests/evidence/creative_render_lifecycle.py"
creative_template = ROOT / "templates/creative/CREATIVE_EVIDENCE.yaml"

for required in (creative_helper, creative_lifecycle, creative_template):
    if not required.exists():
        errors.append(f"Missing creative evidence artifact: {required.relative_to(ROOT)}")
        continue
    if required.suffix == ".py":
        compiled = subprocess.run(
            [sys.executable, "-m", "py_compile", str(required)],
            capture_output=True,
            text=True,
        )
        if compiled.returncode != 0:
            errors.append(
                f"Creative evidence syntax failed: {required.relative_to(ROOT)}: {compiled.stderr.strip()}"
            )

if creative_lifecycle.exists():
    try:
        focused = subprocess.run(
            [sys.executable, str(creative_lifecycle)],
            capture_output=True,
            text=True,
            timeout=45,
        )
    except subprocess.TimeoutExpired:
        errors.append("Creative render lifecycle timed out after 45 seconds")
    else:
        if focused.returncode != 0:
            errors.append(
                f"Creative render lifecycle failed: {focused.stdout.strip()} {focused.stderr.strip()}"
            )
