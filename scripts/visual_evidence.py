#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml

PASS_DECISIONS = {"PASS", "PASS_WITH_COMMENTS"}
REVIEW_DECISIONS = PASS_DECISIONS | {"REQUEST_CHANGES", "BLOCK"}
PHASES = ("before", "after")


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def artifact_exists(project: Path, value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    path = Path(value)
    if not path.is_absolute():
        path = project / path
    return path.is_file() and path.stat().st_size > 0


def validate_capture(errors: list[str], project: Path, phase: str, index: int, capture: object) -> None:
    prefix = f"verification.{phase}[{index}]"
    require(errors, isinstance(capture, dict), f"{prefix} must be an object")
    if not isinstance(capture, dict):
        return

    require(errors, bool(capture.get("id")), f"{prefix}.id is required")
    require(errors, capture.get("kind") in {"screenshot", "rendered_artifact"}, f"{prefix}.kind must be screenshot or rendered_artifact")
    require(errors, bool(capture.get("target")), f"{prefix}.target is required")
    require(errors, bool(capture.get("state")), f"{prefix}.state is required")
    require(errors, artifact_exists(project, capture.get("artifact")), f"{prefix}.artifact must reference a non-empty captured artifact")

    viewport = capture.get("viewport")
    require(errors, isinstance(viewport, dict), f"{prefix}.viewport is required")
    if isinstance(viewport, dict):
        require(errors, isinstance(viewport.get("width"), int) and viewport.get("width", 0) > 0, f"{prefix}.viewport.width must be a positive integer")
        require(errors, isinstance(viewport.get("height"), int) and viewport.get("height", 0) > 0, f"{prefix}.viewport.height must be a positive integer")

    provenance = capture.get("provenance")
    require(errors, isinstance(provenance, dict), f"{prefix}.provenance is required")
    if isinstance(provenance, dict):
        require(errors, bool(provenance.get("provider")), f"{prefix}.provenance.provider is required")
        require(errors, bool(provenance.get("source_revision")), f"{prefix}.provenance.source_revision is required")
        require(errors, bool(provenance.get("captured_at")), f"{prefix}.provenance.captured_at is required")


def validate(audit_path: Path, project: Path) -> dict:
    data = yaml.safe_load(audit_path.read_text(encoding="utf-8")) or {}
    errors: list[str] = []

    require(errors, data.get("version") == 1, "version must be 1")
    require(errors, data.get("mode") in {"V1", "V2"}, "mode must be V1 or V2")
    require(errors, data.get("status") in {"in_progress", "pass", "pass_with_comments", "request_changes", "blocked"}, "status is invalid")

    verification = data.get("verification")
    require(errors, isinstance(verification, dict), "verification is required")
    captures: dict[str, list] = {}
    if isinstance(verification, dict):
        for phase in PHASES:
            value = verification.get(phase)
            require(errors, isinstance(value, list), f"verification.{phase} must be a list")
            captures[phase] = value if isinstance(value, list) else []
            for index, capture in enumerate(captures[phase]):
                validate_capture(errors, project, phase, index, capture)

        required_viewports = verification.get("required_viewports") or []
        require(errors, isinstance(required_viewports, list), "verification.required_viewports must be a list")
        captured_labels = {
            capture.get("viewport", {}).get("label")
            for phase in PHASES
            for capture in captures.get(phase, [])
            if isinstance(capture, dict) and isinstance(capture.get("viewport"), dict)
        }
        for viewport in required_viewports if isinstance(required_viewports, list) else []:
            require(errors, viewport in captured_labels, f"required viewport not captured: {viewport}")

        required_states = verification.get("required_states") or []
        require(errors, isinstance(required_states, list), "verification.required_states must be a list")
        captured_states = {
            capture.get("state")
            for phase in PHASES
            for capture in captures.get(phase, [])
            if isinstance(capture, dict)
        }
        for state in required_states if isinstance(required_states, list) else []:
            require(errors, state in captured_states, f"required state not captured: {state}")

    findings = data.get("findings") or []
    require(errors, isinstance(findings, list), "findings must be a list")
    if isinstance(findings, list):
        for index, finding in enumerate(findings):
            prefix = f"findings[{index}]"
            require(errors, isinstance(finding, dict), f"{prefix} must be an object")
            if not isinstance(finding, dict):
                continue
            if finding.get("status") in {"fixed", "closed"}:
                root = finding.get("root_cause")
                require(errors, isinstance(root, dict) and any(root.get(key) for key in ("source", "style", "token", "mechanism")), f"{prefix} closed finding requires implementation root-cause evidence")

    review = data.get("review")
    require(errors, isinstance(review, dict), "review is required")
    if isinstance(review, dict):
        decision = review.get("decision")
        require(errors, decision in REVIEW_DECISIONS | {"PENDING"}, "review.decision is invalid")
        require(errors, review.get("quality_assessed_by") in {"human", "agent_eval", "visual_review"}, "review.quality_assessed_by must identify a visual quality reviewer")
        require(errors, isinstance(review.get("checks"), list) and bool(review.get("checks")), "review.checks must contain observable review results")

    status = data.get("status")
    if status in {"pass", "pass_with_comments"}:
        require(errors, bool(captures.get("before")), "PASS requires before rendered evidence")
        require(errors, bool(captures.get("after")), "PASS requires after rendered evidence")
        if isinstance(review, dict):
            require(errors, review.get("decision") in PASS_DECISIONS, "PASS requires a passing Visual Quality Review decision")
        remaining = data.get("remaining_material_findings") or []
        require(errors, not remaining, "PASS cannot retain material findings")

    return {
        "valid": not errors,
        "errors": errors,
        "evidence_integrity": "PASS" if not errors else "FAIL",
        "visual_quality_inferred": False,
        "note": "Deterministic validation checks evidence integrity only; it never infers visual quality from artifact existence.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate provider-neutral rendered visual evidence integrity.")
    parser.add_argument("audit", type=Path)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args()

    result = validate(args.audit.resolve(), args.project.resolve())
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"VISUAL EVIDENCE {'PASSED' if result['valid'] else 'FAILED'}")
        for error in result["errors"]:
            print(f"- {error}")
        print(result["note"])
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
