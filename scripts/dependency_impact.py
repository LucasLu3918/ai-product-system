"""Classify dependency updates and recommend deterministic validation evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config/dependency-policy.yaml"
ECOSYSTEMS = {"pip", "github-actions"}


def normalize_name(ecosystem: str, name: str) -> str:
    value = name.strip().casefold()
    if ecosystem == "pip":
        return re.sub(r"[-_.]+", "-", value)
    if ecosystem == "github-actions":
        return value.split("@", 1)[0]
    return value


def validate_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if policy.get("version") != 1:
        errors.append("version must be 1")
    if policy.get("automatic_merge_authorized") is not False:
        errors.append("automatic_merge_authorized must remain false")
    if policy.get("automatic_policy_changes_authorized") is not False:
        errors.append("automatic_policy_changes_authorized must remain false")
    classes = policy.get("classes")
    if not isinstance(classes, dict) or not classes:
        errors.append("classes must be a non-empty mapping")
        classes = {}
    for class_name, definition in classes.items():
        if not isinstance(definition, dict):
            errors.append(f"classes.{class_name} must be a mapping")
            continue
        if definition.get("risk") not in {"LOW", "MEDIUM", "HIGH"}:
            errors.append(f"classes.{class_name}.risk is invalid")
        if not isinstance(definition.get("validation_plan"), list) or not definition["validation_plan"]:
            errors.append(f"classes.{class_name}.validation_plan must be non-empty")
        if not isinstance(definition.get("required_evidence"), list):
            errors.append(f"classes.{class_name}.required_evidence must be a list")
    default_class = policy.get("default_class")
    if default_class not in classes:
        errors.append("default_class must name a configured class")

    rules = policy.get("rules")
    if not isinstance(rules, list):
        errors.append("rules must be a list")
        rules = []
    seen: set[tuple[str, str]] = set()
    wildcards: set[str] = set()
    for index, rule in enumerate(rules):
        prefix = f"rules[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        ecosystem = str(rule.get("ecosystem") or "").strip().casefold()
        name = str(rule.get("name") or "").strip()
        class_name = rule.get("class")
        if ecosystem not in ECOSYSTEMS:
            errors.append(f"{prefix}.ecosystem is unsupported")
        if not name:
            errors.append(f"{prefix}.name is required")
        if class_name not in classes:
            errors.append(f"{prefix}.class must name a configured class")
        key = (ecosystem, "*" if name == "*" else normalize_name(ecosystem, name))
        if key in seen:
            errors.append(f"{prefix} duplicates dependency match {ecosystem}:{name}")
        seen.add(key)
        if name == "*":
            if ecosystem in wildcards:
                errors.append(f"{prefix} duplicates wildcard ecosystem rule")
            wildcards.add(ecosystem)
    return errors


def classify_dependency(
    dependency: dict[str, Any], policy: dict[str, Any], *, include_plan: bool = True
) -> dict[str, Any]:
    errors = validate_policy(policy)
    if errors:
        return {"status": "BLOCKED", "errors": errors, "automatic_merge_authorized": False}
    name = str(dependency.get("name") or "").strip()
    ecosystem = str(dependency.get("ecosystem") or "").strip().casefold()
    if not name or ecosystem not in ECOSYSTEMS:
        return {
            "status": "BLOCKED",
            "errors": ["dependency name and supported ecosystem (pip or github-actions) are required"],
            "automatic_merge_authorized": False,
        }

    normalized = normalize_name(ecosystem, name)
    policy_digest = hashlib.sha256(
        json.dumps(policy, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    exact_rule = next(
        (
            rule
            for rule in policy["rules"]
            if rule["ecosystem"].casefold() == ecosystem
            and rule["name"] != "*"
            and normalize_name(ecosystem, str(rule["name"])) == normalized
        ),
        None,
    )
    rule = exact_rule or next(
        (
            candidate
            for candidate in policy["rules"]
            if candidate["ecosystem"].casefold() == ecosystem and candidate["name"] == "*"
        ),
        None,
    )
    class_name = str((rule or {}).get("class") or policy["default_class"])
    class_policy = policy["classes"][class_name]
    result: dict[str, Any] = {
        "status": "READY",
        "dependency": {
            "name": name,
            "normalized_name": normalized,
            "ecosystem": ecosystem,
            "current_version": str(dependency.get("current_version") or ""),
            "target_version": str(dependency.get("target_version") or ""),
        },
        "classification": class_name,
        "risk": class_policy["risk"],
        "matched_rule": "exact" if exact_rule else "ecosystem_default" if rule else "unclassified_default",
        "policy_sha256": policy_digest,
        "required_evidence": list(class_policy["required_evidence"]),
        "automatic_merge_authorized": False,
        "automatic_policy_changes_authorized": False,
        "human_review_required": class_policy["risk"] == "HIGH",
        "human_decision_required": True,
    }
    if include_plan:
        result["recommended_validation_plan"] = list(class_policy["validation_plan"])
    return result


def build_dependency_report(document: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    if document.get("version") != 1:
        return {"version": 1, "status": "BLOCKED", "errors": ["inventory version must be 1"], "items": []}
    dependencies = document.get("dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        return {"version": 1, "status": "NOT_READY", "errors": ["dependencies must be a non-empty list"], "items": []}
    identities: set[tuple[str, str]] = set()
    duplicate_errors: list[str] = []
    for index, dependency in enumerate(dependencies):
        if not isinstance(dependency, dict):
            continue
        ecosystem = str(dependency.get("ecosystem") or "").strip().casefold()
        name = str(dependency.get("name") or "").strip()
        identity = (ecosystem, normalize_name(ecosystem, name))
        if identity in identities:
            duplicate_errors.append(f"dependencies[{index}] duplicates {ecosystem}:{name}")
        identities.add(identity)
    items = [classify_dependency(row, policy) if isinstance(row, dict) else {
        "status": "BLOCKED", "errors": ["dependency entry must be a mapping"], "automatic_merge_authorized": False
    } for row in dependencies]
    items.sort(key=lambda item: (
        (item.get("dependency") or {}).get("ecosystem", ""),
        (item.get("dependency") or {}).get("normalized_name", ""),
    ))
    errors = duplicate_errors + [error for item in items for error in item.get("errors", [])]
    return {
        "version": 1,
        "status": "BLOCKED" if errors else "READY_FOR_HUMAN_REVIEW",
        "dependency_count": len(items),
        "items": items,
        "errors": errors,
        "automatic_merge_authorized": False,
        "automatic_policy_changes_authorized": False,
        "human_decision_required": True,
    }


def dependency_impact_main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("classify", "plan"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--name", required=True)
        sub.add_argument("--ecosystem", required=True, choices=sorted(ECOSYSTEMS))
        sub.add_argument("--current-version", default="")
        sub.add_argument("--target-version", default="")
        sub.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
        sub.add_argument("--output", type=Path)
    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--input", required=True, type=Path, help="versioned YAML dependency inventory")
    report_parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    report_parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        policy = yaml.safe_load(args.policy.read_text(encoding="utf-8")) or {}
        if not isinstance(policy, dict):
            raise TypeError("policy must be a mapping")
        if args.command == "report":
            document = yaml.safe_load(args.input.read_text(encoding="utf-8")) or {}
            if not isinstance(document, dict):
                raise TypeError("inventory must be a mapping")
            report = build_dependency_report(document, policy)
        else:
            report = classify_dependency(
                {"name": args.name, "ecosystem": args.ecosystem, "current_version": args.current_version,
                 "target_version": args.target_version},
                policy,
                include_plan=args.command == "plan",
            )
    except (OSError, yaml.YAMLError, TypeError, ValueError) as exc:
        report = {"status": "BLOCKED", "errors": [type(exc).__name__], "automatic_merge_authorized": False}
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report.get("status") in {"READY", "READY_FOR_HUMAN_REVIEW"} else 1


if __name__ == "__main__":
    raise SystemExit(dependency_impact_main())
