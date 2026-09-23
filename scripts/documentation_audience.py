#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".html", ".json", ".toml", ".txt"}


def load_config(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError("documentation audience config must be a mapping")
    return value


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if config.get("version") != 1:
        errors.append("version must be 1")
    human_root = str(config.get("human_root") or "")
    if human_root != "docs/human":
        errors.append("human_root must be docs/human")
    if config.get("standalone_human_prefix") != "HUMAN_":
        errors.append("standalone_human_prefix must be HUMAN_")
    shared = config.get("shared_docs")
    human = config.get("human_documents")
    standalone = config.get("standalone_human_documents")
    legacy = config.get("legacy_paths")
    if not isinstance(shared, list):
        errors.append("shared_docs must be a list")
    if not isinstance(human, list) or not human:
        errors.append("human_documents must be a non-empty list")
    if not isinstance(standalone, list):
        errors.append("standalone_human_documents must be a list")
    if not isinstance(legacy, dict):
        errors.append("legacy_paths must be a mapping")
    if isinstance(human, list):
        for path in human:
            if not str(path).startswith("docs/human/"):
                errors.append(f"Human document must live under docs/human/: {path}")
    if isinstance(standalone, list):
        prefix = str(config.get("standalone_human_prefix") or "")
        for path in standalone:
            value = str(path)
            if value.startswith("docs/human/"):
                errors.append(f"Standalone Human artifact must be outside docs/human/: {value}")
            if not Path(value).name.startswith(prefix):
                errors.append(f"Standalone Human artifact must use {prefix} prefix: {value}")
    return errors


def _iter_scan_files(root: Path, config: dict[str, Any]) -> list[Path]:
    files: list[Path] = []
    for raw in config.get("scan_roots") or []:
        target = root / str(raw)
        if target.is_file():
            files.append(target)
        elif target.is_dir():
            files.extend(
                path for path in target.rglob("*")
                if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
            )
    return sorted(set(files))


def validate_layout(root: Path, config: dict[str, Any]) -> list[str]:
    errors = validate_config(config)
    if errors:
        return errors

    human_root = root / config["human_root"]
    if not human_root.is_dir():
        errors.append("docs/human directory is missing")

    for raw in config.get("human_documents") or []:
        path = root / str(raw)
        if not path.is_file():
            errors.append(f"Missing Human-only document: {raw}")

    standalone = {str(path) for path in config.get("standalone_human_documents") or []}
    for raw in standalone:
        path = root / raw
        if not path.is_file():
            errors.append(f"Missing standalone Human-only artifact: {raw}")

    shared = {str(path) for path in config.get("shared_docs") or []}
    docs_root = root / "docs"
    if docs_root.is_dir():
        for child in docs_root.iterdir():
            rel = child.relative_to(root).as_posix()
            if child.is_file() and child.name in {".DS_Store", "Thumbs.db", "desktop.ini"}:
                continue
            if child.is_dir() and rel == "docs/human":
                continue
            if child.is_file() and rel in shared:
                continue
            errors.append(
                f"Unclassified docs-root entry {rel}; Human-only docs belong under docs/human/ "
                "and shared canonical docs must be allowlisted"
            )

    legacy = config.get("legacy_paths") or {}
    config_path = (root / "config/documentation-audience.yaml").resolve()
    for path in _iter_scan_files(root, config):
        if path.resolve() == config_path:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(root).as_posix()
        audience_marker = 'name="aips-audience" content="human"'
        if path.suffix.lower() == ".html" and audience_marker in text:
            allowed_human = rel.startswith(config["human_root"] + "/") or rel in standalone
            if not allowed_human:
                errors.append(
                    f"Human-audience artifact outside {config['human_root']}/ must be registered "
                    f"as a standalone {config['standalone_human_prefix']} artifact: {rel}"
                )
        for old, new in legacy.items():
            if old in text:
                errors.append(f"Legacy Human documentation path in {rel}: {old} -> {new}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(ROOT / "config/documentation-audience.yaml"),
    )
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()

    config = load_config(Path(args.config))
    errors = validate_layout(Path(args.root), config)
    if errors:
        print("DOCUMENTATION AUDIENCE VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("DOCUMENTATION AUDIENCE VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
