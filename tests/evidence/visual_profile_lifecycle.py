#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts" / "visual_profile.py"


def run(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def git(project: Path, *args: str) -> str:
    result = run(["git", *args], cwd=project)
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def status(project: Path) -> dict:
    result = run([
        sys.executable,
        str(HELPER),
        "status",
        "--project",
        str(project),
        "--format",
        "json",
    ])
    require(result.returncode == 0, f"visual profile status failed: {result.stdout} {result.stderr}")
    return json.loads(result.stdout)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "project"
        (project / "docs" / "design").mkdir(parents=True)
        (project / "src" / "components").mkdir(parents=True)
        (project / "src" / "styles").mkdir(parents=True)
        (project / "src" / "pages").mkdir(parents=True)

        (project / "src" / "components" / "Button.tsx").write_text(
            "export const Button = () => <button>Save</button>;\n",
            encoding="utf-8",
        )
        (project / "src" / "styles" / "tokens.css").write_text(
            ":root { --control-radius: 8px; }\n",
            encoding="utf-8",
        )
        (project / "src" / "pages" / "Home.tsx").write_text(
            "export const Home = () => <main>Home</main>;\n",
            encoding="utf-8",
        )
        (project / "README.md").write_text("# Fixture\n", encoding="utf-8")

        git(project, "init", "-q")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Test")
        git(project, "add", ".")
        git(project, "commit", "-qm", "initial ui")
        baseline = git(project, "rev-parse", "HEAD")

        profile = {
            "version": 1,
            "status": "APPROVED",
            "last_verified_commit": baseline,
            "direction": {
                "archetype": "quiet-premium",
                "status": "inferred",
                "confidence": "medium",
                "principles": ["calm hierarchy"],
            },
            "sources": {
                "brand_profile": None,
                "visual_system": None,
                "design_tokens": ["src/styles/tokens.css"],
                "inferred_from_existing_ui": True,
            },
            "typography": {"families": [], "scale": [], "rules": []},
            "spacing": {"scale": [4, 8, 16, 24], "rules": []},
            "controls": {
                "button": {
                    "golden_component": "src/components/Button.tsx",
                    "variants": {"default": {"radius": 8}},
                }
            },
            "icons": {"rules": []},
            "state_rules": {"geometry_must_remain_stable": True, "rules": []},
            "representative_routes": ["/"],
            "golden_components": {
                "button": {
                    "source": "src/components/Button.tsx",
                    "reason": "canonical shared implementation",
                }
            },
            "exceptions": [],
            "must_avoid": ["arbitrary_pixel_nudges_for_shared_layout"],
            "watch": {
                "paths": ["src/components/**", "src/styles/**"],
                "signals": ["design_token_change", "shared_component_change"],
            },
            "evidence": {
                "routes": ["/"],
                "screenshots": ["evidence/home-desktop.png"],
                "implementation_refs": [
                    "src/components/Button.tsx",
                    "src/styles/tokens.css",
                ],
            },
        }
        profile_path = project / "docs" / "design" / "PROJECT_VISUAL_PROFILE.yaml"
        profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")
        git(project, "add", str(profile_path.relative_to(project)))
        git(project, "commit", "-qm", "add visual profile")

        initial = status(project)
        require(initial.get("profile_loaded") is True, "profile must be loaded before deciding on rescans")
        require(initial.get("decision") == "REUSE", "unchanged watched sources must reuse profile")
        require(initial.get("full_rescan_required") is False, "unchanged profile must not trigger full rescan")
        require(initial.get("direction_status") == "inferred", "subjective archetype must remain inferred")

        (project / "README.md").write_text("# Fixture\n\nDocs only.\n", encoding="utf-8")
        git(project, "add", "README.md")
        git(project, "commit", "-qm", "unrelated docs")
        unrelated = status(project)
        require(unrelated.get("decision") == "REUSE", "unrelated commit must not rebuild visual baseline")
        require(
            "README.md" in (unrelated.get("changed_paths") or []),
            "unrelated change should remain observable",
        )
        require(not (unrelated.get("affected_watched_paths") or []), "unrelated path must not affect visual watch scope")

        (project / "src" / "styles" / "tokens.css").write_text(
            ":root { --control-radius: 10px; }\n",
            encoding="utf-8",
        )
        git(project, "add", "src/styles/tokens.css")
        git(project, "commit", "-qm", "change visual token")
        token_change = status(project)
        require(token_change.get("decision") == "TARGETED_REFRESH", "watched token change must target refresh")
        require(token_change.get("full_rescan_required") is False, "watched change should not force full rescan")
        require(
            "src/styles/tokens.css" in (token_change.get("affected_watched_paths") or []),
            "changed token must be reported as affected",
        )

        with (project / "src" / "components" / "Button.tsx").open("a", encoding="utf-8") as fh:
            fh.write("// dirty shared component\n")
        dirty = status(project)
        require(dirty.get("decision") == "TARGETED_REFRESH", "dirty watched component must target refresh")
        require(
            "src/components/Button.tsx" in (dirty.get("affected_watched_paths") or []),
            "dirty shared component must be reported as affected",
        )
        git(project, "checkout", "--", "src/components/Button.tsx")

        profile["last_verified_commit"] = None
        profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")
        missing_base = status(project)
        require(missing_base.get("decision") == "FULL_DISCOVERY", "missing baseline commit must fail closed")
        require(missing_base.get("full_rescan_required") is True, "missing baseline must require full discovery")

    print("VISUAL PROFILE LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
