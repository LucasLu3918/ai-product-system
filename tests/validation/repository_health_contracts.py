from __future__ import annotations
import json
import subprocess
import sys
from .static_contracts import ROOT, errors

required = (
    ROOT / "config/repository-health.yaml",
    ROOT / "scripts/repository_health.py",
    ROOT / "orchestration/REPOSITORY_HEALTH.md",
    ROOT / "tests/evidence/repository_health_lifecycle.py",
    ROOT / "tests/scenarios/147-repository-health-architecture-drift.md",
)
for path in required:
    if not path.exists():
        errors.append(f"Missing Repository Health artifact: {path.relative_to(ROOT)}")

script = ROOT / "scripts/repository_health.py"
if script.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(script)], capture_output=True, text=True)
    if compiled.returncode:
        errors.append(f"Repository Health syntax failed: {compiled.stderr.strip()}")
    else:
        result = subprocess.run([sys.executable, str(script), "audit", "--format", "json"],
                                cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            errors.append(f"Repository Health baseline drift detected: {result.stdout.strip()} {result.stderr.strip()}")
        else:
            report = json.loads(result.stdout)
            if report.get("status") != "PASS":
                errors.append("Repository Health baseline must PASS")
            for key, findings in (report.get("drift") or {}).items():
                if findings:
                    errors.append(f"Repository Health {key} must be empty on baseline")
            execution = report.get("execution") or {}
            for key in ("credential_required", "external_network_required", "automatic_remediation_performed"):
                if execution.get(key) is not False:
                    errors.append(f"Repository Health execution.{key} must remain false")
            authority = report.get("authority") or {}
            for key in ("automatic_remediation_authorized", "code_change_authorized",
                        "branch_or_pr_authorized", "merge_authorized",
                        "release_authorized", "publication_authorized"):
                if authority.get(key) is not False:
                    errors.append(f"Repository Health authority.{key} must remain false")

lifecycle = ROOT / "tests/evidence/repository_health_lifecycle.py"
if lifecycle.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(lifecycle)], capture_output=True, text=True)
    if compiled.returncode:
        errors.append(f"Repository Health lifecycle syntax failed: {compiled.stderr.strip()}")
    else:
        result = subprocess.run([sys.executable, str(lifecycle)], cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            errors.append(f"Repository Health lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
