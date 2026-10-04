"""Resolve AIPS runtime paths and expose a credential-free runtime context."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Mapping


FULL_MODULES = ("yaml", "ruff", "mypy", "playwright", "openapi_spec_validator", "jsonschema", "cryptography")


def default_validation_venv(project_root: Path) -> Path:
    root = project_root.expanduser().resolve()
    suffix = hashlib.sha256(str(root).encode()).hexdigest()[:12]
    return Path(tempfile.gettempdir()) / f"aips-validation-{suffix}"


def candidate_python_paths(system_root: Path, project_root: Path, env: Mapping[str, str] | None = None) -> list[Path]:
    values = os.environ if env is None else env
    root = project_root.expanduser().resolve()
    candidates: list[Path] = []
    if values.get("AIPS_VALIDATION_PYTHON"):
        candidates.append(Path(values["AIPS_VALIDATION_PYTHON"]).expanduser())
    if values.get("AIPS_VALIDATION_VENV"):
        candidates.append(Path(values["AIPS_VALIDATION_VENV"]).expanduser() / "bin/python")
    candidates.extend((root / ".venv/bin/python", default_validation_venv(root) / "bin/python"))
    candidates.extend((system_root / ".venv/bin/python", Path(sys.executable)))
    resolved: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            seen.add(key)
            resolved.append(candidate)
    return resolved


def python_capabilities(candidate: Path) -> dict[str, Any]:
    probe = subprocess.run(
        [str(candidate), "-c", "import importlib.util,json,sys; print(json.dumps({'version':list(sys.version_info[:3]),'modules':{m:importlib.util.find_spec(m) is not None for m in " + repr(FULL_MODULES) + "}}))"],
        capture_output=True, text=True, check=False,
    )
    if probe.returncode:
        return {"available": False, "reason": "probe_failed"}
    try:
        value = json.loads(probe.stdout)
    except json.JSONDecodeError:
        return {"available": False, "reason": "invalid_probe_output"}
    return {"available": True, **value}


def resolve_python(system_root: Path, project_root: Path, *, require_full: bool, env: Mapping[str, str] | None = None) -> tuple[Path | None, list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    for candidate in candidate_python_paths(system_root, project_root, env):
        if not candidate.is_file() or not os.access(candidate, os.X_OK):
            attempts.append({"path": str(candidate), "selected": False, "reason": "not_executable"})
            continue
        capability = python_capabilities(candidate)
        modules = capability.get("modules", {})
        version = capability.get("version", [])
        complete = capability.get("available") and version[:2] == [3, 12] and all(modules.get(name) for name in FULL_MODULES)
        usable = bool(complete if require_full else capability.get("available") and modules.get("yaml"))
        attempts.append({"path": str(candidate), "selected": usable, "reason": "ready" if usable else capability.get("reason", "missing_full_validation_capabilities"), "version": version, "modules": modules, "missing_modules": [name for name in FULL_MODULES if not modules.get(name)]})
        if usable:
            return candidate, attempts
    return None, attempts


def fallback_home() -> Path:
    return Path(tempfile.gettempdir()) / f"aips-runtime-cache-{os.getuid()}"


def trusted_fallback(path: Path) -> bool:
    if path.is_symlink():
        raise PermissionError("temporary AIPS cache must not be a symlink")
    if path.exists():
        info = path.stat()
        if not path.is_dir() or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise PermissionError("temporary AIPS cache must be a private directory owned by this user")
        return True
    return False


def writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=path, prefix=".aips-write-probe-"):
            pass
        return True
    except OSError:
        return False


def private_fallback(*, fallback_home_fn: Any = None, trusted_fallback_fn: Any = None) -> Path:
    fallback_fn = fallback_home if fallback_home_fn is None else fallback_home_fn
    trusted_fn = trusted_fallback if trusted_fallback_fn is None else trusted_fallback_fn
    path = fallback_fn()
    trusted_fn(path)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    trusted_fn(path)
    return path


def cache_home(
    env: Mapping[str, str] | None = None,
    *,
    for_write: bool = False,
    namespace: str = "aips",
    fallback_home_fn: Any = None,
    trusted_fallback_fn: Any = None,
    writable_fn: Any = None,
    private_fallback_fn: Any = None,
) -> Path:
    values = os.environ if env is None else env
    if values.get("XDG_CACHE_HOME"):
        return Path(values["XDG_CACHE_HOME"])
    default = Path(values.get("HOME") or Path.home()) / ".cache"
    fallback_fn = fallback_home if fallback_home_fn is None else fallback_home_fn
    trusted_fn = trusted_fallback if trusted_fallback_fn is None else trusted_fallback_fn
    writable_check = writable if writable_fn is None else writable_fn
    private_fn = private_fallback if private_fallback_fn is None else private_fallback_fn
    fallback = fallback_fn()
    if trusted_fn(fallback):
        return fallback
    if not for_write or writable_check(default / namespace):
        return default
    return private_fn()


def cache_environment(env: Mapping[str, str] | None = None, **resolver_overrides: Any) -> dict[str, str]:
    result = dict(os.environ if env is None else env)
    result["XDG_CACHE_HOME"] = str(cache_home(result, for_write=True, namespace="gh", **resolver_overrides))
    return result


def invocation_mode(project_root: Path) -> str:
    git_entry = project_root / ".git"
    if git_entry.is_file():
        return "linked_worktree"
    if git_entry.is_dir():
        try:
            inside = subprocess.run(["git", "-C", str(project_root), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
            if Path(inside).resolve() != project_root.resolve():
                return "linked_worktree"
        except (OSError, subprocess.CalledProcessError):
            pass
        return "source_checkout"
    return "installed_system"


def collect_runtime_context(system_root: Path, project_root: Path, *, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    values = os.environ if env is None else env
    full_python, attempts = resolve_python(system_root, project_root, require_full=True, env=values)
    base_python, _ = resolve_python(system_root, project_root, require_full=False, env=values)
    selected = full_python or base_python
    selected_probe = next((item for item in attempts if item.get("selected")), {})
    modules = selected_probe.get("modules") or {}
    cache = cache_home(values)
    try:
        import aips_identity  # type: ignore[import-not-found]
        config = Path(aips_identity.config_home())
    except (ImportError, AttributeError):
        config = Path(values.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return {
        "version": 1,
        "invocation_mode": invocation_mode(project_root),
        "system_root": str(system_root.resolve()),
        "project_root": str(project_root.resolve()),
        "python": {"selected": str(selected) if selected else None, "full_validation": str(full_python) if full_python else None, "base_runtime": str(base_python) if base_python else None, "selection_attempts": attempts},
        "paths": {"config_home": str(config), "cache_home": str(cache), "validation_venv": str(default_validation_venv(project_root)), "github_config": values.get("GH_CONFIG_DIR") or str(config / "gh")},
        "capabilities": {
            "python_full_validation": {"available": full_python is not None, "reason_code": "ready" if full_python else "full_validation_python_unavailable"},
            "openapi": {"available": bool(modules.get("openapi_spec_validator")), "reason_code": "ready" if modules.get("openapi_spec_validator") else "module_missing"},
            "playwright": {"available": bool(modules.get("playwright")), "reason_code": "ready" if modules.get("playwright") else "module_missing"},
            "browser": {"executable_available": None, "launch_verified": False, "reason_code": "launch_probe_not_run"},
            "sandbox": {"status": "NOT_PROBED", "reason_code": "sandbox_provider_not_verified"},
            "offline": values.get("AIPS_OFFLINE", "").lower() in ("1", "true", "yes"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("resolve-python", choices=("resolve-python",))
    parser.add_argument("--system-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--require-full", action="store_true")
    parser.add_argument("--format", choices=("path", "json"), default="path")
    args = parser.parse_args()
    selected, attempts = resolve_python(args.system_root, args.project_root, require_full=args.require_full)
    if args.format == "json":
        print(json.dumps({"selected": str(selected) if selected else None, "attempts": attempts}, sort_keys=True))
    elif selected:
        print(selected)
    return 0 if selected else 1


if __name__ == "__main__":
    raise SystemExit(main())
