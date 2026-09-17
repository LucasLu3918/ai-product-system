from pathlib import Path
import subprocess
import sys

from .static_contracts import ROOT, errors

required = (
    ROOT / "orchestration/EVOLUTION_RADAR.md",
    ROOT / "config/evolution-sources.yaml",
    ROOT / "templates/evolution/EVOLUTION_RADAR.yaml",
    ROOT / "scripts/evolution_radar.py",
    ROOT / "scripts/evolution_radar_rollup.py",
    ROOT / ".github/workflows/evolution-radar.yml",
    ROOT / "tests/evidence/evolution_radar_lifecycle.py",
)
for path in required:
    if not path.exists():
        errors.append(f"Missing Evolution Radar artifact: {path.relative_to(ROOT)}")

for path in (
    ROOT / "scripts/evolution_radar.py",
    ROOT / "scripts/evolution_radar_rollup.py",
    ROOT / "tests/evidence/evolution_radar_lifecycle.py",
):
    if not path.exists():
        continue
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Evolution Radar syntax failed: {path.relative_to(ROOT)}: {compiled.stderr.strip()}")

config_check = ROOT / "scripts/evolution_radar.py"
if config_check.exists():
    result = subprocess.run(
        [sys.executable, str(config_check), "validate-config", "--config", str(ROOT / "config/evolution-sources.yaml")],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        errors.append(f"Evolution Radar source config failed: {result.stdout.strip()} {result.stderr.strip()}")

lifecycle = ROOT / "tests/evidence/evolution_radar_lifecycle.py"
if lifecycle.exists():
    try:
        result = subprocess.run([sys.executable, str(lifecycle)], capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        errors.append("Evolution Radar lifecycle timed out after 45 seconds")
    else:
        if result.returncode != 0:
            errors.append(f"Evolution Radar lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
