#!/usr/bin/env python3
"""Canonical AIPS portable command registry, renderer and managed projections."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "harness" / "commands" / "REGISTRY.yaml"
SCHEMA_VERSION = 1


def _now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_registry() -> dict[str, Any]:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    if data.get("version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported portable command registry version: {data.get('version')}")
    commands = data.get("commands")
    hosts = data.get("hosts")
    if not isinstance(commands, list) or not isinstance(hosts, dict):
        raise ValueError("portable command registry requires commands and hosts")
    ids = [item.get("id") for item in commands]
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        raise ValueError("portable command ids must be unique and non-empty")
    return data


def _command(registry: dict[str, Any], command_id: str) -> dict[str, Any]:
    for item in registry["commands"]:
        if item["id"] == command_id:
            return item
    raise ValueError(f"unknown portable command: {command_id}")


def _host(registry: dict[str, Any], host: str) -> dict[str, Any]:
    try:
        return registry["hosts"][host]
    except KeyError as exc:
        raise ValueError(f"unknown host: {host}") from exc


def _source_lines(command: dict[str, Any]) -> str:
    return "\n".join(f"- `{item}`" for item in command["canonical_sources"])


def render_command(command_id: str, host: str = "generic", objective: str = "") -> str:
    registry = load_registry()
    command = _command(registry, command_id)
    host_data = _host(registry, host)
    renderer = host_data["renderer"]
    objective = objective or "Execute the canonical AIPS workflow for the current request."
    authority = command["authority"]
    authority_lines = "\n".join(f"- `{key}`: `{str(value).lower()}`" for key, value in authority.items())
    invocation = command["invocation"]["slash"] if renderer == "markdown-command" else command["invocation"]["skill"]
    invocation_text = ", ".join(f"`{item}`" for item in invocation)
    content = f"""# {command_id}\n\n<!-- AIPS-MANAGED-BEGIN -->\nCanonical ID: `{command_id}`\nRegistry version: `{registry['version']}`\nHost: `{host}`\nRenderer: `{renderer}`\nInvocation: {invocation_text}\n\n## Objective\n\n{objective}\n\n## Canonical sources\n\n{_source_lines(command)}\n\nRead the canonical sources from the installed AIPS system. This projection is a thin wrapper and is not a governance source of truth.\n\n## Required behavior\n\n- Preserve current project and runtime instructions.\n- Report evidence, assumptions, risks, unresolved questions and next actions.\n- Apply all listed gates before proposing a protected operation.\n- Do not claim private chain-of-thought.\n\n## Authority boundaries\n\n{authority_lines}\n\n## Inputs\n\n{', '.join(f'`{item}`' for item in command['inputs'])}\n\n## Outputs\n\n{', '.join(f'`{item}`' for item in command['outputs'])}\n\n<!-- AIPS-MANAGED-END -->\n"""

    if host == "opencode":
        for source in command["canonical_sources"]:
            content = content.replace(f"`{source}`", f"`{ROOT / source}`")
        objective = objective if objective != "Execute the canonical AIPS workflow for the current request." else "$ARGUMENTS"
        content = content.replace("Execute the canonical AIPS workflow for the current request.", objective)
        return "---\n" + yaml.safe_dump({"description": command["purpose"]}, sort_keys=False) + "---\n" + content
    return content


def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "aips"


def root_home() -> Path:
    return config_home() / "commands"


def projection_path(host: str, command_id: str) -> Path:
    safe_id = command_id.replace(".", "-") + ".md"
    if host == "opencode":
        from opencode_skill_projection import config_root
        return config_root() / "commands" / safe_id
    return root_home() / "projections" / host / safe_id


def ownership_path() -> Path:
    return root_home() / "ownership.yaml"


