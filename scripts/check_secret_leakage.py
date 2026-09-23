#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Iterable

SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "vendor", "dist", "build",
    "coverage", ".next", ".cache", "target", "__pycache__",
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


def entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = {c: value.count(c) for c in set(value)}
    n = len(value)
    return -sum((count / n) * math.log2(count / n) for count in counts.values())


def placeholder(value: str) -> bool:
    low = value.lower()
    if any(h in low for h in PLACEHOLDER_HINTS):
        return True
    if value.startswith("${") or value.startswith("{{") or value.startswith("<"):
        return True
    return False


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]


def iter_files(root: Path, explicit: list[str]) -> Iterable[Path]:
    if explicit:
        for item in explicit:
            p = (root / item).resolve() if not Path(item).is_absolute() else Path(item).resolve()
            if p.is_file():
                yield p
        return
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".venv.")]
        for name in files:
            p = Path(base) / name
            if p.suffix.lower() in BINARY_EXT:
                continue
            try:
                if p.stat().st_size > 2_000_000:
                    continue
            except OSError:
                continue
            yield p


def add_finding(findings: list[dict], path: Path, root: Path, line: int, detector: str, value: str) -> None:
    try:
        shown = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        shown = str(path)
    findings.append({
        "path": shown,
        "line": line,
        "detector": detector,
        "fingerprint": fingerprint(value),
        "secret_length": len(value),
    })


def scan_text(text: str, location: str = "<payload>") -> list[dict]:
    """Scan one in-memory payload without ever returning the detected value."""
    findings: list[dict] = []
    root = Path(".").resolve()
    path = Path(location)
    if "AIPS-SECRET-SCAN-IGNORE-FILE" in text:
        return findings
    for line_no, line in enumerate(text.splitlines(), start=1):
        if "AIPS-SECRET-SCAN-IGNORE-LINE" in line:
            continue
        for detector, pattern in PATTERNS:
            for match in pattern.finditer(line):
                add_finding(findings, path, root, line_no, detector, match.group(0))
        for match in ASSIGNMENT.finditer(line):
            value = match.group(2)
            if placeholder(value):
                continue
            if len(value) < 20 or entropy(value) < 3.25:
                continue
            add_finding(findings, path, root, line_no, "generic-secret-assignment", value)
    return findings


def scan_file(path: Path, root: Path, findings: list[dict]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return
    findings.extend(scan_text(text, str(path)))


def main() -> int:
    parser = argparse.ArgumentParser(description="High-confidence secret leakage checker with redacted output")
    parser.add_argument("--root", default=".")
    parser.add_argument("--path", action="append", default=[], dest="paths")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    findings: list[dict] = []
    for path in iter_files(root, args.paths):
        scan_file(path, root, findings)

    result = {
        "status": "FAIL" if findings else "PASS",
        "findings": findings,
        "note": "Secret values are never emitted; fingerprint is SHA-256 prefix only.",
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"SECRET_SCAN_{result['status']}")
        for item in findings:
            print(
                f"{item['path']}:{item['line']} detector={item['detector']} "
                f"fingerprint={item['fingerprint']} length={item['secret_length']}"
            )
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
