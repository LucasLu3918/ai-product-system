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


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def init_git(root: Path) -> None:
    git(root, "init", "-q")
    git(root, "config", "user.email", "aips@example.invalid")
    git(root, "config", "user.name", "AIPS Test")
    git(root, "add", ".")
    git(root, "commit", "-qm", "fixture baseline")


def run(root: Path) -> tuple[int, dict]:
    result = subprocess.run(
        [
            sys.executable,
            str(HELPER),
            "audit",
            "--root",
            str(root),
            "--config",
            "config/repository-health.yaml",
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
    )
    return result.returncode, json.loads(result.stdout)


def build_fixture(root: Path) -> str:
    capability_doc = "# Fixture capability\n"
    repository_health_doc = (
        "# Fixture\n\nCanonical surface: scripts/core_guard.py\n"
    )
    write(root / "docs/capability.md", capability_doc)
    write(root / "scripts/core_guard.py", "print('fixture')\n")
    shutil.copy2(
        SCENARIO_HELPER,
        root / "scripts/scenario_conformance.py",
    )
    write(
        root / "orchestration/REPOSITORY_HEALTH.md",
        repository_health_doc,
    )
    write(
        root / "workflow.yml",
        "jobs:\n  repository-validation: true\n",
    )
    write(
        root / "tests/scenarios/001-fixture.md",
        "# Fixture Scenario\n",
    )
    write(
        root / "tests/validate_repository.py",
        "from validation import fixture_contracts\n",
    )
    write(
        root / "tests/validation/fixture_contracts.py",
        "# fixture validation\n",
    )
    write(
        root / "references/evolution/CAPABILITY_MAP.yaml",
        yaml.safe_dump(
            {
                "version": 1,
                "capabilities": [
                    {
                        "id": "fixture-capability",
                        "name_en": "Fixture",
                        "docs": ["docs/capability.md"],
                    }
                ],
            },
            sort_keys=False,
        ),
    )
    write(
        root / "tests/scenario_coverage.yaml",
        yaml.safe_dump(
            {
                "version": 1,
                "policy": {
                    "release_requires": {
                        "no_uncovered": True,
                    }
                },
                "scenarios": [
                    {
                        "id": "001",
                        "path": "tests/scenarios/001-fixture.md",
                        "coverage": "deterministic",
                        "evidence": ["scripts/core_guard.py"],
                    }
                ],
            },
            sort_keys=False,
        ),
    )
    write(
        root / "config/architecture-surfaces.yaml",
        yaml.safe_dump(
            {
                "version": 1,
                "policy": {
                    "capability_accounting": "complete",
                    "validation_binding": (
                        "scenario_or_repository_validator"
                    ),
                },
                "surfaces": [
                    {
                        "id": "fixture",
                        "capabilities": ["fixture-capability"],
                        "required_paths": [
                            "scripts/core_guard.py",
                            "docs/capability.md",
                        ],
                        "canonical_docs": ["docs/capability.md"],
                        "validation_paths": [
                            "scripts/core_guard.py",
                            "tests/validation/fixture_contracts.py",
                        ],
                    }
                ],
            },
            sort_keys=False,
        ),
    )
    write(
        root / "config/repository-health.yaml",
        yaml.safe_dump(
            {
                "version": 1,
                "evidence_binding": {
                    "manifest": "complete",
                    "dirty_workspace": "report_non_reproducible",
                },
                "truth_sources": {
                    "capability_map": (
                        "references/evolution/CAPABILITY_MAP.yaml"
                    ),
                    "architecture_surfaces": (
                        "config/architecture-surfaces.yaml"
                    ),
                    "repository_validator": (
                        "tests/validate_repository.py"
                    ),
                    "scenario_registry": (
                        "tests/scenario_coverage.yaml"
                    ),
                    "scenario_dir": "tests/scenarios",
                    "scenario_helper": (
                        "scripts/scenario_conformance.py"
                    ),
                },
                "surface_discovery": {
                    "patterns": ["scripts/*_guard.py"],
                    "ignore": [],
                },
                "documentation_bindings": [
                    {
                        "source": (
                            "orchestration/REPOSITORY_HEALTH.md"
                        ),
                        "required_references": [
                            "scripts/core_guard.py"
                        ],
                    }
                ],
                "contract_files": [
                    {
                        "path": "workflow.yml",
                        "required_strings": [
                            "repository-validation"
                        ],
                    }
                ],
            },
            sort_keys=False,
        ),
    )
    return repository_health_doc


with tempfile.TemporaryDirectory(
    prefix="aips-repository-health-"
) as tmp:
    fixture = Path(tmp)
    baseline_health_doc = build_fixture(fixture)
    init_git(fixture)

    code1, report1 = run(fixture)
    code2, report2 = run(fixture)
    assert code1 == 0 and report1["status"] == "PASS", report1
    assert code2 == 0 and report2 == report1, (
        report1,
        report2,
    )

    workspace = report1["workspace"]
    binding = report1["evidence_binding"]
    manifest = report1["inputs"]["manifest"]
    manifest_paths = {
        item["path"] for item in manifest["entries"]
    }

    assert workspace["git_available"] is True
    assert workspace["dirty"] is False
    assert workspace["dirty_paths"] == []
    assert binding["status"] == "EXACT_REVISION"
    assert binding["revision_reproducible"] is True
    assert binding["input_manifest_digest"] == manifest["digest"]
    assert binding["evidence_fingerprint"].startswith("sha256:")
    assert manifest["count"] == len(manifest["entries"])
    assert {
        "config/repository-health.yaml",
        "config/architecture-surfaces.yaml",
        "references/evolution/CAPABILITY_MAP.yaml",
        "tests/validate_repository.py",
        "tests/validation/fixture_contracts.py",
        "scripts/scenario_conformance.py",
        "scripts/core_guard.py",
        "docs/capability.md",
        "orchestration/REPOSITORY_HEALTH.md",
        "workflow.yml",
        "tests/scenarios/001-fixture.md",
        "tests/scenario_coverage.yaml",
    }.issubset(manifest_paths)

    architecture = report1["architecture_surfaces"]
    assert architecture["surface_count"] == 1
    assert architecture["capability_count"] == 1
    assert architecture["capability_accounted"] == 1
    assert architecture["unclassified_capabilities"] == []
    assert architecture["validation_path_count"] == 2

    assert report1["execution"]["credential_required"] is False
    assert report1["execution"]["external_network_required"] is False
    assert (
        report1["execution"]["automatic_remediation_performed"]
        is False
    )
    assert all(
        value is False
        for value in report1["authority"].values()
    )

    write(
        fixture / "orchestration/REPOSITORY_HEALTH.md",
        baseline_health_doc
        + "\nEvidence binding remains deterministic.\n",
    )
    dirty_code, dirty_report = run(fixture)
    assert dirty_code == 0
    assert dirty_report["status"] == "PASS"
    assert dirty_report["workspace"]["dirty"] is True
    assert (
        "orchestration/REPOSITORY_HEALTH.md"
        in dirty_report["workspace"]["dirty_paths"]
    )
    assert (
        dirty_report["evidence_binding"]["status"]
        == "DIRTY_WORKTREE"
    )
    assert (
        dirty_report["evidence_binding"][
            "revision_reproducible"
        ]
        is False
    )
    assert (
        dirty_report["inputs"]["manifest"]["digest"]
        != manifest["digest"]
    )
    assert (
        dirty_report["evidence_binding"][
            "evidence_fingerprint"
        ]
        != binding["evidence_fingerprint"]
    )

    write(
        fixture / "orchestration/REPOSITORY_HEALTH.md",
        baseline_health_doc,
    )
    clean_code, clean_report = run(fixture)
    assert clean_code == 0
    assert clean_report == report1

    (fixture / "docs/capability.md").unlink()
    code, report = run(fixture)
    assert code != 0
    assert report["drift"]["missing_capability_targets"]
    missing_entry = next(
        item
        for item in report["inputs"]["manifest"]["entries"]
        if item["path"] == "docs/capability.md"
    )
    assert missing_entry["exists"] is False
    assert missing_entry["digest"] is None
    write(
        fixture / "docs/capability.md",
        "# Fixture capability\n",
    )

    capability_map = yaml.safe_load(
        (
            fixture / "references/evolution/CAPABILITY_MAP.yaml"
        ).read_text(encoding="utf-8")
    )
    capability_map["capabilities"].append(
        {
            "id": "unclassified-capability",
            "name_en": "Unclassified",
            "docs": ["docs/capability.md"],
        }
    )
    write(
        fixture / "references/evolution/CAPABILITY_MAP.yaml",
        yaml.safe_dump(capability_map, sort_keys=False),
    )
    code, report = run(fixture)
    assert code != 0
    assert any(
        "unclassified-capability" in item
        for item in report["drift"]["architecture_surface_drift"]
    )
    capability_map["capabilities"].pop()
    write(
        fixture / "references/evolution/CAPABILITY_MAP.yaml",
        yaml.safe_dump(capability_map, sort_keys=False),
    )

    inventory = yaml.safe_load(
        (
            fixture / "config/architecture-surfaces.yaml"
        ).read_text(encoding="utf-8")
    )
    inventory["surfaces"][0]["required_paths"].append(
        "scripts/missing_surface.py"
    )
    write(
        fixture / "config/architecture-surfaces.yaml",
        yaml.safe_dump(inventory, sort_keys=False),
    )
    code, report = run(fixture)
    assert code != 0
    assert any(
        "missing_surface.py" in item
        for item in report["drift"]["architecture_surface_drift"]
    )
    inventory["surfaces"][0]["required_paths"].pop()
    write(
        fixture / "config/architecture-surfaces.yaml",
        yaml.safe_dump(inventory, sort_keys=False),
    )

    write(
        fixture / "tests/evidence/unbound_validation.py",
        "# not registered\n",
    )
    inventory["surfaces"][0]["validation_paths"].append(
        "tests/evidence/unbound_validation.py"
    )
    write(
        fixture / "config/architecture-surfaces.yaml",
        yaml.safe_dump(inventory, sort_keys=False),
    )
    code, report = run(fixture)
    assert code != 0
    assert any(
        "unbound_validation.py" in item
        for item in report["drift"]["architecture_surface_drift"]
    )
    inventory["surfaces"][0]["validation_paths"].pop()
    write(
        fixture / "config/architecture-surfaces.yaml",
        yaml.safe_dump(inventory, sort_keys=False),
    )
    (fixture / "tests/evidence/unbound_validation.py").unlink()

    write(
        fixture / "scripts/orphan_guard.py",
        "print('orphan')\n",
    )
    code, report = run(fixture)
    assert code != 0
    assert any(
        "orphan_guard.py" in item
        for item in report["drift"][
            "orphan_capability_surfaces"
        ]
    )
    (fixture / "scripts/orphan_guard.py").unlink()

    write(fixture / "workflow.yml", "jobs: {}\n")
    code, report = run(fixture)
    assert code != 0
    assert report["drift"]["workflow_contract_drift"]
    write(
        fixture / "workflow.yml",
        "jobs:\n  repository-validation: true\n",
    )

    coverage = yaml.safe_load(
        (
            fixture / "tests/scenario_coverage.yaml"
        ).read_text(encoding="utf-8")
    )
    coverage["scenarios"][0]["evidence"] = [
        "scripts/missing.py"
    ]
    write(
        fixture / "tests/scenario_coverage.yaml",
        yaml.safe_dump(coverage, sort_keys=False),
    )
    code, report = run(fixture)
    assert code != 0
    assert report["drift"]["scenario_evidence_drift"]
    missing_evidence = next(
        item
        for item in report["inputs"]["manifest"]["entries"]
        if item["path"] == "scripts/missing.py"
    )
    assert missing_evidence["exists"] is False

print("repository_health_lifecycle=PASS")
