#!/usr/bin/env python3
"""Read-only version-tag provenance readiness; never creates or moves tags."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
UNRELEASED_HEADING_RE = re.compile(r"^## Unreleased[ \t]*$")
H2_HEADING_RE = re.compile(r"^##[ \t]+")


def unreleased_section_errors(changelog_text: str | None) -> list[str]:
    """Require one canonical, empty Unreleased section in the changelog."""
    if changelog_text is None:
        return ["CHANGELOG.md could not be read; Unreleased section readiness is unknown"]

    lines = changelog_text.splitlines()
    headings = [index for index, line in enumerate(lines) if UNRELEASED_HEADING_RE.fullmatch(line)]
    if len(headings) != 1:
        return ["CHANGELOG.md must contain exactly one canonical '## Unreleased' heading"]

    start = headings[0] + 1
    end = next((index for index in range(start, len(lines)) if H2_HEADING_RE.match(lines[index])), len(lines))
    if any(line.strip() for line in lines[start:end]):
        return ["CHANGELOG.md '## Unreleased' section must be empty before release readiness"]
    return []


def evaluate(
    version: str,
    candidate_sha: str,
    main_sha: str,
    existing_tag_sha: str | None,
    expected_version: str | None = None,
    changelog_text: str | None = None,
) -> dict[str, Any]:
    errors = unreleased_section_errors(changelog_text)
    if not VERSION_RE.fullmatch(version):
        errors.append("VERSION must be a stable SemVer X.Y.Z value")
    if expected_version is not None and version != expected_version:
        errors.append("candidate VERSION does not match the requested release version")
    if not re.fullmatch(r"[0-9a-f]{40,64}", candidate_sha):
        errors.append("candidate commit must be a full Git object SHA")
    if not re.fullmatch(r"[0-9a-f]{40,64}", main_sha):
        errors.append("main commit must be a full Git object SHA")
    if candidate_sha != main_sha:
        errors.append("candidate commit is not the exact main commit")
    if existing_tag_sha and existing_tag_sha != candidate_sha:
        errors.append("version tag already exists at a different commit; moved tags are blocked")
    return {
        "version": version, "tag": f"v{version}", "candidate_sha": candidate_sha,
        "main_sha": main_sha, "existing_tag_sha": existing_tag_sha,
        "status": "BLOCKED" if errors else "READY_FOR_EXPLICIT_RELEASE_APPROVAL",
        "errors": errors, "tag_write_authorized": False, "historical_backfill": False,
    }


def git(root: Path, *args: str, check: bool = True) -> str | None:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip() if result.returncode == 0 else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--version-file", default="VERSION")
    parser.add_argument("--main-ref", default="origin/main")
    parser.add_argument("--candidate-sha", help="Require this exact full commit SHA to be the release candidate")
    parser.add_argument("--expected-version", help="Require VERSION to match this exact stable SemVer value")
    parser.add_argument("--changelog-file", default="CHANGELOG.md", help="Changelog whose Unreleased section must be empty")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    version = (repo / args.version_file).read_text(encoding="utf-8").strip()
    candidate = args.candidate_sha or git(repo, "rev-parse", "HEAD") or ""
    main_sha = git(repo, "rev-parse", args.main_ref) or ""
    tag_sha = git(repo, "rev-parse", "refs/tags/v" + version + "^{commit}", check=False)
    try:
        changelog_text = (repo / args.changelog_file).read_text(encoding="utf-8")
    except OSError:
        changelog_text = None
    report = evaluate(version, candidate, main_sha, tag_sha, args.expected_version, changelog_text)
    print(json.dumps(report, indent=2) if args.json else f"{report['status']}: {report['tag']} {report['candidate_sha']}")
    return 0 if report["status"] == "READY_FOR_EXPLICIT_RELEASE_APPROVAL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
