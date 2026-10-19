"""Read-only local Content Safety diagnostics for explicit Git candidates."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from governance_guard import commit_safety
from publication_authority import PublicationError


def _recovery_payload(diagnostic: dict[str, Any]) -> dict[str, Any]:
    evidence = []
    for finding in diagnostic.get("findings") or []:
        if not isinstance(finding, dict):
            continue
        safe = {key: finding[key] for key in
                ("category", "detector", "rule_id", "file", "line", "finding_fingerprint")
                if key in finding}
        if safe:
            evidence.append(safe)
    next_step = diagnostic.get("next_step_zh") or diagnostic.get("next_step")
    return {
        "summary": diagnostic.get("detail_zh") or diagnostic.get("detail"),
        "blocking_phase": diagnostic.get("phase"),
        "evidence": evidence,
        "next_steps": [next_step] if next_step else [],
        "human_approval_required": diagnostic.get("reason_code") == "CONTENT_REVIEW_REQUIRED",
        "matched_content_included": False,
    }


def diagnose_commit(worktree: Path, message_file: Path) -> dict[str, Any]:
    """Inspect staged blobs and a message file using the native Hook implementation."""
    root = worktree.resolve()
    message = message_file.resolve()
    command = shlex.join(["git", "commit", "-F", str(message)])
    try:
        result = commit_safety(root, command)
    except PublicationError as exc:
        diagnostic = exc.diagnostic()
        diagnostic["recovery"] = _recovery_payload(diagnostic)
        return {"decision": "BLOCK", "diagnostic": diagnostic}
    except Exception as exc:  # noqa: BLE001 - unexpected scanner errors are safe, closed denials.
        diagnostic = PublicationError("internal commit scanner failure", "CONTENT_SCANNER_FAILED",
                                      context={"error_class": type(exc).__name__},
                                      phase="content_scan").diagnostic()
        diagnostic["recovery"] = _recovery_payload(diagnostic)
        return {"decision": "BLOCK", "diagnostic": diagnostic}
    if result.get("decision") == "BLOCK":
        finding_fields = {key: result.get(key) for key in
                          ("diagnostic_id", "reason_code", "phase", "source", "category", "retryable", "findings")}
        diagnostic = PublicationError("", result.get("reason_code") or "CONTENT_SAFETY_BLOCKED",
                                      phase=result.get("phase") or "content_scan").diagnostic()
        diagnostic.update({key: value for key, value in finding_fields.items() if value is not None})
        diagnostic["recovery"] = _recovery_payload(diagnostic)
        return {"decision": "BLOCK", "diagnostic": diagnostic}
    # Never serialize commit text or scanner payloads in a read-only report.
    return {"decision": "ALLOW", "diagnostic": None}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    commit = sub.add_parser("commit", help="Inspect staged Git content and an explicit message file; does not mutate Git")
    commit.add_argument("--worktree", type=Path, default=Path.cwd())
    commit.add_argument("--message-file", type=Path, required=True)
    commit.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args(argv)

    result = diagnose_commit(args.worktree, args.message_file)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["decision"] == "ALLOW":
        print("允許：commit 訊息與暫存內容通過安全掃描。")
    else:
        diagnostic = result["diagnostic"]
        print(f"拒絕：{diagnostic.get('detail_zh', 'commit 安全掃描未通過。')}")
        print(f"原因：{diagnostic.get('reason_code')}；診斷 ID：{diagnostic.get('diagnostic_id')}")
        print(diagnostic.get("next_step_zh", "修正候選後重新執行唯讀診斷。"))
        for finding in diagnostic.get("findings", []):
            location = finding.get("file") or finding.get("source")
            print(f"  - {finding.get('category')}/{finding.get('detector')} ({location})")
    return 0 if result["decision"] == "ALLOW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
