"""Measure tracked documentation and evidence sizes without enforcing a gate."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config/document-size-policy.yaml"


def validate_document_size_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if policy.get("version") != 1:
        errors.append("version must be 1")
    threshold = policy.get("hot_document_max_bytes")
    if not isinstance(threshold, int) or threshold <= 0:
        errors.append("hot_document_max_bytes must be a positive integer")
    roots = policy.get("scan_roots")
    if not isinstance(roots, list) or not roots or not all(isinstance(item, str) and item for item in roots):
        errors.append("scan_roots must be a non-empty list of repository-relative paths")
    else:
        for item in roots:
            path = PurePosixPath(item)
            if path.is_absolute() or ".." in path.parts:
                errors.append(f"scan root must remain repository-relative: {item}")
    extensions = policy.get("extensions")
    if not isinstance(extensions, list) or not extensions or not all(
        isinstance(item, str) and item.startswith(".") for item in extensions
    ):
        errors.append("extensions must be a non-empty list of suffixes")
    if policy.get("threshold_behavior") != "WARN":
        errors.append("threshold_behavior must be WARN")
    if policy.get("gate_blocking") is not False:
        errors.append("gate_blocking must remain false")
    if policy.get("archive_or_move") is not False:
        errors.append("archive_or_move must remain false")
    return errors


def tracked_document_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached"],
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("tracked file inventory is unavailable")
    return sorted(path.decode("utf-8", errors="surrogateescape") for path in result.stdout.split(b"\0") if path)


def is_in_scope(path: str, roots: list[str], extensions: list[str]) -> bool:
    candidate = PurePosixPath(path)
    return candidate.suffix.casefold() in set(extensions) and any(
        path == base or path.startswith(base.rstrip("/") + "/") for base in roots
    )


def build_document_size_report(root: Path, policy: dict[str, Any]) -> dict[str, Any]:
    errors = validate_document_size_policy(policy)
    if errors:
        return {"version": 1, "status": "BLOCKED", "errors": errors, "gate_blocking": False}
    project = root.resolve()
    threshold = policy["hot_document_max_bytes"]
    files: list[dict[str, Any]] = []
    for relative in tracked_document_paths(project):
        if not is_in_scope(relative, policy["scan_roots"], policy["extensions"]):
            continue
        path = project / relative
        if path.is_symlink():
            continue
        resolved = path.resolve()
        if not resolved.is_relative_to(project) or not path.is_file():
            continue
        size = path.stat().st_size
        text = path.read_text(encoding="utf-8", errors="replace") if path.suffix == ".md" else ""
        headings = [line.strip() for line in text.splitlines() if line.startswith("## ")][:12]
        files.append({"path": relative, "bytes": size, "status": "WARN" if size > threshold else "OK",
                      "reading_sections": headings,
                      "source_kind": "canonical_machine_readable" if path.suffix in {".yaml", ".yml", ".json"} else "document"})
    files.sort(key=lambda row: (-row["bytes"], row["path"]))
    oversized = [row for row in files if row["status"] == "WARN"]
    return {
        "version": 1,
        "status": "WARN" if oversized else "PASS",
        "measurement_only": True,
        "threshold_bytes": threshold,
        "threshold_behavior": "WARN",
        "gate_blocking": False,
        "archive_or_move": False,
        "files_scanned": len(files),
        "oversized_count": len(oversized),
        "files": files,
    }


def document_size_audit_main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--output", type=Path, help="optional JSON report destination")
    args = parser.parse_args()
    try:
        policy = yaml.safe_load(args.policy.read_text(encoding="utf-8")) or {}
        if not isinstance(policy, dict):
            raise TypeError("policy must be a mapping")
        report = build_document_size_report(args.root, policy)
    except (OSError, RuntimeError, yaml.YAMLError, TypeError, ValueError):
        report = {"version": 1, "status": "BLOCKED", "errors": ["input_or_inventory_error"], "gate_blocking": False}
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    # Size warnings are informational and always return success.
    return 0 if report.get("status") in {"PASS", "WARN"} else 1


if __name__ == "__main__":
    raise SystemExit(document_size_audit_main())
