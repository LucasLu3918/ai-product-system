from __future__ import annotations

import copy
import sys
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
    assert report["selection_policy_changed"] is False
    assert report["automatic_source_policy_changes_authorized"] is False

    empty = yaml.safe_load((ROOT / "config/evolution-relevance-labels.yaml").read_text(encoding="utf-8"))
    not_ready = evolution_relevance.evaluate(empty)
    assert not_ready["status"] == "NOT_READY" and not_ready["precision_recall"] is None
    assert not_ready["confusion"] is None, "empty human-label corpus must not imply zero errors"

    uncertain = copy.deepcopy(fixture)
    uncertain["labels"][0]["relevance"] = "UNCERTAIN"
    blocked = evolution_relevance.evaluate(uncertain)
    assert blocked["status"] == "NOT_READY" and blocked["precision_recall"] is None
    assert blocked["incomplete_count"] == 1

    duplicate = copy.deepcopy(fixture)
    duplicate["labels"].append(copy.deepcopy(duplicate["labels"][0]))
    duplicate_report = evolution_relevance.evaluate(duplicate)
    assert duplicate_report["status"] == "NOT_READY"
    assert any("duplicated" in item for item in duplicate_report["errors"])

    print("EVOLUTION HUMAN RELEVANCE LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
