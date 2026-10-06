from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import evolution_relevance


def main() -> int:
    fixture = yaml.safe_load((ROOT / "tests/fixtures/evolution-relevance/labels.yaml").read_text(encoding="utf-8"))
    report = evolution_relevance.evaluate(fixture, generated_at="2026-10-05T00:00:00Z")
    assert report["status"] == "READY_FOR_HUMAN_REVIEW"
    assert report["confusion"] == {"true_positive": 1, "false_positive": 1, "false_negative": 1, "true_negative": 1}
    assert report["precision_recall"] == {"precision": 0.5, "recall": 0.5}
    assert report["metrics"]["actionable_yield"] == 0.5
    assert report["metrics"]["source_yield"]["github-blog"]["yield"] == 0.5
    assert report["metrics"]["source_yield"]["hn"]["yield"] == 0.5
    assert report["selection_policy_changed"] is False
    assert report["automatic_source_policy_changes_authorized"] is False

    sample_input = {
        "version": 1,
        "candidates": [
            {key: row[key] for key in ("signal_fingerprint", "source_ids", "selection")}
            for row in fixture["labels"]
        ]
    }
    sample = evolution_relevance.sample_candidates(sample_input, period="2026-10", sample_size=3)
    repeated = evolution_relevance.sample_candidates(sample_input, period="2026-10", sample_size=3)
    assert sample == repeated, "monthly review sample must be reproducible"
    assert sample["status"] == "AWAITING_HUMAN_LABELS" and sample["sample_size"] == 3
    assert "label_rationale" not in sample["sample"][0], "sample manifest must not invent or expose Human labels"
    assert sample["policy_changed"] is False
    assert evolution_relevance.sample_candidates(sample_input, period="2026-13")["status"] == "NOT_READY"
    assert evolution_relevance.sample_candidates({**sample_input, "version": 2}, period="2026-10")["status"] == "NOT_READY"

    with tempfile.TemporaryDirectory() as directory:
        candidates_path = Path(directory) / "candidates.yaml"
        candidates_path.write_text(yaml.safe_dump(sample_input), encoding="utf-8")
        cli = subprocess.run(
            [sys.executable, str(ROOT / "scripts/evolution_relevance.py"), "--sample-from", str(candidates_path), "--period", "2026-10"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert cli.returncode == 0, cli.stderr
        cli_report = json.loads(cli.stdout)
        assert cli_report["sample_size"] == 4, "CLI sample size must be bounded by available candidates"

    empty = yaml.safe_load((ROOT / "config/evolution-relevance-labels.yaml").read_text(encoding="utf-8"))
    not_ready = evolution_relevance.evaluate(empty)
    assert not_ready["status"] == "NOT_READY" and not_ready["precision_recall"] is None
    assert not_ready["confusion"] is None, "empty human-label corpus must not imply zero errors"

    uncertain = copy.deepcopy(fixture)
    uncertain["labels"][0]["relevance"] = "UNCERTAIN"
    blocked = evolution_relevance.evaluate(uncertain)
    assert blocked["status"] == "NOT_READY" and blocked["precision_recall"] is None
    assert blocked["incomplete_count"] == 1

    uncertain_actionability = copy.deepcopy(fixture)
    uncertain_actionability["labels"][0]["actionability"] = "UNCERTAIN"
    blocked_actionability = evolution_relevance.evaluate(uncertain_actionability)
    assert blocked_actionability["status"] == "NOT_READY"
    assert blocked_actionability["metrics"] is None

    duplicate = copy.deepcopy(fixture)
    duplicate["labels"].append(copy.deepcopy(duplicate["labels"][0]))
    duplicate_report = evolution_relevance.evaluate(duplicate)
    assert duplicate_report["status"] == "NOT_READY"
    assert any("duplicated" in item for item in duplicate_report["errors"])

    duplicate_sample = evolution_relevance.sample_candidates(
        {"candidates": sample_input["candidates"] + [copy.deepcopy(sample_input["candidates"][0])]},
        period="2026-10",
    )
    assert duplicate_sample["status"] == "NOT_READY"
    assert duplicate_sample["sample"] == []

    print("EVOLUTION HUMAN RELEVANCE LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
