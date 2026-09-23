#!/usr/bin/env python3
"""Deterministic browser discovery and launch probes for visual evidence."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


SYSTEM_BROWSER_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)


def provider_request() -> str:
    value = os.environ.get("AIPS_BROWSER_PROVIDER", "auto").strip().lower()
    if value not in {"auto", "managed", "system"}:
        raise ValueError("AIPS_BROWSER_PROVIDER must be auto, managed, or system")
    return value


def managed_browser_binary() -> str | None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    playwright = sync_playwright().start()
    try:
        path = Path(playwright.chromium.executable_path)
        return str(path) if path.is_file() else None
    finally:
        playwright.stop()


def system_browser_binary() -> str | None:
    candidates = (
        os.environ.get("CHROME_BIN"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        *SYSTEM_BROWSER_CANDIDATES,
        os.environ.get("PROGRAMFILES", "") + r"\\Google\\Chrome\\Application\\chrome.exe",
        os.environ.get("PROGRAMFILES(X86)", "") + r"\\Google\\Chrome\\Application\\chrome.exe",
    )
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    return None


def discover_browser(provider: str | None = None) -> dict[str, Any]:
    requested = provider or provider_request()
    if requested in {"auto", "managed"}:
        managed = managed_browser_binary()
        if managed:
            return {"provider": "managed", "path": managed, "requested": requested}
        if requested == "managed":
            return {"provider": "managed", "path": None, "requested": requested}
    system = system_browser_binary()
    return {"provider": "system", "path": system, "requested": requested}


def probe_browser(path: str | None, *, provider: str, timeout: float = 10.0) -> dict[str, Any]:
    if not path:
        return {"status": "BROWSER_NOT_FOUND", "provider": provider, "path": None}
    binary = Path(path)
    if not binary.is_file() or not os.access(binary, os.X_OK):
        return {"status": "BROWSER_NOT_EXECUTABLE", "provider": provider, "path": path}

    version = subprocess.run(
        [path, "--version"], capture_output=True, text=True, timeout=timeout, check=False
    )
    if version.returncode != 0:
        return {
            "status": "BROWSER_VERSION_FAILED",
            "provider": provider,
            "path": path,
            "exit_code": version.returncode,
            "stderr": (version.stderr or version.stdout).strip()[-1000:],
        }

    with tempfile.TemporaryDirectory(prefix="aips-browser-probe-") as profile:
        command = [
            path,
            "--headless=new",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={profile}",
            "--dump-dom",
            "data:text/html,<title>aips-browser-probe</title><body>ok</body>",
        ]
        try:
            launch = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            return {
                "status": "BROWSER_LAUNCH_TIMEOUT",
                "provider": provider,
                "path": path,
                "timeout_seconds": timeout,
                "stderr": str(exc)[-1000:],
            }
    if launch.returncode != 0:
        return {
            "status": "BROWSER_LAUNCH_FAILED",
            "provider": provider,
            "path": path,
            "exit_code": launch.returncode,
            "version": (version.stdout or version.stderr).strip()[-300:],
            "stderr": (launch.stderr or launch.stdout).strip()[-1000:],
        }
    return {
        "status": "READY",
        "provider": provider,
        "path": path,
        "version": (version.stdout or version.stderr).strip()[-300:],
    }


def playwright_launch_kwargs(playwright: Any) -> tuple[dict[str, Any], str]:
    selection = discover_browser()
    if selection["provider"] == "managed":
        return {"headless": True}, "playwright-managed"
    path = selection.get("path")
    if not path:
        raise RuntimeError("No system Chrome/Chromium binary available for rendered visual evidence")
    return {"executable_path": path, "headless": True}, f"system-{Path(path).name}"
