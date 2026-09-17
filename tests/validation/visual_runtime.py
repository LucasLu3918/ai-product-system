from pathlib import Path
import subprocess
import sys

from .static_contracts import ROOT, errors

capture_helper = ROOT / "scripts" / "visual_capture.py"
review_helper = ROOT / "scripts" / "visual_consistency_review.py"
render_evidence = ROOT / "tests" / "evidence" / "visual_render_capture_lifecycle.py"

for required in (capture_helper, review_helper, render_evidence):
    if not required.exists():
        errors.append(f"Missing real visual render artifact: {required.relative_to(ROOT)}")
    else:
        compiled = subprocess.run(
            [sys.executable, "-m", "py_compile", str(required)],
            capture_output=True,
            text=True,
        )
        if compiled.returncode != 0:
            errors.append(
                f"Real visual render artifact syntax failed: {required.relative_to(ROOT)}: {compiled.stderr.strip()}"
            )

if render_evidence.exists():
    focused = subprocess.run(
        [sys.executable, str(render_evidence)],
        capture_output=True,
        text=True,
    )
    if focused.returncode != 0:
        errors.append(
            f"Real visual render/capture lifecycle evidence failed: {focused.stdout.strip()} {focused.stderr.strip()}"
        )
