#!/usr/bin/env python3
from __future__ import annotations

import sys
import subprocess
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from ci_validation_plan import PlanError, build_plan, changed_paths


def main() -> int:
    config = yaml.safe_load((ROOT / "config/ci-validation-plan.yaml").read_text(encoding="utf-8"))
    docs = build_plan(config, ["docs/human/MAINTENANCE.md"], base="a", head="b")
    assert docs["needs_node"] and not docs["needs_browser"] and not docs["needs_openapi"]
    openapi = build_plan(config, ["scripts/openapi_contracts.py"], base="a", head="b")
    assert openapi["needs_openapi"] and not openapi["needs_browser"] and not openapi["needs_node"]
    visual = build_plan(config, ["tests/evidence/visual_render_lifecycle.py"], base="a", head="b")
    assert visual["needs_browser"] and not visual["needs_openapi"]
    sensitive = build_plan(config, [".github/workflows/validate.yml"], base="a", head="b")
    assert sensitive["full_validation"] and all(sensitive[key] for key in ("needs_node", "needs_browser", "needs_openapi"))
    unknown = build_plan(config, ["mystery/file.bin"], base="a", head="b")
    assert unknown["full_validation"] and unknown["unknown_paths"] == ["mystery/file.bin"]
    ordinary = build_plan(config, ["scripts/aips_identity.py"], base="a", head="b")
    assert not ordinary["full_validation"] and not any(ordinary[key] for key in ("needs_node", "needs_browser", "needs_openapi"))
    with tempfile.TemporaryDirectory(prefix="aips-plan-git-") as temp:
        repo = Path(temp)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "planner-test"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Planner Test"], check=True)
        (repo / "docs").mkdir()
        (repo / "docs/guide.md").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
        base_sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        (repo / "docs/guide.md").write_text("changed\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "commit", "-qam", "docs update"], check=True)
        head_sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        assert changed_paths(repo, base_sha, head_sha) == ["docs/guide.md"]
        try:
            changed_paths(repo, "missing-base", head_sha)
        except PlanError:
            pass
        else:
            raise AssertionError("unresolvable refs must fail the planner closed")
    print("CI validation planning lifecycle: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
