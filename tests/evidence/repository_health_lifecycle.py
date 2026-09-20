from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts/repository_health.py"
SCENARIO_HELPER = ROOT / "scripts/scenario_conformance.py"

def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def run(root: Path) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(HELPER), "audit", "--root", str(root),
         "--config", "config/repository-health.yaml", "--format", "json"],
        capture_output=True, text=True,
    )
    return result.returncode, json.loads(result.stdout)

def build_fixture(root: Path) -> None:
    write(root / "docs/capability.md", "# Fixture capability\n")
    write(root / "scripts/core_guard.py", "print('fixture')\n")
    shutil.copy2(SCENARIO_HELPER, root / "scripts/scenario_conformance.py")
    write(root / "orchestration/REPOSITORY_HEALTH.md", "# Fixture\n\nCanonical surface: scripts/core_guard.py\n")
    write(root / "workflow.yml", "jobs:\n  repository-validation: true\n")
    write(root / "tests/scenarios/001-fixture.md", "# Fixture Scenario\n")
    write(root / "references/evolution/CAPABILITY_MAP.yaml", yaml.safe_dump({
        "version": 1, "capabilities": [{"id": "fixture-capability", "name_en": "Fixture",
                                       "docs": ["docs/capability.md"]}]}, sort_keys=False))
    write(root / "tests/scenario_coverage.yaml", yaml.safe_dump({
        "version": 1, "policy": {"release_requires": {"no_uncovered": True}},
        "scenarios": [{"id": "001", "path": "tests/scenarios/001-fixture.md",
                       "coverage": "deterministic", "evidence": ["scripts/core_guard.py"]}]}, sort_keys=False))
    write(root / "config/repository-health.yaml", yaml.safe_dump({
        "version": 1,
        "truth_sources": {
            "capability_map": "references/evolution/CAPABILITY_MAP.yaml",
            "scenario_registry": "tests/scenario_coverage.yaml",
            "scenario_dir": "tests/scenarios",
            "scenario_helper": "scripts/scenario_conformance.py",
        },
        "capability_surfaces": {"fixture-capability": {"required": ["scripts/core_guard.py", "docs/capability.md"]}},
        "surface_discovery": {"patterns": ["scripts/*_guard.py"], "ignore": []},
        "documentation_bindings": [{"source": "orchestration/REPOSITORY_HEALTH.md",
                                    "required_references": ["scripts/core_guard.py"]}],
        "contract_files": [{"path": "workflow.yml", "required_strings": ["repository-validation"]}],
    }, sort_keys=False))

with tempfile.TemporaryDirectory(prefix="aips-repository-health-") as tmp:
    fixture = Path(tmp)
    build_fixture(fixture)
    code1, report1 = run(fixture)
    code2, report2 = run(fixture)
    assert code1 == 0 and report1["status"] == "PASS", report1
    assert code2 == 0 and report2 == report1, (report1, report2)
    assert report1["execution"]["credential_required"] is False
    assert report1["execution"]["external_network_required"] is False
    assert report1["execution"]["automatic_remediation_performed"] is False
    assert all(value is False for value in report1["authority"].values())

    (fixture / "docs/capability.md").unlink()
    code, report = run(fixture)
    assert code != 0 and report["drift"]["missing_capability_targets"], report
    write(fixture / "docs/capability.md", "# Fixture capability\n")

    write(fixture / "scripts/orphan_guard.py", "print('orphan')\n")
    code, report = run(fixture)
    assert code != 0 and any("orphan_guard.py" in item for item in report["drift"]["orphan_capability_surfaces"]), report
    (fixture / "scripts/orphan_guard.py").unlink()

    write(fixture / "workflow.yml", "jobs: {}\n")
    code, report = run(fixture)
    assert code != 0 and report["drift"]["workflow_contract_drift"], report
    write(fixture / "workflow.yml", "jobs:\n  repository-validation: true\n")

    coverage = yaml.safe_load((fixture / "tests/scenario_coverage.yaml").read_text(encoding="utf-8"))
    coverage["scenarios"][0]["evidence"] = ["scripts/missing.py"]
    write(fixture / "tests/scenario_coverage.yaml", yaml.safe_dump(coverage, sort_keys=False))
    code, report = run(fixture)
    assert code != 0 and report["drift"]["scenario_evidence_drift"], report

print("repository_health_lifecycle=PASS")
