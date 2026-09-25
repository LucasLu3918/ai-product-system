#!/usr/bin/env python3
"""Deterministic secret scan with redacted findings and publication-candidate mode."""

from __future__ import annotations

import argparse
from datetime import date
import fnmatch
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any, Iterable

import yaml

DEFAULT_POLICY = Path(__file__).resolve().parents[1] / "config" / "secret-scan.yaml"
SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "vendor", "dist", "build",
    "coverage", ".next", ".cache", ".ruff_cache", ".pytest_cache", "target", "__pycache__",
}
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".ico", ".pdf",
    ".zip", ".gz", ".tar", ".7z", ".woff", ".woff2", ".ttf", ".otf",
    ".mp3", ".mp4", ".mov", ".sqlite", ".db",
}
PLACEHOLDER_HINTS = {
    "placeholder", "example", "dummy", "fake", "changeme", "replace_me",
    "replace-me", "your_", "your-", "xxxxx", "redacted", "sample", "fixture",
}
PATTERNS = [
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,255}|github_pat_[A-Za-z0-9_]{30,255})\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,255}\b")),
    ("stripe-live-key", re.compile(r"\bsk_live_[A-Za-z0-9]{20,255}\b")),
]
ASSIGNMENT = re.compile(
    r"""(?ix)
    \b(password|passwd|pwd|secret|api[_-]?key|access[_-]?token|client[_-]?secret|private[_-]?key)
    \s*[:=]\s*
    ["']?([^\s"' ,;}{\]]{12,})["']?
    """
)


class ScanError(ValueError):
    """A candidate could not be scanned completely or safely."""


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8"))


def load_policy(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    try:
        policy = yaml.safe_load(raw.decode("utf-8"))
    except (UnicodeError, yaml.YAMLError) as exc:
        raise ScanError("secret-scan policy is not valid UTF-8 YAML") from exc
    if not isinstance(policy, dict) or policy.get("version") != 1:
        raise ScanError("secret-scan policy version must be 1")
    limits = policy.get("limits") or {}
    if not isinstance(limits, dict) or not isinstance(limits.get("max_file_bytes"), int) or limits["max_file_bytes"] < 1:
        raise ScanError("secret-scan policy requires a positive limits.max_file_bytes")
    generated = policy.get("generated_paths") or []
    lockfiles = policy.get("lockfiles") or {}
    allowlist = policy.get("allowlist") or []
    if not isinstance(generated, list) or not all(isinstance(x, str) and x for x in generated):
        raise ScanError("secret-scan policy generated_paths must be a list of globs")
    if not isinstance(lockfiles, dict) or not isinstance(lockfiles.get("path_patterns"), list) or not isinstance(lockfiles.get("disabled_detectors"), list):
        raise ScanError("secret-scan policy lockfiles configuration is invalid")
    if not isinstance(allowlist, list):
        raise ScanError("secret-scan policy allowlist must be a list")
    for item in allowlist:
        if not isinstance(item, dict) or not all(item.get(key) for key in ("path", "detector", "fingerprint", "reason", "expires")):
            raise ScanError("each allowlist entry requires path, detector, fingerprint, reason, and expires")
        if not re.fullmatch(r"[0-9a-f]{16}", str(item["fingerprint"])):
            raise ScanError("allowlist fingerprint must be a 16-character lowercase SHA-256 prefix")
        try:
            expiry = date.fromisoformat(str(item["expires"]))
        except ValueError as exc:
            raise ScanError("allowlist expiry must use YYYY-MM-DD") from exc
        if expiry < date.today():
            raise ScanError("secret-scan policy contains an expired allowlist entry")
    return policy, sha256(raw)


def entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = {c: value.count(c) for c in set(value)}
    n = len(value)
    return -sum((count / n) * math.log2(count / n) for count in counts.values())


def placeholder(value: str) -> bool:
    low = value.lower()
    return any(h in low for h in PLACEHOLDER_HINTS) or value.startswith(("${", "{{", "<"))


def fingerprint(value: str) -> str:
    return sha256(value.encode("utf-8", errors="replace"))[:16]


def normalize_path(path: str) -> str:
    normalized = PurePosixPath(path.replace("\\", "/")).as_posix()
    return normalized[2:] if normalized.startswith("./") else normalized


def glob_matches(path: str, pattern: str) -> bool:
    normalized = normalize_path(path)
    return fnmatch.fnmatch(normalized, pattern) or (
        pattern.startswith("**/") and fnmatch.fnmatch(normalized, pattern[3:])
    )


def generated_path(path: str, policy: dict[str, Any]) -> bool:
    normalized = normalize_path(path)
    parts = PurePosixPath(normalized).parts
    if any(part in SKIP_DIRS or part.startswith(".venv.") for part in parts):
        return True
    return any(glob_matches(normalized, pattern) for pattern in policy.get("generated_paths", []))


def active_allowlist(path: str, detector: str, value_fingerprint: str, policy: dict[str, Any]) -> bool:
    today = date.today()
    for item in policy.get("allowlist", []):
        if item["expires"] < today.isoformat():
            raise ScanError("secret-scan policy contains an expired allowlist entry")
        if (
            glob_matches(path, str(item["path"]))
            and item["detector"] == detector
            and item["fingerprint"] == value_fingerprint
        ):
            return True
    return False


def add_finding(
    findings: list[dict[str, Any]], path: str, line: int, detector: str, value: str,
    policy: dict[str, Any], *, revision: str | None = None,
) -> None:
    value_fingerprint = fingerprint(value)
    if active_allowlist(path, detector, value_fingerprint, policy):
        return
    result: dict[str, Any] = {
        "path": normalize_path(path),
        "line": line,
        "detector": detector,
        "fingerprint": value_fingerprint,
        "secret_length": len(value),
    }
    if revision:
        result["revision"] = revision
    findings.append(result)


def scan_text(
    text: str, location: str = "<payload>", policy: dict[str, Any] | None = None, *,
    strict: bool = False, findings: list[dict[str, Any]] | None = None,
    revision: str | None = None,
) -> list[dict[str, Any]]:
    # Keep the original two-argument API used by Runtime Content Safety.
    if policy is None:
        policy = {"allowlist": [], "lockfiles": {"path_patterns": [], "disabled_detectors": []}}
    if findings is None:
        findings = []
    if not strict and "AIPS-SECRET-SCAN-IGNORE-FILE" in text:
        return findings
    lockfiles = policy.get("lockfiles") or {}
    is_lockfile = any(glob_matches(location, pattern) for pattern in lockfiles.get("path_patterns", []))
    disabled = set(lockfiles.get("disabled_detectors", [])) if is_lockfile else set()
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not strict and "AIPS-SECRET-SCAN-IGNORE-LINE" in line:
            continue
        for detector, pattern in PATTERNS:
            if detector in disabled:
                continue
            for match in pattern.finditer(line):
                add_finding(findings, location, line_no, detector, match.group(0), policy, revision=revision)
        if "generic-secret-assignment" not in disabled:
            for match in ASSIGNMENT.finditer(line):
                value = match.group(2)
                if placeholder(value):
                    continue
                if len(value) < 20 or entropy(value) < 3.25:
                    continue
                add_finding(findings, location, line_no, "generic-secret-assignment", value, policy, revision=revision)
    return findings


def iter_files(root: Path, explicit: list[str], policy: dict[str, Any]) -> Iterable[Path]:
    if explicit:
        for item in explicit:
            path = (root / item).resolve() if not Path(item).is_absolute() else Path(item).resolve()
            if path.is_file():
                yield path
        return
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".venv.")]
        for name in files:
            path = Path(base) / name
            relative = path.relative_to(root).as_posix()
            if not generated_path(relative, policy) and path.suffix.lower() not in BINARY_EXT:
                yield path


