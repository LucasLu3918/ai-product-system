"""Bind standalone/shadow dependency findings to one exact PR candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def canonical_findings(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: canonical_findings(item) for key, item in value.items()}
    if isinstance(value, list):
        return sorted((canonical_findings(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True))
    return value


def capture(env: Mapping[str, str]) -> dict[str, Any]:
    findings: dict[str, Any] = {}
    available = True
    for key in ("DEPENDENCY_CHANGES", "VULNERABLE_CHANGES", "INVALID_LICENSE_CHANGES", "DENIED_CHANGES"):
        try:
            value = json.loads(env.get(key, ""))
            if not isinstance(value, list):
                raise TypeError("array required")
            findings[key.lower()] = canonical_findings(value)
        except (ValueError, TypeError):
            available = False
            findings[key.lower()] = None
    head, base = env.get("CANDIDATE_HEAD", ""), env.get("CANDIDATE_BASE", "")
    available = (available and env.get("REVIEW_OUTCOME") in {"success", "failure"}
                 and bool(re.fullmatch(r"[0-9a-f]{40}", head) and re.fullmatch(r"[0-9a-f]{40}", base)))
    digest = hashlib.sha256(json.dumps(findings, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"version": 1, "head": head, "base": base, "variant": "shadow" if env.get("IS_SHADOW") == "true" else "standalone",
            "run_id": env.get("GITHUB_RUN_ID"), "outcome": env.get("REVIEW_OUTCOME", "unavailable"),
            "findings_available": available, "findings": findings, "findings_sha256": digest,
            "promotion_authorized": False}


def compare(first: dict[str, Any], second: dict[str, Any]) -> str:
    def valid(report: dict[str, Any]) -> bool:
        findings = report.get("findings")
        return (type(report.get("version")) is int and report.get("version") == 1 and report.get("findings_available") is True
                and report.get("variant") in ("standalone", "shadow")
                and report.get("outcome") in {"success", "failure"}
                and isinstance(findings, dict)
                and set(findings) == {"dependency_changes", "vulnerable_changes", "invalid_license_changes", "denied_changes"}
                and all(isinstance(value, list) for value in findings.values())
                and all(re.fullmatch(r"[0-9a-f]{40}", str(report.get(key, ""))) for key in ("head", "base"))
                and report.get("findings_sha256") == hashlib.sha256(json.dumps(findings, sort_keys=True, separators=(",", ":")).encode()).hexdigest())

    if (not valid(first) or not valid(second)
            or first.get("head") != second.get("head") or first.get("base") != second.get("base")
            or {first.get("variant"), second.get("variant")} != {"standalone", "shadow"}):
        return "UNKNOWN"
    return "PARITY" if first["findings"] == second["findings"] and first["outcome"] == second["outcome"] else "MISMATCH"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(capture(os.environ), sort_keys=True, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
