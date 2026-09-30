#!/usr/bin/env python3
"""Validate OpenAPI specs, conservatively classify diffs, and bind test evidence."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import unquote, urlsplit

import yaml

SUPPORTED_OPENAPI = re.compile(r"^3\.(?:0|1|2)\.\d+(?:[-+].*)?$")
HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace", "query"}
DOC_FIELDS = {"summary", "description", "externalDocs", "example", "examples"}


class ContractError(Exception):
    """Invalid input or evidence that cannot be safely evaluated."""


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256_stream(stream: Any) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(65536), b""):
        digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_revision(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False, capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return "unbound"
    return result.stdout.strip()


def load_yaml(path: Path) -> Any:
    try:
        class UniqueKeyLoader(yaml.SafeLoader):
            pass

        def construct_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
            mapping: dict[Any, Any] = {}
            for key_node, value_node in node.value:
                key = loader.construct_object(key_node, deep=deep)
                try:
                    duplicate = key in mapping
                except TypeError as exc:
                    raise ContractError("YAML mapping keys must be scalar values") from exc
                if duplicate:
                    raise ContractError(f"duplicate YAML key: {key}")
                mapping[key] = loader.construct_object(value_node, deep=deep)
            return mapping

        UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
        return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ContractError(f"cannot read YAML/JSON input: {exc}") from exc


def _repo_path(path: Path, root: Path) -> str:
    resolved = path.resolve(strict=True)
    try:
        return resolved.relative_to(root.resolve(strict=True)).as_posix()
    except ValueError as exc:
        raise ContractError("input or reference escapes the permitted repository root") from exc


def _check_local_refs(doc: Any, source: Path, root: Path, visited: set[Path], seen_values: set[int] | None = None) -> None:
    if seen_values is None:
        seen_values = set()
    if isinstance(doc, (dict, list)):
        if id(doc) in seen_values:
            return
        seen_values.add(id(doc))
    if isinstance(doc, dict):
        ref = doc.get("$ref")
        if isinstance(ref, str):
            parts = urlsplit(ref)
            if parts.scheme or parts.netloc or ref.startswith("//"):
                raise ContractError("network and absolute URI $ref values are not allowed")
            if parts.path:
                target = (source.parent / unquote(parts.path)).resolve(strict=False)
                try:
                    target.relative_to(root.resolve(strict=True))
                except ValueError as exc:
                    raise ContractError("$ref escapes the permitted repository root") from exc
                if not target.is_file():
                    raise ContractError(f"local $ref does not resolve: {parts.path}")
                if target not in visited:
                    visited.add(target)
                    _check_local_refs(load_yaml(target), target, root, visited, seen_values)
        for value in doc.values():
            _check_local_refs(value, source, root, visited, seen_values)
    elif isinstance(doc, list):
        for value in doc:
            _check_local_refs(value, source, root, visited, seen_values)


def validate_spec(path: Path, root: Path) -> dict[str, Any]:
    path = path.resolve(strict=True)
    root = root.resolve(strict=True)
    relpath = _repo_path(path, root)
    doc = load_yaml(path)
    if not isinstance(doc, dict):
        raise ContractError("OpenAPI document root must be an object")
    version = doc.get("openapi")
    if not isinstance(version, str) or not SUPPORTED_OPENAPI.fullmatch(version):
        raise ContractError("supported OpenAPI versions are 3.0.x, 3.1.x, and 3.2.x")
    _check_local_refs(doc, path, root, {path})
    try:
        from openapi_spec_validator import validate
    except ImportError as exc:
        raise ContractError("openapi-spec-validator is unavailable; install requirements-validation.txt") from exc
    try:
        from openapi_spec_validator.readers import read_from_filename

        spec_dict, base_uri = read_from_filename(str(path))
        validate(spec_dict, base_uri=base_uri)
    except Exception as exc:  # Validator exceptions vary by supported OpenAPI version.
        raise ContractError(f"OpenAPI validation failed: {type(exc).__name__}: {exc}") from exc
    return {
        "schema_version": 1,
        "status": "PASS",
        "kind": "openapi_validation",
        "openapi_version": version,
        "spec": {"path": relpath, "sha256": sha256_file(path)},
        "repository_revision": git_revision(root),
        "validator": "openapi-spec-validator==0.9.0",
        "network_references": "DENIED",
    }


def _operations(doc: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    paths = doc.get("paths")
    if not isinstance(paths, dict):
        return {}
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() in HTTP_METHODS and isinstance(operation, dict):
                result[(str(path), method.lower())] = operation
    return result


def _behavioral(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _behavioral(item) for key, item in value.items() if key not in DOC_FIELDS}
    if isinstance(value, list):
        return [_behavioral(item) for item in value]
    return value


def _parameter_map(value: Any) -> dict[tuple[str, str], dict[str, Any]]:
    if not isinstance(value, list):
        return {}
    return {
        (str(item.get("in")), str(item.get("name"))): item
        for item in value if isinstance(item, dict) and isinstance(item.get("name"), str)
    }


def compare_specs(base: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    before, after = _operations(base), _operations(candidate)
    changes: list[dict[str, str]] = []
    for key in sorted(before.keys() - after.keys()):
        changes.append({"classification": "BREAKING", "location": f"{key[1].upper()} {key[0]}", "reason": "operation_removed"})
    for key in sorted(after.keys() - before.keys()):
        changes.append({"classification": "NON_BREAKING", "location": f"{key[1].upper()} {key[0]}", "reason": "operation_added"})

    for key in sorted(before.keys() & after.keys()):
        old, new = before[key], after[key]
        location = f"{key[1].upper()} {key[0]}"
        old_id, new_id = old.get("operationId"), new.get("operationId")
        if old_id != new_id:
            changes.append({"classification": "BREAKING", "location": location, "reason": "operation_id_changed"})
        old_params = _parameter_map(old.get("parameters"))
        new_params = _parameter_map(new.get("parameters"))
        for param in sorted(old_params.keys() - new_params.keys()):
            changes.append({"classification": "BREAKING", "location": f"{location} parameter {param[0]}.{param[1]}", "reason": "parameter_removed"})
        for param in sorted(new_params.keys() - old_params.keys()):
            required = new_params[param].get("required") is True
            changes.append({"classification": "BREAKING" if required else "NON_BREAKING", "location": f"{location} parameter {param[0]}.{param[1]}", "reason": "required_parameter_added" if required else "optional_parameter_added"})
        for param in sorted(old_params.keys() & new_params.keys()):
            if _behavioral(old_params[param]) != _behavioral(new_params[param]):
                changes.append({"classification": "UNKNOWN", "location": f"{location} parameter {param[0]}.{param[1]}", "reason": "parameter_semantics_changed"})
        if any(isinstance(item, dict) and "$ref" in item for item in (old.get("parameters") or []) + (new.get("parameters") or [])) and _behavioral(old.get("parameters")) != _behavioral(new.get("parameters")):
            changes.append({"classification": "UNKNOWN", "location": f"{location} parameters", "reason": "referenced_parameter_change"})

        old_body, new_body = old.get("requestBody"), new.get("requestBody")
        if old_body is None and isinstance(new_body, dict) and new_body.get("required") is True:
            changes.append({"classification": "BREAKING", "location": location, "reason": "required_request_body_added"})
        elif old_body is None and isinstance(new_body, dict) and new_body.get("required") is not True:
            changes.append({"classification": "NON_BREAKING", "location": f"{location} requestBody", "reason": "optional_request_body_added"})
        elif _behavioral(old_body) != _behavioral(new_body) and not (
            old_body is None and isinstance(new_body, dict) and new_body.get("required") is not True
        ):
            changes.append({"classification": "UNKNOWN", "location": f"{location} requestBody", "reason": "request_body_semantics_changed"})

        old_responses = old.get("responses", {})
        new_responses = new.get("responses", {})
        if isinstance(old_responses, dict) and isinstance(new_responses, dict):
            for code in sorted(old_responses.keys() - new_responses.keys(), key=str):
                changes.append({"classification": "BREAKING", "location": f"{location} response {code}", "reason": "response_status_removed"})
            for code in sorted(new_responses.keys() - old_responses.keys(), key=str):
                changes.append({"classification": "NON_BREAKING", "location": f"{location} response {code}", "reason": "response_status_added"})
            for code in sorted(old_responses.keys() & new_responses.keys(), key=str):
                if _behavioral(old_responses[code]) != _behavioral(new_responses[code]):
                    changes.append({"classification": "UNKNOWN", "location": f"{location} response {code}", "reason": "response_semantics_changed"})

        old_remainder = {k: _behavioral(v) for k, v in old.items() if k not in {"parameters", "requestBody", "responses"}}
        new_remainder = {k: _behavioral(v) for k, v in new.items() if k not in {"parameters", "requestBody", "responses"}}
        if old_remainder != new_remainder:
            changes.append({"classification": "UNKNOWN", "location": location, "reason": "unclassified_operation_change"})

    base_paths, candidate_paths = base.get("paths") or {}, candidate.get("paths") or {}
    for path in sorted(base_paths.keys() & candidate_paths.keys()):
        before_item, after_item = base_paths[path] or {}, candidate_paths[path] or {}
        if before_item.get("$ref") != after_item.get("$ref"):
            changes.append({"classification": "UNKNOWN", "location": f"path {path}", "reason": "path_item_reference_changed"})
        if _behavioral(before_item.get("parameters")) != _behavioral(after_item.get("parameters")):
            changes.append({"classification": "UNKNOWN", "location": f"path {path}", "reason": "path_level_parameters_changed"})
    if base.get("openapi") != candidate.get("openapi"):
        changes.append({"classification": "UNKNOWN", "location": "openapi", "reason": "specification_dialect_changed"})
    if base.get("components") != candidate.get("components"):
        # Component/reference resolution and transitive consumer impact are not inferred here.
        changes.append({"classification": "UNKNOWN", "location": "components", "reason": "component_change_requires_reference_aware_review"})
    if base.get("servers") != candidate.get("servers"):
        changes.append({"classification": "UNKNOWN", "location": "servers", "reason": "server_target_changed"})
    if base.get("security") != candidate.get("security"):
        changes.append({"classification": "UNKNOWN", "location": "security", "reason": "global_security_changed"})
    if base.get("webhooks") != candidate.get("webhooks"):
        changes.append({"classification": "UNKNOWN", "location": "webhooks", "reason": "webhook_change_requires_review"})
    ignored_top_level = {"openapi", "info", "paths", "components", "servers", "security", "webhooks", "tags", "externalDocs"}
    if {k: v for k, v in base.items() if k not in ignored_top_level} != {k: v for k, v in candidate.items() if k not in ignored_top_level}:
        changes.append({"classification": "UNKNOWN", "location": "document", "reason": "unclassified_top_level_change"})
    if not changes:
        status = "NO_CHANGE"
    elif any(item["classification"] == "BREAKING" for item in changes):
        status = "BREAKING"
    elif any(item["classification"] == "UNKNOWN" for item in changes):
        status = "UNKNOWN"
    else:
        status = "NON_BREAKING"
    return {"status": status, "changes": changes, "automated_approval": False}


def verify_evidence(report_path: Path, root: Path) -> dict[str, Any]:
    report_path = report_path.resolve(strict=True)
    root = root.resolve(strict=True)
    _repo_path(report_path, root)
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read evidence JSON: {exc}") from exc
    if not isinstance(report, dict) or report.get("schema_version") != 1:
        raise ContractError("unsupported evidence report schema")
    validate_report_shape(report)
    stale: list[str] = []

    def check_file(group: dict[str, Any], label: str) -> None:
        relpath, expected = group.get("path"), group.get("sha256")
        if not isinstance(relpath, str) or not isinstance(expected, str):
            stale.append(f"{label}:missing_path_or_digest")
            return
        target = (root / relpath).resolve(strict=False)
        try:
            target.relative_to(root)
        except ValueError:
            stale.append(f"{label}:path_outside_repository")
            return
        if not target.is_file():
            stale.append(f"{label}:missing_file")
        elif sha256_file(target) != expected:
            stale.append(f"{label}:content_digest_changed")

    kind = report.get("kind")
    if kind == "openapi_validation":
        check_file(report.get("spec") or {}, "spec")
    elif kind == "openapi_compatibility":
        check_file(report.get("baseline") or {}, "baseline")
        check_file(report.get("candidate") or {}, "candidate")
    elif kind == "openapi_contract_test":
        check_file(report.get("spec") or {}, "spec")
        junit = report.get("junit") or {}
        check_file({"path": junit.get("path"), "sha256": junit.get("sha256")}, "junit")
    else:
        raise ContractError("unknown evidence kind")
    current_revision = git_revision(root)
    if not report.get("repository_revision") or report["repository_revision"] != current_revision:
        stale.append("repository_revision_changed")
    return {"status": "PASS" if not stale else "STALE", "report": _repo_path(report_path, root),
            "repository_revision": current_revision, "stale_reasons": stale}


def _write_json(path: Path | None, value: dict[str, Any]) -> None:
    rendered = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path:
        path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


def validate_report_shape(report: dict[str, Any]) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "templates/implementation/OPENAPI_EVIDENCE_REPORT.schema.json"
    try:
        from jsonschema import validate as validate_json

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validate_json(report, schema)
    except ImportError as exc:
        raise ContractError("jsonschema is unavailable; install requirements-validation.txt") from exc
    except Exception as exc:
        raise ContractError(f"evidence report does not match the v1 schema: {type(exc).__name__}: {exc}") from exc


def _run(args: argparse.Namespace) -> int:
    root = args.repo_root.resolve(strict=True)
    spec_path = args.spec.resolve(strict=True)
    validation = validate_spec(spec_path, root)
    operations = _operations(load_yaml(spec_path))
    operation_ids = sorted({
        operation["operationId"] for operation in operations.values()
        if isinstance(operation.get("operationId"), str) and operation["operationId"]
    })
    if not operation_ids or len(operation_ids) != len(operations):
        raise ContractError("the contract test runner requires unique operationId values on every operation")
    command = json.loads(args.command)
    if not isinstance(command, list) or not command or not all(isinstance(item, str) for item in command):
        raise ContractError("--command must be a non-empty JSON array of strings")
    started = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    monotonic = time.monotonic()
    report_candidate = args.junit if args.junit.is_absolute() else root / args.junit
    report_candidate = report_candidate.resolve(strict=False)
    try:
        report_candidate.relative_to(root)
    except ValueError as exc:
        raise ContractError("JUnit report path escapes the permitted repository root") from exc
    if report_candidate.exists():
        raise ContractError("JUnit report path already exists; refusing to reuse stale test output")
    report_candidate.parent.mkdir(parents=True, exist_ok=True)
    command_env = os.environ.copy()
    command_env["AIPS_JUNIT_XML"] = str(report_candidate)
    with tempfile.TemporaryFile() as stdout_tmp, tempfile.TemporaryFile() as stderr_tmp:
        try:
            result = subprocess.run(command, cwd=root, env=command_env, check=False,
                                    stdout=stdout_tmp, stderr=stderr_tmp, timeout=args.timeout)
            returncode = result.returncode
        except subprocess.TimeoutExpired:
            returncode = 124
        stdout_tmp.seek(0)
        stderr_tmp.seek(0)
        stdout_digest = sha256_stream(stdout_tmp)
        stderr_digest = sha256_stream(stderr_tmp)
    finished = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    report_path = report_candidate.resolve(strict=True)
    _repo_path(report_path, root)
    try:
        suite = ET.parse(report_path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise ContractError(f"cannot parse project JUnit XML report: {exc}") from exc
    cases = list(suite.iter("testcase"))
    covered: set[str] = set()
    failed = skipped = 0
    for case in cases:
        name = f"{case.attrib.get('classname', '')} {case.attrib.get('name', '')}"
        for operation_id in operation_ids:
            if re.search(rf"(?:^|[^A-Za-z0-9_]){re.escape(operation_id)}(?:$|[^A-Za-z0-9_])", name):
                covered.add(operation_id)
        failed += sum(1 for child in case if child.tag in {"failure", "error"})
        skipped += sum(1 for child in case if child.tag == "skipped")
    missing = sorted(set(operation_ids) - covered)
    status = "PASS" if returncode == 0 and cases and failed == 0 and not missing and not skipped else "UNVERIFIED"
    if returncode not in (0, 124) or failed:
        status = "FAIL"
    report = {
        "schema_version": 1,
        "kind": "openapi_contract_test",
        "status": status,
        "spec": validation["spec"],
        "repository_revision": git_revision(root),
        "validator": validation["validator"],
        "command": {"argv_sha256": sha256_bytes(json.dumps(command, separators=(",", ":")).encode()), "exit_code": returncode,
                    "stdout_sha256": stdout_digest, "stderr_sha256": stderr_digest, "duration_seconds": round(time.monotonic() - monotonic, 3)},
        "junit": {"path": _repo_path(report_path, root), "sha256": sha256_file(report_path), "cases": len(cases), "failures_or_errors": failed, "skipped": skipped},
        "operation_coverage": {"expected": operation_ids, "covered": sorted(covered), "missing": missing},
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "finished_at": finished.isoformat().replace("+00:00", "Z"),
        "raw_output_persisted": False,
    }
    validate_report_shape(report)
    _write_json(args.output, report)
    return 0 if status == "PASS" else (1 if status == "FAIL" else 2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    validate = sub.add_parser("validate", help="validate an OpenAPI 3.0/3.1/3.2 document")
    validate.add_argument("spec", type=Path)
    validate.add_argument("--repo-root", type=Path, default=Path.cwd())
    validate.add_argument("--output", type=Path)
    compare = sub.add_parser("compare", help="conservatively compare an approved baseline and candidate")
    compare.add_argument("baseline", type=Path)
    compare.add_argument("candidate", type=Path)
    compare.add_argument("--repo-root", type=Path, default=Path.cwd())
    compare.add_argument("--baseline-authority", choices=("canonical", "descriptive", "proposed", "unresolved"), required=True)
    compare.add_argument("--output", type=Path)
    verify = sub.add_parser("verify-evidence", help="reject evidence whose revision or content hashes are stale")
    verify.add_argument("report", type=Path)
    verify.add_argument("--repo-root", type=Path, default=Path.cwd())
    verify.add_argument("--output", type=Path)
    run = sub.add_parser("run-contract-tests", help="run project tests and bind JUnit evidence to OpenAPI operations")
    run.add_argument("spec", type=Path)
    run.add_argument("--repo-root", type=Path, default=Path.cwd())
    run.add_argument("--command", required=True, help="argv as a JSON string array; no shell is used")
    run.add_argument("--junit", type=Path, required=True)
    run.add_argument("--timeout", type=int, default=600)
    run.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "validate":
            result = validate_spec(args.spec, args.repo_root)
            validate_report_shape(result)
            _write_json(args.output, result)
            return 0
        if args.action == "compare":
            root = args.repo_root.resolve(strict=True)
            base_path, candidate_path = args.baseline.resolve(strict=True), args.candidate.resolve(strict=True)
            base_doc, candidate_doc = load_yaml(base_path), load_yaml(candidate_path)
            if not isinstance(base_doc, dict) or not isinstance(candidate_doc, dict):
                raise ContractError("baseline and candidate roots must be objects")
            validate_spec(base_path, root)
            validate_spec(candidate_path, root)
            if args.baseline_authority != "canonical":
                result = {"status": "BLOCKED", "reason": "baseline_authority_is_not_canonical", "automated_approval": False}
            else:
                result = compare_specs(base_doc, candidate_doc)
            result.update({"kind": "openapi_compatibility", "schema_version": 1, "baseline_authority": args.baseline_authority,
                           "baseline": {"path": _repo_path(base_path, root), "sha256": sha256_file(base_path)},
                           "candidate": {"path": _repo_path(candidate_path, root), "sha256": sha256_file(candidate_path)},
                           "repository_revision": git_revision(root)})
            validate_report_shape(result)
            _write_json(args.output, result)
            return 0 if result["status"] in {"NO_CHANGE", "NON_BREAKING"} else 2
        if args.action == "verify-evidence":
            result = verify_evidence(args.report, args.repo_root)
            _write_json(args.output, result)
            return 0 if result["status"] == "PASS" else 2
        if args.action == "run-contract-tests":
            if args.timeout < 1 or args.timeout > 3600:
                raise ContractError("--timeout must be between 1 and 3600 seconds")
            return _run(args)
    except (ContractError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
