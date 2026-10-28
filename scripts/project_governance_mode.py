"""Private per-repository optional governance mode configuration."""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any

import yaml
from aips_identity import project_root, repository_identity

SCHEMA_VERSION = 1
MODES = {"off", "observe", "assist", "enforce"}
ENFORCEABLE_ACTIONS = {
    "git_commit",
    "git_push",
    "git_tag",
    "gh_pr_create",
    "gh_pr_merge",
    "gh_release_create",
    "publish_ship",
}


class ModeConfigError(ValueError):
    """Mode configuration is invalid or cannot be trusted."""


def repository_id(project: Path) -> str:
    root = project_root(project.expanduser())
    return repository_identity(root)["repository_id"]


def config_path(project: Path) -> Path:
    config_root = Path(
        os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    ).expanduser().resolve()
    return config_root / "aips" / "projects" / f"{repository_id(project)}.yaml"


def _validate_record(record: Any, expected_repository_id: str) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ModeConfigError("project mode configuration must be a mapping")
    if set(record) != {"schema_version", "repository_id", "mode", "enforce_scope"}:
        raise ModeConfigError("project mode configuration contains unsupported fields")
    if type(record.get("schema_version")) is not int or record.get("schema_version") != SCHEMA_VERSION:
        raise ModeConfigError("unsupported project mode configuration schema")
    if record.get("repository_id") != expected_repository_id:
        raise ModeConfigError("project mode configuration identity does not match this repository")
    mode = record.get("mode")
    if not isinstance(mode, str) or mode not in MODES:
        raise ModeConfigError("project mode must be off, observe, assist, or enforce")
    scope = record.get("enforce_scope", [])
    if not isinstance(scope, list) or any(not isinstance(item, str) for item in scope):
        raise ModeConfigError("project enforce scope must be a list of action names")
    normalized_scope = sorted(set(scope))
    if normalized_scope != scope:
        raise ModeConfigError("project enforce scope must be unique and sorted")
    if mode == "enforce":
        if not scope:
            raise ModeConfigError("enforce mode requires an explicit action scope")
        if not set(scope).issubset(ENFORCEABLE_ACTIONS):
            raise ModeConfigError("project enforce scope contains an unsupported action")
    elif scope:
        raise ModeConfigError("only enforce mode may declare a blocking action scope")
    return {
        "schema_version": SCHEMA_VERSION,
        "repository_id": expected_repository_id,
        "mode": mode,
        "enforce_scope": normalized_scope,
    }


def resolve(project: Path) -> dict[str, Any]:
    root = project_root(project.expanduser())
    if not root.is_dir():
        raise ModeConfigError("project path must be an existing directory")
    identity = repository_identity(root)["repository_id"]
    path = config_path(root)
    try:
        parent_info = path.parent.lstat()
    except FileNotFoundError:
        return {
            "schema_version": SCHEMA_VERSION,
            "repository_id": identity,
            "mode": "off",
            "enforce_scope": [],
            "configured": False,
            "config_path": path,
        }
    except OSError as exc:
        raise ModeConfigError("project mode storage directory cannot be inspected") from exc
    if stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(parent_info.st_mode):
        raise ModeConfigError("project mode storage path must be a real directory")
    try:
        info = path.lstat()
    except FileNotFoundError:
        return {
            "schema_version": SCHEMA_VERSION,
            "repository_id": identity,
            "mode": "off",
            "enforce_scope": [],
            "configured": False,
            "config_path": path,
        }
    except OSError as exc:
        raise ModeConfigError("project mode configuration cannot be inspected") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ModeConfigError("project mode configuration must be a regular non-symlink file")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise ModeConfigError("project mode configuration permissions must be 0600")
    try:
        with path.open("r", encoding="utf-8") as stream:
            record = yaml.safe_load(stream)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ModeConfigError("project mode configuration cannot be read safely") from exc
    result = _validate_record(record, identity)
    result.update({"configured": True, "config_path": path})
    return result


def _ensure_private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise ModeConfigError("project mode storage directory must be a real directory")
    os.chmod(path, 0o700)


def set_mode(project: Path, mode: str, enforce_scope: list[str] | None = None) -> dict[str, Any]:
    root = project_root(project.expanduser())
    if not root.is_dir():
        raise ModeConfigError("project path must be an existing directory")
    identity = repository_identity(root)["repository_id"]
    if not isinstance(mode, str) or mode not in MODES:
        raise ModeConfigError("project mode must be off, observe, assist, or enforce")
    raw_scope = enforce_scope or []
    if not isinstance(raw_scope, list) or any(not isinstance(item, str) for item in raw_scope):
        raise ModeConfigError("project enforce scope must contain action names")
    scope = sorted(set(raw_scope))
    if mode == "enforce":
        if not scope:
            raise ModeConfigError("enforce mode requires an explicit action scope")
        if not set(scope).issubset(ENFORCEABLE_ACTIONS):
            raise ModeConfigError("project enforce scope contains an unsupported action")
    elif scope:
        raise ModeConfigError("only enforce mode may declare a blocking action scope")

    path = config_path(root)
    _ensure_private_directory(path.parent)
    record = {
        "schema_version": SCHEMA_VERSION,
        "repository_id": identity,
        "mode": mode,
        "enforce_scope": scope,
    }
    body = yaml.safe_dump(record, sort_keys=False, allow_unicode=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".project-mode-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        if path.is_symlink():
            raise ModeConfigError("project mode configuration cannot replace a symlink")
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary)
    result = resolve(root)
    result["configured"] = True
    return result


def _format_result(result: dict[str, Any], output_format: str) -> str:
    value = {
        "status": "OK",
        "repository_id": result["repository_id"],
        "mode": result["mode"],
        "enforce_scope": result["enforce_scope"],
        "configured": result["configured"],
        "config_path": str(result["config_path"]),
    }
    if output_format == "json":
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    scope = ", ".join(value["enforce_scope"]) if value["enforce_scope"] else "none"
    return (
        f"Project governance mode: {value['mode']}\n"
        f"Enforce scope: {scope}\n"
        f"Stored outside repository: {value['config_path']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage optional per-project AIPS governance mode")
    subparsers = parser.add_subparsers(dest="action", required=True)
    show = subparsers.add_parser("show", help="show the project mode (default: off)")
    show.add_argument("--project", type=Path, default=Path.cwd())
    show.add_argument("--format", choices=("text", "json"), default="text")
    set_parser = subparsers.add_parser("set", help="set a per-project mode")
    set_parser.add_argument("mode", choices=sorted(MODES))
    set_parser.add_argument("--project", type=Path, default=Path.cwd())
    set_parser.add_argument("--scope", help="comma-separated action names required for enforce mode")
    set_parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        if args.action == "show":
            result = resolve(args.project)
        else:
            scope = [item.strip() for item in args.scope.split(",") if item.strip()] if args.scope else []
            result = set_mode(args.project, args.mode, scope)
    except (OSError, ModeConfigError, ValueError) as exc:
        parser.error(str(exc))
    print(_format_result(result, args.format))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
