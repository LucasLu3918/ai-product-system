"""Read-only summaries of actual local creative trials and separate visual review."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from creative_image_validation import valid_raster
from performance_evidence import observed_distribution

DIMENSIONS = {"character_identity", "outfit_consistency", "composition", "reference_edit", "recovery"}
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


def summarize_trials(project: Path, evidence: dict[str, Any]) -> dict[str, Any]:
    """Verify artifact binding; supplied visual ratings remain Human evidence."""
    if not isinstance(evidence, dict):
        raise TypeError("benchmark evidence must be a mapping")
    trials = evidence.get("trials")
    if evidence.get("version") != 1 or not isinstance(trials, list) or len(trials) > 100:
        raise ValueError("benchmark requires version 1 and at most 100 trials")
    root = project.resolve(strict=True)
    observations = []
    invalid = 0
    for trial in trials:
        if not isinstance(trial, dict) or trial.get("source") != "observed_host":
            invalid += 1
            continue
        if set(trial) - {"source", "provider", "model_revision", "device", "output", "sha256", "elapsed_ms", "visual_review", "user_acceptance"}:
            invalid += 1
            continue
        if trial.get("provider") not in {"mflux_local", "comfyui_local"} or any(
            not isinstance(trial.get(key), str) or not trial[key].strip() for key in ("model_revision", "device")
        ):
            invalid += 1
            continue
        raw = trial.get("output")
        if not isinstance(raw, str) or not raw or Path(raw).is_absolute() or ".." in Path(raw).parts:
            invalid += 1
            continue
        output = root / raw
        try:
            expected = trial.get("sha256")
            if (output.is_symlink() or not output.resolve().is_relative_to(root) or not output.is_file()
                    or output.stat().st_size > 25 * 1024 * 1024 or not valid_raster(output)
                    or not isinstance(expected, str) or not DIGEST.fullmatch(expected)
                    or "sha256:" + hashlib.sha256(output.read_bytes()).hexdigest() != expected):
                invalid += 1
                continue
        except OSError:
            invalid += 1
            continue
        observations.append(trial)
    visual: dict[str, dict[str, int | str]] = {}
    for dimension in sorted(DIMENSIONS):
        ratings = []
        for trial in observations:
            review = trial.get("visual_review")
            if not isinstance(review, dict) or review.get("reviewer_type") != "human" or not review.get("reviewer"):
                continue
            assessment = review.get("dimensions")
            if isinstance(assessment, dict) and isinstance(assessment.get(dimension), str) and assessment[dimension] in {"PASS", "REVISE"}:
                ratings.append(assessment[dimension])
        visual[dimension] = {"status": "RECORDED_HUMAN_REVIEW" if ratings else "UNVERIFIED",
                             "sample_count": len(ratings), "pass": ratings.count("PASS"), "revise": ratings.count("REVISE")}
    return {"version": 1, "status": "RECORDED" if observations else "UNKNOWN", "read_only": True,
            "artifact_bound_samples": len(observations), "invalid_or_unobserved": invalid,
            "elapsed_ms": observed_distribution([trial.get("elapsed_ms") for trial in observations]),
            "visual_dimensions": visual,
            "user_acceptance_count": sum(trial.get("user_acceptance") == "ACCEPTED" for trial in observations),
            "user_acceptance_status": "RECORDED" if any(trial.get("user_acceptance") in ("ACCEPTED", "REJECTED") for trial in observations) else "NOT_RECORDED",
            "runtime_attestation": "UNVERIFIED", "authority": "NONE"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.evidence.stat().st_size > 1024 * 1024:
            raise ValueError("benchmark evidence exceeds the input bound")
        report = summarize_trials(args.project, json.loads(args.evidence.read_text()))
    except (OSError, ValueError, TypeError):
        print(json.dumps({"status": "BLOCKED", "reason_code": "benchmark_input_invalid"}))
        return 2
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
