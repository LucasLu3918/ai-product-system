#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, sys
from pathlib import Path
from typing import Any
import yaml

PROTECTED = {
    "git_push": re.compile(r"(^|[;&|]\\s*)git\\s+push(?:\\s|$)"),
    "git_tag": re.compile(r"(^|[;&|]\\s*)git\\s+tag(?:\\s|$)"),
    "gh_pr_create": re.compile(r"(^|[;&|]\\s*)gh\\s+pr\\s+create(?:\\s|$)"),
    "gh_release_create": re.compile(r"(^|[;&|]\\s*)gh\\s+release\\s+create(?:\\s|$)"),
}
SET_LIKE_KEYS = {"files", "boundaries", "operations"}

def canonicalize(value: Any, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {k: canonicalize(value[k], k) for k in sorted(value)}
    if isinstance(value, list):
        items = [canonicalize(v) for v in value]
        if key in SET_LIKE_KEYS:
            return sorted(items, key=lambda v: json.dumps(v, ensure_ascii=False, sort_keys=True))
        return items
    return value

def fingerprint(value: Any) -> str:
    payload = json.dumps(canonicalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()

def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("approval record must be a mapping")
    return data

def git_output(cwd: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=5)
    return r.stdout.strip() if r.returncode == 0 else ""

def actual_scope(cwd: Path, operation: str) -> dict:
    root_text = git_output(cwd, "rev-parse", "--show-toplevel")
    root = Path(root_text) if root_text else cwd
    branch = git_output(root, "branch", "--show-current") or None
    commit = git_output(root, "rev-parse", "HEAD") or None
    upstream = git_output(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    files = []
    if upstream:
        files = [x for x in git_output(root, "diff", "--name-only", upstream + "...HEAD").splitlines() if x]
    return {"branch": branch, "candidate_commit": commit, "files": sorted(files), "boundaries": [], "operations": [operation]}

def approval_path(cwd: Path) -> Path | None:
    env = os.environ.get("AIPS_APPROVAL_RECORD")
    if env:
        return Path(env).expanduser()
    state = cwd / ".ai" / "STATE.yaml"
    if state.exists():
        data = yaml.safe_load(state.read_text(encoding="utf-8")) or {}
        rel = (data.get("governance") or {}).get("active_approval")
        if rel:
            p = Path(str(rel))
            return p if p.is_absolute() else cwd / p
    default = cwd / ".ai" / "approvals" / "ACTIVE.yaml"
    return default if default.exists() else None

def verify_record(path: Path, operation: str, cwd: Path, check_actual: bool = True):
    doc = load_yaml(path)
    approval = doc.get("approval") or {}
    scope = doc.get("scope") or {}
    if approval.get("status") != "APPROVED":
        return False, "approval is not APPROVED", doc
    stored = scope.get("fingerprint")
    scoped = {k: v for k, v in scope.items() if k != "fingerprint"}
    if not stored or stored != fingerprint(scoped):
        return False, "approval scope fingerprint is missing or stale", doc
    if operation not in (scope.get("operations") or []):
        return False, "operation is outside approved scope", doc
    if check_actual:
        actual = actual_scope(cwd, operation)
        for key in ("branch", "candidate_commit"):
            if scope.get(key) and actual.get(key) != scope.get(key):
                return False, "current " + key + " does not match approved scope", doc
        expected_files = sorted(scope.get("files") or [])
        if expected_files and actual.get("files") != expected_files:
            return False, "current changed-file set does not match approved scope", doc
    return True, "approval binding valid", doc

def operation_for(command: str):
    for name, pattern in PROTECTED.items():
        if pattern.search(command):
            return name
    return None

def hook(runtime: str) -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    command = str((payload.get("tool_input") or {}).get("command") or "")
    operation = operation_for(command)
    if not operation:
        print("{}")
        return 0
    cwd = Path(str(payload.get("cwd") or os.getcwd())).resolve()
    path = approval_path(cwd)
    ok = False
    reason = "no active AIPS Approval Record"
    if path and path.exists():
        try:
            ok, reason, _ = verify_record(path, operation, cwd)
        except Exception as exc:
            reason = "approval verification failed: " + str(exc)
    if runtime == "claude-code":
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow" if ok else "deny",
            "permissionDecisionReason": "AIPS approval binding verified" if ok else "AIPS blocked protected publication: " + reason,
        }}))
    else:
        result = {"decision": "allow" if ok else "deny"}
        if not ok:
            result["reason"] = "AIPS blocked protected publication: " + reason
        print(json.dumps(result))
    return 0

def main() -> int:
    p = argparse.ArgumentParser(description="AIPS deterministic approval binding and publication guard")
    sub = p.add_subparsers(dest="command", required=True)
    fp = sub.add_parser("fingerprint")
    fp.add_argument("--file", required=True)
    vr = sub.add_parser("verify")
    vr.add_argument("--approval", required=True)
    vr.add_argument("--operation", required=True, choices=sorted(PROTECTED))
    vr.add_argument("--cwd", default=os.getcwd())
    vr.add_argument("--no-actual", action="store_true")
    hk = sub.add_parser("hook")
    hk.add_argument("--runtime", required=True, choices=["claude-code", "gemini-cli"])
    a = p.parse_args()
    if a.command == "fingerprint":
        path = Path(a.file)
        value = yaml.safe_load(path.read_text(encoding="utf-8")) if path.suffix in {".yaml", ".yml"} else json.loads(path.read_text(encoding="utf-8"))
        print(fingerprint(value))
        return 0
    if a.command == "verify":
        ok, reason, _ = verify_record(Path(a.approval), a.operation, Path(a.cwd), not a.no_actual)
        print(json.dumps({"status": "VALID" if ok else "APPROVAL_STALE", "reason": reason}))
        return 0 if ok else 2
    return hook(a.runtime)

if __name__ == "__main__":
    raise SystemExit(main())