def load_ownership() -> dict[str, Any]:
    path = ownership_path()
    if not path.is_file():
        return {"version": 1, "artifacts": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {"version": 1, "artifacts": []}


def save_ownership(data: dict[str, Any]) -> None:
    root_home().mkdir(parents=True, exist_ok=True)
    ownership_path().write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _artifact(registry: dict[str, Any], host: str, command_id: str) -> dict[str, Any]:
    content = render_command(command_id, host)
    command = _command(registry, command_id)
    return {
        "command_id": command_id,
        "host": host,
        "renderer": _host(registry, host)["renderer"],
        "source_version": command["version"],
        "source_commit": _git_commit(),
        "source_digest": _digest(content),
        "generated_digest": _digest(content),
        "path": str(projection_path(host, command_id)),
        "scope": "global-managed-projection",
        "status": "CURRENT",
        "updated_at": _now(),
    }


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def install(host: str, command_ids: list[str]) -> dict[str, Any]:
    registry = load_registry()
    _host(registry, host)
    if host == "opencode":
        from opencode_skill_projection import OwnedFiles
        desired = {"commands/" + command_id.replace(".", "-") + ".md": render_command(command_id, host) for command_id in command_ids}
        return OwnedFiles("commands").sync(desired, remove_stale=set(command_ids) == {c["id"] for c in registry["commands"]})
    ownership = load_ownership()
    artifacts = [item for item in ownership.get("artifacts", []) if item.get("host") != host or item.get("command_id") not in command_ids]
    results = []
    for command_id in command_ids:
        path = projection_path(host, command_id)
        content = render_command(command_id, host)
        existing = path.read_text(encoding="utf-8") if path.is_file() else None
        old = next((item for item in ownership.get("artifacts", []) if item.get("path") == str(path)), None)
        if existing is not None and (old is None or _digest(existing) != old.get("generated_digest")):
            results.append({"command_id": command_id, "host": host, "status": "CONFLICT", "path": str(path)})
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        item = _artifact(registry, host, command_id)
        artifacts.append(item)
        results.append({"command_id": command_id, "host": host, "status": "INSTALLED", "path": str(path)})
    ownership = {"version": 1, "artifacts": artifacts}
    save_ownership(ownership)
    return {"status": "CONFLICT" if any(item["status"] == "CONFLICT" for item in results) else "READY", "results": results}


def status(host: str = "generic") -> dict[str, Any]:
    registry = load_registry()
    if host == "opencode":
        from opencode_skill_projection import OwnedFiles
        desired = {"commands/" + item["id"].replace(".", "-") + ".md": render_command(item["id"], host) for item in registry["commands"]}
        return OwnedFiles("commands").status(desired)
    ownership = load_ownership()
    results = []
    for item in ownership.get("artifacts", []):
        path = Path(item["path"])
        if not path.is_file():
            current = "MISSING"
        elif _digest(path.read_text(encoding="utf-8")) != item.get("generated_digest"):
            current = "CONFLICT"
        else:
            current = "CURRENT"
        item = dict(item)
        item["status"] = current
        results.append(item)
    from opencode_skill_projection import OwnedFiles
    manager = OwnedFiles("commands")
    if manager.manifest.exists():
        desired = {"commands/" + item["id"].replace(".", "-") + ".md": render_command(item["id"], "opencode") for item in registry["commands"]}
        results.extend({**item, "host": "opencode"} for item in manager.status(desired)["results"])
    return {"status": "READY", "registry_version": registry["version"], "artifacts": results}


def uninstall(host: str | None = None) -> dict[str, Any]:
    from opencode_skill_projection import OwnedFiles
    native = OwnedFiles("commands").sync({}) if host in {None, "opencode"} else {"status": "READY", "results": []}
    if host == "opencode":
        return native
    ownership = load_ownership()
    remaining = []
    results = []
    for item in ownership.get("artifacts", []):
        if host and item.get("host") != host:
            remaining.append(item)
            continue
        path = Path(item["path"])
        if path.is_file() and _digest(path.read_text(encoding="utf-8")) != item.get("generated_digest"):
            results.append({"path": str(path), "status": "CONFLICT"})
            remaining.append(item)
            continue
        if path.is_file():
            path.unlink()
        results.append({"path": str(path), "status": "REMOVED"})
    save_ownership({"version": 1, "artifacts": remaining})
    results.extend(native["results"])
    return {"status": "CONFLICT" if any(item["status"] == "CONFLICT" for item in results) else "READY", "results": results}


def _output(value: Any, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(value, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(value, sort_keys=False, allow_unicode=True), end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["list", "inspect", "render", "install", "status", "upgrade", "uninstall"])
    parser.add_argument("command_id", nargs="?")
    parser.add_argument("--host", default="generic")
    parser.add_argument("--objective", default="")
    parser.add_argument("--format", choices=["yaml", "json"], default="yaml")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args(argv)
    try:
        registry = load_registry()
        if args.action == "list":
            value = {"status": "READY", "commands": registry["commands"], "hosts": registry["hosts"]}
        elif args.action == "inspect":
            if args.command_id:
                value = {"status": "READY", "command": _command(registry, args.command_id), "hosts": registry["hosts"]}
            else:
                value = {"status": "READY", "registry": registry}
        elif args.action == "render":
            if not args.command_id:
                raise ValueError("render requires command_id")
            value = {"status": "READY", "command_id": args.command_id, "host": args.host, "content": render_command(args.command_id, args.host, args.objective)}
        elif args.action in {"install", "upgrade"}:
            ids = [args.command_id] if args.command_id else [item["id"] for item in registry["commands"]]
            value = install(args.host, ids)
        elif args.action == "status":
            value = status(args.host)
        elif args.action == "uninstall":
            value = uninstall(None if args.all else args.host)
        else:
            raise AssertionError(args.action)
        _output(value, args.format)
        return 1 if value.get("status") in {"CONFLICT", "DRIFT", "BLOCKED"} else 0
    except (OSError, ValueError, yaml.YAMLError) as exc:
        _output({"status": "BLOCKED", "reason": str(exc)}, args.format)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
