"""Read-only summaries of actual local creative trials and separate visual review."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml
from creative_image_validation import valid_raster
from performance_evidence import observed_distribution

ROOT = Path(__file__).resolve().parents[1]
DIMENSIONS = {"character_identity", "outfit_consistency", "composition", "reference_edit", "recovery"}
FAILURE_STAGES = ("model", "check", "compiler")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
REASON_CODE = re.compile(r"[a-z0-9_]{1,64}")
IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")


def load_dataset() -> dict[str, Any]:
    path = ROOT / "templates/creative/CREATIVE_QUALITY_DATASET.yaml"
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("version") != 1 or value.get("id") != "aips-creative-quality-v1":
        raise ValueError("creative quality dataset is invalid")
    profiles, cases = value.get("profiles"), value.get("cases")
    if (not isinstance(profiles, list) or not 1 <= len(profiles) <= 12
            or not isinstance(cases, list) or not 1 <= len(cases) <= 24):
        raise ValueError("creative quality dataset is outside its bounds")
    profile_ids = [item.get("id") for item in profiles if isinstance(item, dict)]
    case_ids = [item.get("id") for item in cases if isinstance(item, dict)]
    if len(profile_ids) != len(profiles) or len(set(profile_ids)) != len(profile_ids) or any(
        not isinstance(item, str) or not IDENTIFIER.fullmatch(item) for item in profile_ids
    ):
        raise ValueError("creative quality profile ids are invalid")
    if len(case_ids) != len(cases) or len(set(case_ids)) != len(case_ids) or any(
        not isinstance(item, str) or not IDENTIFIER.fullmatch(item) for item in case_ids
    ):
        raise ValueError("creative quality case ids are invalid")
    for case in cases:
        dimensions = case.get("dimensions")
        if not isinstance(dimensions, list) or any(item not in DIMENSIONS for item in dimensions):
            raise ValueError("creative quality case dimensions are invalid")
    required = value.get("required_dimensions")
    if not isinstance(required, list) or len(required) != len(DIMENSIONS) or set(required) != DIMENSIONS:
        raise ValueError("creative quality required dimensions are invalid")
    archetypes = {item.get("archetype") for item in profiles}
    if archetypes != {"human_character", "animal_character", "nonhuman_character"}:
        raise ValueError("creative quality profile archetypes are invalid")
    return value


def _bound_output(root: Path, trial: dict[str, Any]) -> bool:
    raw, expected = trial.get("output"), trial.get("sha256")
    if raw is None and expected is None:
        return False
    if not isinstance(raw, str) or not raw or Path(raw).is_absolute() or ".." in Path(raw).parts:
        return False
    output = root / raw
    try:
        return bool(
            not output.is_symlink() and output.resolve().is_relative_to(root) and output.is_file()
            and output.stat().st_size <= 25 * 1024 * 1024 and valid_raster(output)
            and isinstance(expected, str) and DIGEST.fullmatch(expected)
            and "sha256:" + hashlib.sha256(output.read_bytes()).hexdigest() == expected
        )
    except OSError:
        return False


def summarize_trials(project: Path, evidence: dict[str, Any]) -> dict[str, Any]:
    """Verify local artifact bindings and report bounded cross-profile evidence."""
    if not isinstance(evidence, dict):
        raise TypeError("benchmark evidence must be a mapping")
    trials = evidence.get("trials")
    version = evidence.get("version")
    if version not in {1, 2} or not isinstance(trials, list) or len(trials) > 100:
        raise ValueError("benchmark requires version 1 or 2 and at most 100 trials")
    dataset = load_dataset() if version == 2 else None
    if version == 2 and evidence.get("dataset_id") != dataset["id"]:
        raise ValueError("benchmark dataset id is not registered")
    root = project.resolve(strict=True)
    observations = []
    artifacts = []
    failures = {stage: 0 for stage in FAILURE_STAGES}
    invalid = 0
    legacy_fields = {"source", "provider", "model_revision", "device", "output", "sha256",
                     "elapsed_ms", "visual_review", "user_acceptance"}
    dataset_fields = {"profile_id", "case_id", "status", "failure_stage", "reason_code"}
    profile_ids = {item["id"] for item in dataset["profiles"]} if dataset else set()
    case_ids = {item["id"] for item in dataset["cases"]} if dataset else set()
    for trial in trials:
        if not isinstance(trial, dict) or trial.get("source") != "observed_host":
            invalid += 1
            continue
        allowed = legacy_fields | dataset_fields if version == 2 else legacy_fields
        if set(trial) - allowed:
            invalid += 1
            continue
        if trial.get("provider") not in {"mflux_local", "comfyui_local"} or any(
            not isinstance(trial.get(key), str) or not trial[key].strip() for key in ("model_revision", "device")
        ):
            invalid += 1
            continue
        result_status = trial.get("status", "COMPLETE")
        failure_stage = None
        if version == 2:
            if (trial.get("profile_id") not in profile_ids or trial.get("case_id") not in case_ids
                    or result_status not in {"COMPLETE", "FAILED"}):
                invalid += 1
                continue
            if result_status == "FAILED":
                stage, reason = trial.get("failure_stage"), trial.get("reason_code")
                if stage not in FAILURE_STAGES or not isinstance(reason, str) or not REASON_CODE.fullmatch(reason):
                    invalid += 1
                    continue
                failure_stage = stage
            elif "failure_stage" in trial or "reason_code" in trial:
                invalid += 1
                continue
            acceptance = trial.get("user_acceptance")
            if acceptance is not None and acceptance not in {"ACCEPTED", "REJECTED", "NOT_RECORDED"}:
                invalid += 1
                continue
        has_output = trial.get("output") is not None or trial.get("sha256") is not None
        output_valid = _bound_output(root, trial) if has_output else False
        if has_output and not output_valid:
            invalid += 1
            continue
        if result_status == "COMPLETE" and not output_valid:
            invalid += 1
            continue
        observations.append(trial)
        if failure_stage:
            failures[failure_stage] += 1
        if output_valid and result_status == "COMPLETE":
            artifacts.append(trial)
    visual: dict[str, dict[str, int | str]] = {}
    for dimension in sorted(DIMENSIONS):
        ratings = []
        for trial in artifacts:
            review = trial.get("visual_review")
            if not isinstance(review, dict) or review.get("reviewer_type") != "human" or not review.get("reviewer"):
                continue
            assessment = review.get("dimensions")
            if isinstance(assessment, dict) and isinstance(assessment.get(dimension), str) and assessment[dimension] in {"PASS", "REVISE"}:
                ratings.append(assessment[dimension])
        visual[dimension] = {"status": "RECORDED_HUMAN_REVIEW" if ratings else "UNVERIFIED",
                             "sample_count": len(ratings), "pass": ratings.count("PASS"), "revise": ratings.count("REVISE")}
    profile_reports = []
    missing_cells = []
    if dataset:
        observed_cells = {(item["profile_id"], item["case_id"]) for item in observations}
        for profile in dataset["profiles"]:
            profile_trials = [item for item in observations if item["profile_id"] == profile["id"]]
            expected_cases = [item["id"] for item in dataset["cases"]]
            present = sorted({item["case_id"] for item in profile_trials})
            missing = sorted(set(expected_cases) - set(present))
            missing_cells.extend({"profile_id": profile["id"], "case_id": case_id} for case_id in missing)
            profile_reports.append({
                "profile_id": profile["id"], "archetype": profile["archetype"],
                "expected_cases": len(expected_cases), "observed_cases": len(present),
                "complete_trials": sum(item.get("status") == "COMPLETE" for item in profile_trials),
                "failed_trials": sum(item.get("status") == "FAILED" for item in profile_trials),
                "coverage_status": "RECORDED" if not missing else "PARTIAL" if present else "UNKNOWN",
                "missing_case_ids": missing,
                "failures_by_stage": {stage: sum(item.get("status") == "FAILED" and item.get("failure_stage") == stage
                                                  for item in profile_trials) for stage in FAILURE_STAGES},
            })
        coverage = {"status": "RECORDED" if not missing_cells else "PARTIAL" if observed_cells else "UNKNOWN",
                    "dataset_id": dataset["id"], "expected_cells": len(dataset["profiles"]) * len(dataset["cases"]),
                    "observed_cells": len(observed_cells), "missing_cells": missing_cells,
                    "profiles": profile_reports}
    else:
        coverage = {"status": "UNVERIFIED", "dataset_id": None, "expected_cells": None,
                    "observed_cells": None, "missing_cells": [], "profiles": []}
    return {"version": 1, "status": "RECORDED" if observations else "UNKNOWN", "read_only": True,
            "dataset_coverage": coverage,
            "trials_observed": len(observations), "artifact_bound_samples": len(artifacts),
            "invalid_or_unobserved": invalid, "failures_by_stage": failures,
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
    except (OSError, ValueError, TypeError, yaml.YAMLError):
        print(json.dumps({"status": "BLOCKED", "reason_code": "benchmark_input_invalid"}))
        return 2
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
