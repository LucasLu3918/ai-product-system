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
VISUAL_EVIDENCE = ROOT / "scripts" / "visual_evidence.py"


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


def visual_evidence(project: Path, audit: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
    result = run([
        sys.executable,
        str(VISUAL_EVIDENCE),
        str(audit),
        "--project",
        str(project),
        "--format",
        "json",
    ])
    try:
        data = json.loads(result.stdout)
    except Exception as exc:
        raise AssertionError(f"visual evidence output invalid: {result.stdout} {result.stderr}") from exc
    return result, data


def exercise_visual_evidence(project: Path) -> None:
    evidence = project / "evidence" / "visual"
    evidence.mkdir(parents=True)
    before = evidence / "home-desktop-before.png"
    after = evidence / "home-desktop-after.png"
    mobile_before = evidence / "home-mobile-before.png"
    mobile_after = evidence / "home-mobile-after.png"
    for path in (before, after, mobile_before, mobile_after):
        path.write_bytes(b"fixture-rendered-artifact\n")

    base_capture = {
        "kind": "screenshot",
        "target": "/",
        "state": "default",
        "provenance": {
            "provider": "fixture-browser",
            "source_revision": "fixture-revision",
            "captured_at": "2026-09-17T00:00:00Z",
            "command": "fixture capture",
        },
    }
    audit_data = {
        "version": 1,
        "mode": "V2",
        "status": "pass",
        "target": {"routes": ["/"], "components": ["Button"]},
        "baseline_source": "docs/design/PROJECT_VISUAL_PROFILE.yaml",
        "component_inventory": [{"component": "Button", "source": "src/components/Button.tsx"}],
        "findings": [{
            "id": "VIS-001",
            "component": "Button",
            "route": "/",
            "symptom": "fixture spacing outlier",
            "classification": "outlier",
            "valid_variant": False,
            "approved_exception": False,
            "root_cause": {"source": "src/components/Button.tsx", "style": None, "token": None, "mechanism": None},
            "fix": "normalize shared component spacing",
            "status": "fixed",
        }],
        "verification": {
            "required_viewports": ["desktop", "mobile"],
            "required_states": ["default"],
            "before": [
                {**base_capture, "id": "desktop-before", "viewport": {"label": "desktop", "width": 1440, "height": 900}, "artifact": str(before.relative_to(project))},
                {**base_capture, "id": "mobile-before", "viewport": {"label": "mobile", "width": 390, "height": 844}, "artifact": str(mobile_before.relative_to(project))},
            ],
            "after": [
                {**base_capture, "id": "desktop-after", "viewport": {"label": "desktop", "width": 1440, "height": 900}, "artifact": str(after.relative_to(project))},
                {**base_capture, "id": "mobile-after", "viewport": {"label": "mobile", "width": 390, "height": 844}, "artifact": str(mobile_after.relative_to(project))},
            ],
        },
        "review": {
            "decision": "PASS",
            "quality_assessed_by": "visual_review",
            "checks": [{"area": "composition", "result": "pass", "evidence": [str(after.relative_to(project))]}],
            "notes": [],
        },
        "profile_updated": True,
        "remaining_material_findings": [],
    }
    audit = project / "VISUAL_AUDIT.yaml"
    audit.write_text(yaml.safe_dump(audit_data, sort_keys=False), encoding="utf-8")

    passing, passing_data = visual_evidence(project, audit)
    require(passing.returncode == 0, f"complete visual evidence must validate: {passing_data}")
    require(passing_data.get("evidence_integrity") == "PASS", "evidence integrity must pass")
    require(passing_data.get("visual_quality_inferred") is False, "deterministic validator must never infer visual quality")

    missing_artifact = yaml.safe_load(audit.read_text(encoding="utf-8"))
    missing_artifact["verification"]["after"][0]["artifact"] = "evidence/visual/missing.png"
    audit.write_text(yaml.safe_dump(missing_artifact, sort_keys=False), encoding="utf-8")
    missing, missing_data = visual_evidence(project, audit)
    require(missing.returncode != 0, "missing rendered artifact must fail closed")
    require(any("artifact" in error for error in missing_data.get("errors", [])), "missing artifact failure must be observable")

    no_review = yaml.safe_load(yaml.safe_dump(audit_data))
    no_review["review"]["decision"] = "PENDING"
    audit.write_text(yaml.safe_dump(no_review, sort_keys=False), encoding="utf-8")
    blocked, blocked_data = visual_evidence(project, audit)
    require(blocked.returncode != 0, "PASS without a Visual Quality Review decision must fail closed")
    require(any("Visual Quality Review" in error for error in blocked_data.get("errors", [])), "review gate failure must be explicit")

    no_root = yaml.safe_load(yaml.safe_dump(audit_data))
    no_root["findings"][0]["root_cause"] = {"source": None, "style": None, "token": None, "mechanism": None}
    audit.write_text(yaml.safe_dump(no_root, sort_keys=False), encoding="utf-8")
    root_failed, root_data = visual_evidence(project, audit)
    require(root_failed.returncode != 0, "closed finding without root-cause evidence must fail closed")
    require(any("root-cause" in error for error in root_data.get("errors", [])), "root-cause failure must be explicit")


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

        exercise_visual_evidence(project)

    print("VISUAL PROFILE / EVIDENCE LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
