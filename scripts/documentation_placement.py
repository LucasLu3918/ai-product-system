#!/usr/bin/env python3
from __future__ import annotations
import fnmatch
import os
from pathlib import Path
import re
import subprocess
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "documentation-placement.yaml"
H2 = re.compile(r"^##\s+(.+?)\s*$")
H1 = re.compile(r"^#\s+(.+?)\s*$")
VERSION_HEADING = re.compile(r"^##+\s+(?:v?\d+\.\d+|Scenario\s+\d+)", re.I)
NUMERIC_H2 = re.compile(r"^##\s+(\d+[A-Z]?)\.\s+")

def load_config() -> dict[str, Any]:
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise RuntimeError("documentation placement config must be a mapping")
    return data

def heading_ranges(text: str) -> dict[str, tuple[int, int]]:
    lines = text.splitlines()
    items: list[tuple[str, int]] = []
    for index, line in enumerate(lines, start=1):
        m = H2.match(line)
        if m:
            items.append((m.group(1), index))
    result: dict[str, tuple[int, int]] = {}
    for i, (name, start) in enumerate(items):
        end = items[i + 1][1] - 1 if i + 1 < len(items) else len(lines)
        result[name] = (start, end)
    return result

def static_errors(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for raw_path, spec in (config.get("current_behavior_docs") or {}).items():
        path = ROOT / raw_path
        if not path.is_file():
            errors.append(f"missing current-behavior Human doc: {raw_path}")
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        h1 = [line for line in lines if H1.match(line)]
        if len(h1) != 1:
            errors.append(f"{raw_path}: expected exactly one H1, found {len(h1)}")
        for line in lines:
            if VERSION_HEADING.match(line):
                errors.append(f"{raw_path}: release/scenario heading forbidden in current-behavior docs: {line}")
        seen: set[str] = set()
        for line in lines:
            m = NUMERIC_H2.match(line)
            if m:
                if m.group(1) in seen:
                    errors.append(f"{raw_path}: duplicate numeric H2 prefix: {m.group(1)}")
                seen.add(m.group(1))
        ranges = heading_ranges(text)
        for heading in spec.get("required_h2") or []:
            if heading not in ranges:
                errors.append(f"{raw_path}: missing canonical H2 section: {heading}")
    for raw_path in config.get("legacy_append_forbidden") or []:
        path = ROOT / raw_path
        if path.is_file() and "<section" in path.read_text(encoding="utf-8").lower():
            errors.append(f"{raw_path}: legacy HTML must be a compatibility stub")
    return errors

def changed_files(base: str) -> list[str]:
    proc = subprocess.run(["git","diff","--name-only",f"{base}...HEAD"],cwd=ROOT,capture_output=True,text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git diff failed")
    return [x for x in proc.stdout.splitlines() if x]

def changed_new_lines(base: str, path: str) -> list[int]:
    proc = subprocess.run(["git","diff","--unified=0",f"{base}...HEAD","--",path],cwd=ROOT,capture_output=True,text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git diff failed for {path}")
    result: list[int] = []
    for line in proc.stdout.splitlines():
        if not line.startswith("@@"):
            continue
        m = re.search(r"\+(\d+)(?:,(\d+))?", line)
        if m:
            start = int(m.group(1))
            count = int(m.group(2) or "1")
            result.extend(range(start, start + max(count, 1)))
    return result

def matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)

def placement_errors(config: dict[str, Any], base: str) -> list[str]:
    files = changed_files(base)
    errors: list[str] = []
    for rule in config.get("placement_rules") or []:
        if not any(matches_any(path, rule.get("triggers") or []) for path in files):
            continue
        for doc, allowed in (rule.get("placements") or {}).items():
            if doc not in files:
                errors.append(f"{rule['id']}: required canonical Human doc was not changed: {doc}")
                continue
            ranges = heading_ranges((ROOT / doc).read_text(encoding="utf-8"))
            allowed_ranges = [ranges[name] for name in allowed if name in ranges]
            if not allowed_ranges:
                errors.append(f"{rule['id']}: no configured canonical placement section exists in {doc}")
                continue
            lines = changed_new_lines(base, doc)
            if not any(start <= line <= end for line in lines for start, end in allowed_ranges):
                errors.append(f"{rule['id']}: {doc} changed outside allowed canonical sections; do not append release-style notes")
    return errors

def audit() -> list[str]:
    config = load_config()
    errors = static_errors(config)
    base = os.environ.get("AIPS_DOCS_DIFF_BASE","").strip()
    if base:
        errors.extend(placement_errors(config, base))
    return errors

if __name__ == "__main__":
    failures = audit()
    if failures:
        print("DOCUMENTATION PLACEMENT FAILED")
        for item in failures:
            print(f"- {item}")
        raise SystemExit(1)
    print("DOCUMENTATION PLACEMENT PASSED")
