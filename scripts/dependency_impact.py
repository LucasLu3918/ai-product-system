"""Classify dependency updates and recommend deterministic validation evidence."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config/dependency-policy.yaml"
ECOSYSTEMS = {"pip", "github-actions"}

# Closed set of path patterns a documentation exemption may name. Policy can
# narrow it but never widen it; each pattern is bound to exactly one line shape.
EXEMPTION_PATH_SHAPES = {
    ".github/workflows/*.yml": "github-actions",
    ".github/workflows/*.yaml": "github-actions",
    "requirements*.txt": "pip",
    "constraints/*.txt": "pip",
}
PURE = "PURE_DEPENDENCY_UPDATE"
NOT_PURE = "NOT_PURE"
ACTION_LINE = re.compile(
    r"(?P<prefix> *(?:- +)?)uses: (?P<action>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_./-]+)?)"
    r"@(?P<ref>\S+?)(?: +# +(?P<ver>v?[0-9]+(?:\.[0-9]+){0,3}))?",
    re.ASCII,
)
PINNED_SHA = re.compile(r"[0-9a-f]{40}", re.ASCII)
PIP_LINE = re.compile(r"(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)==(?P<ver>[0-9]+(?:\.[0-9]+){0,3})", re.ASCII)
HUNK = re.compile(r"@@ -\d+(?:,(?P<old>\d+))? \+\d+(?:,(?P<new>\d+))? @@")


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
    return errors + validate_documentation_exemption(policy)


def validate_documentation_exemption(policy: dict[str, Any]) -> list[str]:
    exemption = policy.get("documentation_exemption")
    if exemption is None:
        return []
    if not isinstance(exemption, dict):
        return ["documentation_exemption must be a mapping"]
    errors: list[str] = []
    if not isinstance(exemption.get("enabled"), bool):
        errors.append("documentation_exemption.enabled must be a boolean")
    paths = exemption.get("paths")
    if not isinstance(paths, list) or not paths:
        errors.append("documentation_exemption.paths must be a non-empty list")
    else:
        for path in paths:
            if path not in EXEMPTION_PATH_SHAPES:
                errors.append(f"documentation_exemption.paths entry is not an allowed dependency manifest pattern: {path}")
    for key, ceiling in (("max_files", 50), ("max_line_pairs", 200)):
        value = exemption.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= ceiling:
            errors.append(f"documentation_exemption.{key} must be an integer between 1 and {ceiling}")
    if not isinstance(exemption.get("high_risk_classes_exempt"), bool):
        errors.append("documentation_exemption.high_risk_classes_exempt must be a boolean")
    return errors


def _release(version: str) -> tuple[int, ...]:
    parts = [int(part) for part in version.removeprefix("v").split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def _exemption_path_shape(path: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        # fnmatch lets "*" cross "/"; require the same directory depth as the pattern.
        if fnmatch.fnmatchcase(path, pattern) and path.count("/") == pattern.count("/"):
            return EXEMPTION_PATH_SHAPES[pattern]
    return None


class _NotPure(Exception):
    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.detail = detail[:200]


def _git(root: Path, *args: str) -> str:
    # Bytes, not text mode: universal-newline decoding would hide CR characters.
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)
    if proc.returncode:
        raise _NotPure("GIT_ERROR", f"git {args[0]} failed")
    return proc.stdout.decode("utf-8")


def _pair_action(path: str, old: str, new: str) -> dict[str, Any]:
    before, after = ACTION_LINE.fullmatch(old), ACTION_LINE.fullmatch(new)
    if not before or not after:
        raise _NotPure("OUT_OF_SHAPE", f"{path}: line is not a pinned uses: reference")
    if before["prefix"] != after["prefix"]:
        raise _NotPure("OUT_OF_SHAPE", f"{path}: uses: indentation or list position changed")
    if before["action"] != after["action"]:
        raise _NotPure("ACTION_IDENTITY_CHANGED", f"{path}: {before['action']} -> {after['action']}")
    if not PINNED_SHA.fullmatch(before["ref"]) or not PINNED_SHA.fullmatch(after["ref"]):
        raise _NotPure("UNPINNED_REFERENCE", f"{path}: {after['action']} is not pinned to a full commit SHA")
    if (before["ver"] is None) != (after["ver"] is None):
        raise _NotPure("OUT_OF_SHAPE", f"{path}: version comment added or removed")
    if before["ref"] == after["ref"] and before["ver"] == after["ver"]:
        raise _NotPure("OUT_OF_SHAPE", f"{path}: uses: line changed without a reference change")
    if before["ver"] is not None and _release(after["ver"]) < _release(before["ver"]):
        raise _NotPure("ACTION_DOWNGRADE", f"{path}: {after['action']} {before['ver']} -> {after['ver']}")
    owner_repo = "/".join(after["action"].split("/")[:2])
    return {
        "path": path,
        "ecosystem": "github-actions",
        "name": owner_repo,
        "current_version": before["ver"] or before["ref"],
        "target_version": after["ver"] or after["ref"],
        "current_ref": before["ref"],
        "target_ref": after["ref"],
        "repinned_same_version": before["ver"] is not None and before["ver"] == after["ver"],
    }


def _pair_pip(path: str, old: str, new: str) -> dict[str, Any]:
    before, after = PIP_LINE.fullmatch(old), PIP_LINE.fullmatch(new)
    if not before or not after:
        raise _NotPure("OUT_OF_SHAPE", f"{path}: line is not an exact name==version pin")
    if normalize_name("pip", before["name"]) != normalize_name("pip", after["name"]):
        raise _NotPure("PACKAGE_IDENTITY_CHANGED", f"{path}: {before['name']} -> {after['name']}")
    if _release(after["ver"]) == _release(before["ver"]):
        raise _NotPure("PIP_NO_CHANGE", f"{path}: {after['name']} version unchanged")
    if _release(after["ver"]) < _release(before["ver"]):
        raise _NotPure("PIP_DOWNGRADE", f"{path}: {after['name']} {before['ver']} -> {after['ver']}")
    return {
        "path": path,
        "ecosystem": "pip",
        "name": after["name"],
        "current_version": before["ver"],
        "target_version": after["ver"],
    }


def _parse_patch(patch: str, shapes: dict[str, str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    path: str | None = None
    removed: list[str] = []
    added: list[str] = []

    def flush() -> None:
        if len(removed) != len(added):
            raise _NotPure("UNPAIRED_LINE", f"{path}: hunk adds or removes lines without a 1:1 replacement")
        pair = _pair_action if shapes[str(path)] == "github-actions" else _pair_pip
        items.extend(pair(str(path), old, new) for old, new in zip(removed, added))
        removed.clear()
        added.clear()

    in_hunk = False
    for line in patch.split("\n"):
        if line.startswith("diff --git "):
            if in_hunk:
                flush()
            in_hunk, path = False, None
            continue
        if not in_hunk:
            if line.startswith("+++ "):
                target = line[4:]
                if not target.startswith("b/") or target[2:] not in shapes:
                    raise _NotPure("PATH_NOT_ALLOWED", "patch target is not an allowlisted manifest")
                path = target[2:]
            elif line.startswith("@@"):
                if path is None:
                    raise _NotPure("OUT_OF_SHAPE", "hunk without a file target")
                in_hunk = True
                if not HUNK.match(line):
                    raise _NotPure("OUT_OF_SHAPE", f"{path}: unrecognized hunk header")
            continue
        if line.startswith("@@"):
            flush()
            if not HUNK.match(line):
                raise _NotPure("OUT_OF_SHAPE", f"{path}: unrecognized hunk header")
        elif line.startswith("-"):
            if added:
                raise _NotPure("UNPAIRED_LINE", f"{path}: interleaved hunk")
            removed.append(line[1:])
        elif line.startswith("+"):
            added.append(line[1:])
        elif line == "":
            continue
        else:
            # Context lines cannot appear with -U0; "\ No newline" and anything else fail closed.
            raise _NotPure("OUT_OF_SHAPE", f"{path}: unsupported patch line")
    if in_hunk:
        flush()
    return items


def pure_dependency_update(
    base: str,
    head: str | None = "HEAD",
    root: Path = ROOT,
    *,
    policy: dict[str, Any] | None = None,
    planned_paths: list[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    """Decide whether a candidate only bumps pinned dependency versions.

    Content-only and deterministic: labels, authors and commit messages are never
    consulted. Every failure is NOT_PURE so callers keep their full rules.
    """
    result: dict[str, Any] = {
        "status": NOT_PURE,
        "reason": "",
        "detail": "",
        "files": [],
        "items": [],
        "automatic_merge_authorized": False,
        "human_decision_required": True,
        "human_review_required": True,
    }
    try:
        if policy is None:
            policy = yaml.safe_load((root / "config/dependency-policy.yaml").read_text(encoding="utf-8")) or {}
        if not isinstance(policy, dict) or validate_policy(policy):
            raise _NotPure("CLASSIFIER_BLOCKED", "dependency policy is invalid")
        exemption = policy.get("documentation_exemption") or {}
        if exemption.get("enabled") is not True:
            raise _NotPure("DISABLED", "documentation exemption is disabled by policy")
        if planned_paths:
            raise _NotPure("PLANNED_PATHS_PRESENT", "prospective paths cannot be content-verified")
        rev = [f"{base}...{head}"] if head is not None else [base]
        if head is None and _git(root, "ls-files", "--others", "--exclude-standard").strip():
            raise _NotPure("UNTRACKED_PRESENT", "working tree has untracked files")
        common = ["diff", "--no-renames", "--no-ext-diff", "--no-textconv", "--full-index", *rev]
        raw = [line for line in _git(root, *common, "--raw", "--").splitlines() if line]
        if not raw:
            raise _NotPure("NO_CHANGES", "candidate has no changed files")
        if len(raw) > int(exemption["max_files"]):
            raise _NotPure("SIZE_LIMIT", f"{len(raw)} files exceed max_files")
        shapes: dict[str, str] = {}
        for entry in raw:
            meta, _, path = entry.partition("\t")
            fields = meta.split()
            if len(fields) != 5 or fields[4] != "M" or fields[0] != ":100644" or fields[1] != "100644":
                raise _NotPure("FILE_ENTRY_NOT_ALLOWED", f"{path}: not a plain in-place modification")
            shape = _exemption_path_shape(path, list(exemption["paths"]))
            if shape is None:
                raise _NotPure("PATH_NOT_ALLOWED", f"{path}: not an allowlisted dependency manifest")
            shapes[path] = shape
        for entry in _git(root, *common, "--numstat", "--").splitlines():
            if entry.startswith("-\t"):
                raise _NotPure("FILE_ENTRY_NOT_ALLOWED", "binary change")
        patch = _git(root, *common, "-U0", "--")
        if not patch.isascii() or "\r" in patch or "\t" in "".join(
            line for line in patch.split("\n") if line[:1] in {"+", "-"} and not line.startswith(("+++ ", "--- "))
        ):
            raise _NotPure("OUT_OF_SHAPE", "changed lines must be ASCII without CR or tab characters")
        items = _parse_patch(patch, shapes)
        if len(items) > int(exemption["max_line_pairs"]):
            raise _NotPure("SIZE_LIMIT", f"{len(items)} line pairs exceed max_line_pairs")
        if not items or {item["path"] for item in items} != set(shapes):
            raise _NotPure("OUT_OF_SHAPE", "every changed file must contain a recognized update")
        for item in items:
            classification = classify_dependency(item, policy, include_plan=False)
            if classification.get("status") != "READY":
                raise _NotPure("CLASSIFIER_BLOCKED", f"{item['path']}: dependency classification blocked")
            item.update({key: classification[key] for key in ("classification", "risk", "required_evidence", "human_review_required")})
            if classification["risk"] == "HIGH" and exemption["high_risk_classes_exempt"] is not True:
                raise _NotPure("HIGH_RISK_NOT_EXEMPT", f"{item['name']} is {classification['classification']}")
        result.update({
            "status": PURE,
            "reason": PURE,
            "files": sorted(shapes),
            "items": items,
            "human_review_required": any(item["human_review_required"] for item in items),
            "policy_sha256": hashlib.sha256(
                json.dumps(policy, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            ).hexdigest(),
            "diff_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
            "exempted_scope": "documentation_requirements_only",
        })
    except _NotPure as exc:
        result.update({"reason": exc.reason, "detail": exc.detail})
    except (OSError, TypeError, ValueError, KeyError, yaml.YAMLError) as exc:
        result.update({"reason": "INTERNAL_ERROR", "detail": type(exc).__name__})
    return result


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
    diff_parser = subparsers.add_parser("classify-diff", help="decide whether a candidate is a pure dependency update")
    diff_parser.add_argument("--base", required=True)
    diff_parser.add_argument("--head", default="HEAD")
    diff_parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    diff_parser.add_argument("--output", type=Path)
    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--input", required=True, type=Path, help="versioned YAML dependency inventory")
    report_parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    report_parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        policy = yaml.safe_load(args.policy.read_text(encoding="utf-8")) or {}
        if not isinstance(policy, dict):
            raise TypeError("policy must be a mapping")
        if args.command == "classify-diff":
            report = pure_dependency_update(args.base, args.head, ROOT, policy=policy)
        elif args.command == "report":
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
    return 0 if report.get("status") in {"READY", "READY_FOR_HUMAN_REVIEW", PURE} else 1


if __name__ == "__main__":
    raise SystemExit(dependency_impact_main())
