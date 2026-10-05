"""Install explicitly requested requirements while withholding raw package diagnostics."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def failure_category(output: str) -> str:
    text = output.lower()
    for code, markers in (
        ("HTTP_FORBIDDEN", ("403", "forbidden")),
        ("PROXY_ERROR", ("proxyerror", "cannot connect to proxy", "proxy authentication")),
        ("DNS_UNAVAILABLE", ("name resolution", "nodename nor servname", "could not resolve")),
        ("TLS_ERROR", ("certificate_verify_failed", "sslerror")),
        ("PACKAGE_UNAVAILABLE", ("no matching distribution", "could not find a version")),
    ):
        if any(marker in text for marker in markers):
            return code
    return "INSTALL_FAILED"


def install(python: str, requirements: Path, constraints: Path | None = None) -> dict[str, str]:
    try:
        command = [python, "-m", "pip", "install", "--disable-pip-version-check", "-q"]
        if constraints is not None:
            command.extend(("-c", str(constraints)))
        command.extend(("-r", str(requirements)))
        result = subprocess.run(
            command,
            capture_output=True, text=True, timeout=600, check=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "BLOCKED", "reason_code": "INSTALL_TIMEOUT", "next_step": "Check package-index connectivity and retry the explicit install command."}
    except OSError:
        return {"status": "BLOCKED", "reason_code": "INSTALL_RUNTIME_UNAVAILABLE", "next_step": "Verify the selected Python executable and pip installation."}
    if result.returncode == 0:
        return {"status": "PASS"}
    code = failure_category(result.stdout + "\n" + result.stderr)
    return {
        "status": "BLOCKED", "reason_code": code,
        "next_step": "Check the configured package-index access, proxy, DNS or TLS settings for this category, then retry the explicit install command. Package-index access is separate from GitHub authentication. Raw diagnostics are withheld because they may contain credentials.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", required=True)
    parser.add_argument("--requirements", required=True, type=Path)
    parser.add_argument("--constraints", type=Path, help="Optional tested version constraints for a reproducible package set")
    args = parser.parse_args()
    result = install(args.python, args.requirements, args.constraints)
    print(json.dumps(result))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
