"""Evaluate Evolution selection against explicit Human relevance labels offline."""
from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config/evolution-relevance-labels.yaml"


def evaluate(document: dict[str, Any], *, generated_at: str | None = None) -> dict[str, Any]:
    errors: list[str] = []
    if document.get("version") != 1:
        errors.append("version must be 1")
    if document.get("label_authority") != "human":
        errors.append("label_authority must be human")
    if document.get("automatic_policy_changes") is not False:
        errors.append("automatic_policy_changes must remain false")
    rows = document.get("labels")
    if not isinstance(rows, list):
        rows = []
        errors.append("labels must be a list")
    if len(rows) > 1000:
        errors.append("labels exceeds the 1000-record bound")

    seen: set[str] = set()
    incomplete: list[str] = []
    counts = {"true_positive": 0, "false_positive": 0, "false_negative": 0, "true_negative": 0}
    for index, row in enumerate(rows[:1000]):
        prefix = f"labels[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        fingerprint = str(row.get("signal_fingerprint") or "")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", fingerprint):
            errors.append(f"{prefix}.signal_fingerprint must be a SHA-256 fingerprint")
        elif fingerprint in seen:
            errors.append(f"{prefix}.signal_fingerprint is duplicated")
        seen.add(fingerprint)
        if row.get("label_source") != "human" or not str(row.get("reviewer") or "").strip():
            errors.append(f"{prefix} requires explicit human label provenance")
        timestamp = str(row.get("reviewed_at") or "")
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            errors.append(f"{prefix}.reviewed_at must be an ISO-8601 timestamp")
        label = row.get("relevance")
        action = row.get("selection")
        if label not in {"RELEVANT", "NOT_RELEVANT", "UNCERTAIN"}:
            errors.append(f"{prefix}.relevance is invalid")
        if action not in {"SELECTED", "REJECTED", "PENDING"}:
            errors.append(f"{prefix}.selection is invalid")
        if not str(row.get("label_rationale") or "").strip():
            errors.append(f"{prefix}.label_rationale is required")
        if not str(row.get("selection_reason") or "").strip():
            errors.append(f"{prefix}.selection_reason is required")
        if label == "UNCERTAIN" or action == "PENDING":
            incomplete.append(fingerprint or f"record-{index}")
            continue
        if label not in {"RELEVANT", "NOT_RELEVANT"} or action not in {"SELECTED", "REJECTED"}:
            continue
        if action == "SELECTED" and label == "RELEVANT":
            counts["true_positive"] += 1
        elif action == "SELECTED":
            counts["false_positive"] += 1
        elif label == "RELEVANT":
            counts["false_negative"] += 1
        else:
            counts["true_negative"] += 1

    cohort_complete = bool(rows) and not incomplete and not errors
    precision_denominator = counts["true_positive"] + counts["false_positive"]
    recall_denominator = counts["true_positive"] + counts["false_negative"]
    metrics = None if not cohort_complete else {
        "precision": counts["true_positive"] / precision_denominator if precision_denominator else None,
        "recall": counts["true_positive"] / recall_denominator if recall_denominator else None,
    }
    return {
        "version": 1,
        "status": "READY_FOR_HUMAN_REVIEW" if cohort_complete else "NOT_READY",
        "generated_at": generated_at or datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "label_count": len(rows),
        "complete_binary_label_count": sum(counts.values()),
        "incomplete_count": len(incomplete),
        "incomplete_fingerprints": incomplete,
        "confusion": counts if cohort_complete else None,
        "precision_recall": metrics,
        "errors": errors,
        "selection_policy_changed": False,
        "automatic_source_policy_changes_authorized": False,
        "human_decision_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("labels", nargs="?", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        document = yaml.safe_load(args.labels.read_text(encoding="utf-8")) or {}
        if not isinstance(document, dict):
            raise TypeError("label document must be a mapping")
        report = evaluate(document)
    except (OSError, yaml.YAMLError, ValueError, TypeError) as exc:
        report = {"version": 1, "status": "NOT_READY", "errors": [type(exc).__name__], "selection_policy_changed": False, "automatic_source_policy_changes_authorized": False, "human_decision_required": True}
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "READY_FOR_HUMAN_REVIEW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
