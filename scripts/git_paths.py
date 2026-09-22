"""Read Git path output without display quoting or line-based splitting."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import threading

MAX_GIT_PATH_OUTPUT_BYTES = 32 * 1024 * 1024
GIT_PATH_TIMEOUT_SECONDS = 20


class GitPathsError(RuntimeError):
    """A Git path listing was unavailable or incomplete."""


def run_git_nul_output(root: Path, args: list[str]) -> bytes:
    """Read bounded binary output from a Git command requested with ``-z``."""
    if "-z" not in args:
        raise ValueError("Git path commands must request -z output")
    try:
        proc = subprocess.Popen(
            ["git", "-C", str(root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise GitPathsError("git_paths_command_unavailable") from exc

    timed_out = threading.Event()

    def stop_on_timeout() -> None:
        if proc.poll() is None:
            try:
                proc.kill()
            except ProcessLookupError:
                return
            timed_out.set()

    timer = threading.Timer(GIT_PATH_TIMEOUT_SECONDS, stop_on_timeout)
    timer.start()
    data = bytearray()
    too_large = False
    try:
        assert proc.stdout is not None
        while chunk := proc.stdout.read(65536):
            data.extend(chunk)
            if len(data) > MAX_GIT_PATH_OUTPUT_BYTES:
                too_large = True
                if proc.poll() is None:
                    try:
                        proc.kill()
                    except ProcessLookupError:
                        pass
                break
        returncode = proc.wait()
    finally:
        timer.cancel()
        if proc.stdout is not None:
            proc.stdout.close()
        if proc.poll() is None:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            proc.wait()

    if timed_out.is_set():
        raise GitPathsError("git_paths_timeout")
    if too_large:
        raise GitPathsError("git_paths_output_limit")
    if returncode != 0:
        raise GitPathsError("git_paths_command_failed")
    return bytes(data)


def run_git_paths(root: Path, args: list[str]) -> list[str]:
    """Return paths without display quoting or line-based splitting."""
    data = run_git_nul_output(root, args)
    if data and data[-1] != 0:
        raise GitPathsError("git_paths_incomplete_output")
    return [os.fsdecode(part) for part in data.split(b"\0") if part]
