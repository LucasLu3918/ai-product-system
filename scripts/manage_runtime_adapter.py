#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
from pathlib import Path

import yaml

BEGIN = "<!-- AIPS-MANAGED-BEGIN -->"
END = "<!-- AIPS-MANAGED-END -->"
HOOK_MARKER = "AIPS_MANAGED_HOOK=1"

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""

def managed_block(source: str) -> str:
    return f"{BEGIN}\n{source.strip()}\n{END}"

def extract(text: str) -> str | None:
    m = re.search(re.escape(BEGIN) + r"\n?(.*?)\n?" + re.escape(END), text, flags=re.DOTALL)
    return m.group(0) if m else None

def install_block(target: Path, source: Path, snapshot: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    desired = managed_block(read(source))
    current = read(target)
    existing = extract(current)
    previous = read(snapshot).strip() if snapshot.exists() else ""
    if existing:
        if previous and existing.strip() != previous:
            return "CONFLICT", "existing AIPS managed block was modified; preserved"
        updated = current.replace(existing, desired)
    else:
        sep = "" if not current else ("\n" if current.endswith("\n") else "\n\n")
        updated = current + sep + desired + "\n"
    target.write_text(updated, encoding="utf-8")
    snapshot.write_text(desired + "\n", encoding="utf-8")
    return "OK", str(target)

def uninstall_block(target: Path, snapshot: Path):
    if not target.exists() or not snapshot.exists():
        return "OK", "nothing to remove"
    current = read(target)
    existing = extract(current)
    expected = read(snapshot).strip()
    if not existing:
        snapshot.unlink(missing_ok=True)
        return "OK", "managed block already absent"
    if existing.strip() != expected:
        return "CONFLICT", "managed block changed; preserved"
    updated = current.replace(existing, "")
    updated = re.sub(r"\n{3,}", "\n\n", updated).strip()
    if updated:
        target.write_text(updated + "\n", encoding="utf-8")
    else:
        target.unlink(missing_ok=True)
    snapshot.unlink(missing_ok=True)
    return "OK", str(target)

def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("settings root must be an object")
    return data

def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".aips.tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)

def claude_hook_entry(command: str) -> dict:
    return {"hooks": [{"type": "command", "command": command, "timeout": 10}]}

def claude_guard_entry(command: str) -> dict:
    return {"matcher": "Bash", "hooks": [{"type": "command", "command": command, "timeout": 10}]}

def is_aips_hook(group: dict) -> bool:
    return any(HOOK_MARKER in str(h.get("command", "")) for h in (group.get("hooks") or []) if isinstance(h, dict))

def _install_aips_group(groups: list, entry: dict):
    for i, group in enumerate(groups):
        if isinstance(group, dict) and is_aips_hook(group):
            groups[i] = entry
            return
    groups.append(entry)

def install_claude_hook(settings: Path, command: str, guard_command: str | None = None):
    try:
        data = load_json(settings)
    except Exception as exc:
        return "ERROR", f"cannot safely parse Claude settings: {exc}"
    hooks = data.setdefault("hooks", {})
    prompt_groups = hooks.setdefault("UserPromptSubmit", [])
    if not isinstance(prompt_groups, list):
        return "ERROR", "Claude hooks.UserPromptSubmit is not a list"
    _install_aips_group(prompt_groups, claude_hook_entry(command))
    if guard_command:
        guard_groups = hooks.setdefault("PreToolUse", [])
        if not isinstance(guard_groups, list):
            return "ERROR", "Claude hooks.PreToolUse is not a list"
        _install_aips_group(guard_groups, claude_guard_entry(guard_command))
    save_json(settings, data)
    return "OK", str(settings)

def uninstall_claude_hook(settings: Path):
    if not settings.exists():
        return "OK", "settings absent"
    try:
        data = load_json(settings)
    except Exception as exc:
        return "ERROR", f"cannot safely parse Claude settings: {exc}"
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return "OK", "no hooks"
    for event in ("UserPromptSubmit", "PreToolUse"):
        groups = hooks.get(event)
        if isinstance(groups, list):
            hooks[event] = [g for g in groups if not (isinstance(g, dict) and is_aips_hook(g))]
            if not hooks[event]:
                hooks.pop(event, None)
    if not hooks:
        data.pop("hooks", None)
    save_json(settings, data)
    return "OK", str(settings)

def host_ids(system: Path) -> list[str]:
    registry = yaml.safe_load((system / "harness/adapters/REGISTRY.yaml").read_text())
    return [key for key, value in registry["adapters"].items() if value.get("detect_command")]

def write_manifest(system: Path, state: Path, owned: Path, binary: Path, target: Path):
    adapters = {}
    resources = []
    for key in host_ids(system):
        path = state / f"{key}.yaml"
        adapters[key] = yaml.safe_load(path.read_text()) if path.exists() else {"status": "NOT_DETECTED", "capability": "UNSUPPORTED", "governance_enforcement": "UNSUPPORTED", "strategy": "", "resource": ""}
        entry = adapters[key]
        if entry.get("status") == "AUTOMATIC" and entry.get("resource"):
            kind = {"codex": "runtime_managed_block", "claude-code": "runtime_composed_resources", "gemini-cli": "runtime_registration", "opencode": "runtime_owned_projections"}[key]
            resource = {"type": kind, "runtime": key}
            resource[{"codex": "path", "gemini-cli": "id"}.get(key, "resource")] = entry["resource"]
            if key in {"codex", "claude-code"}:
                resource["snapshot"] = str(owned / f"{key}.block")
            if key == "opencode":
                resource["manifest_directory"] = str(owned / key)
            resources.append(resource)
    link = binary / "aips"
    if link.is_symlink() and os.readlink(link) == str(system / "bin/aips"):
        resources.insert(0, {"type": "cli_symlink", "path": str(link)})
    commit = subprocess.run(["git", "-C", str(system), "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip()
    data = {"version": 1, "installed_at": dt.datetime.now(dt.UTC).isoformat(), "system": {"root": str(system), "version": (system / "VERSION").read_text().strip(), "commit": commit}, "harness": {"enabled": True, "bootstrap": str(system / "harness/BOOTSTRAP.md")}, "owned_resources": resources, "adapters": adapters, "preservation_policy": {key: "preserved" if key == "project_ai_workspace" else "untouched" for key in ("user_agent_instructions", "user_skills", "project_agent_instructions", "project_skills", "project_source", "project_ai_workspace")}}
    from opencode_skill_projection import atomic_write
    atomic_write(target, yaml.safe_dump(data, sort_keys=False))
    return "OK", str(target)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["install-block","uninstall-block","install-claude-hook","uninstall-claude-hook","host-ids","write-manifest"])
    p.add_argument("--target"); p.add_argument("--source"); p.add_argument("--snapshot")
    p.add_argument("--settings"); p.add_argument("--command"); p.add_argument("--guard-command")
    p.add_argument("--system-root"); p.add_argument("--state-home"); p.add_argument("--owned-home"); p.add_argument("--bin-home")
    a = p.parse_args()
    if a.action == "host-ids":
        print("\n".join(host_ids(Path(a.system_root))))
        return 0
    if a.action == "write-manifest":
        status, message = write_manifest(Path(a.system_root), Path(a.state_home), Path(a.owned_home), Path(a.bin_home), Path(a.target))
    elif a.action == "install-block":
        status, message = install_block(Path(a.target), Path(a.source), Path(a.snapshot))
    elif a.action == "uninstall-block":
        status, message = uninstall_block(Path(a.target), Path(a.snapshot))
    elif a.action == "install-claude-hook":
        status, message = install_claude_hook(Path(a.settings), str(a.command), str(a.guard_command) if a.guard_command else None)
    else:
        status, message = uninstall_claude_hook(Path(a.settings))
    print(json.dumps({"status": status, "message": message}, ensure_ascii=False))
    return 0 if status == "OK" else 2

if __name__ == "__main__":
    raise SystemExit(main())
