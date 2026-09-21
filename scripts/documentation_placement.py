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


def h2_items(text: str) -> list[tuple[str, int]]:
    result: list[tuple[str, int]] = []
    for index, line in enumerate(text.splitlines(), start=1):
        match = H2.match(line)
        if match:
            result.append((match.group(1), index))
    return result


def heading_ranges(text: str) -> dict[str, tuple[int, int]]:
    lines = text.splitlines()
    items = h2_items(text)
    result: dict[str, tuple[int, int]] = {}
    for index, (name, start) in enumerate(items):
        end = items[index + 1][1] - 1 if index + 1 < len(items) else len(lines)
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
                errors.append(
                    f"{raw_path}: release/scenario heading forbidden in current-behavior docs: {line}"
                )

        seen: set[str] = set()
        for line in lines:
            match = NUMERIC_H2.match(line)
            if match:
                if match.group(1) in seen:
                    errors.append(f"{raw_path}: duplicate numeric H2 prefix: {match.group(1)}")
                seen.add(match.group(1))

        actual_h2 = [name for name, _ in h2_items(text)]
        required_h2 = list(spec.get("required_h2") or [])
        for heading in required_h2:
            if heading not in actual_h2:
                errors.append(f"{raw_path}: missing canonical H2 section: {heading}")

        if spec.get("strict_h2"):
            unexpected = [name for name in actual_h2 if name not in required_h2]
            if unexpected:
                errors.append(
                    f"{raw_path}: H2 sections are not in the placement contract: {unexpected}; "
                    "add a real topic to config/documentation-placement.yaml instead of appending ad-hoc sections"
                )

    for raw_path in config.get("legacy_append_forbidden") or []:
        path = ROOT / raw_path
        if path.is_file() and "<section" in path.read_text(encoding="utf-8").lower():
            errors.append(f"{raw_path}: legacy HTML must be a compatibility stub")
    return errors


def git_base_resolves(base: str) -> bool:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def changed_files(base: str) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git diff failed")
    return [item for item in proc.stdout.splitlines() if item]


def added_line_numbers(base: str, path: str) -> list[int]:
    proc = subprocess.run(
        ["git", "diff", "--unified=0", f"{base}...HEAD", "--", path],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git diff failed for {path}")

    result: list[int] = []
    for line in proc.stdout.splitlines():
        if not line.startswith("@@"):
            continue
        match = re.search(r"\+(\d+)(?:,(\d+))?", line)
        if not match:
            continue
        start = int(match.group(1))
        count = int(match.group(2) or "1")
        if count > 0:
            result.extend(range(start, start + count))
    return result


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def line_has_content(lines: list[str], number: int) -> bool:
    return 1 <= number <= len(lines) and bool(lines[number - 1].strip())


def placement_errors(config: dict[str, Any], base: str) -> list[str]:
    migration_bases = set((config.get("policy") or {}).get("one_time_structure_migration_bases") or [])
    if base in migration_bases:
        return []
    files = changed_files(base)
    errors: list[str] = []

    for rule in config.get("placement_rules") or []:
        if not any(matches_any(path, rule.get("triggers") or []) for path in files):
            continue

        for doc, allowed in (rule.get("placements") or {}).items():
            if doc not in files:
                errors.append(f"{rule['id']}: required canonical Human doc was not changed: {doc}")
                continue

            text = (ROOT / doc).read_text(encoding="utf-8")
            lines = text.splitlines()
            ranges = heading_ranges(text)
            missing = [name for name in allowed if name not in ranges]
            if missing:
                errors.append(
                    f"{rule['id']}: configured canonical sections missing from {doc}: {missing}"
                )
                continue

            allowed_ranges = [ranges[name] for name in allowed]
            first_h2_line = min((start for start, _ in ranges.values()), default=len(lines) + 1)
            added = [number for number in added_line_numbers(base, doc) if line_has_content(lines, number)]
            misplaced = [
                number
                for number in added
                if number >= first_h2_line
                and not any(start <= number <= end for start, end in allowed_ranges)
            ]
            if misplaced:
                preview = ", ".join(str(number) for number in misplaced[:12])
                errors.append(
                    f"{rule['id']}: {doc} has added content outside allowed canonical sections "
                    f"(lines {preview}); move the explanation into its topic section or update "
                    "config/documentation-placement.yaml when introducing a genuine new topic"
                )

    return errors


def audit() -> list[str]:
    config = load_config()
    errors = static_errors(config)
    base = os.environ.get("AIPS_DOCS_DIFF_BASE", "").strip()
    if base and git_base_resolves(base):
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
