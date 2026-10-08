"""Contract checks for the local-only character artwork workflow."""

import subprocess
import sys

from .static_contracts import ROOT, errors

required = (
    ROOT / "scripts/character_artifacts.py",
    ROOT / "tests/evidence/character_artifacts_lifecycle.py",
    ROOT / "templates/creative/CHARACTER_PROFILE.yaml",
    ROOT / "templates/creative/STYLE_PROFILE.yaml",
    ROOT / "templates/creative/CHARACTER_ARTWORK_MANIFEST.yaml",
    ROOT / "orchestration/CREATIVE_DIRECTION.md",
)
for path in required:
    if not path.is_file():
        errors.append(f"Missing character artwork artifact: {path.relative_to(ROOT)}")

if all(path.is_file() for path in required):
    compile_result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(required[0]), str(required[1])],
        capture_output=True,
        text=True,
        check=False,
    )
    if compile_result.returncode:
        errors.append(
            "Character artwork syntax failed: " + compile_result.stderr.strip()
        )
    else:
        lifecycle = subprocess.run(
            [sys.executable, str(required[1])],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if lifecycle.returncode:
            errors.append(
                "Character artwork lifecycle failed: "
                + lifecycle.stdout
                + lifecycle.stderr
            )
        else:
            print(lifecycle.stdout.strip())
