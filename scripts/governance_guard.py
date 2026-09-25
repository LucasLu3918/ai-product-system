#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, re, shlex, subprocess, sys
from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

try:
    from content_safety import safe_emit
except ModuleNotFoundError:  # imported as a repository module
    from scripts.content_safety import safe_emit

PROTECTED = ("git_push", "git_tag", "gh_pr_create", "gh_release_create")
CONTENT_SENSITIVE = ("git_commit", "git_push", "git_tag", "gh_pr_create", "gh_release_create")
SET_LIKE_KEYS = {"files", "boundaries", "operations"}
ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
CONTROL_TOKENS = {";", ";;", "&", "&&", "|", "||"}

GIT_GLOBAL_WITH_VALUE = {
    "-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix",
    "--config-env", "--exec-path",
}
GH_GLOBAL_WITH_VALUE = {"-R", "--repo", "--hostname"}
ENV_WITH_VALUE = {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"}
SUDO_WITH_VALUE = {"-u", "--user", "-g", "--group", "-h", "--host", "-p", "--prompt", "-C", "--close-from"}


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


def _shell_tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _segments(command: str) -> list[list[str]]:
    try:
        tokens = _shell_tokens(command)
    except ValueError:
        return []
    result: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in CONTROL_TOKENS or (token and all(ch in ";&|" for ch in token)):
            if current:
                result.append(current)
                current = []
        else:
            current.append(token)
    if current:
        result.append(current)
    return result


def _strip_options(tokens: list[str], with_value: set[str]) -> list[str]:
    result: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == "--":
            result.extend(tokens[i + 1:])
            break
        matched = next((opt for opt in with_value if token == opt), None)
        if matched:
            i += 2
            continue
        matched_prefix = next((opt for opt in with_value if token.startswith(opt + "=")), None)
        if matched_prefix:
            i += 1
            continue
        if token.startswith("-"):
            i += 1
            continue
        result.extend(tokens[i:])
        break
    return result


def _unwrap(tokens: list[str]) -> list[str]:
    tokens = list(tokens)
    while tokens:
        while tokens and ASSIGNMENT_RE.match(tokens[0]):
            tokens.pop(0)
        if not tokens:
            return []
        exe = Path(tokens[0]).name
        if exe == "env":
            tokens = _strip_options(tokens[1:], ENV_WITH_VALUE)
            while tokens and ASSIGNMENT_RE.match(tokens[0]):
                tokens.pop(0)
            continue
        if exe == "sudo":
            tokens = _strip_options(tokens[1:], SUDO_WITH_VALUE)
            continue
        if exe == "command":
            tokens = _strip_options(tokens[1:], set())
            continue
        break
    return tokens


def _direct_operations(tokens: list[str]) -> list[str]:
    tokens = _unwrap(tokens)
    if not tokens:
        return []
    exe = Path(tokens[0]).name

    if exe in {"bash", "sh", "zsh"}:
        for i, token in enumerate(tokens[1:], start=1):
            if token == "-c" and i + 1 < len(tokens):
                return operations_for(tokens[i + 1])
            if token.startswith("-") and "c" in token[1:] and i + 1 < len(tokens):
                return operations_for(tokens[i + 1])
        return []

    if exe == "eval" and len(tokens) > 1:
        return operations_for(" ".join(tokens[1:]))

    if exe == "git":
        args = _strip_options(tokens[1:], GIT_GLOBAL_WITH_VALUE)
        if not args:
            return []
        if args[0] == "push":
            return ["git_push"]
        if args[0] == "commit":
            return ["git_commit"]
        if args[0] == "tag":
            return ["git_tag"]
        return []

    if exe == "gh":
        args = _strip_options(tokens[1:], GH_GLOBAL_WITH_VALUE)
        if len(args) >= 2 and args[0:2] == ["pr", "create"]:
            return ["gh_pr_create"]
        if len(args) >= 2 and args[0:2] == ["release", "create"]:
            return ["gh_release_create"]
    return []


def operations_for(command: str) -> list[str]:
    operations: list[str] = []
    for segment in _segments(command):
        for operation in _direct_operations(segment):
            if operation not in operations:
                operations.append(operation)
    return operations


def operation_for(command: str):
    operations = operations_for(command)
    return operations[0] if operations else None


def hook(runtime: str) -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    command = str((payload.get("tool_input") or {}).get("command") or "")
    try:
        from runtime_policy import action_from_hook, evaluate, load_policy

        runtime_action = action_from_hook(payload, runtime)
        if runtime_action is not None:
            cwd_for_policy = Path(str(payload.get("cwd") or os.getcwd())).resolve()
            policy_path = Path(os.environ.get("AIPS_RUNTIME_POLICY_PATH", str(ROOT / "config/runtime-policy.yaml"))).expanduser()
            policy, policy_bytes = load_policy(policy_path)
            cap = "TOOL_GUARDED" if runtime in {"claude-code", "gemini-cli"} else "ADVISORY"
            decision = evaluate(runtime_action, policy, runtime_capability=cap, policy_bytes=policy_bytes,
                                approval_path=approval_path(cwd_for_policy), project_root=cwd_for_policy)
            event = decision.get("audit") or {}
            ledger = os.environ.get("AIPS_GOVERNANCE_AUDIT_LEDGER")
            if ledger:
                try:
                    from governance_audit import append_event
                    from datetime import datetime, timezone
                    append_event(Path(ledger), {
                        "event_type": event.get("event_type", "RUNTIME_ACTION_BLOCKED"),
                        "occurred_at": datetime.now(timezone.utc).isoformat(),
                        "actor": {"type": "runtime", "id": runtime},
                        "authority": {"source": "runtime_policy", "approval_id": None},
                        "binding": {"proposal_fingerprint": event.get("policy_digest"),
                                    "approval_scope_fingerprint": None, "candidate_commit": None,
                                    "branch": None, "operation": "external_data_egress",
                                    "result": decision.get("decision"), "files": [], "boundaries": [],
                                    "evidence_digests": [event.get("action_digest")] if event.get("action_digest") else []},
                        "metadata": {"correlation_id": None, "notes": "Runtime policy decision; action payload omitted."},
                    })
                except Exception:
                    if decision.get("decision") == "ALLOW":
                        decision["decision"] = "BLOCKED"
                        decision["reason"] = "required governance audit append failed"
            if decision.get("decision") != "ALLOW":
                reason = "AIPS runtime policy " + str(decision.get("decision")) + ": " + str(decision.get("reason"))
                if runtime == "claude-code":
                    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))
                else:
                    print(json.dumps({"decision": "deny", "reason": reason}))
                return 0
    except Exception as exc:
        reason = "AIPS runtime policy BLOCKED: policy evaluation failed (" + type(exc).__name__ + ")"
        if runtime == "claude-code":
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))
        else:
            print(json.dumps({"decision": "deny", "reason": reason}))
        return 0
    operations = operations_for(command)
    if not operations:
        print("{}")
        return 0

    cwd = Path(str(payload.get("cwd") or os.getcwd())).resolve()
    for operation in operations:
        if operation in CONTENT_SENSITIVE:
            sink = {
                "git_commit": "git_commit",
                "git_push": "source_artifact",
                "git_tag": "source_artifact",
                "gh_pr_create": "github_pr",
                "gh_release_create": "release_notes",
            }[operation]
            safety = safe_emit(sink=sink, payload={"command": command})
            if safety["decision"] == "BLOCK":
                reason = "content safety blocked " + operation
                if runtime == "claude-code":
                    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "AIPS blocked: " + reason}}))
                else:
                    print(json.dumps({"decision": "deny", "reason": "AIPS blocked: " + reason}))
                return 0
    path = approval_path(cwd)
    ok = False
    reason = "no active AIPS Approval Record"
    approval_operations = [operation for operation in operations if operation in PROTECTED]
    if not approval_operations:
        ok = True
        reason = "content safety passed; no publish approval required"
    elif path and path.exists():
        try:
            failures = []
            for operation in approval_operations:
                valid, op_reason, _ = verify_record(path, operation, cwd)
                if not valid:
                    failures.append(f"{operation}: {op_reason}")
            ok = not failures
            reason = "approval binding valid" if ok else "; ".join(failures)
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