def scan_worktree(root: Path, policy: dict[str, Any], *, strict: bool, paths: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    findings: list[dict[str, Any]] = []
    blockers: list[str] = []
    for path in iter_files(root, paths, policy):
        relative = path.relative_to(root).as_posix()
        if generated_path(relative, policy) or path.suffix.lower() in BINARY_EXT:
            continue
        try:
            if path.stat().st_size > policy["limits"]["max_file_bytes"]:
                if strict:
                    blockers.append(f"candidate file exceeds scan limit: {relative}")
                continue
            payload = path.read_bytes()
            text = payload.decode("utf-8")
            if "\x00" in text:
                if strict:
                    blockers.append(f"candidate file has unknown binary format: {relative}")
                continue
        except (OSError, UnicodeError):
            if strict:
                blockers.append(f"candidate file is unreadable or not UTF-8 text: {relative}")
            continue
        scan_text(text, relative, policy, strict=strict, findings=findings)
    return findings, blockers


def git(root: Path, *args: str, check: bool = True) -> bytes:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True)
    if check and proc.returncode:
        raise ScanError("Git could not resolve the exact publication candidate")
    return proc.stdout


def git_text(root: Path, *args: str, check: bool = True) -> str:
    return git(root, *args, check=check).decode("utf-8", errors="replace").strip()


def decode_tree_paths(raw: bytes) -> list[tuple[str, str, str]]:
    entries = []
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        metadata, path = entry.split(b"\t", 1)
        mode, kind, sha = metadata.decode("ascii").split()
        entries.append((mode, sha, path.decode("utf-8", errors="strict")))
    return entries


