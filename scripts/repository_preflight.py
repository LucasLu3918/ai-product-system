#!/usr/bin/env python3
"""Fast, diff-aware checks that must pass before expensive lifecycle validation."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import documentation_audience  # noqa: E402
import documentation_placement  # noqa: E402
import documentation_sync  # noqa: E402


MARKDOWN_LINK = re.compile(r"!?(?:\[[^\]]*\])\(\s*(<[^>]+>|[^\s)]+)")


def markdown_files_changed(base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMRT", f"{base}...{head}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        return []
    return [path for path in result.stdout.splitlines() if path.lower().endswith(".md")]


def check_markdown_links(root: Path, paths: list[str]) -> list[str]:
    errors: list[str] = []
    for rel_path in paths:
        source = (root / rel_path).resolve()
        if not source.is_file() or not source.is_relative_to(root.resolve()):
            continue
        text = source.read_text(encoding="utf-8")
        text = re.sub(r"(?ms)^(```|~~~).*?^\1[^\S\r\n]*$", "", text)
        for match in MARKDOWN_LINK.finditer(text):
            raw = match.group(1).strip("<>")
            parsed = urlsplit(raw)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target_text = unquote(parsed.path)
            if target_text.startswith("/"):
                site_root = root / "docs/human" if source.is_relative_to((root / "docs/human").resolve()) else root
                target = (site_root / target_text.lstrip("/")).resolve()
            else:
                target = (source.parent / target_text).resolve()
            if not target.is_relative_to(root.resolve()):
                errors.append(f"{rel_path}: local Markdown link escapes the repository: {raw}")
                continue
            candidates = [target]
            if target.is_dir():
                candidates.extend((target / "index.md", target / "index.html"))
            if not any(candidate.is_file() for candidate in candidates):
                errors.append(f"{rel_path}: local Markdown link target does not exist: {raw}")
    return errors


def build_docs_site() -> list[str]:
    if not shutil.which("node"):
        return ["documentation site build requires Node.js on PATH; install Node.js or add its bin directory to PATH, then run `npm run docs:build`"]
    vitepress = ROOT / "node_modules/.bin/vitepress"
    if not vitepress.exists():
        return ["VitePress dependencies are not installed; run `npm install` or `pnpm install`, then rerun the publication preflight"]
    command = [str(vitepress), "build", "docs/human"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        detail = (result.stdout + "\n" + result.stderr).strip().splitlines()[-12:]
        return ["documentation site build failed: " + " | ".join(detail)]
    return []


def run(base: str, head: str, docs_build: bool = False) -> list[str]:
    errors: list[str] = []
    diff = subprocess.run(
        ["git", "diff", "--check", f"{base}...{head}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if diff.returncode:
        errors.append(f"git diff --check failed: {diff.stdout.strip() or diff.stderr.strip()}")

    changed_markdown = markdown_files_changed(base, head)
    try:
        files = documentation_sync.changed_files_from_git(base, head)
    except Exception as exc:
        files = []
        errors.append(f"Documentation consistency failed: {exc}")
    errors.extend(f"Markdown links: {item}" for item in check_markdown_links(ROOT, changed_markdown))
    if docs_build and any(path.startswith("docs/human/") or path in {"package.json", "package-lock.json"} for path in files):
        errors.extend(build_docs_site())

    sync_config = yaml.safe_load((ROOT / "config/documentation-sync.yaml").read_text(encoding="utf-8")) or {}
    errors.extend(
        f"Documentation consistency: {item}"
        for item in documentation_sync.evaluate_changes(files, sync_config)
    )

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
    parser.add_argument("--docs-build", action="store_true", help="Build the VitePress documentation site when documentation paths changed.")
    args = parser.parse_args()
    errors = run(args.base, args.head, docs_build=args.docs_build)
    if errors:
        print("REPOSITORY PREFLIGHT FAILED")
        for item in errors:
            print(f"- {item}")
        return 1
    print("REPOSITORY PREFLIGHT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
