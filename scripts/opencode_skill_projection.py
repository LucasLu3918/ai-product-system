"""OpenCode native projections with conservative, digest-bound ownership."""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml
from skill_index import generate

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- AIPS-MANAGED-BEGIN -->"
END = "<!-- AIPS-MANAGED-END -->"


def config_root() -> Path:
    return Path(os.environ.get("OPENCODE_CONFIG_DIR", Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "opencode")).expanduser().absolute()


def state_root() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "aips/harness/owned/opencode"


def digest(body: str) -> str:
    return hashlib.sha256(body.encode()).hexdigest()


def safe_path(path: Path) -> None:
    """Refuse symlinks anywhere below the canonical OS temp/home ancestors."""
    # macOS /tmp and /var are OS aliases; canonicalize those ancestors only.
    path = path.absolute()
    for item in (path, *path.parents):
        if item.is_symlink() and str(item) not in {"/tmp", "/var"}:
            raise ValueError(f"symlink refused: {item}")
    if path.exists() and not path.is_file() and not path.is_dir():
        raise ValueError("unsupported filesystem object")


def atomic_write(path: Path, body: str) -> None:
    safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".aips-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write(body)
            out.flush()
            os.fsync(out.fileno())
        if path.exists():
            os.chmod(tmp, path.stat().st_mode & 0o777)
        safe_path(path)
        os.replace(tmp, path)
    finally:
        Path(tmp).unlink(missing_ok=True)


class OwnedFiles:
    """A separate manifest per namespace; never trust arbitrary stored paths."""

    def __init__(self, namespace: str, root: Path | None = None, state: Path | None = None):
        if namespace not in {"skills", "commands", "instructions"}:
            raise ValueError("invalid projection namespace")
        self.namespace = namespace
        self.root = root or config_root()
        self.state = state or state_root()
        self.manifest = self.state / f"{namespace}.json"

    def target(self, rel: str) -> Path:
        valid = {"instructions": r"AGENTS\.md", "skills": r"skills/[a-z0-9]+(?:-[a-z0-9]+)*/SKILL\.md", "commands": r"commands/aips-[a-z0-9-]+\.md"}
        if not isinstance(rel, str) or not re.fullmatch(valid[self.namespace], rel):
            raise ValueError("invalid owned path")
        path = self.root / rel
        safe_path(path)
        return path

    def load(self) -> dict:
        safe_path(self.manifest)
        if not self.manifest.exists():
            return {}
        data = json.loads(self.manifest.read_text())
        if not isinstance(data, dict) or data.get("version") != 1 or data.get("root") != str(self.root) or not isinstance(data.get("files"), dict):
            raise ValueError("invalid ownership manifest or changed config root")
        for rel, value in data["files"].items():
            self.target(rel)
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
                raise ValueError("invalid ownership digest")
        return data["files"]

    @contextlib.contextmanager
    def locked(self):
        safe_path(self.state)
        self.state.mkdir(parents=True, exist_ok=True)
        lock = self.state / f"{self.namespace}.lock"
        safe_path(lock)
        with lock.open("a") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            yield

    def owned_body(self, text: str) -> str | None:
        if self.namespace != "instructions":
            return text
        if not text.count(BEGIN) and not text.count(END):
            return None
        if text.count(BEGIN) != 1 or text.count(END) != 1:
            raise ValueError("ambiguous managed instruction markers")
        match = re.search(re.escape(BEGIN) + r".*?" + re.escape(END), text, re.DOTALL)
        if not match:
            raise ValueError("malformed managed instruction block")
        return match.group()

    def sync(self, desired: dict[str, str], *, remove_stale: bool = True) -> dict:
        # Validate all source and ownership paths before any target mutation.
        for rel in desired:
            self.target(rel)
        with self.locked():
            old = self.load()
            files = dict(old)
            results = []
            paths = set(desired) | (set(old) if remove_stale else set())
            for rel in sorted(paths):
                path = self.target(rel)
                current = path.read_text() if path.exists() else ""
                body = self.owned_body(current) if path.exists() else None
                if body is not None and (rel not in old or digest(body) != old[rel]):
                    results.append({"path": rel, "status": "CONFLICT"})
                    continue
                target = desired.get(rel)
                if self.namespace == "instructions":
                    if body is not None:
                        updated = current.replace(body, target or "", 1)
                    else:
                        updated = current + ("\n" if current and not current.endswith("\n") else "") + (target + "\n" if target else "")
                else:
                    updated = target or ""
                if target is None:
                    if path.exists():
                        if self.namespace == "instructions" and updated.strip():
                            atomic_write(path, updated)
                        else:
                            path.unlink()
                    files.pop(rel, None)
                    result = "REMOVED"
                else:
                    atomic_write(path, updated)
                    files[rel] = digest(target)
                    result = "CURRENT"
                # Checkpoint each successful operation. An interrupted write never
                # grants ownership to a file whose digest is not recorded.
                atomic_write(self.manifest, json.dumps({"version": 1, "root": str(self.root), "files": files}, indent=2) + "\n")
                results.append({"path": rel, "status": result})
            return {"status": "CONFLICT" if any(r["status"] == "CONFLICT" for r in results) else "READY", "results": results}

    def status(self, desired: dict[str, str] | None = None) -> dict:
        old = self.load()
        results = []
        paths = set(old) | (set(desired) if desired is not None else set())
        for rel in sorted(paths):
            path = self.target(rel)
            body = self.owned_body(path.read_text()) if path.exists() else None
            status = "MISSING" if body is None else "CONFLICT" if rel not in old or digest(body) != old[rel] else "STALE" if desired is not None and (rel not in desired or digest(desired[rel]) != old[rel]) else "CURRENT"
            results.append({"path": rel, "status": status})
        return {"status": "READY" if all(r["status"] == "CURRENT" for r in results) else "DRIFT", "results": results}


