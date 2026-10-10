#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shlex
import subprocess
import sys
from datetime import UTC
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

PROTECTED = ("git_push", "git_tag", "gh_pr_create", "gh_pr_merge", "gh_release_create")
CONTENT_SENSITIVE = ("git_commit", *PROTECTED)
logger = logging.getLogger(__name__)
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
    from publication_authority import approval_location
    if git_output(cwd, "rev-parse", "--show-toplevel"):
        return approval_location(cwd)
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


def verify_record(path: Path, operation: str, cwd: Path, check_actual: bool = True,
                  *, command: str | None = None, consume: bool = False):
    doc = load_yaml(path)
    if operation in PROTECTED:
        from publication_authority import PublicationError, verify
        from publication_commands import shell_commands
        try:
            commands = shell_commands(command) if command else []
            if len(commands) != 1:
                return False, "one standalone literal publication command required", doc
            verify(doc, operation, cwd, commands[0], consume=consume)
            return True, "external publication authority verified", doc
        except PublicationError as exc:
            return False, str(exc), doc  # Only constant redacted protocol reasons, never payload/path.
        except (OSError, ValueError, TypeError, KeyError, AttributeError, ImportError, yaml.YAMLError, subprocess.TimeoutExpired) as exc:
            # Do not emit exception text from subprocess/network/record parsing.
            return False, "publication authority unavailable or binding rejected (" + type(exc).__name__ + ")", doc
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
    from publication_commands import shell_commands
    return shell_commands(command)


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
            from publication_commands import CommandError
            if any(token.startswith(('-S', '--split-string')) for token in tokens[1:]):
                raise CommandError('env split-string execution requires a standalone command')
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
            if re.fullmatch(r'-[A-Za-z]*c[A-Za-z]*', token) and i + 1 < len(tokens):
                return operations_for(tokens[i + 1])
        from publication_commands import CommandError
        raise CommandError('interpreter file/stdin execution cannot be classified; use literal standalone commands')

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
        if args[0] in {'send-pack', 'http-push', 'receive-pack'}:
            from publication_commands import CommandError
            raise CommandError('Git remote-ref plumbing is unsupported; use the exact signed push workflow')
        if args[0] == "tag":
            query = args[1:]
            read_flags = {"--list", "-l", "--verify", "-v", "--contains", "--no-contains",
                          "--merged", "--no-merged", "--points-at", "--sort", "--format", "--column", "--no-column"}
            if not query or (any(x.split("=")[0] in read_flags or re.fullmatch(r"-n\d*", x) for x in query)
                             and all(not x.startswith("-") or x.split("=")[0] in read_flags or re.fullmatch(r"-n\d*", x) for x in query)):
                return []
            return ["git_tag"]
        # A Git alias may run shell code or publish; unknown verbs are not read-only evidence.
        builtin = subprocess.run(['git', '--list-cmds=builtins'], capture_output=True, text=True, timeout=5, check=False)
        if builtin.returncode or args[0] not in builtin.stdout.split():
            from publication_commands import CommandError
            raise CommandError('unknown Git verb or alias cannot be classified')
        return []

    if exe == "gh":
        args = _strip_options(tokens[1:], GH_GLOBAL_WITH_VALUE)
        if args and args[0] == 'api':
            from publication_commands import CommandError
            # API writes may change Git refs without invoking git push/gh pr merge.
            if '--method' not in args or args.count('--method') != 1 or args[args.index('--method') + 1:args.index('--method') + 2] != ['GET']:
                raise CommandError('unbound GitHub API mutation is unsupported')
            if any(x.startswith(('-f', '-F', '--field', '--raw-field', '--input', '-X', '--method=')) for x in args):
                raise CommandError('ambiguous GitHub API request is unsupported')
        if len(args) >= 2 and args[0:2] == ["pr", "create"]:
            return ["gh_pr_create"]
        if len(args) >= 2 and args[0:2] == ["pr", "merge"]:
            return ["gh_pr_merge"]
        if len(args) >= 2 and args[0:2] == ["release", "create"]:
            return ["gh_release_create"]
        if len(args) >= 2 and (args[0] == 'pr' and args[1] in {'edit', 'close', 'reopen', 'ready'}
                              or args[0] == 'release' and args[1] in {'delete', 'edit', 'upload'}
                              or args[0] == 'repo' and args[1] in {'delete', 'create', 'fork', 'sync'}):
            from publication_commands import CommandError
            raise CommandError('unsupported GitHub mutation requires a separately reviewed workflow')
    return []


