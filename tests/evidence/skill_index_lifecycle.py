"""Executable compatibility and failure-path evidence for canonical Skill metadata."""

import copy
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from skill_index import generate, render


def fixture(root, meta, name="one"):
    path = root / "skills" / name / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n# Body\n")
    return path


def main():
    current = yaml.safe_load((ROOT / "skills/INDEX.yaml").read_text())
    assert generate(ROOT) == current
    assert render(ROOT) == (ROOT / "skills/INDEX.yaml").read_text()
    assert render(ROOT) == render(ROOT)
    for meta in current["skills"].values():
        assert set(meta) == {
            "capability",
            "path",
            "triggers",
            "cost",
            "model_requirements",
        }
        assert (ROOT / "skills" / meta["path"]).is_file()
    first_id, first = next(iter(current["skills"].items()))
    meta = {
        "id": first_id,
        "capability": first["capability"],
        "estimated_context_cost": first["cost"],
        "triggers": first["triggers"],
        "model_requirements": first["model_requirements"],
    }
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = fixture(root, meta)
        target = root / "skills/INDEX.yaml"
        target.write_text(render(root))
        command = [
            sys.executable,
            str(ROOT / "scripts/skill_index.py"),
            "--root",
            str(root),
        ]
        assert subprocess.run(command, capture_output=True, check=False).returncode == 0
        before = target.read_bytes()
        source.write_text(
            source.read_text().replace("triggers:", "triggers:\n- new_trigger", 1)
        )
        assert subprocess.run(command, capture_output=True, check=False).returncode != 0
        assert target.read_bytes() == before
        assert (
            subprocess.run(
                command + ["--write"], capture_output=True, check=False
            ).returncode
            == 0
        )
        assert subprocess.run(command, capture_output=True, check=False).returncode == 0
        fixture(root, meta, "duplicate")
        try:
            generate(root)
            raise AssertionError("duplicate id accepted")
        except (ValueError, TypeError):
            pass
        (root / "skills/duplicate/SKILL.md").unlink()
        invalids = [
            {"applies_when": ["legacy"]},
            {"triggers": []},
            {"triggers": ["x", "x"]},
            {"model_requirements": {}},
            {
                "model_requirements": {
                    **meta["model_requirements"],
                    "minimum_tier": True,
                }
            },
            {
                "model_requirements": {
                    **meta["model_requirements"],
                    "minimum_tier": 4,
                    "preferred_tier": 1,
                }
            },
        ]
        for changes in invalids:
            fixture(root, {**copy.deepcopy(meta), **changes})
            try:
                generate(root)
                raise AssertionError("invalid metadata accepted")
            except (ValueError, TypeError):
                pass
        fixture(root, meta)
        source.write_text(
            source.read_text().replace("capability:", "id: duplicate\ncapability:", 1)
        )
        try:
            generate(root)
            raise AssertionError("duplicate key accepted")
        except (ValueError, TypeError):
            pass
        source.unlink()
        outside = root / "outside.md"
        outside.write_text("---\nid: escape\n---\n")
        source.symlink_to(outside)
        assert (
            subprocess.run(
                command + ["--write"], capture_output=True, check=False
            ).returncode
            != 0
        )
        source.unlink()
        fixture(root, meta)
        target.unlink()
        target.symlink_to(outside)
        assert (
            subprocess.run(
                command + ["--write"], capture_output=True, check=False
            ).returncode
            != 0
        )
        assert outside.read_text() == "---\nid: escape\n---\n"
    print(
        "Skill index lifecycle PASS: v1 compatibility, drift, regeneration, malformed metadata and confinement"
    )


if __name__ == "__main__":
    main()
