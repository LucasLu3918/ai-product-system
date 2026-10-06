"""Evaluate Evolution selection against explicit Human relevance labels offline."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config/evolution-relevance-labels.yaml"
DEFAULT_EVALUATION_POLICY = ROOT / "config/evolution-evaluation.yaml"


def sample_candidates(
    document: dict[str, Any], *, period: str, sample_size: int = 20, maximum_candidates: int = 10000
) -> dict[str, Any]:
    """Create a reproducible, content-minimized monthly Human review sample."""
    errors: list[str] = []
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", period):
        errors.append("period must be a valid YYYY-MM month")
    if document.get("version") != 1:
        errors.append("candidate inventory version must be 1")
    if not 1 <= sample_size <= 100:
        errors.append("sample_size must be between 1 and 100")
    if not 1 <= maximum_candidates <= 10000:
        errors.append("maximum_candidates must be between 1 and 10000")
    rows = document.get("candidates")
    if not isinstance(rows, list):
        rows = []
        errors.append("candidates must be a list")
    if len(rows) > maximum_candidates:
        errors.append("candidates exceeds the configured bound")

    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for index, row in enumerate(rows[:maximum_candidates]):
        prefix = f"candidates[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        fingerprint = str(row.get("signal_fingerprint") or "")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", fingerprint):
            errors.append(f"{prefix}.signal_fingerprint must be a SHA-256 fingerprint")
            continue
        if fingerprint in seen:
            errors.append(f"{prefix}.signal_fingerprint is duplicated")
            continue
        seen.add(fingerprint)
        source_ids = row.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids or any(not str(source).strip() for source in source_ids):
            errors.append(f"{prefix}.source_ids must be a non-empty list")
            continue
        selection = row.get("selection")
        if selection not in {"SELECTED", "REJECTED"}:
            errors.append(f"{prefix}.selection must be SELECTED or REJECTED")
            continue
        candidate = {
            "signal_fingerprint": fingerprint,
            "source_ids": sorted({str(source) for source in source_ids}),
            "selection": selection,
        }
        signal_ref = str(row.get("signal_ref") or "")
        if signal_ref.startswith(("https://", "http://")):
            candidate["signal_ref"] = signal_ref
        candidates.append(candidate)

    ranked = sorted(
        candidates,
        key=lambda row: hashlib.sha256(f"{period}:{row['signal_fingerprint']}".encode()).hexdigest(),
    )
    selected = ranked[:sample_size]
    return {
        "version": 1,
        "status": "AWAITING_HUMAN_LABELS" if selected and not errors else "NOT_READY",
        "period": period,
        "sampling_method": "sha256-period-rank",
        "requested_sample_size": sample_size,
        "sample_size": len(selected),
        "candidate_count": len(candidates),
        "sample": selected if not errors else [],
        "errors": errors,
        "label_authority": "human",
        "automatic_policy_changes": False,
        "policy_changed": False,
    }


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
    actionable_counts = {"actionable": 0, "not_actionable": 0}
    source_counts: dict[str, dict[str, int]] = {}
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
        source_ids = row.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids or any(not str(source).strip() for source in source_ids):
            errors.append(f"{prefix}.source_ids must be a non-empty list")
        actionability = row.get("actionability")
        if actionability not in {"ACTIONABLE", "NOT_ACTIONABLE", "UNCERTAIN"}:
            errors.append(f"{prefix}.actionability is invalid")
        if label == "UNCERTAIN" or action == "PENDING":
            incomplete.append(fingerprint or f"record-{index}")
            continue
        if actionability == "UNCERTAIN":
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
        if actionability in {"ACTIONABLE", "NOT_ACTIONABLE"}:
            key = "actionable" if actionability == "ACTIONABLE" else "not_actionable"
            actionable_counts[key] += 1
        if isinstance(source_ids, list):
            for source in sorted({str(value) for value in source_ids if str(value).strip()}):
                source_count = source_counts.setdefault(source, {"labeled_count": 0, "relevant_count": 0})
                source_count["labeled_count"] += 1
                source_count["relevant_count"] += int(label == "RELEVANT")

    cohort_complete = bool(rows) and not incomplete and not errors
    precision_denominator = counts["true_positive"] + counts["false_positive"]
    recall_denominator = counts["true_positive"] + counts["false_negative"]
    metrics = None if not cohort_complete else {
        "shortlist_precision": counts["true_positive"] / precision_denominator if precision_denominator else None,
        "shortlist_recall": counts["true_positive"] / recall_denominator if recall_denominator else None,
        "actionable_yield": actionable_counts["actionable"] / sum(actionable_counts.values()) if sum(actionable_counts.values()) else None,
        "source_yield": {
            source: {
                **values,
                "yield": values["relevant_count"] / values["labeled_count"] if values["labeled_count"] else None,
            }
            for source, values in sorted(source_counts.items())
        },
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
        "metrics": metrics,
        "precision_recall": None if metrics is None else {
            "precision": metrics["shortlist_precision"],
            "recall": metrics["shortlist_recall"],
        },
        "errors": errors,
        "selection_policy_changed": False,
        "automatic_source_policy_changes_authorized": False,
        "human_decision_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("labels", nargs="?", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--sample-from", type=Path, help="create a deterministic review sample from a candidate YAML file")
    parser.add_argument("--period", help="sample period in YYYY-MM form")
    parser.add_argument("--sample-size", type=int)
    args = parser.parse_args()
    try:
        if args.sample_from:
            document = yaml.safe_load(args.sample_from.read_text(encoding="utf-8")) or {}
            policy = yaml.safe_load(DEFAULT_EVALUATION_POLICY.read_text(encoding="utf-8")) or {}
            cohort = policy.get("cohort") or {}
            sample_size = args.sample_size if args.sample_size is not None else cohort.get("sample_size", 20)
            if not args.period:
                raise ValueError("--period is required with --sample-from")
            report = sample_candidates(
                document,
                period=args.period,
                sample_size=sample_size,
                maximum_candidates=cohort.get("maximum_candidate_signals", 10000),
            )
        else:
            document = yaml.safe_load(args.labels.read_text(encoding="utf-8")) or {}
            report = None
        if not isinstance(document, dict):
            raise TypeError("label document must be a mapping")
        if report is None:
            report = evaluate(document)
    except (OSError, yaml.YAMLError, ValueError, TypeError) as exc:
        report = {"version": 1, "status": "NOT_READY", "errors": [type(exc).__name__], "selection_policy_changed": False, "automatic_source_policy_changes_authorized": False, "human_decision_required": True}
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] in {"READY_FOR_HUMAN_REVIEW", "AWAITING_HUMAN_LABELS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
