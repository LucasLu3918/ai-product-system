#!/usr/bin/env python3
"""Preview and explicitly run an ownership-safe OpenAPI client generator adapter."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from jsonschema import validate as validate_json

from implementation_profile_validate import validate_profile
from openapi_contracts import ContractError, verify_evidence

REPORT_SCHEMA = Path(__file__).resolve().parents[1] / "templates/implementation/GENERATOR_ADAPTER_REPORT.schema.json"
LOG_LIMIT = 1_048_576


class AdapterError(ValueError):
    """A bounded adapter precondition or output contract failed."""


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    return digest(path.read_bytes())


def canonical_digest(value: Any) -> str:
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=False)
    if result.returncode:
        raise AdapterError(f"git {args[0]} failed")
    return result.stdout.strip()


def safe_relative(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise AdapterError(f"{label} must be a normalized repository-relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(part in {"", ".", ".."} for part in value.split("/")):
        raise AdapterError(f"{label} must be a normalized repository-relative path")
    if any(part in {".git", ".aips"} for part in path.parts):
        raise AdapterError(f"{label} cannot target Git or AIPS metadata")
    return value


def repo_path(root: Path, relative: str, *, required: bool = True) -> Path:
    safe_relative(relative, "repository path")
    target = root / relative
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise AdapterError(f"symlink in repository path: {relative}")
    resolved = target.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise AdapterError(f"repository path escapes checkout: {relative}") from exc
    if required and not resolved.is_file():
        raise AdapterError(f"repository file is missing: {relative}")
    return resolved


def load_configuration(root: Path, profile_relative: str, adapter_id: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    profile_path = repo_path(root, profile_relative)
    try:
        profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise AdapterError("cannot read Implementation Profile") from exc
    validation = validate_profile(profile)
    if validation["structural_status"] != "PASS" or validation["implementation_status"] != "READY":
        raise AdapterError("Implementation Profile must be structurally valid and READY")
    generation = profile.get("generation") or {}
    if generation.get("enabled") is not True or generation.get("policy") != "boundary_only":
        raise AdapterError("generation must be explicitly enabled with boundary_only policy")
    adapters = generation.get("adapters") or []
    adapter = next((row for row in adapters if row.get("id") == adapter_id), None)
    if not isinstance(adapter, dict):
        raise AdapterError("configured generator adapter was not found")
    return profile_path, profile, adapter


def verify_openapi(root: Path, profile: dict[str, Any], adapter: dict[str, Any],
                   profile_relative: str) -> tuple[Path, str, list[dict[str, str]]]:
    contract = profile.get("contract") or {}
    if contract.get("type") != "openapi" or contract.get("authority") != "canonical":
        raise AdapterError("client generation requires a canonical OpenAPI contract")
    if adapter.get("spec_path") != contract.get("source"):
        raise AdapterError("adapter spec_path differs from canonical contract source")
    spec_path = repo_path(root, adapter["spec_path"])
    spec_digest = digest_file(spec_path)
    evidence = contract.get("openapi") or {}
    if evidence.get("validation_status") != "PASS" or evidence.get("spec_sha256") != spec_digest:
        raise AdapterError("canonical OpenAPI validation evidence is missing or stale")
    validation_reference = evidence.get("validation_report")
    if not validation_reference:
        raise AdapterError("canonical OpenAPI validation report is required")
    verify_report(root, validation_reference, "openapi_validation", "PASS",
                  candidate_path=adapter["spec_path"], candidate_digest=spec_digest)
    if evidence.get("compatibility_required"):
        if evidence.get("baseline_authority") != "canonical" or evidence.get("compatibility_status") not in {"NO_CHANGE", "NON_BREAKING"}:
            raise AdapterError("required canonical compatibility evidence is not acceptable")
        verify_report(root, evidence.get("compatibility_report"), "openapi_compatibility", evidence.get("compatibility_status"),
                      candidate_path=adapter["spec_path"], candidate_digest=spec_digest)
    inputs = [{"path": adapter["spec_path"], "sha256": spec_digest}]
    for relative in sorted(set(adapter.get("tool_inputs") or [])):
        path = repo_path(root, relative)
        inputs.append({"path": relative, "sha256": digest_file(path)})
    executable = repo_path(root, adapter["executable"])
    if not os.access(executable, os.X_OK):
        raise AdapterError("configured generator executable is not executable")
    executable_digest = digest_file(executable)
    if executable_digest != adapter["executable_sha256"]:
        raise AdapterError("configured generator executable hash is stale")
    inputs.append({"path": adapter["executable"], "sha256": executable_digest})
    for input_row in inputs:
        input_path = PurePosixPath(input_row["path"])
        output = PurePosixPath(adapter["output_dir"])
        profile_path = PurePosixPath(profile_relative)
        if (input_path == output or output in input_path.parents or input_path in output.parents
                or profile_path == output or output in profile_path.parents
                or input_path == output or output in input_path.parents
                or PurePosixPath(adapter["executable"]) == output
                or output in PurePosixPath(adapter["executable"]).parents):
            raise AdapterError("generator output directory overlaps an input or the Implementation Profile")
    return spec_path, spec_digest, inputs


def verify_report(root: Path, relative: str, kind: str, status: str, *,
                  candidate_path: str | None = None, candidate_digest: str | None = None) -> None:
    try:
        path = repo_path(root, relative)
        verification = verify_evidence(path, root)
        report = json.loads(path.read_text(encoding="utf-8"))
    except (AdapterError, ContractError, OSError, json.JSONDecodeError, TypeError) as exc:
        raise AdapterError("OpenAPI evidence is missing, stale or malformed") from exc
    if verification.get("status") != "PASS" or report.get("kind") != kind or report.get("status") != status:
        raise AdapterError("OpenAPI evidence status or revision binding does not pass")
    if kind == "openapi_validation":
        spec = report.get("spec") or {}
        if spec.get("path") != candidate_path and candidate_path is not None:
            raise AdapterError("OpenAPI validation report is bound to a different specification")
        if candidate_digest and spec.get("sha256") != candidate_digest:
            raise AdapterError("OpenAPI validation report has a stale specification digest")
    if kind == "openapi_compatibility":
        candidate = report.get("candidate") or {}
        if candidate.get("path") != candidate_path or candidate.get("sha256") != candidate_digest:
            raise AdapterError("OpenAPI compatibility report is bound to a different candidate")


def check_patterns(adapter: dict[str, Any]) -> list[str]:
    patterns = adapter.get("output_patterns") or []
    for pattern in patterns:
        safe_relative(pattern, "output pattern")
    return patterns


def ownership_and_records(profile: dict[str, Any]) -> tuple[set[str], dict[str, dict[str, Any]]]:
    ownership = profile.get("ownership") or {}
    generated: set[str] = set()
    for row in ownership.get("generated") or []:
        path = row.get("path") if isinstance(row, dict) else row
        if isinstance(path, str):
            generated.add(path)
    records = {row.get("path"): row for row in ((profile.get("enforcement") or {}).get("generation_records") or [])
               if isinstance(row, dict) and isinstance(row.get("path"), str)}
    return generated, records


def file_manifest(directory: Path, patterns: list[str], max_files: int, max_bytes: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    total = 0
    for current, dirs, files in os.walk(directory, followlinks=False):
        current_path = Path(current)
        for name in list(dirs):
            candidate = current_path / name
            if candidate.is_symlink():
                raise AdapterError("generator output contains a symlink directory")
        for name in files:
            candidate = current_path / name
            mode = candidate.lstat().st_mode
            if not stat.S_ISREG(mode):
                raise AdapterError("generator output contains a non-regular file")
            relative = candidate.relative_to(directory).as_posix()
            safe_relative(relative, "generated output path")
            if not any(fnmatch.fnmatchcase(relative, pattern) for pattern in patterns):
                raise AdapterError("generator produced an undeclared output path")
            size = candidate.stat().st_size
            total += size
            if len(rows) + 1 > max_files or total > max_bytes:
                raise AdapterError("generator output exceeds configured file or byte limits")
            rows.append({"path": relative, "sha256": digest_file(candidate), "bytes": size})
    if not rows:
        raise AdapterError("generator produced no output files")
    return sorted(rows, key=lambda row: row["path"])


def validate_existing_output(root: Path, profile: dict[str, Any], adapter: dict[str, Any],
                             inputs: list[dict[str, str]]) -> tuple[Path, bool, dict[str, str]]:
    target_relative = safe_relative(adapter["output_dir"], "output_dir")
    repo_path(root, target_relative, required=False)
    target = root / target_relative
    if not target.exists():
        return target, False, {}
    if target.is_symlink() or not target.is_dir():
        raise AdapterError("existing output target must be a regular directory")
    for index, _part in enumerate(PurePosixPath(target_relative).parts, start=1):
        current = root.joinpath(*PurePosixPath(target_relative).parts[:index])
        if current.is_symlink():
            raise AdapterError("symlink in existing output target")
    generated, records = ownership_and_records(profile)
    current_hashes: dict[str, str] = {}
    patterns = check_patterns(adapter)
    rows = []
    for current, dirs, files in os.walk(target, followlinks=False):
        if any((Path(current) / dirname).is_symlink() for dirname in dirs):
            raise AdapterError("existing generated output contains a symlink directory")
        for filename in files:
            path = Path(current) / filename
            if not stat.S_ISREG(path.lstat().st_mode):
                raise AdapterError("existing generated output contains a non-regular file")
            relative = path.relative_to(target).as_posix()
            repo_relative = f"{target_relative}/{relative}"
            if not any(fnmatch.fnmatchcase(relative, pattern) for pattern in patterns):
                raise AdapterError("existing output contains a path outside this adapter allowlist")
            actual_digest = digest_file(path)
            record = records.get(repo_relative)
            if repo_relative not in generated or not isinstance(record, dict):
                raise AdapterError("existing output is not fully declared as generated")
            expected_inputs = sorted(inputs, key=lambda row: row["path"])
            recorded_inputs = sorted(record.get("inputs") or [], key=lambda row: row.get("path", ""))
            if (record.get("output_sha256") != actual_digest or record.get("tool") != adapter["id"]
                    or record.get("version") != adapter["version"] or recorded_inputs != expected_inputs):
                raise AdapterError("existing generated output was edited or has stale provenance")
            current_hashes[repo_relative] = actual_digest
            rows.append(repo_relative)
    if not rows:
        raise AdapterError("existing output directory is empty and cannot be ownership-verified")
    return target, True, current_hashes


def minimal_env(temporary: Path) -> dict[str, str]:
    allowed = {"PATH", "LANG", "LC_ALL", "SYSTEMROOT", "WINDIR"}
    env = {key: value for key, value in os.environ.items() if key in allowed}
    env.update({"HOME": str(temporary), "TMPDIR": str(temporary), "TMP": str(temporary), "TEMP": str(temporary)})
    return env


def read_limited(stream: Any, limit: int) -> tuple[bytes, bool, int]:
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0)
    return stream.read(limit), size > limit, size


def digest_stream(stream: Any) -> str:
    hasher = hashlib.sha256()
    stream.seek(0)
    while chunk := stream.read(64 * 1024):
        hasher.update(chunk)
    return "sha256:" + hasher.hexdigest()


def run_process(command: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    with tempfile.TemporaryFile() as stream:
        process: subprocess.Popen[bytes] | None = None
        try:
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                       shell=False, start_new_session=True)
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            if process is not None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    process.kill()
                process.wait()
            return {"status": "UNVERIFIED", "exit_code": None, "timed_out": True,
                    "output_sha256": digest(b""), "output_bytes": 0, "output_truncated": False,
                    "duration_ms": int((time.monotonic() - started) * 1000)}
        except OSError as exc:
            raise AdapterError(f"configured generator process unavailable: {type(exc).__name__}") from exc
        output, truncated, size = read_limited(stream, LOG_LIMIT)
        output_digest = digest_stream(stream)
    status = "UNVERIFIED" if truncated else "PASS" if process and process.returncode == 0 else "FAIL"
    return {"status": status, "exit_code": process.returncode if process else None, "timed_out": False,
            "output_sha256": output_digest, "output_bytes": size,
            "output_truncated": truncated, "duration_ms": int((time.monotonic() - started) * 1000),
            "output_preview": output.decode("utf-8", errors="replace")[:8192]}


def staged_command(adapter: dict[str, Any], root: Path, scratch: Path, spec_relative: str) -> list[str]:
    executable = repo_path(root, adapter["executable"])
    staged_inputs = {spec_relative: scratch / "inputs" / "spec"}
    for relative in adapter.get("tool_inputs") or []:
        staged_inputs[relative] = scratch / "inputs" / relative
    for source_relative, destination in staged_inputs.items():
        source = repo_path(root, source_relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(0o444)
    output = scratch / "generated"
    output.mkdir()
    command = [str(executable)]
    for token in adapter["argv"]:
        if token == "{spec}":
            command.append(str(staged_inputs[spec_relative]))
        elif token == "{output}":
            command.append(str(output))
        elif token.startswith("{input:") and token.endswith("}"):
            relative = token[7:-1]
            if relative not in staged_inputs or relative == spec_relative:
                raise AdapterError("argv names an undeclared tool input")
            command.append(str(staged_inputs[relative]))
        else:
            command.append(token)
    return command


def expanded_manifest(root: Path, output_dir: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"path": f"{output_dir}/{row['path']}", "sha256": row["sha256"], "bytes": row["bytes"]}
            for row in rows]


def updated_profile(profile: dict[str, Any], adapter: dict[str, Any], inputs: list[dict[str, str]],
                    outputs: list[dict[str, Any]]) -> bytes:
    result = json.loads(json.dumps(profile))
    generated = result.setdefault("ownership", {}).setdefault("generated", [])
    project_owned = result["ownership"].get("project_owned") or []
    unresolved = result["ownership"].get("unresolved") or []
    protected = {row.get("path") if isinstance(row, dict) else row for row in project_owned + unresolved}
    output_paths = {row["path"] for row in outputs}
    if output_paths & protected:
        raise AdapterError("generated output overlaps project-owned or unresolved ownership")
    generated_paths = {row.get("path") if isinstance(row, dict) else row for row in generated}
    for path in sorted(output_paths - generated_paths):
        generated.append(path)
    enforcement = result.setdefault("enforcement", {"mode": "disabled", "scope_paths": [], "language_profile": None,
                                                        "commands": [], "generation_records": []})
    records = enforcement.setdefault("generation_records", [])
    records[:] = [row for row in records if row.get("path") not in output_paths]
    for row in outputs:
        records.append({"path": row["path"], "tool": adapter["id"], "version": adapter["version"],
                        "output_sha256": row["sha256"], "inputs": inputs})
    return yaml.safe_dump(result, sort_keys=False, allow_unicode=True).encode("utf-8")


def atomic_apply(root: Path, profile_path: Path, profile_before: bytes, profile_after: bytes,
                 target: Path, stage: Path, existing: bool, expected_hashes: dict[str, str]) -> bool:
    if profile_path.read_bytes() != profile_before:
        raise AdapterError("Implementation Profile changed during generator execution")
    if target.exists() != existing:
        raise AdapterError("generator output target changed during execution")
    if existing and target.is_symlink():
        raise AdapterError("generator output target became a symlink")
    if existing:
        current_hashes: dict[str, str] = {}
        for current, _dirs, files in os.walk(target, followlinks=False):
            for filename in files:
                path = Path(current) / filename
                if not stat.S_ISREG(path.lstat().st_mode):
                    raise AdapterError("existing output changed to a non-regular file")
                current_hashes[f"{target.relative_to(root).as_posix()}/{path.relative_to(target).as_posix()}"] = digest_file(path)
        if current_hashes != expected_hashes:
            raise AdapterError("existing generated output changed during generator execution")
    target_backup = target.with_name(f".{target.name}.aips-backup-{os.getpid()}-{time.time_ns()}")
    profile_temp: Path | None = None
    target_moved = False
    new_target_installed = False
    try:
        fd, temp_name = tempfile.mkstemp(prefix=f".{profile_path.name}.aips-", dir=profile_path.parent)
        profile_temp = Path(temp_name)
        with os.fdopen(fd, "wb") as stream:
            stream.write(profile_after)
            stream.flush()
            os.fsync(stream.fileno())
        if existing:
            os.replace(target, target_backup)
            target_moved = True
        os.replace(stage, target)
        new_target_installed = True
        os.replace(profile_temp, profile_path)
        profile_temp = None
    except OSError as exc:
        rollback_failed = False
        if new_target_installed:
            try:
                shutil.rmtree(target)
            except OSError:
                rollback_failed = True
        if target_moved:
            try:
                os.replace(target_backup, target)
            except OSError:
                rollback_failed = True
        if rollback_failed:
            raise AdapterError("apply failed and rollback could not restore the original output; inspect the adjacent backup") from exc
        raise AdapterError(f"apply failed and original output was restored: {type(exc).__name__}") from exc
    finally:
        if profile_temp and profile_temp.exists():
            profile_temp.unlink(missing_ok=True)
    if target_moved:
        try:
            shutil.rmtree(target_backup)
        except OSError:
            return True
    return False


def validate_report(report: dict[str, Any]) -> None:
    try:
        schema = json.loads(REPORT_SCHEMA.read_text(encoding="utf-8"))
        validate_json(report, schema)
    except Exception as exc:
        raise AdapterError(f"generator report violates its schema: {type(exc).__name__}") from exc


def inspect_adapter(root: Path, profile_relative: str, adapter_id: str, *, execute: bool = False) -> dict[str, Any]:
    root = root.resolve(strict=True)
    profile_path, profile, adapter = load_configuration(root, profile_relative, adapter_id)
    profile_relative = profile_path.relative_to(root).as_posix()
    spec_path, spec_digest, inputs = verify_openapi(root, profile, adapter, profile_relative)
    target, existing, old_hashes = validate_existing_output(root, profile, adapter, inputs)
    parent_relative = target.parent.relative_to(root).as_posix()
    if not target.parent.is_dir() or parent_relative == ".":
        raise AdapterError("output_dir parent must already exist inside the repository")
    safe_relative(adapter["output_dir"], "output_dir")
    revision = git(root, "rev-parse", "HEAD")
    profile_before = profile_path.read_bytes()
    profile_sha = digest(profile_before)
    generator = {"id": adapter["id"], "executable": adapter["executable"],
                 "executable_sha256": adapter["executable_sha256"], "version": adapter["version"],
                 "argv_sha256": canonical_digest(adapter["argv"])}
    report: dict[str, Any] = {"schema_version": 1, "kind": "openapi_generator_adapter",
        "status": "READY" if not execute else "UNVERIFIED", "mode": "run" if execute else "preview",
        "candidate_revision": revision, "profile": {"path": profile_relative, "before_sha256": profile_sha,
        "after_sha256": profile_sha}, "contract": {"path": adapter["spec_path"], "sha256": spec_digest},
        "generator": generator, "inputs": inputs, "output_dir": adapter["output_dir"],
        "outputs": [], "runs": [], "deterministic": adapter["deterministic"],
        "determinism_verified": None, "applied": False, "existing_outputs_sha256": old_hashes,
        "cleanup_pending": False, "raw_output_persisted": False}
    if not execute:
        report["fingerprint"] = canonical_digest(report)
        validate_report(report)
        return report

    executable = repo_path(root, adapter["executable"])
    env_tmp = tempfile.TemporaryDirectory(prefix="aips-generator-version-")
    try:
        version_run = run_process([str(executable), *adapter["version_args"]], Path(env_tmp.name),
                                  minimal_env(Path(env_tmp.name)), adapter["timeout_seconds"])
    finally:
        env_tmp.cleanup()
    report["runs"].append({key: value for key, value in version_run.items() if key != "output_preview"})
    if version_run["status"] != "PASS" or version_run.get("output_preview", "").strip() != adapter["version"]:
        report["status"] = "UNVERIFIED" if version_run["status"] == "UNVERIFIED" else "BLOCKED"
        report["fingerprint"] = canonical_digest(report)
        validate_report(report)
        return report
    if version_run.get("output_bytes", 0) > 8192 or version_run.get("output_truncated"):
        report["status"] = "UNVERIFIED"
        report["fingerprint"] = canonical_digest(report)
        validate_report(report)
        return report
    generator["version_output_sha256"] = version_run["output_sha256"]

    scratch_context = tempfile.TemporaryDirectory(prefix=".aips-openapi-generator-", dir=target.parent)
    try:
        scratch = Path(scratch_context.name)
        repeats = 2 if adapter["deterministic"] else 1
        outputs: list[list[dict[str, Any]]] = []
        output_directories: list[Path] = []
        for index in range(repeats):
            run_root = scratch / f"run-{index + 1}"
            run_root.mkdir()
            command = staged_command(adapter, root, run_root, adapter["spec_path"])
            run = run_process(command, run_root, minimal_env(run_root), adapter["timeout_seconds"])
            report["runs"].append({key: value for key, value in run.items() if key != "output_preview"})
            if run["status"] != "PASS":
                report["status"] = run["status"]
                report["fingerprint"] = canonical_digest(report)
                validate_report(report)
                return report
            output = run_root / "generated"
            try:
                outputs.append(file_manifest(output, check_patterns(adapter), adapter.get("max_files", 500),
                                              adapter.get("max_bytes", 25_000_000)))
            except AdapterError:
                report["status"] = "BLOCKED"
                report["fingerprint"] = canonical_digest(report)
                validate_report(report)
                return report
            output_directories.append(output)
        report["determinism_verified"] = len(outputs) == 2 and outputs[0] == outputs[1] if adapter["deterministic"] else False
        if adapter["deterministic"] and outputs[0] != outputs[1]:
            report["status"] = "UNVERIFIED"
            report["fingerprint"] = canonical_digest(report)
            validate_report(report)
            return report
        local_outputs = outputs[-1]
        full_outputs = expanded_manifest(root, adapter["output_dir"], local_outputs)
        profile_after = updated_profile(profile, adapter, sorted(inputs, key=lambda row: row["path"]), full_outputs)
        report["outputs"] = full_outputs
        report["profile"]["after_sha256"] = digest(profile_after)
        # Stage replacement is a directory rename on the same filesystem as the final target.
        prepared = scratch / "prepared-output"
        shutil.copytree(output_directories[-1], prepared)
        report["cleanup_pending"] = atomic_apply(root, profile_path, profile_before, profile_after,
                                                  target, prepared, existing, old_hashes)
        report["status"] = "PASS"
        report["applied"] = True
    finally:
        scratch_context.cleanup()
    report["fingerprint"] = canonical_digest(report)
    validate_report(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path, help="Implementation Profile path")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--adapter-id", required=True)
    parser.add_argument("--execute", action="store_true", help="explicitly authorize local generator execution and output apply")
    parser.add_argument("--report", type=Path, help="write the bounded JSON report to this path; raw generator output is never stored")
    args = parser.parse_args()
    try:
        root = args.repo_root.resolve(strict=True)
        profile = args.profile if args.profile.is_absolute() else root / args.profile
        report = inspect_adapter(root, profile.resolve(strict=True).relative_to(root).as_posix(),
                                 args.adapter_id, execute=args.execute)
        rendered = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        if report["status"] in {"PASS", "READY"}:
            return 0
        return 1 if report["status"] == "FAIL" else 2
    except (AdapterError, ContractError, OSError, ValueError) as exc:
        print(f"OPENAPI GENERATOR ADAPTER BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
