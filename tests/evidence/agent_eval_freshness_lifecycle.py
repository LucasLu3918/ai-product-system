from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from agent_eval_freshness import build_report, load_yaml, validate_config


def main() -> int:
    config = load_yaml(ROOT / "config/eval-freshness.yaml")
    issues = validate_config(ROOT, config)
    assert issues == [], issues
    report = build_report(ROOT, config, ["scripts/project_intelligence.py"])
    selected = {row["case_id"] for row in report["affected_cases"]}
    assert selected == {
        "009-capability-gap", "017-core-change-approval", "019-system-self-improvement",
        "052-project-intelligence-discovery", "084-change-impact-before-mutation",
        "092-core-change-impact-test-matrix", "093-core-change-scope-expansion-retests",
    }
    assert report["status"] == "STALE"
    assert report["manual_scenarios_preserved"] == ["192", "193", "224"]
    clean = build_report(ROOT, config, ["docs/human/USER_GUIDE.md"])
    assert clean["status"] == "CURRENT" and clean["affected_cases"] == []

    invalid = {**config, "behaviors": [{**config["behaviors"][0], "path_patterns": ["../outside"]}]}
    assert any("unsafe dependency pattern" in item for item in validate_config(ROOT, invalid))
    manual_only = build_report(ROOT, config, ["tests/scenarios/224-runtime-preferred-primary-model.md"])
    assert manual_only["affected_cases"] == []
    print("Agent Eval freshness lifecycle: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
