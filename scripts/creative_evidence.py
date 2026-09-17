#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import yaml

PASS_DECISIONS = {"PASS", "PASS WITH COMMENTS"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _path(project: Path, value: object) -> Path:
    return project / str(value or "")


def validate(document: dict, project: Path) -> dict:
    errors: list[str] = []
    if document.get("version") != 1:
        errors.append("version must be 1")

    status = str(document.get("status") or "").upper()
    if status not in {"PENDING", "PASS", "FAIL"}:
        errors.append("status must be PENDING, PASS, or FAIL")

    mode = str(document.get("mode") or "")
    if mode not in {"vague_visual_request", "user_asset_banner"}:
        errors.append("mode must be vague_visual_request or user_asset_banner")

    intake = document.get("intake") or {}
    if intake.get("approved_brand_visual_system_loaded") is not True:
        errors.append("approved Brand/Visual System must be loaded before creative execution")
    if intake.get("user_assets_loaded") is not True:
        errors.append("user-owned assets must be loaded before creative execution")

    references = document.get("references") or {}
    if references.get("analyzed_by_aspect") is not True:
        errors.append("references must be analyzed by visual aspect")
    if references.get("literal_copy") is not False:
        errors.append("references must not be copied literally")
    aspects = references.get("aspects") or []
    for expected in ("layout", "color", "typography", "imagery"):
        if expected not in aspects:
            errors.append(f"references.aspects missing {expected}")
    if mode == "vague_visual_request" and references.get("current_research_used_when_unclear") is not True:
        errors.append("vague visual request requires current reference research when direction remains unclear")

    direction = document.get("direction") or {}
    candidates = direction.get("candidates") or []
    if not isinstance(candidates, list) or not 2 <= len(candidates) <= 3:
        errors.append("direction.candidates must contain 2-3 directions")
        candidates = []
    candidate_ids = [str(item.get("id") or "") for item in candidates if isinstance(item, dict)]
    fingerprints = [str(item.get("fingerprint") or "") for item in candidates if isinstance(item, dict)]
    if len(candidate_ids) != len(set(candidate_ids)) or any(not value for value in candidate_ids):
        errors.append("direction candidate ids must be unique and non-empty")
    if len(fingerprints) != len(set(fingerprints)) or any(not value for value in fingerprints):
        errors.append("direction candidate fingerprints must be materially distinct and non-empty")
    selected = str(direction.get("selected") or "")
    if selected not in candidate_ids:
        errors.append("direction.selected must reference a candidate")

    calibration = document.get("calibration") or {}
    if not calibration.get("likes"):
        errors.append("calibration.likes is required")
    if not calibration.get("dislikes"):
        errors.append("calibration.dislikes is required")
    if not calibration.get("aspect_mix"):
        errors.append("calibration.aspect_mix is required")

    approval = document.get("approval") or {}
    if str(approval.get("status") or "").lower() != "approved":
        errors.append("Creative Direction must be approved")
    if approval.get("before_broad_implementation") is not True:
        errors.append("Creative Direction approval must precede broad implementation")

    artifacts = document.get("artifacts") or {}
    for key in ("creative_brief", "reference_board", "creative_direction", "visual_review"):
        value = artifacts.get(key)
        path = _path(project, value)
        if not value or not path.is_file() or path.stat().st_size == 0:
            errors.append(f"artifacts.{key} must reference a non-empty existing file")

    assets = document.get("assets") or []
    required_asset_types: set[str] = set()
    if not isinstance(assets, list):
        errors.append("assets must be a list")
        assets = []
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            errors.append(f"assets[{index}] must be a mapping")
            continue
        if asset.get("required") is True:
            required_asset_types.add(str(asset.get("type") or ""))
        asset_path_value = asset.get("path")
        asset_path = _path(project, asset_path_value)
        if not asset_path_value or not asset_path.is_file():
            errors.append(f"assets[{index}].path must reference an existing file")
            continue
        actual = sha256_file(asset_path)
        if asset.get("sha256_before") != actual or asset.get("sha256_after") != actual:
            errors.append(f"assets[{index}] changed from the recorded user-owned source bytes")
        if asset.get("used_in_render") is not True:
            errors.append(f"assets[{index}] must be used in the render")
        if asset.get("visible") is not True:
            errors.append(f"assets[{index}] must be visible in the render")
        if asset.get("crop_reviewed") is not True:
            errors.append(f"assets[{index}] must have crop/presentation review evidence")

    if mode == "user_asset_banner":
        for required_type in ("logo", "product"):
            if required_type not in required_asset_types:
                errors.append(f"user_asset_banner requires a preserved required {required_type} asset")

    renders = document.get("renders") or {}
    captures = renders.get("captures") or []
    if not isinstance(captures, list) or len(captures) < 2:
        errors.append("renders.captures must include at least desktop and mobile")
        captures = []
    viewport_labels: set[str] = set()
    for index, capture in enumerate(captures):
        if not isinstance(capture, dict):
            errors.append(f"renders.captures[{index}] must be a mapping")
            continue
        viewport = capture.get("viewport") or {}
        label = str(viewport.get("label") or "")
        viewport_labels.add(label)
        width = viewport.get("width")
        height = viewport.get("height")
        if not isinstance(width, int) or width <= 0 or not isinstance(height, int) or height <= 0:
            errors.append(f"renders.captures[{index}] viewport dimensions must be positive integers")
        artifact_value = capture.get("artifact")
        artifact = _path(project, artifact_value)
        if not artifact_value or not artifact.is_file() or artifact.stat().st_size == 0:
            errors.append(f"renders.captures[{index}].artifact must reference a non-empty screenshot")
    for label in ("desktop", "mobile"):
        if label not in viewport_labels:
            errors.append(f"renders.captures missing {label} viewport")

    render_checks = renders.get("checks") or {}
    for key in ("required_assets_visible", "safe_area_respected", "headline_cta_visible", "crop_reviewed", "no_horizontal_overflow"):
        if render_checks.get(key) is not True:
            errors.append(f"renders.checks.{key} must be true")

    review = document.get("review") or {}
    decision = str(review.get("decision") or "").upper()
    if decision not in {"PASS", "PASS WITH COMMENTS", "REQUEST CHANGES", "BLOCK"}:
        errors.append("review.decision is invalid")
    if review.get("quality_assessed_by") != "visual_review":
        errors.append("review.quality_assessed_by must be visual_review")
    review_checks = review.get("checks") or []
    for expected in ("composition", "headline_cta_readability", "safe_area", "crop", "brand_consistency"):
        if expected not in review_checks:
            errors.append(f"review.checks missing {expected}")

    if status == "PASS" and decision not in PASS_DECISIONS:
        errors.append("PASS requires a passing Visual Quality Review decision")

    return {
        "valid": not errors,
        "status": status,
        "mode": mode,
        "errors": errors,
        "candidate_direction_count": len(candidates),
        "selected_direction": selected,
        "preserved_required_asset_types": sorted(required_asset_types),
        "render_viewports": sorted(viewport_labels),
        "visual_quality_inferred": False,
        "success_inferred_from_artifact_existence": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AIPS creative-direction evidence integrity.")
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--project", type=Path, default=Path("."))
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args()

    if not args.evidence.is_file():
        print(f"creative evidence file not found: {args.evidence}", file=sys.stderr)
        return 2
    try:
        document = yaml.safe_load(args.evidence.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        print(f"creative evidence YAML invalid: {exc}", file=sys.stderr)
        return 2

    result = validate(document, args.project.resolve())
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("CREATIVE EVIDENCE " + ("PASSED" if result["valid"] else "FAILED"))
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
