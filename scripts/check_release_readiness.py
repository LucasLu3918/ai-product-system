#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys
import yaml

def main():
    parser = argparse.ArgumentParser(description="Check AI Product System Release Readiness YAML.")
    parser.add_argument("path", help="Path to RELEASE_READINESS.yaml")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(json.dumps({"status": "error", "error": "file_not_found", "path": str(path)}))
        return 2

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        print(json.dumps({"status": "error", "error": "yaml_parse_failed", "detail": str(exc)}))
        return 2

    declared = data.get("status")
    blockers = data.get("blockers") or []
    security = data.get("security") or {}
    critical = security.get("unresolved_critical")
    high = security.get("unresolved_high")

    findings = []
    if declared == "READY" and blockers:
        findings.append("READY status has blockers")
    if declared == "READY" and isinstance(critical, int) and critical > 0:
        findings.append("READY status has unresolved Critical security findings")
    if declared == "READY" and isinstance(high, int) and high > 0:
        findings.append("READY status has unresolved High security findings")

    summary = {
        "status": "pass" if declared == "READY" and not findings else "not_ready",
        "declared_status": declared,
        "blocker_count": len(blockers),
        "unresolved_critical": critical,
        "unresolved_high": high,
        "findings": findings,
        "evidence_count": len(data.get("evidence") or []),
        "path": str(path),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["status"] == "pass" else 1

if __name__ == "__main__":
    sys.exit(main())
