"""Inspect tracked AIPS state without modifying the worktree or Git index."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from aips_identity import repository_identity


def _classification(name: str) -> str:
    normalized = '/' + name.casefold().replace('\\', '/').strip('/') + '/'
    durable_markers = (
        '/.aips/review/', 'project_overrides', 'source_registry', 'decision',
        'approval', 'accepted', 'rationale', 'policy', 'proposal',
    )
    return 'possible_durable_knowledge' if any(marker in normalized for marker in durable_markers) else 'review_required'


def inspect_path(root: Path, name: str) -> dict:
    row = {'path': name, 'classification': _classification(name), 'kind': 'unavailable', 'sha256': None}
    if not all(hasattr(os, name) for name in ('O_DIRECTORY', 'O_NOFOLLOW', 'O_NONBLOCK')) or not {os.open, os.stat}.issubset(os.supports_dir_fd):
        return row
    parts = Path(name).parts
    if not parts or any(part in ('', '.', '..') for part in parts):
        return row
    parent_fd = None
    try:
        parent_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        for part in parts[:-1]:
            info = os.stat(part, dir_fd=parent_fd, follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                row['kind'] = 'symlink'
                return row
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = next_fd
        info = os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
        if stat.S_ISLNK(info.st_mode):
            row['kind'] = 'symlink'
            return row
        if not stat.S_ISREG(info.st_mode):
            row['kind'] = 'other'
            return row
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent_fd)
        with os.fdopen(fd, 'rb') as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                return row
            digest = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
            after = os.fstat(stream.fileno())
            identity = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
            if identity(before) != identity(after):
                return row
        row.update(kind='file', sha256=digest.hexdigest())
    except OSError:
        pass
    finally:
        if parent_fd is not None:
            os.close(parent_fd)
    return row



def tracked_ignore_status(root: Path, names: list[str]) -> dict[str, bool | None]:
    result: dict[str, bool | None] = dict.fromkeys(names)
    if not names:
        return result
    payload = b''.join(os.fsencode(name) + b'\0' for name in names)
    try:
        proc = subprocess.run(
            ['git', '-C', str(root), 'check-ignore', '--no-index', '-v', '-z', '--non-matching', '--stdin'],
            input=payload, capture_output=True, check=False,
        )
    except OSError:
        return result
    if proc.returncode not in (0, 1):
        return result
    parts = proc.stdout.split(b'\0')
    if not parts or parts[-1] != b'' or (len(parts) - 1) != 4 * len(names):
        return result
    seen: set[str] = set()
    for i in range(0, len(parts) - 1, 4):
        source, _line, pattern, raw_name = parts[i:i + 4]
        name = os.fsdecode(raw_name)
        if name not in result or name in seen:
            return dict.fromkeys(names)
        seen.add(name)
        result[name] = bool(source and pattern and not pattern.startswith(b'!'))
    return result


def inventory(project: Path) -> dict:
    root_result = subprocess.run(['git', '-C', str(project), 'rev-parse', '--show-toplevel'],
                                 capture_output=True, check=False)
    if root_result.returncode:
        raise ValueError('project is not an accessible Git worktree')
    root = Path(os.fsdecode(root_result.stdout[:-1]))
    entries: dict[str, str] = {}
    categories = (
        ('tracked', []),
        ('untracked', ['--others', '--exclude-standard']),
        ('ignored', ['--others', '--ignored', '--exclude-standard']),
    )
    for tracking, options in categories:
        result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z', *options, '--', '.ai', '.aips'],
                                capture_output=True, check=False)
        if result.returncode:
            raise ValueError(f'could not inspect {tracking} AIPS paths')
        for raw in result.stdout.split(b'\0'):
            if raw:
                entries.setdefault(os.fsdecode(raw), tracking)
    ignored_tracked = tracked_ignore_status(root, [name for name, tracking in entries.items() if tracking == 'tracked'])
    files = []
    for name, tracking in sorted(entries.items()):
        row = inspect_path(root, name)
        row['tracking'] = tracking
        row['tracked_and_ignored'] = ignored_tracked.get(name) if tracking == 'tracked' else False
        files.append(row)
    return {'version': 1, 'scope': 'Git-listed AIPS working-tree paths',
            'limitations': ['Empty directories and contents of nested repositories may not be listed.'],
            'files': files}


def _copy_verified_file(root: Path, name: str, destination: Path, expected_sha256: str) -> None:
    """Copy one regular project file without following source symlinks."""
    if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY'):
        raise ValueError('safe no-follow file operations are unavailable on this platform')
    parts = Path(name).parts
    if not parts or any(part in ('', '.', '..') for part in parts):
        raise ValueError('inventory contains an unsafe relative path')
    parent_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    source_fd = None
    target_fd = None
    try:
        for part in parts[:-1]:
            info = os.stat(part, dir_fd=parent_fd, follow_symlinks=False)
            if not stat.S_ISDIR(info.st_mode):
                raise ValueError('source path changed or contains a symlink')
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = next_fd
        before = os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('source path changed or is not a regular file')
        source_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent_fd)
        opened = os.fstat(source_fd)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ValueError('source file changed during backup')

        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(destination.parent, 0o700)
        target_fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        digest = hashlib.sha256()
        while True:
            chunk = os.read(source_fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            view = memoryview(chunk)
            while view:
                written = os.write(target_fd, view)
                view = view[written:]
        os.fsync(target_fd)
        after = os.fstat(source_fd)
        identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
        if identity(opened) != identity(after) or digest.hexdigest() != expected_sha256:
            raise ValueError('source changed or checksum did not match the inventory')
        os.fchmod(target_fd, 0o600)
    except Exception:
        if target_fd is not None:
            with contextlib.suppress(OSError):
                os.close(target_fd)
            target_fd = None
        with contextlib.suppress(FileNotFoundError):
            destination.unlink()
        raise
    finally:
        if source_fd is not None:
            os.close(source_fd)
        if target_fd is not None:
            os.close(target_fd)
        os.close(parent_fd)


def backup(project: Path, destination: Path) -> dict:
    """Create and verify a private external backup without changing the project."""
    root_result = subprocess.run(['git', '-C', str(project), 'rev-parse', '--show-toplevel'],
                                 capture_output=True, check=False)
    if root_result.returncode:
        raise ValueError('project is not an accessible Git worktree')
    root = Path(os.fsdecode(root_result.stdout[:-1])).resolve()
    target = destination.expanduser()
    if not target.is_absolute():
        raise ValueError('backup destination must be an absolute path')
    parent = target.parent.resolve()
    resolved_target = parent / target.name
    if resolved_target == root or root in resolved_target.parents:
        raise ValueError('backup destination must be outside the project repository')
    try:
        parent_info = parent.lstat()
    except OSError as exc:
        raise ValueError('backup destination parent must already exist') from exc
    if not stat.S_ISDIR(parent_info.st_mode) or stat.S_ISLNK(parent_info.st_mode):
        raise ValueError('backup destination parent must be a real directory')
    if resolved_target.exists() or resolved_target.is_symlink():
        raise ValueError('backup destination already exists')

    report = inventory(root)
    unsafe = [row['path'] for row in report['files'] if row['kind'] != 'file' or not row['sha256']]
    if unsafe:
        raise ValueError('backup stopped because inventory entries are unavailable or unsafe')
    temporary = Path(tempfile.mkdtemp(prefix='.aips-migration-backup-', dir=parent))
    os.chmod(temporary, 0o700)
    try:
        files_root = temporary / 'files'
        files_root.mkdir(mode=0o700)
        for row in report['files']:
            _copy_verified_file(root, row['path'], files_root / row['path'], row['sha256'])
        manifest = {
            'version': 1,
            'status': 'BACKUP_VERIFIED',
            'created_at': datetime.now(UTC).isoformat(),
            'repository_id': repository_identity(root)['repository_id'],
            'scope': report['scope'],
            'limitations': report['limitations'],
            'file_count': len(report['files']),
            'files': [
                {key: row.get(key) for key in (
                    'path', 'classification', 'tracking', 'tracked_and_ignored', 'kind', 'sha256',
                )}
                for row in report['files']
            ],
        }
        manifest_path = temporary / 'manifest.json'
        descriptor = os.open(manifest_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(manifest, stream, ensure_ascii=True, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.rename(temporary, resolved_target)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {
        'status': 'BACKUP_VERIFIED',
        'destination': str(resolved_target),
        'manifest': str(resolved_target / 'manifest.json'),
        'file_count': len(report['files']),
    }


def apply_migration(project: Path, destination: Path, confirmation: str) -> dict:
    """Back up AIPS state, then untrack it while preserving working-tree files."""
    root_result = subprocess.run(['git', '-C', str(project), 'rev-parse', '--show-toplevel'],
                                 capture_output=True, check=False)
    if root_result.returncode:
        raise ValueError('project is not an accessible Git worktree')
    root = Path(os.fsdecode(root_result.stdout[:-1])).resolve()
    repo_id = repository_identity(root)['repository_id']
    if confirmation != repo_id:
        raise ValueError(f'confirmation must exactly match repository_id: {repo_id}')

    backup_result = backup(root, destination)
    tracked = [row['path'] for row in inventory(root)['files'] if row['tracking'] == 'tracked']
    if tracked:
        proc = subprocess.run(
            ['git', '-C', str(root), 'rm', '--cached', '--force', '--ignore-unmatch', '-r', '--', '.ai', '.aips'],
            capture_output=True, text=True, check=False,
        )
        if proc.returncode:
            raise ValueError(f'backup verified at {backup_result["destination"]}; Git index update failed: {proc.stderr.strip()}')
    remaining = subprocess.run(
        ['git', '-C', str(root), 'ls-files', '-z', '--', '.ai', '.aips'],
        capture_output=True, check=False,
    )
    if remaining.returncode or remaining.stdout:
        raise ValueError(f'backup verified at {backup_result["destination"]}; tracked AIPS paths remain in the index')
    return {
        **backup_result,
        'status': 'MIGRATION_APPLIED',
        'repository_id': repo_id,
        'untracked_from_index': tracked,
        'working_tree_files_preserved': True,
        'recovery': 'git restore --staged -- .ai .aips',
    }



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--dry-run', action='store_true', help='inspect only; do not migrate')
    action.add_argument('--backup-to', type=Path, help='create a verified private backup outside the project')
    action.add_argument('--apply', action='store_true', help='back up, then remove .ai/.aips from the Git index only')
    parser.add_argument('--confirm-repository-id', help='required with --apply; exact repository identity confirmation')
    args = parser.parse_args()
    try:
        if args.dry_run:
            if args.confirm_repository_id:
                raise ValueError('--confirm-repository-id is only valid with --apply')
            result = inventory(args.project)
        elif args.apply:
            if not args.backup_to or not args.confirm_repository_id:
                raise ValueError('--apply requires both --backup-to and --confirm-repository-id')
            result = apply_migration(args.project, args.backup_to, args.confirm_repository_id)
        else:
            if args.confirm_repository_id:
                raise ValueError('--confirm-repository-id is only valid with --apply')
            result = backup(args.project, args.backup_to)
        print(json.dumps(result, ensure_ascii=True, indent=2))
    except (OSError, ValueError) as exc:
        print(f'inventory: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
