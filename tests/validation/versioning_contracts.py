from __future__ import annotations

import re

from .static_contracts import ROOT

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
HEADING = re.compile(r"^## (.+?)\s*$", re.MULTILINE)


def validate_changelog(changelog: str, version: str) -> list[str]:
    errors: list[str] = []
    headings = HEADING.findall(changelog)
    if not headings or headings[0] != "Unreleased":
        errors.append("CHANGELOG.md must start its release headings with ## Unreleased")
    if headings.count("Unreleased") != 1:
        errors.append("CHANGELOG.md must contain exactly one ## Unreleased heading")
    releases = headings[1:] if headings and headings[0] == "Unreleased" else [item for item in headings if item != "Unreleased"]
    parsed: list[tuple[int, int, int]] = []
    for heading in releases:
        match = SEMVER.fullmatch(heading)
        if not match:
            errors.append(f"CHANGELOG.md contains an invalid release heading: {heading}")
            continue
        parsed.append(tuple(int(part) for part in match.groups()))
    if len(set(releases)) != len(releases):
        errors.append("CHANGELOG.md release headings must be unique")
    if any(left <= right for left, right in zip(parsed, parsed[1:])):
        errors.append("CHANGELOG.md released versions must be strictly descending")
    if not SEMVER.fullmatch(version):
        errors.append(f"VERSION is not SemVer x.y.z: {version!r}")
    elif not parsed or parsed[0] != tuple(int(part) for part in version.split(".")):
        errors.append("VERSION must equal the newest released CHANGELOG.md heading")
    return errors


changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
errors = validate_changelog(changelog, version)

valid = "## Unreleased\n\n## 0.72.1\n\n## 0.72.0\n"
if validate_changelog(valid, "0.72.1"):
    errors.append("valid changelog/version fixture was rejected")
for invalid in (
    "## Unreleased\n\n## 0.72.1\n\n## Unreleased\n",
    "## 0.72.1\n\n## Unreleased\n",
    "## Unreleased\n\n## 0.72.1\n\n## 0.72.2\n",
    "## Unreleased\n\n## 0.72.1\n\n## 0.72.1\n",
):
    if not validate_changelog(invalid, "0.72.1"):
        errors.append("invalid changelog/version fixture was accepted")
