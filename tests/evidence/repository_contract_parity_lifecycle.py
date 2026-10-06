"""Exercise strict parsing and parity behavior for the repository contract pilot."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "validation"))

from repository_contract_policy import (
    RepositoryContractPolicyError,
    load_policy,
    missing_required_file_findings,
    parse_policy_text,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def rejected(text: str, expected: str) -> None:
    try:
        parse_policy_text(text)
    except RepositoryContractPolicyError as exc:
        require(expected in str(exc), f"expected {expected!r}, got {exc!r}")
    else:
        raise AssertionError(f"policy unexpectedly accepted: {text!r}")


def main() -> int:
    valid = "version: 1\nrequired_files:\n  - README.md\n  - SYSTEM.md\n"
    paths = parse_policy_text(valid)
    require(paths == ["README.md", "SYSTEM.md"], "valid policy must preserve declared paths")

    rejected("version: 1\nversion: 1\nrequired_files: [README.md]\n", "duplicate mapping key")
    rejected("version: 2\nrequired_files: [README.md]\n", "version must be integer 1")
    rejected("version: true\nrequired_files: [README.md]\n", "version must be integer 1")
    rejected("version: 1\nrequired_files: README.md\n", "non-empty list")
    rejected("version: 1\nrequired_files: [README.md, README.md]\n", "duplicate required_files path")
    rejected("version: 1\nrequired_files: [../README.md]\n", "safe repository-relative")
    rejected("version: 1\nrequired_files: [/etc/passwd]\n", "safe repository-relative")
    rejected("version: 1\nrequired_files: [docs/*.md]\n", "safe repository-relative")
    rejected("version: 1\nrequired_files: [README.md]\nextra: true\n", "exactly version and required_files")
    rejected("required_files: [README.md]\n", "exactly version and required_files")
    rejected("version: [\nrequired_files: [README.md]\n", "invalid YAML")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        try:
            load_policy(root / "missing-policy.yaml")
        except RepositoryContractPolicyError as exc:
            require("cannot read policy" in str(exc), f"unexpected missing-policy diagnostic: {exc!r}")
        else:
            raise AssertionError("missing policy unexpectedly accepted")
        (root / "README.md").write_text("present\n", encoding="utf-8")
        legacy = ["README.md", "missing.txt"]
        mirrored = ["README.md", "missing.txt"]
        require(set(legacy) == set(mirrored), "fixture required path sets must match")
        legacy_findings = missing_required_file_findings(legacy, root)
        mirrored_findings = missing_required_file_findings(mirrored, root)
        require(legacy_findings == ["Missing required file: missing.txt"], "legacy missing-file diagnostic changed")
        require(mirrored_findings == legacy_findings, "parallel policy must preserve missing-file findings")

        mismatched = ["README.md", "different.txt"]
        require(set(legacy) != set(mismatched), "mismatched fixture must be distinguishable")
        require(
            missing_required_file_findings(mismatched, root) != legacy_findings,
            "mismatched policy must change the missing-file diagnostic",
        )

        (root / "escape-link").symlink_to(Path(tmp).parent, target_is_directory=True)
        try:
            missing_required_file_findings(["escape-link"], root)
        except RepositoryContractPolicyError as exc:
            require("escapes repository" in str(exc), f"unexpected path escape diagnostic: {exc!r}")
        else:
            raise AssertionError("symlink path escape unexpectedly accepted")

    print("repository contract parity lifecycle: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
