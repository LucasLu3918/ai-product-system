#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

try:
    import yaml
except Exception:
    yaml = None


def git_output(args: list[str], cwd: Path | None = None) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def git_root(path: Path) -> Path | None:
    root = git_output(["-C", str(path), "rev-parse", "--show-toplevel"])
    return Path(root).resolve() if root else None


def detect_runtime(explicit: str | None) -> str:
    if explicit:
        return explicit
    env = os.environ
    if env.get("GEMINI_CWD") or env.get("GEMINI_PROJECT_DIR"):
        return "gemini-cli"
    if env.get("CLAUDE_PROJECT_DIR") or env.get("CLAUDE_CODE"):
        return "claude-code"
    if env.get("CODEX_HOME"):
        return "codex"
    return "unknown"


def load_adapter_status(config_home: Path, runtime: str) -> str | None:
    path = config_home / "harness" / "adapters" / f"{runtime}.yaml"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if line.startswith("status:"):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def hierarchy(root: Path, cwd: Path) -> list[Path]:
    root = root.resolve()
    cwd = cwd.resolve()
    try:
        rel = cwd.relative_to(root)
    except ValueError:
        return [root]
    dirs = [root]
    cur = root
    for part in rel.parts:
        cur = cur / part
        dirs.append(cur)
    return dirs


def project_agent_files(root: Path, cwd: Path) -> list[str]:
    found: list[str] = []
    for directory in hierarchy(root, cwd):
        # Override is runtime-specific in Codex, but exposing it here is useful evidence.
        for name in ("AGENTS.md", "AGENTS.override.md"):
            path = directory / name
            if path.is_file():
                found.append(str(path))
    return found


def runtime_native_files(runtime: str, project_root: Path, cwd: Path) -> list[str]:
    home = Path.home()
    candidates: list[Path] = []
    if runtime == "codex":
        codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex"))
        candidates.append(codex_home / "AGENTS.md")
    elif runtime == "claude-code":
        candidates.append(home / ".claude" / "CLAUDE.md")
        for directory in hierarchy(project_root, cwd):
            candidates.append(directory / "CLAUDE.md")
    elif runtime == "gemini-cli":
        candidates.append(home / ".gemini" / "GEMINI.md")
        for directory in hierarchy(project_root, cwd):
            candidates.append(directory / "GEMINI.md")

    seen: set[str] = set()
    result: list[str] = []
    for path in candidates:
        key = str(path)
        if path.is_file() and key not in seen:
            seen.add(key)
            result.append(key)
    return result


def output(data: dict, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if yaml is not None:
        print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip())
        return
    # JSON is valid YAML 1.2 and is a safe fallback.
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve AIPS harness/runtime/project context")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--project")
    parser.add_argument("--runtime", choices=["codex", "claude-code", "gemini-cli", "unknown"])
    parser.add_argument("--format", choices=["yaml", "json"], default="yaml")
    args = parser.parse_args()

    script = Path(__file__).resolve()
    system_dir = script.parents[1]
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "aips"
    cwd = Path(args.cwd).expanduser().resolve()
    if not cwd.exists():
        print(f"ERROR: cwd does not exist: {cwd}", file=sys.stderr)
        return 2

    explicit = bool(args.project)
    if explicit:
        project_root = Path(args.project).expanduser().resolve()
        if not project_root.is_dir():
            print(f"ERROR: project does not exist: {project_root}", file=sys.stderr)
            return 2
    else:
        project_root = git_root(cwd) or cwd

    runtime = detect_runtime(args.runtime)
    attached = (project_root / ".ai").is_dir()
    knowledge_index = project_root / ".ai" / "knowledge" / "KNOWLEDGE_INDEX.yaml"
    state_path = project_root / ".ai" / "STATE.yaml"

    version = "unknown"
    version_path = system_dir / "VERSION"
    if version_path.exists():
        version = version_path.read_text(encoding="utf-8").strip()
    commit = git_output(["-C", str(system_dir), "rev-parse", "HEAD"]) or "unknown"

    data = {
        "version": 1,
        "harness": {
            "active": True,
            "version": version,
            "bootstrap": str(system_dir / "harness" / "BOOTSTRAP.md"),
        },
        "runtime": {
            "id": runtime,
            "detected": runtime != "unknown",
            "adapter_status": load_adapter_status(config_home, runtime) if runtime != "unknown" else None,
            "native_instructions": runtime_native_files(runtime, project_root, cwd),
        },
        "project": {
            "detected": True,
            "root": str(project_root),
            "mode": "ATTACHED" if attached else "EPHEMERAL",
            "explicit": explicit,
        },
        "instructions": {
            "project": project_agent_files(project_root, cwd),
            "authoritative_docs": [],
        },
        "knowledge": {
            "available": attached and knowledge_index.is_file(),
            "index": str(knowledge_index) if attached and knowledge_index.is_file() else None,
        },
        "state": {
            "persistent": attached,
            "path": str(state_path) if attached and state_path.is_file() else None,
        },
        "system": {
            "root": str(system_dir),
            "version": version,
            "commit": commit,
            "entry": str(system_dir / "AGENTS.md"),
            "router": str(system_dir / "SYSTEM.md"),
        },
    }
    output(data, args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