def operations_for(command: str) -> list[str]:
    from publication_commands import CommandError
    operations: list[str] = []
    for segment in _segments(command):
        effective = _unwrap(segment)
        if effective and any('$' in word or '`' in word or '\0' in word for word in effective[:1]):
            raise CommandError('dynamic executable cannot be classified')
        if effective and Path(effective[0]).name in {'git', 'gh'} and any('$' in word or '`' in word or '\0' in word for word in effective[1:3]):
            raise CommandError('dynamic Git/GitHub subcommand cannot be classified')
        if effective and Path(effective[0]).name in {'bash', 'sh', 'zsh'} and '<<' in command:
            raise CommandError('shell heredoc execution requires an inspected standalone command')
        for operation in _direct_operations(segment):
            if operation not in operations:
                operations.append(operation)
    return operations


def operation_for(command: str):
    operations = operations_for(command)
    return operations[0] if operations else None


def commit_safety(cwd: Path, command: str) -> dict:
    """Scan actual commit messages and staged blobs; exempt only final author email metadata."""
    from content_safety import scan_payload
    from publication_authority import PublicationError, git
    from publication_commands import shell_commands
    commands = shell_commands(command)
    if len(commands) != 1 or commands[0][:2] != ["git", "commit"]:
        raise PublicationError("commit must be standalone without context-changing wrappers")
    args = commands[0][2:]
    if any('$' in word or '`' in word or '\0' in word for word in args):
        raise PublicationError("commit message/file must be literal without shell expansion")
    # Alternate index/worktree environment can change what Git commits.
    if any(os.environ.get(key) for key in ['GIT_INDEX_FILE', 'GIT_DIR', 'GIT_WORK_TREE']):
        raise PublicationError("alternate Git commit environment unsupported")
    messages = []
    i = 0
    while i < len(args):
        word = args[i]
        if word in {'-m', '--message', '-F', '--file'}:
            if i + 1 >= len(args):
                raise PublicationError("commit message value missing")
            value = args[i + 1]
            if word in {'-F', '--file'}:
                if value == '-':
                    raise PublicationError("stdin commit message cannot be inspected")
                value = (cwd / value).read_text()
            messages.append(value)
            i += 2
        elif word.startswith('--message=') or word.startswith('-m') and len(word) > 2:
            messages.append(word.split('=', 1)[1] if word.startswith('--message=') else word[2:])
            i += 1
        elif word in {'--allow-empty', '--allow-empty-message', '--no-verify', '--signoff', '-s', '--quiet', '-q'}:
            i += 1
        else:
            # -a, --only, --amend, re-use/editor messages and path selection change the candidate.
            raise PublicationError("unsupported commit option requires an explicit inspected staged commit")
    if not messages:
        raise PublicationError("explicit commit message required")
    message = '\n\n'.join(messages)
    original = scan_payload(message, sink='git_commit')
    if any(item.type == 'SECRET' and item.action == 'BLOCK' for item in original):
        return {'decision': 'BLOCK', 'reason_codes': ['SECRET']}
    blocks = message.rstrip().split('\n\n')
    trailer = re.compile(r'^(Co-Authored-By: [^<>\r\n]+ <)([A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})(>)$', re.IGNORECASE)
    if len(blocks) > 1 and all(trailer.fullmatch(line) for line in blocks[-1].splitlines()):
        blocks[-1] = '\n'.join(trailer.sub(r'\1git-email-metadata\3', line) for line in blocks[-1].splitlines())
        message = '\n\n'.join(blocks)
    safety = safe_emit(sink='git_commit', payload={'message': message})
    if safety['decision'] == 'BLOCK':
        return safety
    root = Path(git(cwd, 'rev-parse', '--show-toplevel'))
    staged = subprocess.run(['git', 'diff', '--cached', '--name-only', '-z', '--diff-filter=ACMR'], cwd=root,
                            capture_output=True, timeout=10, check=False)
    if staged.returncode:
        raise PublicationError("staged file list unavailable")
    for name in staged.stdout.split(b'\0'):
        if not name:
            continue
        blob = subprocess.run(['git', 'show', ':' + os.fsdecode(name)], cwd=root, capture_output=True, timeout=10, check=False)
        if blob.returncode or len(blob.stdout) > 8 * 1024 * 1024:
            raise PublicationError("staged blob unavailable or too large")
        result = safe_emit(sink='git_commit', payload={'staged_blob': blob.stdout.decode('utf-8', errors='replace')})
        if result['decision'] == 'BLOCK':
            return result
    return safety


