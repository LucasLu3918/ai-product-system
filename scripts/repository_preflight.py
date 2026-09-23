#!/usr/bin/env python3
"""Fast, diff-aware checks that must pass before expensive lifecycle validation."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import documentation_audience  # noqa: E402
import documentation_placement  # noqa: E402
import documentation_sync  # noqa: E402


def run(base: str, head: str) -> list[str]:
    errors: list[str] = []
    diff = subprocess.run(
        ["git", "diff", "--check", f"{base}...{head}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if diff.returncode:
        errors.append(f"git diff --check failed: {diff.stdout.strip() or diff.stderr.strip()}")

    sync_config = yaml.safe_load((ROOT / "config/documentation-sync.yaml").read_text(encoding="utf-8")) or {}
    try:
        files = documentation_sync.changed_files_from_git(base, head)
        errors.extend(
            f"Documentation consistency: {item}"
            for item in documentation_sync.evaluate_changes(files, sync_config)
        )
    except Exception as exc:
        errors.append(f"Documentation consistency failed: {exc}")

    previous = os.environ.get("AIPS_DOCS_DIFF_BASE")
    os.environ["AIPS_DOCS_DIFF_BASE"] = base
    try:
        errors.extend(
            f"Documentation placement: {item}"
            for item in documentation_placement.audit()
        )
    finally:
        if previous is None:
            os.environ.pop("AIPS_DOCS_DIFF_BASE", None)
        else:
            os.environ["AIPS_DOCS_DIFF_BASE"] = previous

    audience_config = documentation_audience.load_config(ROOT / "config/documentation-audience.yaml")
    errors.extend(
        f"Documentation audience: {item}"
        for item in documentation_audience.validate_layout(ROOT, audience_config)
    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    args = parser.parse_args()
    errors = run(args.base, args.head)
    if errors:
        print("REPOSITORY PREFLIGHT FAILED")
        for item in errors:
            print(f"- {item}")
        return 1
    print("REPOSITORY PREFLIGHT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
