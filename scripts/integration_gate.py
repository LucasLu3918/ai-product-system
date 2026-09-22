#!/usr/bin/env python3
"""Deterministic Integration/Janitor Gate for an exact Git candidate."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import yaml


class GateError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise GateError(f"expected mapping: {path}")
    return data


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def git(*args: str) -> str:
    proc = subprocess.run(["git", *args], text=True, capture_output=True)
    if proc.returncode != 0:
        raise GateError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def resolve_commit(ref: str) -> str:
    return git("rev-parse", f"{ref}^{{commit}}")


def changed_files(base_sha: str, head_sha: str) -> list[str]:
    out = git("diff", "--name-only", f"{base_sha}...{head_sha}")
    return sorted(line.strip() for line in out.splitlines() if line.strip())


def profile_checks(profile: dict[str, Any], files: list[str]) -> list[dict[str, Any]]:
    if profile.get("version") != 1:
        raise GateError("validation profile version must be 1")
    raw = profile.get("checks")
    if not isinstance(raw, list) or not raw:
        raise GateError("validation profile checks must be a non-empty list")

    ids: set[str] = set()
    checks: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise GateError("each validation check must be a mapping")
        check_id = item.get("id")
        if not isinstance(check_id, str) or not check_id:
            raise GateError("each validation check requires id")
        if check_id in ids:
            raise GateError(f"duplicate validation check id: {check_id}")
        ids.add(check_id)
        argv = item.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            raise GateError(f"check {check_id}: argv must be a non-empty string list")
        paths = item.get("paths") or ["**"]
        if not isinstance(paths, list) or not all(isinstance(x, str) and x for x in paths):
            raise GateError(f"check {check_id}: paths must be a list of glob strings")
        env = item.get("env") or {}
        if not isinstance(env, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in env.items()):
            raise GateError(f"check {check_id}: env must be a string mapping")
        applies = not files or any(any(fnmatch.fnmatch(path, pattern) for pattern in paths) for path in files)
        enriched = dict(item)
        enriched["applies"] = applies
        enriched["env"] = env
        checks.append(enriched)
    return checks


def matrix_required_for_candidate(profile: dict[str, Any], files: list[str], change_class: str) -> bool:
    if bool(profile.get("matrix_required", False)):
        return True
    classes = profile.get("matrix_required_change_classes") or []
    if not isinstance(classes, list) or not all(isinstance(x, str) for x in classes):
        raise GateError("matrix_required_change_classes must be a list of strings")
    if change_class in classes:
        return True
    patterns = profile.get("matrix_required_paths") or []
    if not isinstance(patterns, list) or not all(isinstance(x, str) and x for x in patterns):
        raise GateError("matrix_required_paths must be a list of glob strings")
    return any(any(fnmatch.fnmatch(path, pattern) for pattern in patterns) for path in files)


def matrix_fingerprint(
    path: Path | None,
    required: bool,
    *,
    base_sha: str,
    changed_files_hash: str,
) -> tuple[str | None, dict[str, Any] | None]:
    if path is None:
        if required:
            raise GateError("candidate requires Core Change Test Matrix")
        return None, None
    matrix = load_yaml(path)
    if not required:
        return canonical_hash(matrix), matrix
    if matrix.get("status") not in {"READY", "APPROVED", "PASS"}:
        raise GateError(f"Core Change Test Matrix status is not executable: {matrix.get('status')!r}")
    blockers = matrix.get("blockers") or []
    if blockers:
        raise GateError("Core Change Test Matrix contains blockers")
    if not matrix.get("actual_diff_reconciled"):
        raise GateError("Core Change Test Matrix actual_diff_reconciled must be true")
    binding = matrix.get("candidate") or {}
    if binding.get("base_sha") != base_sha:
        raise GateError("Core Change Test Matrix base_sha does not match candidate")
    if binding.get("changed_files_hash") != changed_files_hash:
        raise GateError("Core Change Test Matrix changed_files_hash does not match candidate")
    return canonical_hash(matrix), matrix


def run_check(item: dict[str, Any], *, omit_output_tail: bool = False) -> dict[str, Any]:
    if not item["applies"]:
        return {"id": item["id"], "category": item.get("category"), "status": "SKIPPED", "reason": "path_filter"}
    timeout = item.get("timeout_seconds", 600)
    if not isinstance(timeout, int) or timeout < 1:
        raise GateError(f"check {item['id']}: timeout_seconds must be >= 1")
    check_env = dict(os.environ)
    check_env.update(item.get("env") or {})
    started = time.monotonic()
    try:
        proc = subprocess.run(item["argv"], text=True, capture_output=True, timeout=timeout, env=check_env)
        duration_ms = int((time.monotonic() - started) * 1000)
        output = (proc.stdout + proc.stderr).strip()
        result = {
            "id": item["id"],
            "category": item.get("category"),
            "required": bool(item.get("required", True)),
            "status": "PASS" if proc.returncode == 0 else "FAIL",
            "exit_code": proc.returncode,
            "duration_ms": duration_ms,
        }
        if omit_output_tail:
            result["output_sha256"] = hashlib.sha256(output.encode("utf-8", errors="replace")).hexdigest()
        else:
            result["output_tail"] = output[-4000:]
        return result
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        result = {
            "id": item["id"],
            "category": item.get("category"),
            "required": bool(item.get("required", True)),
            "status": "FAIL",
            "exit_code": None,
            "duration_ms": duration_ms,
            "reason": "timeout",
        }
        if not omit_output_tail:
            result["output_tail"] = f"timeout after {timeout}s: {exc}"
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--base-tip")
    parser.add_argument("--change-class", choices=("standard", "large", "core"), default="standard")
    parser.add_argument("--matrix", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    parser.add_argument("--omit-output-tail", action="store_true", help="Omit check output from the report and stdout")
    args = parser.parse_args()

    try:
        profile = load_yaml(args.profile)
        base_sha = resolve_commit(args.base)
        head_sha = resolve_commit(args.head)
        base_tip_sha = resolve_commit(args.base_tip) if args.base_tip else None
        if base_tip_sha is not None and base_tip_sha != base_sha:
            raise GateError(f"candidate base is stale: declared={base_sha} current={base_tip_sha}")
        current_sha = resolve_commit("HEAD")
        if current_sha != head_sha:
            raise GateError(f"candidate checkout mismatch: HEAD={current_sha} expected={head_sha}")
        files = changed_files(base_sha, head_sha)
        files_hash = canonical_hash(files)
        matrix_required = matrix_required_for_candidate(profile, files, args.change_class)
        matrix_hash, _ = matrix_fingerprint(
            args.matrix,
            matrix_required,
            base_sha=base_sha,
            changed_files_hash=files_hash,
        )
        checks = profile_checks(profile, files)
        profile_hash = canonical_hash(profile)
        candidate = {
            "base_sha": base_sha,
            "base_tip_sha": base_tip_sha,
            "head_sha": head_sha,
            "change_class": args.change_class,
            "changed_files": files,
            "changed_files_hash": files_hash,
            "profile_hash": profile_hash,
            "matrix_required": matrix_required,
            "matrix_hash": matrix_hash,
        }
        candidate_fingerprint = canonical_hash(candidate)
        results = [run_check(item, omit_output_tail=args.omit_output_tail) for item in checks]
        failures = [r["id"] for r in results if r.get("status") == "FAIL" and r.get("required", True)]
        report = {
            "version": 1,
            "profile_id": profile.get("profile_id"),
            "candidate": candidate,
            "candidate_fingerprint": candidate_fingerprint,
            "checks": results,
            "status": "PASS" if not failures else "FAIL",
            "blockers": failures,
            "authority": {
                "merge_authorized": False,
                "release_authorized": False,
                "human_authority_preserved": True,
            },
        }
    except (OSError, yaml.YAMLError, GateError) as exc:
        print(f"INTEGRATION GATE BLOCKED: {exc}")
        return 2

    rendered = (
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.format == "json"
        else yaml.safe_dump(report, sort_keys=False, allow_unicode=True)
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