def skill_files(root: Path = ROOT) -> dict[str, str]:
    entries = generate(root)["skills"]
    desired = {}
    for sid, meta in entries.items():
        if len(sid) > 64:
            raise ValueError("OpenCode skill names must be at most 64 characters")
        source = root / "skills" / meta["path"]
        text = source.read_text()
        body = re.split(r"\A---\r?\n.*?\r?\n---(?:\r?\n|$)", text, maxsplit=1, flags=re.DOTALL)[1]
        # Canonical backtick references are repository-relative, not projection-relative.
        body = re.sub(r"`((?:orchestration|templates|scripts|skills|docs|core|harness|config)/[^`]+|SYSTEM(?:_CORE)?\.md)`", lambda m: "`" + str(root / m.group(1)) + "`", body)
        body = re.sub(r"\]\(([^)]+)\)", lambda m, source=source: m.group() if re.match(r"(?:[a-z]+:|#)", m.group(1)) else "](" + str((source.parent / m.group(1).split('#')[0]).resolve()) + ("#" + m.group(1).split('#', 1)[1] if '#' in m.group(1) else "") + ")", body)
        header = {"name": sid, "description": meta["description"], "compatibility": "opencode", "metadata": {"aips-source": str(source), "aips-source-sha256": digest(text)}}
        desired[f"skills/{sid}/SKILL.md"] = "---\n" + yaml.safe_dump(header, sort_keys=False) + "---\n\nCanonical AIPS source: `" + str(source) + "`. Resolve other relative resources from its directory. Edit the canonical source, then reinstall; this is a generated projection.\n" + body
    return desired


def instructions() -> dict[str, str]:
    source = ROOT / "harness/adapters/opencode/AGENTS.md"
    return {"AGENTS.md": BEGIN + "\n" + source.read_text().strip() + "\n" + END}


def probe() -> dict:
    command = shutil.which("opencode")
    if not command:
        return {"status": "BLOCKED", "installation": "NOT_DETECTED", "version": None, "runtime_verification": "UNVERIFIED"}
    try:
        result = subprocess.run([command, "--version"], capture_output=True, text=True, timeout=10, check=False)
        match = re.fullmatch(r"(?:opencode\s+)?v?(\d+\.\d+\.\d+)\s*", result.stdout)
        version = match.group(1) if result.returncode == 0 and match else None
    except (OSError, subprocess.TimeoutExpired):
        version = None
    compatible = bool(version and version.split(".")[0] in {"1", "2"})
    return {"status": "READY" if compatible else "BLOCKED", "compatibility": "KNOWN_MAJOR_CONTRACT" if compatible else "UNKNOWN_VERSION", "installation": "DETECTED" if version else "PROBE_FAILED", "version": version, "runtime_verification": "UNVERIFIED", "pre_tool_guard": "UNSUPPORTED", "mcp": "NOT_CONFIGURED"}


def operate(action: str) -> dict:
    if action == "probe":
        return probe()
    managers = {"instructions": OwnedFiles("instructions"), "skills": OwnedFiles("skills")}
    desired = {} if action == "uninstall" else {"instructions": instructions(), "skills": skill_files()}
    if action == "install":
        results = {name: manager.sync(desired[name]) for name, manager in managers.items()}
    elif action == "uninstall":
        results = {name: manager.sync({}) for name, manager in managers.items()}
    else:
        results = {name: manager.status(desired[name]) for name, manager in managers.items()}
    return {"status": "READY" if all(r["status"] == "READY" for r in results.values()) else "CONFLICT", "config_root": str(config_root()), "capability": "CONTEXT_ALWAYS", "governance_enforcement": "ADVISORY", "runtime_verification": "UNVERIFIED", "probe": probe(), "projections": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "status", "check", "doctor", "uninstall", "probe"])
    args = parser.parse_args()
    try:
        result = operate(args.action)
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        result = {"status": "BLOCKED", "reason": str(exc)}
    print(json.dumps(result, indent=2))
    return 0 if result.get("status", "READY") == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
