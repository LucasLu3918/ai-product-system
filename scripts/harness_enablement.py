"""Read conservative Harness enablement evidence without changing user state."""
from __future__ import annotations

import argparse
import fcntl
import os
import stat
from pathlib import Path

import yaml

MAX_RECORD_BYTES = 16 * 1024


def safe_directory(path: Path) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(path, flags)
    info = os.fstat(fd)
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o022:
        os.close(fd)
        raise ValueError('unsafe directory')
    return fd


def safe_record(directory_fd: int, name: str) -> bytes:
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid() or before.st_mode & 0o022:
            raise ValueError('unsafe record')
        data = stream.read(MAX_RECORD_BYTES + 1)
        after = os.fstat(stream.fileno())
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns
        ) or len(data) > MAX_RECORD_BYTES:
            raise ValueError('record changed or too large')
        return data


def disabled_record(system: Path) -> bytes:
    root = str(system.resolve())
    if "\n" in root or "\r" in root:
        raise ValueError('invalid system path')
    return (root + '\n').encode('utf-8')


def set_disabled(config: Path, system: Path, *, disabled: bool) -> None:
    config_fd = safe_directory(config)
    try:
        harness_fd = os.open('harness', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=config_fd)
        try:
            info = os.fstat(harness_fd)
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o022:
                raise ValueError('unsafe Harness directory')
            expected = disabled_record(system)
            try:
                current = safe_record(harness_fd, 'disabled')
            except FileNotFoundError:
                current = None
            if disabled:
                if current == expected:
                    return
                if current is not None:
                    raise ValueError('existing disable record is not owned by this system')
                fd = os.open('disabled', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=harness_fd)
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(expected)
                    stream.flush()
                    os.fsync(stream.fileno())
                return
            if current is None:
                return
            if current != expected:
                raise ValueError('disable record belongs to another system')
            os.unlink('disabled', dir_fd=harness_fd)
        finally:
            os.close(harness_fd)
    finally:
        os.close(config_fd)


def classify(config: Path, system: Path, *, require_install_marker: bool = False) -> str:
    if not all(hasattr(os, name) for name in ('O_DIRECTORY', 'O_NOFOLLOW', 'O_NONBLOCK', 'getuid')):
        return 'UNKNOWN'
    config_fd = None
    harness_fd = None
    try:
        try:
            config_fd = safe_directory(config)
        except FileNotFoundError:
            return 'OFF'
        try:
            harness_fd = os.open('harness', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=config_fd)
        except FileNotFoundError:
            return 'OFF'
        info = os.fstat(harness_fd)
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o022:
            return 'UNKNOWN'
        try:
            disabled = safe_record(harness_fd, 'disabled')
        except FileNotFoundError:
            disabled = None
        if disabled is not None:
            return 'OFF' if disabled == disabled_record(system) else 'UNKNOWN'
        try:
            system_dir = safe_record(config_fd, 'system-dir').decode('utf-8').removesuffix('\n')
        except FileNotFoundError:
            if require_install_marker:
                return 'UNKNOWN'
            system_dir = None
        manifest = yaml.safe_load(safe_record(harness_fd, 'installation.yaml'))
        if not isinstance(manifest, dict) or type(manifest.get('version')) is not int or manifest['version'] != 1:
            return 'UNKNOWN'
        system_info = manifest.get('system')
        harness_info = manifest.get('harness')
        if not isinstance(system_info, dict) or not isinstance(harness_info, dict):
            return 'UNKNOWN'
        recorded_root = system_info.get('root')
        if not isinstance(recorded_root, str) or system_dir == '' or harness_info.get('enabled') is not True:
            return 'UNKNOWN'
        if not Path(recorded_root).is_absolute() or (system_dir is not None and not Path(system_dir).is_absolute()):
            return 'UNKNOWN'
        expected = system.resolve()
        marker_matches = system_dir is None or Path(system_dir).resolve() == expected
        return 'ACTIVE' if marker_matches and Path(recorded_root).resolve() == expected else 'UNKNOWN'
    except (OSError, ValueError, UnicodeError, RuntimeError, RecursionError, yaml.YAMLError):
        return 'UNKNOWN'
    finally:
        if harness_fd is not None:
            os.close(harness_fd)
        if config_fd is not None:
            os.close(config_fd)


def exec_locked(config: Path, command: list[str]) -> None:
    if not command:
        raise ValueError('locked command is required')
    config.mkdir(mode=0o700, parents=True, exist_ok=True)
    config_fd = safe_directory(config)
    try:
        fd = os.open('harness-lifecycle.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=config_fd)
    finally:
        os.close(config_fd)
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        os.close(fd)
        raise ValueError('unsafe Harness lifecycle lock')
    fcntl.flock(fd, fcntl.LOCK_EX)
    os.set_inheritable(fd, True)
    os.execvp(command[0], command)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--require-install-marker', action='store_true')
    parser.add_argument('--lock-exec', nargs=argparse.REMAINDER, help='run a lifecycle command while holding the per-user Harness lock')
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--mark-disabled', action='store_true')
    action.add_argument('--clear-disabled', action='store_true')
    args = parser.parse_args()
    if args.lock_exec is not None:
        try:
            exec_locked(args.config, args.lock_exec)
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        return 127
    if args.mark_disabled or args.clear_disabled:
        try:
            set_disabled(args.config, args.system, disabled=args.mark_disabled)
        except (OSError, ValueError, RuntimeError) as exc:
            parser.error(str(exc))
        return 0
    print(classify(args.config, args.system, require_install_marker=args.require_install_marker))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
