"""Contract checks for the profile-driven creative quality extension."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    profile = yaml.safe_load((ROOT / "templates/creative/MODEL_CAPABILITY_PROFILE.yaml").read_text())
    assert profile["version"] == 1 and profile["models"] == []
    report_schema = json.loads((ROOT / "templates/creative/VISUAL_REVIEW_REPORT.schema.json").read_text())
    assert report_schema["properties"]["status"]["const"] == "ADVISORY_REVIEW"
    assert report_schema["properties"]["authority"]["const"] == "NONE"
    assert report_schema["properties"]["user_acceptance"]["const"] == "NOT_RECORDED"
    template = yaml.safe_load((ROOT / "templates/creative/CREATIVE_COLLECTION_PROFILE.yaml").read_text())
    assert set(template["style_lock"]) == {"id", "must_match", "must_avoid", "palette"}
    result = subprocess.run([sys.executable, str(ROOT / "tests/evidence/creative_quality_lifecycle.py")], cwd=ROOT,
                            check=False, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    plugin = (ROOT / "harness/adapters/opencode/plugin.ts").read_text()
    assert '"review-assist"' in plugin and "vision_model" in plugin
    assert '"review-assist"' in (ROOT / "scripts/creative_request_policy.py").read_text()
    print("Creative quality contracts PASS: additive profiles, advisory report authority, local lifecycle, and OpenCode action")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
