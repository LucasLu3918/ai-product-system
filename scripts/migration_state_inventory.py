"""Inspect tracked AIPS state without modifying the worktree or Git index."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path


def inspect_path(root: Path, name: str) -> dict:
    row = {'path': name, 'classification': 'review_required', 'kind': 'unavailable', 'sha256': None}
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
    files = []
    for name, tracking in sorted(entries.items()):
        row = inspect_path(root, name)
        row['tracking'] = tracking
        files.append(row)
    return {'version': 1, 'scope': 'Git-listed AIPS working-tree paths',
            'limitations': ['Empty directories and contents of nested repositories may not be listed.'],
            'files': files}



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true', required=True, help='inspect only; do not migrate')
    args = parser.parse_args()
    try:
        print(json.dumps(inventory(args.project), ensure_ascii=True, indent=2))
    except (OSError, ValueError) as exc:
        print(f'inventory: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
