"""Read-only creative asset inventory backed by a private external cache."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

ASSETS = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"}
PROFILES = {"character_profile.yaml", "style_profile.yaml", "character_artwork_manifest.yaml", "creative_direction.yaml"}
SKIP = {".git", ".ai", "node_modules", ".venv", "venv", "vendor", "dist", "build", "target"}
MAX_ASSETS = 500
MAX_PROFILE_FILES = 200
MAX_FILES_SCANNED = 20000
MAX_FILE_BYTES = 12 * 1024 * 1024


def cache_path(project: Path) -> Path:
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")).expanduser()
    identity = hashlib.sha256(str(project).encode()).hexdigest()[:24]
    return cache / "aips/creative-workspaces" / f"{identity}.json"


def _atomic_private_write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    fd, temporary = tempfile.mkstemp(prefix=".aips-creative-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        Path(temporary).unlink(missing_ok=True)


def scan(project: Path) -> dict[str, Any]:
    root = project.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("project must be a directory")
    assets: list[dict[str, Any]] = []
    profiles: list[str] = []
    truncated = False
    files_scanned = 0
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        depth = len(current_path.relative_to(root).parts)
        directories[:] = [name for name in sorted(directories) if name not in SKIP and not (current_path / name).is_symlink()]
        if depth >= 6:
            directories[:] = []
        for filename in sorted(files):
            files_scanned += 1
            if files_scanned > MAX_FILES_SCANNED:
                truncated = True
                break
            path = current_path / filename
            if path.is_symlink():
                continue
            relative = path.relative_to(root).as_posix()
            if filename.casefold() in PROFILES:
                if len(profiles) < MAX_PROFILE_FILES:
                    profiles.append(relative)
                else:
                    truncated = True
            if path.suffix.casefold() not in ASSETS:
                continue
            try:
                info = path.stat(follow_symlinks=False)
                if not path.is_file() or info.st_size > MAX_FILE_BYTES:
                    continue
                assets.append({"path": relative, "format": path.suffix.lower().lstrip("."), "bytes": info.st_size, "modified_ns": info.st_mtime_ns})
            except OSError:
                continue
            if len(assets) >= MAX_ASSETS:
                truncated = True
                break
        if truncated:
            break
    assets.sort(key=lambda item: item["path"].casefold())
    profiles.sort()
    record = {"version": 1, "project_id": hashlib.sha256(str(root).encode()).hexdigest()[:24], "mode": "EPHEMERAL", "read_only_scan": True, "asset_count": len(assets), "files_scanned": min(files_scanned, MAX_FILES_SCANNED), "assets": assets, "profile_files": profiles, "truncated": truncated}
    target = cache_path(root)
    _atomic_private_write(target, json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return {**record, "cache": str(target), "overwrite_policy": "never", "scan_scope": "asset metadata only; file contents and prompts are not cached"}


def next_version(project: Path, target: str) -> dict[str, Any]:
    root = project.expanduser().resolve(strict=True)
    candidate = Path(target).expanduser()
    if candidate.is_absolute():
        raise ValueError("target must be relative to the project")
    resolved = (root / candidate).resolve(strict=False)
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("target escapes project root") from exc
    if relative.suffix.casefold() not in ASSETS:
        raise ValueError("target must use a supported image or SVG extension")
    stem, suffix = relative.stem, relative.suffix
    version = 1
    while (root / relative.parent / f"{stem}-v{version}{suffix}").exists():
        version += 1
    output = relative.parent / f"{stem}-v{version}{suffix}"
    return {"status": "AVAILABLE" if not (root / output).exists() else "CONFLICT", "path": output.as_posix(), "created": False, "overwrite": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    scan_parser = sub.add_parser("scan")
    scan_parser.add_argument("--project", type=Path, required=True)
    version_parser = sub.add_parser("next-version")
    version_parser.add_argument("--project", type=Path, required=True)
    version_parser.add_argument("--target", required=True)
    args = parser.parse_args()
    try:
        result = scan(args.project) if args.action == "scan" else next_version(args.project, args.target)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
