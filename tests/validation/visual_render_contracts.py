import subprocess
import sys

from .static_contracts import ROOT, errors

visual_render_evidence = ROOT / "tests/evidence/visual_render_lifecycle.py"
visual_dependency = ROOT / "requirements-visual.txt"

for required in (visual_render_evidence, visual_dependency):
    if not required.exists():
        errors.append(f"Missing visual render lifecycle artifact: {required.relative_to(ROOT)}")

if visual_render_evidence.exists():
    compiled = subprocess.run(
        [sys.executable, "-m", "py_compile", str(visual_render_evidence)],
        capture_output=True,
        text=True,
    )
    if compiled.returncode != 0:
        errors.append(f"Visual render lifecycle syntax failed: {compiled.stderr.strip()}")
    else:
        focused = subprocess.run(
            [sys.executable, str(visual_render_evidence)],
            capture_output=True,
            text=True,
        )
        if focused.returncode != 0:
            errors.append(
                f"Visual render lifecycle evidence failed: {focused.stdout.strip()} {focused.stderr.strip()}"
            )