def deny_hook_input(runtime: str, reason: str) -> int:
    """Return the runtime's normal deny envelope without echoing input data."""
    if runtime == "claude-code":
        result = {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "AIPS blocked: invalid hook input (" + reason + ")",
        }}
    else:
        result = {"decision": "deny", "reason": "AIPS blocked: invalid hook input (" + reason + ")"}
    print(json.dumps(result))
    return 0


def hook(runtime: str) -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.warning("Hook input could not be parsed as JSON")
        return deny_hook_input(runtime, "invalid_json")
    if not isinstance(payload, dict):
        logger.warning("Hook input must be a JSON object")
        return deny_hook_input(runtime, "invalid_payload")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict) and not isinstance(payload.get("aips_runtime_action"), dict):
        logger.warning("Hook input is missing a valid tool_input object")
        return deny_hook_input(runtime, "missing_tool_input")
    if tool_input is not None and not isinstance(tool_input, dict):
        logger.warning("Hook tool_input must be a JSON object")
        return deny_hook_input(runtime, "invalid_tool_input")
    command_value = (tool_input or {}).get("command", "")
    if not isinstance(command_value, str):
        logger.warning("Hook command must be a string")
        return deny_hook_input(runtime, "invalid_command")
    command = command_value
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
                    from datetime import datetime

                    from governance_audit import append_event
                    append_event(Path(ledger), {
                        "event_type": event.get("event_type", "RUNTIME_ACTION_BLOCKED"),
                        "occurred_at": datetime.now(UTC).isoformat(),
                        "actor": {"type": "runtime", "id": runtime},
                        "authority": {"source": "runtime_policy", "approval_id": None},
                        "binding": {"proposal_fingerprint": event.get("policy_digest"),
                                    "approval_scope_fingerprint": None, "candidate_commit": None,
                                    "branch": None, "operation": "external_data_egress",
                                    "result": decision.get("decision"), "files": [], "boundaries": [],
                                    "evidence_digests": [event.get("action_digest")] if event.get("action_digest") else []},
                        "metadata": {"correlation_id": None, "notes": "Runtime policy decision; action payload omitted."},
                    })
                except Exception as exc:
                    logger.exception("Required governance audit append failed: %s", type(exc).__name__)
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
        logger.exception("Runtime policy evaluation failed closed: %s", type(exc).__name__)
        reason = "AIPS runtime policy BLOCKED: policy evaluation failed (" + type(exc).__name__ + ")"
        if runtime == "claude-code":
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))
        else:
            print(json.dumps({"decision": "deny", "reason": reason}))
        return 0
    try:
        operations = operations_for(command)
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, ImportError, subprocess.TimeoutExpired):
        return deny_hook_input(runtime, "unsupported_shell_syntax")
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
                "gh_pr_merge": "github_pr",
                "gh_release_create": "release_notes",
            }[operation]
            try:
                safety = commit_safety(cwd, command) if operation == 'git_commit' else safe_emit(sink=sink, payload={"command": command})
            except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, ImportError, subprocess.TimeoutExpired):
                return deny_hook_input(runtime, "content_candidate_unavailable")
            if safety["decision"] == "BLOCK":
                reason = "content safety blocked " + operation
                if runtime == "claude-code":
                    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "AIPS blocked: " + reason}}))
                else:
                    print(json.dumps({"decision": "deny", "reason": "AIPS blocked: " + reason}))
                return 0
    ok = False
    reason = "no active AIPS Approval Record"
    merge_confirmation = None
    approval_operations = [operation for operation in operations if operation in PROTECTED]
    if not approval_operations:
        ok = True
        reason = "content safety passed; no publish approval required"
    else:
        try:
            if len(approval_operations) != 1:
                raise ValueError('one protected publication operation per invocation required')
            from publication_authority import (
                PublicationError,
                publication_mode,
                validate_personal_action,
            )
            mode = publication_mode()
            if mode == 'personal':
                from publication_commands import shell_commands
                parsed = shell_commands(command)
                if len(parsed) != 1 or len(approval_operations) != 1:
                    raise PublicationError('one standalone publication operation required')
                publication = validate_personal_action(cwd, approval_operations[0], parsed[0])
                if approval_operations[0] == 'gh_pr_merge':
                    merge_confirmation = publication.get('merge_confirmation')
                    if not merge_confirmation:
                        raise PublicationError('merge confirmation binding unavailable')
                    names = ', '.join(merge_confirmation['required_checks']) or 'none reported'
                    reason = (
                        f"Confirm PR merge #{merge_confirmation['pr_number']} in {publication['github_repo']} "
                        f"into {merge_confirmation['base_branch']} (base SHA {merge_confirmation['base_sha']})? "
                        f"Head SHA: {merge_confirmation['head_sha']}. Required checks: {names}. "
                        "GitHub pins the head SHA at merge; the base SHA is a pre-execution observation."
                    )
                else:
                    reason = 'personal publication checks passed'
                ok = True
            else:
                path = approval_path(cwd)
                if path and not path.exists():
                    reason = "selected approval pointer does not exist; no fallback to a different scope"
                elif path:
                    valid, reason, _ = verify_record(path, approval_operations[0], cwd, command=command, consume=True)
                    ok = valid
        except (OSError, ValueError, TypeError, KeyError, AttributeError, ImportError, yaml.YAMLError, subprocess.TimeoutExpired) as exc:
            logger.exception("Approval verification failed closed: %s", type(exc).__name__)
            reason = "publication authorization failed (" + type(exc).__name__ + ")"

    if runtime == "claude-code":
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask" if ok and merge_confirmation else "allow" if ok else "deny",
            "permissionDecisionReason": "AIPS " + reason if ok else "AIPS blocked protected publication: " + reason,
        }}))
    else:
        result = {"decision": "allow" if ok else "deny"}
        if ok and merge_confirmation:
            result['systemMessage'] = 'AIPS per-merge confirmation: ' + reason
        if not ok:
            result["reason"] = "AIPS blocked protected publication: " + reason
        print(json.dumps(result))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="AIPS deterministic approval binding and publication guard")
    sub = p.add_subparsers(dest="command", required=True)
    fp = sub.add_parser("fingerprint")
    fp.add_argument("--file", required=True)
    vr = sub.add_parser("verify", aliases=["status"])
    vr.add_argument("--approval", required=True)
    vr.add_argument("--operation", required=True, choices=sorted(PROTECTED))
    vr.add_argument("--cwd", default=os.getcwd())
    vr.add_argument("--no-actual", action="store_true")
    vr.add_argument("--command", dest="actual_command", help="Exact standalone publication command; verification never consumes")
    pp = sub.add_parser("propose")
    pp.add_argument("--operation", required=True, choices=sorted(PROTECTED))
    pp.add_argument("--cwd", default=os.getcwd())
    pp.add_argument("--base", required=True)
    pp.add_argument("--command", dest="actual_command", required=True)
    hk = sub.add_parser("hook")
    hk.add_argument("--runtime", required=True, choices=["claude-code", "gemini-cli"])
    a = p.parse_args()
    if a.command == "fingerprint":
        path = Path(a.file)
        value = yaml.safe_load(path.read_text(encoding="utf-8")) if path.suffix in {".yaml", ".yml"} else json.loads(path.read_text(encoding="utf-8"))
        print(fingerprint(value))
        return 0
    if a.command in {"verify", "status"}:
        ok, reason, _ = verify_record(Path(a.approval), a.operation, Path(a.cwd), not a.no_actual, command=a.actual_command)
        print(json.dumps({"status": "VALID" if ok else "APPROVAL_STALE", "reason": reason}))
        return 0 if ok else 2
    if a.command == "propose":
        from publication_authority import proposal
        from publication_commands import shell_commands
        try:
            commands = shell_commands(a.actual_command)
            if len(commands) != 1:
                raise ValueError("one standalone command required")
            print(yaml.safe_dump(proposal(Path(a.cwd), a.operation, commands[0], a.base), sort_keys=False))
            return 0
        except (OSError, ValueError, TypeError, KeyError, AttributeError, ImportError, subprocess.TimeoutExpired) as exc:
            print(json.dumps({'status': 'BLOCKED', 'reason': type(exc).__name__}))
            return 2
    return hook(a.runtime)


if __name__ == "__main__":
    raise SystemExit(main())
