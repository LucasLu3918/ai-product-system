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
CHUNK_BYTES = 1024 * 1024


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


def _project_root(project: Path, label: str) -> Path:
    root = project.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"{label} must be a directory")
    return root


def _relative_path(root: Path, value: str, label: str) -> tuple[Path, Path]:
    relative = Path(value)
    if relative.is_absolute() or not value or "\\" in value or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError(f"{label} must be a confined project-relative path")
    target = root.joinpath(*relative.parts)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{label} must not traverse symlinks")
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes its project root") from exc
    return relative, target


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def _candidate_body(candidate: dict[str, Any]) -> bytes:
    payload = {key: value for key, value in candidate.items() if key != "candidate_sha256"}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _candidate_store(source_root: Path) -> Path:
    identity = hashlib.sha256(str(source_root).encode()).hexdigest()[:24]
    return cache_path(source_root).parent / f"{identity}.imports"


def _has_git_metadata(root: Path) -> bool:
    return any((parent / ".git").exists() for parent in (root, *root.parents))


def import_candidate(source_project: Path, source: str, destination_project: Path, target: str) -> dict[str, Any]:
    """Create a private, hash-bound import proposal without changing either project."""
    source_root = _project_root(source_project, "source project")
    destination_root = _project_root(destination_project, "destination project")
    if _has_git_metadata(destination_root):
        raise ValueError("destination must be a non-Git EPHEMERAL creative workspace")
    source_relative, source_path = _relative_path(source_root, source, "source")
    target_relative, target_path = _relative_path(destination_root, target, "target")
    if source_relative.suffix.casefold() not in ASSETS or target_relative.suffix.casefold() not in ASSETS:
        raise ValueError("source and target must use supported image or SVG extensions")
    if source_relative.suffix.casefold() != target_relative.suffix.casefold():
        raise ValueError("target extension must match the source asset format")
    source_info = source_path.stat(follow_symlinks=False)
    if not source_path.is_file() or source_info.st_size > MAX_FILE_BYTES:
        raise ValueError("source must be a regular asset no larger than 12 MiB")
    if not target_path.parent.is_dir():
        raise ValueError("target parent directory must already exist")
    if target_path.exists() or target_path.is_symlink():
        status = "CONFLICT"
        target_state: dict[str, Any] = {"state": "EXISTS", "existing_sha256": _sha256_file(target_path) if target_path.is_file() and not target_path.is_symlink() else None}
    else:
        status = "READY"
        target_state = {"state": "ABSENT", "existing_sha256": None}
    candidate: dict[str, Any] = {
        "version": 1,
        "mode": "EPHEMERAL",
        "status": status,
        "source_project": {"id": hashlib.sha256(str(source_root).encode()).hexdigest()[:24], "path": str(source_root)},
        "source": {"path": source_relative.as_posix(), "sha256": _sha256_file(source_path), "bytes": source_info.st_size, "format": source_relative.suffix.lower().lstrip(".")},
        "destination_project": {"id": hashlib.sha256(str(destination_root).encode()).hexdigest()[:24], "path": str(destination_root)},
        "destination": {"path": target_relative.as_posix(), **target_state},
        "overwrite": False,
        "source_content_cached": False,
        "created": False,
    }
    candidate["candidate_sha256"] = hashlib.sha256(_candidate_body(candidate)).hexdigest()
    candidate_file = _candidate_store(source_root) / f"{candidate['candidate_sha256']}.json"
    _atomic_private_write(candidate_file, json.dumps(candidate, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return {**candidate, "candidate_file": str(candidate_file)}


def import_asset(candidate_file: Path, accept_hash: str) -> dict[str, Any]:
    """Copy only the exact reviewed candidate, with source rehash and create-only output."""
    candidate_path = candidate_file.expanduser().resolve(strict=True)
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    recorded_hash = candidate.get("candidate_sha256")
    if not isinstance(recorded_hash, str) or recorded_hash != accept_hash or hashlib.sha256(_candidate_body(candidate)).hexdigest() != recorded_hash:
        raise ValueError("candidate hash does not match the accepted, unmodified candidate")
    if candidate.get("status") != "READY" or candidate.get("overwrite") is not False:
        raise ValueError("candidate is not an importable create-only proposal")
    source_root = _project_root(Path(candidate["source_project"]["path"]), "source project")
    destination_root = _project_root(Path(candidate["destination_project"]["path"]), "destination project")
    if _has_git_metadata(destination_root):
        raise ValueError("destination must be a non-Git EPHEMERAL creative workspace")
    source_relative, source_path = _relative_path(source_root, candidate["source"]["path"], "source")
    target_relative, target_path = _relative_path(destination_root, candidate["destination"]["path"], "target")
    if not source_path.is_file() or source_path.is_symlink() or source_path.stat(follow_symlinks=False).st_size != candidate["source"]["bytes"]:
        raise ValueError("source asset changed after candidate creation")
    if _sha256_file(source_path) != candidate["source"]["sha256"]:
        raise ValueError("source asset hash changed after candidate creation")
    if not target_path.parent.is_dir():
        raise ValueError("target parent directory is no longer available")
    if target_path.exists() or target_path.is_symlink():
        raise ValueError("destination appeared after candidate creation; overwrite is prohibited")
    temporary: Path | None = None
    digest = hashlib.sha256()
    copied = 0
    try:
        fd, temporary_name = tempfile.mkstemp(prefix=".aips-import-", dir=target_path.parent)
        temporary = Path(temporary_name)
        with os.fdopen(fd, "wb") as output, source_path.open("rb") as source_stream:
            while chunk := source_stream.read(CHUNK_BYTES):
                output.write(chunk)
                digest.update(chunk)
                copied += len(chunk)
            output.flush()
            os.fsync(output.fileno())
        if digest.hexdigest() != candidate["source"]["sha256"] or copied != candidate["source"]["bytes"]:
            raise ValueError("source asset changed while importing")
        os.link(temporary, target_path)
        temporary.unlink()
        temporary = None
        directory_fd = os.open(target_path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except FileExistsError as exc:
        raise ValueError("destination appeared during import; overwrite is prohibited") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {"status": "IMPORTED", "candidate_sha256": recorded_hash, "source": source_relative.as_posix(), "destination": target_relative.as_posix(), "sha256": digest.hexdigest(), "bytes": copied, "created": True, "overwrite": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    scan_parser = sub.add_parser("scan")
    scan_parser.add_argument("--project", type=Path, required=True)
    version_parser = sub.add_parser("next-version")
    version_parser.add_argument("--project", type=Path, required=True)
    version_parser.add_argument("--target", required=True)
    candidate_parser = sub.add_parser("import-candidate")
    candidate_parser.add_argument("--source-project", type=Path, required=True)
    candidate_parser.add_argument("--source", required=True)
    candidate_parser.add_argument("--destination-project", type=Path, required=True)
    candidate_parser.add_argument("--target", required=True)
    import_parser = sub.add_parser("import")
    import_parser.add_argument("--candidate", type=Path, required=True)
    import_parser.add_argument("--accept-hash", required=True, help="Exact candidate SHA-256 shown by import-candidate")
    args = parser.parse_args()
    try:
        if args.action == "scan":
            result = scan(args.project)
        elif args.action == "next-version":
            result = next_version(args.project, args.target)
        elif args.action == "import-candidate":
            result = import_candidate(args.source_project, args.source, args.destination_project, args.target)
        else:
            result = import_asset(args.candidate, args.accept_hash)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
