#!/usr/bin/env python3
"""Inspect Phase 3 implementation evidence for an exact Git candidate."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from jsonschema import validate as validate_json

from implementation_profile_validate import validate_language_profile, validate_profile
from openapi_contracts import ContractError, verify_evidence

MAX_OUTPUT_BYTES = 1_048_576
SHELLS = {"sh", "bash", "zsh", "fish", "cmd", "powershell", "pwsh"}
REPORT_SCHEMA = Path(__file__).resolve().parents[1] / "templates/implementation/IMPLEMENTATION_ENFORCEMENT_REPORT.schema.json"


class EnforcementError(ValueError):
    pass


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def canonical_digest(value: Any) -> str:
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def validate_report(report: dict[str, Any]) -> None:
    try:
        validate_json(report, json.loads(REPORT_SCHEMA.read_text(encoding="utf-8")))
    except Exception as exc:
        raise EnforcementError(f"Phase 3 report violates v1 schema: {type(exc).__name__}") from exc


def repo_file(root: Path, relative: str, *, required: bool = True) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise EnforcementError("repository path is missing or malformed")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or pure.as_posix() != relative or any(part in {"", ".", ".."} for part in relative.split("/")):
        raise EnforcementError(f"unsafe repository path: {relative}")
    target = (root / relative).resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise EnforcementError(f"repository path escapes root: {relative}") from exc
    if required and not target.is_file():
        raise EnforcementError(f"repository file is missing: {relative}")
    return target


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=False)
    if result.returncode:
        raise EnforcementError(f"git {args[0]} failed")
    return result.stdout.strip()


def exact_candidate(root: Path, base: str, head: str) -> tuple[str, str, list[str]]:
    base_sha = git(root, "rev-parse", f"{base}^{{commit}}")
    head_sha = git(root, "rev-parse", f"{head}^{{commit}}")
    if git(root, "rev-parse", "HEAD") != head_sha:
        raise EnforcementError("checked-out HEAD differs from candidate head")
    git(root, "merge-base", "--is-ancestor", base_sha, head_sha)
    if git(root, "diff", "--name-only") or git(root, "diff", "--cached", "--name-only"):
        raise EnforcementError("tracked working tree changes make candidate evidence ambiguous")
    files = sorted(set(git(root, "diff", "--name-only", f"{base_sha}...{head_sha}").splitlines()))
    return base_sha, head_sha, files


def load_profile(path: Path) -> dict[str, Any]:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise EnforcementError("cannot read Implementation Profile") from exc
    result = validate_profile(doc)
    if result["structural_status"] != "PASS":
        raise EnforcementError("Implementation Profile structure is invalid: " + "; ".join(result["errors"][:5]))
    return doc


def issue(checks: list[dict[str, Any]], identifier: str, status: str, reason: str, path: str | None = None) -> None:
    row: dict[str, Any] = {"id": identifier, "status": status, "reason": reason}
    if path:
        row["path"] = path
    checks.append(row)


def command_by_id(profile: dict[str, Any], identifier: str) -> dict[str, Any]:
    for row in (profile.get("enforcement") or {}).get("commands") or []:
        if row.get("id") == identifier:
            return row
    raise EnforcementError(f"unknown project command: {identifier}")


def command_identity(root: Path, command: dict[str, Any]) -> dict[str, str]:
    source = command["source"]
    return {
        "argv_sha256": canonical_digest(command["argv"]),
        "source_sha256": digest_file(repo_file(root, source)),
    }


def run_command(profile_path: Path, root: Path, identifier: str, repeat: int) -> dict[str, Any]:
    """Explicit local collection; the Integration Gate never calls this function."""
    root = root.resolve(strict=True)
    profile_path = repo_file(root, profile_path.resolve(strict=True).relative_to(root).as_posix())
    profile = load_profile(profile_path)
    command = command_by_id(profile, identifier)
    if repeat not in {1, 2}:
        raise EnforcementError("repeat must be 1 or 2")
    if command["deterministic"] and repeat != 2:
        raise EnforcementError("deterministic commands require repeat=2")
    executable = Path(command["argv"][0]).name.lower()
    if executable in SHELLS or any(arg in {"-c", "--command"} for arg in command["argv"][1:]):
        raise EnforcementError("shell or inline-code command is not an approved project command")
    if "/" in command["argv"][0] or "\\" in command["argv"][0]:
        repo_file(root, command["argv"][0])
    identity = command_identity(root, command)
    revision = git(root, "rev-parse", "HEAD")
    if git(root, "diff", "--name-only") or git(root, "diff", "--cached", "--name-only"):
        raise EnforcementError("tracked working tree changes make command evidence ambiguous")
    runs: list[dict[str, Any]] = []
    environment = {k: v for k, v in os.environ.items() if k in {"PATH", "LANG", "LC_ALL", "TMPDIR", "SYSTEMROOT"}}
    with tempfile.TemporaryDirectory(prefix="aips-implementation-command-") as temporary:
        environment["HOME"] = temporary
        for index in range(repeat):
            with tempfile.TemporaryFile() as stream:
                try:
                    completed = subprocess.run(command["argv"], cwd=root, env=environment, stdout=stream,
                                               stderr=subprocess.STDOUT, timeout=command["timeout_seconds"], check=False)
                    exit_code: int | None = completed.returncode
                    timed_out = False
                except subprocess.TimeoutExpired:
                    exit_code = None
                    timed_out = True
                except OSError as exc:
                    raise EnforcementError(f"project command unavailable: {type(exc).__name__}") from exc
                stream.seek(0, os.SEEK_END)
                size = stream.tell()
                stream.seek(0)
                output_hash = digest_bytes(stream.read(MAX_OUTPUT_BYTES))
                runs.append({"index": index + 1, "exit_code": exit_code, "timed_out": timed_out,
                             "output_sha256": output_hash, "output_bytes": min(size, MAX_OUTPUT_BYTES),
                             "output_truncated": size > MAX_OUTPUT_BYTES})
    statuses = {(r["exit_code"], r["timed_out"], r["output_sha256"], r["output_truncated"]) for r in runs}
    if any(r["timed_out"] or r["output_truncated"] for r in runs):
        status = "UNVERIFIED"
    elif any(r["exit_code"] != 0 for r in runs):
        status = "FAIL"
    elif command["deterministic"] and len(statuses) != 1:
        status = "UNVERIFIED"
    else:
        status = "PASS"
    report = {"schema_version": 1, "kind": "implementation_command", "status": status,
            "profile_sha256": digest_file(profile_path), "repository_revision": revision,
            "command_id": identifier, **identity, "runs": runs, "raw_output_persisted": False}
    validate_report(report)
    return report


def command_evidence(profile: dict[str, Any], profile_digest: str, root: Path, head_sha: str,
                     requirement: dict[str, Any]) -> tuple[str, str]:
    relative = requirement["evidence_report"]
    try:
        path = repo_file(root, relative)
        if subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative],
                          capture_output=True, check=False).returncode == 0:
            return "UNVERIFIED", "command_evidence_must_be_ephemeral"
        report = json.loads(path.read_text(encoding="utf-8"))
        validate_report(report)
        command = command_by_id(profile, requirement["command_id"])
        identity = command_identity(root, command)
    except (EnforcementError, OSError, json.JSONDecodeError, KeyError):
        return "UNVERIFIED", "command_evidence_missing_or_invalid"
    if not isinstance(report, dict) or report.get("schema_version") != 1 or report.get("kind") != "implementation_command":
        return "UNVERIFIED", "command_evidence_schema_invalid"
    expected = {"profile_sha256": profile_digest, "repository_revision": head_sha,
                "command_id": requirement["command_id"], **identity, "raw_output_persisted": False}
    if any(report.get(key) != value for key, value in expected.items()):
        return "UNVERIFIED", "command_evidence_stale"
    runs = report.get("runs")
    if not isinstance(runs, list) or len(runs) != (2 if command["deterministic"] else 1):
        return "UNVERIFIED", "command_runs_missing"
    if any(not isinstance(row, dict) or row.get("output_truncated") is not False or row.get("timed_out") is not False
           or not isinstance(row.get("output_sha256"), str) for row in runs):
        return "UNVERIFIED", "command_run_incomplete"
    if command["deterministic"] and len({(row.get("exit_code"), row.get("output_sha256")) for row in runs}) != 1:
        return "UNVERIFIED", "command_not_reproducible"
    if any(row.get("exit_code") != 0 for row in runs) or report.get("status") == "FAIL":
        return "FAIL", "project_command_failed"
    if report.get("status") != "PASS":
        return "UNVERIFIED", "command_evidence_not_pass"
    return "PASS", "verified_command_evidence"


def openapi_checks(profile: dict[str, Any], root: Path, checks: list[dict[str, Any]]) -> None:
    contract = profile.get("contract") or {}
    if contract.get("type") != "openapi" or contract.get("affects_change") is not True:
        return
    evidence = contract.get("openapi") or {}
    required = [("validation", "validation_report", {"PASS"})]
    if evidence.get("compatibility_required"):
        required.append(("compatibility", "compatibility_report", {"NO_CHANGE", "NON_BREAKING"}))
    required.append(("conformance", "conformance_report", {"PASS"}))
    kinds = {"validation": "openapi_validation", "compatibility": "openapi_compatibility",
             "conformance": "openapi_contract_test"}
    for identifier, key, accepted in required:
        reference = evidence.get(key)
        if not reference:
            issue(checks, "openapi-" + identifier, "UNVERIFIED", "openapi_evidence_missing")
            continue
        try:
            report_path = repo_file(root, reference)
            verification = verify_evidence(report_path, root)
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (EnforcementError, ContractError, OSError, json.JSONDecodeError):
            issue(checks, "openapi-" + identifier, "BLOCKED", "openapi_evidence_invalid", reference)
            continue
        if verification["status"] != "PASS":
            issue(checks, "openapi-" + identifier, "BLOCKED", "openapi_evidence_stale", reference)
        elif report.get("kind") != kinds[identifier]:
            issue(checks, "openapi-" + identifier, "BLOCKED", "openapi_evidence_kind_mismatch", reference)
        elif identifier in {"validation", "conformance", "compatibility"} and (
            (report.get("candidate" if identifier == "compatibility" else "spec") or {}).get("path") != contract.get("source")
            or (report.get("candidate" if identifier == "compatibility" else "spec") or {}).get("sha256") != evidence.get("spec_sha256")
        ):
            issue(checks, "openapi-" + identifier, "BLOCKED", "openapi_spec_binding_mismatch", reference)
        elif report.get("status") not in accepted or evidence.get({"validation": "validation_status", "compatibility": "compatibility_status",
                                                        "conformance": "implementation_conformance_status"}[identifier]) != report.get("status"):
            issue(checks, "openapi-" + identifier, "BLOCKED", "openapi_evidence_status_mismatch", reference)
        else:
            issue(checks, "openapi-" + identifier, "PASS", "verified_openapi_evidence", reference)


def inspect_profile(profile_path: Path, root: Path, base: str, head: str, *, mode: str = "report",
                    expected_profile_sha256: str | None = None) -> dict[str, Any]:
    root = root.resolve(strict=True)
    base_sha, head_sha, changed = exact_candidate(root, base, head)
    profile_path = repo_file(root, profile_path.resolve(strict=True).relative_to(root).as_posix())
    profile = load_profile(profile_path)
    policy = profile.get("enforcement") or {}
    if policy.get("mode") == "disabled":
        raise EnforcementError("Phase 3 enforcement is disabled in the Profile")
    profile_digest = digest_file(profile_path)
    checks: list[dict[str, Any]] = []
    if expected_profile_sha256 and profile_digest != expected_profile_sha256:
        issue(checks, "profile-fingerprint", "BLOCKED", "profile_fingerprint_mismatch")
    else:
        issue(checks, "profile-fingerprint", "PASS", "profile_fingerprint_recorded")
    patterns = policy.get("scope_paths") or []
    applicable = sorted(path for path in changed if any(fnmatch.fnmatch(path, pattern) for pattern in patterns))
    if not applicable:
        result = {"schema_version": 1, "kind": "implementation_enforcement", "mode": mode, "status": "SKIPPED",
                  "profile": {"path": profile_path.relative_to(root).as_posix(), "sha256": profile_digest},
                  "candidate": {"base_sha": base_sha, "head_sha": head_sha, "changed_files": changed, "applicable_files": []},
                  "checks": [], "authority": {"merge_authorized": False, "human_authority_preserved": True}}
        result["fingerprint"] = canonical_digest(result)
        return result

    language_relative = policy.get("language_profile")
    language_result: dict[str, str] | None = None
    try:
        language_path = repo_file(root, language_relative)
        language = yaml.safe_load(language_path.read_text(encoding="utf-8"))
        errors = validate_language_profile(language)
        if errors or language["identity"]["language"] != profile["technology"]["language"]["name"]:
            issue(checks, "language-profile", "BLOCKED", "language_profile_invalid_or_mismatched", language_relative)
        else:
            issue(checks, "language-profile", "PASS", "language_profile_verified", language_relative)
            language_result = {"path": language_relative, "sha256": digest_file(language_path)}
    except (EnforcementError, OSError, yaml.YAMLError, KeyError, TypeError):
        issue(checks, "language-profile", "BLOCKED", "language_profile_missing", language_relative)

    ownership = profile["ownership"]
    categories: dict[str, tuple[str, Any]] = {}
    for category in ("generated", "scaffolded", "project_owned", "unresolved"):
        for entry in ownership.get(category) or []:
            path = entry.get("path") if isinstance(entry, dict) else entry
            categories[path] = category, entry
    records = {row["path"]: row for row in policy.get("generation_records") or []}
    for entry in ownership.get("generated") or []:
        generated_path = entry.get("path") if isinstance(entry, dict) else entry
        if generated_path not in records:
            issue(checks, "generation-provenance", "BLOCKED", "generation_record_missing", generated_path)
    for path in applicable:
        category, entry = categories.get(path, ("unknown", None))
        if category in {"unknown", "unresolved"}:
            issue(checks, "ownership", "BLOCKED", "ownership_unresolved", path)
        elif category == "generated":
            if path not in records:
                issue(checks, "ownership", "BLOCKED", "generation_record_missing", path)
            else:
                issue(checks, "ownership", "PASS", "generated_boundary_declared", path)
        elif not isinstance(entry, dict) or not (entry.get("source") or entry.get("reference")):
            issue(checks, "ownership", "UNVERIFIED", "ownership_source_missing", path)
        else:
            issue(checks, "ownership", "PASS", "ownership_source_recorded", path)
    for path, record in sorted(records.items()):
        if categories.get(path, (None,))[0] != "generated":
            issue(checks, "generation-provenance", "BLOCKED", "generation_record_unowned", path)
            continue
        try:
            output = repo_file(root, path)
            if digest_file(output) != record["output_sha256"]:
                raise EnforcementError("generated output changed")
            for source in record["inputs"]:
                if digest_file(repo_file(root, source["path"])) != source["sha256"]:
                    raise EnforcementError("generator input changed")
        except (EnforcementError, OSError, KeyError):
            issue(checks, "generation-provenance", "BLOCKED", "generation_record_stale", path)
        else:
            issue(checks, "generation-provenance", "PASS", "generation_hashes_match", path)

    for category in ("mandatory", "project_required", "risk_triggered"):
        for row in profile["quality"].get(category) or []:
            if not isinstance(row, dict):
                issue(checks, "quality-" + category, "UNVERIFIED", "quality_requirement_unbound")
                continue
            status, reason = command_evidence(profile, profile_digest, root, head_sha, row)
            issue(checks, "quality-" + row["id"], status, reason, row["evidence_report"])
    openapi_checks(profile, root, checks)
    statuses = {row["status"] for row in checks}
    status = next((item for item in ("FAIL", "BLOCKED", "UNVERIFIED") if item in statuses), "PASS")
    report = {"schema_version": 1, "kind": "implementation_enforcement", "mode": mode, "status": status,
              "profile": {"path": profile_path.relative_to(root).as_posix(), "sha256": profile_digest},
              "language_profile": language_result,
              "candidate": {"base_sha": base_sha, "head_sha": head_sha, "changed_files": changed,
                            "applicable_files": applicable},
              "checks": checks, "authority": {"merge_authorized": False, "human_authority_preserved": True}}
    report["fingerprint"] = canonical_digest(report)
    validate_report(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    inspect = sub.add_parser("inspect", help="recompute a bounded Phase 3 report")
    inspect.add_argument("profile", type=Path)
    inspect.add_argument("--repo-root", type=Path, default=Path.cwd())
    inspect.add_argument("--base", required=True)
    inspect.add_argument("--head", default="HEAD")
    inspect.add_argument("--mode", choices=("report", "enforce"), default="report")
    inspect.add_argument("--expected-profile-sha256")
    inspect.add_argument("--output", type=Path)
    collect = sub.add_parser("run-command", help="explicitly execute a declared project command")
    collect.add_argument("profile", type=Path)
    collect.add_argument("--repo-root", type=Path, default=Path.cwd())
    collect.add_argument("--command-id", required=True)
    collect.add_argument("--repeat", type=int, default=1)
    collect.add_argument("--execute", action="store_true", help="required acknowledgement for local execution")
    collect.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        root = args.repo_root.resolve(strict=True)
        profile_path = args.profile if args.profile.is_absolute() else root / args.profile
        if args.action == "inspect":
            report = inspect_profile(profile_path, root, args.base, args.head, mode=args.mode,
                                     expected_profile_sha256=args.expected_profile_sha256)
        else:
            if not args.execute:
                raise EnforcementError("run-command requires --execute")
            report = run_command(profile_path, root, args.command_id, args.repeat)
        rendered = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        if args.action == "run-command":
            return 0 if report["status"] == "PASS" else 1
        return 0 if args.mode == "report" or report["status"] in {"PASS", "SKIPPED"} else 1
    except (EnforcementError, OSError, ValueError) as exc:
        print(f"IMPLEMENTATION ENFORCEMENT BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