def scan_candidate(root: Path, base: str, head: str, policy: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], str, str]:
    base_sha = git_text(root, "rev-parse", "--verify", f"{base}^{{commit}}")
    head_sha = git_text(root, "rev-parse", "--verify", f"{head}^{{commit}}")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", base_sha, head_sha], cwd=root, capture_output=True
    )
    if ancestor.returncode != 0:
        raise ScanError("candidate base is not an ancestor of candidate head")

    findings: list[dict[str, Any]] = []
    blockers: list[str] = []
    max_bytes = policy["limits"]["max_file_bytes"]

    # Scan the committed final tree, not a possibly dirty filesystem view.
    for mode, blob_sha, path in decode_tree_paths(git(root, "ls-tree", "-rz", "--full-tree", head_sha)):
        if mode == "160000" or generated_path(path, policy) or PurePosixPath(path).suffix.lower() in BINARY_EXT:
            continue
        if mode == "120000":
            continue
        try:
            if int(git_text(root, "cat-file", "-s", blob_sha)) > max_bytes:
                blockers.append(f"candidate file exceeds scan limit: {normalize_path(path)}")
                continue
            payload = git(root, "cat-file", "blob", blob_sha)
            text = payload.decode("utf-8")
            if "\x00" in text:
                blockers.append(f"candidate file has unknown binary format: {normalize_path(path)}")
                continue
        except (ScanError, UnicodeError):
            blockers.append(f"candidate file is unreadable or not UTF-8 text: {normalize_path(path)}")
            continue
        scan_text(text, path, policy, strict=True, findings=findings)

    # Scan every reachable commit's added/modified blobs so a secret removed by
    # a later commit still blocks publication of the history containing it.
    commits = git_text(root, "rev-list", "--reverse", f"{base_sha}..{head_sha}").splitlines()
    for commit in commits:
        message = git_text(root, "show", "-s", "--format=%B", commit)
        scan_text(message, "<commit-message>", policy, strict=True, findings=findings, revision=commit)
        parent = git_text(root, "rev-parse", f"{commit}^", check=False)
        if not parent:
            continue
        changed = git(root, "diff-tree", "--no-commit-id", "--diff-filter=AM", "--no-renames", "-r", "--name-only", "-z", parent, commit)
        for raw_path in changed.split(b"\0"):
            if not raw_path:
                continue
            try:
                path = raw_path.decode("utf-8", errors="strict")
            except UnicodeError:
                blockers.append("candidate history contains a path that is not UTF-8")
                continue
            if generated_path(path, policy) or PurePosixPath(path).suffix.lower() in BINARY_EXT:
                continue
            try:
                object_spec = f"{commit}:{path}"
                if int(git_text(root, "cat-file", "-s", object_spec)) > max_bytes:
                    blockers.append(f"candidate history file exceeds scan limit: {normalize_path(path)}")
                    continue
                payload = git(root, "cat-file", "blob", object_spec)
                text = payload.decode("utf-8")
                if "\x00" in text:
                    blockers.append(f"candidate history file has unknown binary format: {normalize_path(path)}")
                    continue
            except (ScanError, UnicodeError):
                blockers.append(f"candidate history file is unreadable or not UTF-8 text: {normalize_path(path)}")
                continue
            scan_text(text, path, policy, strict=True, findings=findings, revision=commit)

    # De-duplicate identical findings from final tree and repeated history blobs.
    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for item in findings:
        key = (item["path"], item["line"], item["detector"], item["fingerprint"], item.get("revision"))
        unique[key] = item
    return list(unique.values()), blockers, base_sha, head_sha


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--path", action="append", default=[], dest="paths")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--strict", action="store_true", help="Disable inline ignore markers and fail on incomplete scans")
    parser.add_argument("--publication-candidate", action="store_true", help="Scan exact Git tree and every commit in base..head")
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    findings: list[dict[str, Any]] = []
    blockers: list[str] = []
    candidate: dict[str, str] | None = None
    try:
        policy_path = args.policy.expanduser().resolve()
        policy, policy_hash = load_policy(policy_path)
        strict = args.strict or args.publication_candidate
        if args.publication_candidate:
            args.base = args.base or os.environ.get("AIPS_GATE_BASE_SHA")
            args.head = args.head or os.environ.get("AIPS_GATE_HEAD_SHA")
            if not args.base or not args.head:
                raise ScanError("publication-candidate mode requires --base and --head")
            findings, blockers, base_sha, head_sha = scan_candidate(root, args.base, args.head, policy)
            candidate = {"base_sha": base_sha, "head_sha": head_sha}
        else:
            findings, blockers = scan_worktree(root, policy, strict=strict, paths=args.paths)
        scanner_hash = sha256(Path(__file__).read_bytes())
    except (OSError, UnicodeError, ScanError, yaml.YAMLError, ValueError) as exc:
        blockers.append(str(exc))
        policy_hash = sha256(b"unavailable")
        scanner_hash = sha256(Path(__file__).read_bytes())

    if blockers:
        status = "BLOCKED"
    elif findings:
        status = "FAIL"
    else:
        status = "PASS"
    result: dict[str, Any] = {
        "status": status,
        "findings": findings,
        "blockers": blockers,
        "policy_sha256": policy_hash,
        "scanner_sha256": scanner_hash,
        "note": "Secret values are never emitted; fingerprint is SHA-256 prefix only.",
    }
    if candidate:
        result["candidate"] = candidate
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"SECRET_SCAN_{status}")
        for item in findings:
            revision = f" revision={item['revision']}" if item.get("revision") else ""
            print(
                f"{item['path']}:{item['line']} detector={item['detector']} "
                f"fingerprint={item['fingerprint']} length={item['secret_length']}{revision}"
            )
        for blocker in blockers:
            print(f"BLOCKER: {blocker}")
    return 0 if status == "PASS" else 1 if status == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
