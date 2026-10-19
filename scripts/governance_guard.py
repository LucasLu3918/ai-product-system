#!/usr/bin/env python3
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import logging
import os
import re
import shlex
import subprocess
import sys
import uuid
from datetime import UTC
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from publication_authority import PublicationError

try:
    from content_safety import safe_emit
except ModuleNotFoundError:  # imported as a repository module
    from scripts.content_safety import safe_emit

PROTECTED = ("git_push", "git_tag", "gh_pr_create", "gh_pr_merge", "gh_release_create")
CONTENT_SENSITIVE = ("git_commit", *PROTECTED)
logger = logging.getLogger(__name__)
READ_ONLY_GIT_ENV = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
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
            diagnostic = exc.diagnostic()
            return False, diagnostic['reason_code'] + ': ' + diagnostic['detail'] + ' ' + diagnostic['next_step'], doc
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
                raise CommandError('env split-string execution requires a standalone command', 'UNSUPPORTED_WRAPPER')
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


def _dynamic_word(token: str) -> bool:
    return "$" in token or "`" in token or "\0" in token


def _after_global_options(tokens: list[str], with_value: set[str]) -> list[str]:
    """Locate a CLI verb after its global options without accepting dynamic context."""
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if not token.startswith("-") or token == "-":
            return tokens[index:]
        if _dynamic_word(token):
            from publication_commands import CommandError
            raise CommandError("dynamic CLI global option cannot be classified", "DYNAMIC_CLI_OPTION")
        option = token.split("=", 1)[0]
        if option in with_value:
            if "=" in token:
                index += 1
                continue
            if index + 1 >= len(tokens):
                from publication_commands import CommandError
                raise CommandError("CLI global option is missing its value")
            if _dynamic_word(tokens[index + 1]):
                from publication_commands import CommandError
                raise CommandError("dynamic CLI global option value cannot bind a stable target", "DYNAMIC_CLI_OPTION")
            index += 2
            continue
        index += 1
    return []


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
        raise CommandError('interpreter file/stdin execution cannot be classified; use literal standalone commands', 'UNSUPPORTED_INTERPRETER')

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
            raise CommandError('Git remote-ref plumbing is unsupported; use the exact signed push workflow', 'UNSUPPORTED_GIT_PLUMBING')
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
            raise CommandError('unknown Git verb or alias cannot be classified', 'UNKNOWN_GIT_COMMAND')
        return []

    if exe == "gh":
        args = _strip_options(tokens[1:], GH_GLOBAL_WITH_VALUE)
        if args and args[0] == 'api':
            from publication_commands import CommandError
            # API writes may change Git refs without invoking git push/gh pr merge.
            if '--method' not in args or args.count('--method') != 1 or args[args.index('--method') + 1:args.index('--method') + 2] != ['GET']:
                raise CommandError('unbound GitHub API mutation is unsupported', 'UNBOUND_GITHUB_API_MUTATION')
            if any(x.startswith(('-f', '-F', '--field', '--raw-field', '--input', '-X', '--method=')) for x in args):
                raise CommandError('ambiguous GitHub API request is unsupported', 'AMBIGUOUS_GITHUB_API_REQUEST')
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
            raise CommandError('unsupported GitHub mutation requires a separately reviewed workflow', 'UNSUPPORTED_GITHUB_MUTATION')
    return []


def operations_for(command: str) -> list[str]:
    from publication_commands import CommandError
    operations: list[str] = []
    for segment in _segments(command):
        effective = _unwrap(segment)
        if effective and _dynamic_word(effective[0]):
            raise CommandError('dynamic executable cannot be classified', 'DYNAMIC_EXECUTABLE')
        if effective and Path(effective[0]).name == 'git':
            args = _after_global_options(effective[1:], GIT_GLOBAL_WITH_VALUE)
            if args and _dynamic_word(args[0]):
                raise CommandError('dynamic Git subcommand cannot be classified', 'DYNAMIC_SUBCOMMAND')
        if effective and Path(effective[0]).name == 'gh':
            args = _after_global_options(effective[1:], GH_GLOBAL_WITH_VALUE)
            if any(_dynamic_word(word) for word in args[:2]):
                raise CommandError('dynamic GitHub CLI command cannot be classified', 'DYNAMIC_SUBCOMMAND')
        if effective and Path(effective[0]).name in {'bash', 'sh', 'zsh'} and '<<' in command:
            raise CommandError('shell heredoc execution requires an inspected standalone command', 'UNSUPPORTED_HEREDOC')
        for operation in _direct_operations(segment):
            if operation not in operations:
                operations.append(operation)
    return operations


def operation_for(command: str):
    operations = operations_for(command)
    return operations[0] if operations else None


def commit_safety(cwd: Path, command: str) -> dict:
    """Scan actual commit messages and staged blobs; exempt only final author email metadata."""
    from content_safety import added_line_numbers_from_diff, scan_payload
    from publication_authority import PublicationError
    from publication_commands import shell_commands
    commands = shell_commands(command)
    if len(commands) != 1 or commands[0][:2] != ["git", "commit"]:
        raise PublicationError("commit must be standalone without context-changing wrappers", reason_code='COMMAND_FORM_UNSUPPORTED')
    args = commands[0][2:]
    if any('$' in word or '`' in word or '\0' in word for word in args):
        raise PublicationError("commit message/file must be literal without shell expansion", reason_code='PUBLICATION_INPUT_UNBOUND')
    # Alternate index/worktree environment can change what Git commits.
    if any(os.environ.get(key) for key in ['GIT_INDEX_FILE', 'GIT_DIR', 'GIT_WORK_TREE']):
        raise PublicationError("alternate Git commit environment unsupported", reason_code='ALTERNATE_GIT_ENVIRONMENT')
    messages = []
    i = 0
    while i < len(args):
        word = args[i]
        if word in {'-m', '--message', '-F', '--file'}:
            if i + 1 >= len(args):
                raise PublicationError("commit message value missing", reason_code='PUBLICATION_OPTION_INVALID', phase='commit_message')
            value = args[i + 1]
            if word in {'-F', '--file'}:
                if value == '-':
                    raise PublicationError("stdin commit message cannot be inspected", reason_code='CONTENT_INSPECTION_UNAVAILABLE')
                try:
                    value = (cwd / value).read_text(encoding='utf-8')
                except (OSError, UnicodeError) as exc:
                    raise PublicationError("commit message file unavailable", reason_code='MESSAGE_FILE_UNAVAILABLE',
                                           context={'error_class': type(exc).__name__}, phase='commit_message') from exc
            messages.append(value)
            i += 2
        elif word.startswith('--message=') or word.startswith('-m') and len(word) > 2:
            messages.append(word.split('=', 1)[1] if word.startswith('--message=') else word[2:])
            i += 1
        elif word in {'--allow-empty', '--allow-empty-message', '--no-verify', '--signoff', '-s', '--quiet', '-q'}:
            i += 1
        else:
            # -a, --only, --amend, re-use/editor messages and path selection change the candidate.
            raise PublicationError("unsupported commit option requires an explicit inspected staged commit", reason_code='COMMAND_FORM_UNSUPPORTED')
    if not messages:
        raise PublicationError("explicit commit message required", reason_code='PUBLICATION_INPUT_UNBOUND')
    message = '\n\n'.join(messages)
    try:
        original = scan_payload(message, sink='git_commit', context={'source_path': '<commit-message>'}, strict=True)
    except Exception as exc:  # Any scanner error blocks the candidate.
        reason_code = getattr(exc, 'reason_code', 'CONTENT_SCANNER_FAILED')
        raise PublicationError("commit message scanner failed", reason_code,
                               context={'error_class': type(exc).__name__}, phase='commit_message') from exc
    if any(item.type == 'SECRET' and item.action == 'BLOCK' for item in original):
        return _commit_block([item.as_dict() for item in original], 'commit_message', None)
    blocks = message.rstrip().split('\n\n')
    trailer = re.compile(r'^(Co-Authored-By: [^<>\r\n]+ <)([A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})(>)$', re.IGNORECASE)
    if len(blocks) > 1 and all(trailer.fullmatch(line) for line in blocks[-1].splitlines()):
        blocks[-1] = '\n'.join(trailer.sub(r'\1git-email-metadata\3', line) for line in blocks[-1].splitlines())
        message = '\n\n'.join(blocks)
    try:
        safety = safe_emit(sink='git_commit', payload={'message': message},
                           context={'source_path': '<commit-message>'}, strict=True)
    except Exception as exc:  # Scanner failures must fail closed with a safe class.
        reason_code = getattr(exc, 'reason_code', 'CONTENT_SCANNER_FAILED')
        raise PublicationError("commit message scanner failed", reason_code,
                               context={'error_class': type(exc).__name__}, phase='commit_message') from exc
    if safety['decision'] in {'BLOCK', 'REVIEW'}:
        return _commit_block(safety['findings'], 'commit_message', None)
    try:
        root_proc = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=cwd, env=READ_ONLY_GIT_ENV,
                                   capture_output=True, text=True, timeout=10, check=False)
        if root_proc.returncode:
            raise OSError('repository root unavailable')
        root = Path(root_proc.stdout.strip())
        staged = subprocess.run(['git', 'diff', '--cached', '--name-only', '-z', '--diff-filter=ACMR'], cwd=root,
                                env=READ_ONLY_GIT_ENV, capture_output=True, timeout=10, check=False)
        index = subprocess.run(['git', 'ls-files', '--stage', '-z'], cwd=root, env=READ_ONLY_GIT_ENV,
                               capture_output=True, timeout=10, check=False)
    except subprocess.TimeoutExpired as exc:
        raise PublicationError("staged index inspection timed out", "STAGED_INDEX_UNAVAILABLE",
                               context={'error_class': type(exc).__name__}, phase='staged_index') from exc
    except OSError as exc:
        raise PublicationError("repository index unavailable", "STAGED_INDEX_UNAVAILABLE",
                               context={'error_class': type(exc).__name__}, phase='staged_index') from exc
    if staged.returncode:
        raise PublicationError("staged file list unavailable", "STAGED_INDEX_UNAVAILABLE", phase='staged_index')
    if index.returncode:
        raise PublicationError("staged index entries unavailable", "STAGED_INDEX_UNAVAILABLE", phase='staged_index')
    index_modes: dict[bytes, set[bytes]] = {}
    for record in index.stdout.split(b'\0'):
        if not record:
            continue
        header, separator, index_path = record.partition(b'\t')
        fields = header.split()
        if separator and len(fields) == 3:
            index_modes.setdefault(index_path, set()).add(fields[0])
    for name in staged.stdout.split(b'\0'):
        if not name:
            continue
        if b'160000' in index_modes.get(name, set()):
            raise PublicationError("staged submodule content cannot be inspected", "STAGED_CONTENT_UNSUPPORTED_BINARY",
                                   phase='staged_blob')
        relative = os.fsdecode(name)
        suffix = PurePosixPath(relative).suffix.lower()
        font_suffixes = {'.ttf', '.otf', '.woff', '.woff2'}
        from media_metadata import MEDIA_SUFFIXES
        media_suffixes = MEDIA_SUFFIXES
        try:
            size = subprocess.run(['git', 'cat-file', '-s', ':' + relative], cwd=root, env=READ_ONLY_GIT_ENV,
                                  capture_output=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PublicationError("staged blob size unavailable", "STAGED_BLOB_UNAVAILABLE",
                                   context={'error_class': type(exc).__name__}, phase='staged_blob') from exc
        if size.returncode:
            raise PublicationError("staged blob size unavailable", "STAGED_BLOB_UNAVAILABLE", phase='staged_blob')
        try:
            blob_size = int(size.stdout.strip())
        except ValueError as exc:
            raise PublicationError("staged blob size invalid", "STAGED_BLOB_UNAVAILABLE", phase='staged_blob') from exc
        limit = 8 * 1024 * 1024
        if blob_size > limit:
            reason = "M4A_TOO_LARGE" if suffix == '.m4a' else (
                "STAGED_FONT_RESOURCE_LIMIT" if suffix in font_suffixes else
                "STAGED_MEDIA_RESOURCE_LIMIT" if suffix in media_suffixes else
                "STAGED_CONTENT_TOO_LARGE"
            )
            raise PublicationError("staged blob exceeds inspection limit", reason,
                                   context={'file': relative, 'format': suffix[1:]}, phase='staged_blob')
        try:
            blob = subprocess.run(['git', 'show', ':' + relative], cwd=root, env=READ_ONLY_GIT_ENV,
                                  capture_output=True, timeout=10, check=False)
        except subprocess.TimeoutExpired as exc:
            raise PublicationError("staged blob inspection timed out", "STAGED_BLOB_UNAVAILABLE",
                                   context={'error_class': type(exc).__name__}, phase='staged_blob') from exc
        except OSError as exc:
            raise PublicationError("staged blob process unavailable", "STAGED_BLOB_UNAVAILABLE",
                                   context={'error_class': type(exc).__name__}, phase='staged_blob') from exc
        if blob.returncode:
            raise PublicationError("staged blob unavailable", "STAGED_BLOB_UNAVAILABLE", phase='staged_blob')
        if len(blob.stdout) > limit:
            reason = "M4A_TOO_LARGE" if suffix == '.m4a' else (
                "STAGED_FONT_RESOURCE_LIMIT" if suffix in font_suffixes else
                "STAGED_MEDIA_RESOURCE_LIMIT" if suffix in media_suffixes else
                "STAGED_CONTENT_TOO_LARGE"
            )
            raise PublicationError("staged blob exceeds inspection limit", reason,
                                   context={'file': relative, 'format': suffix[1:]}, phase='staged_blob')
        if suffix in media_suffixes | font_suffixes:
            from media_metadata import (
                MediaInspectionError,
                extract_metadata,
                media_diagnostic_code,
            )
            try:
                staged_text = extract_metadata(blob.stdout, suffix)
            except MediaInspectionError as exc:
                raw_reason = getattr(exc, 'reason_code', str(exc))
                reason = raw_reason if raw_reason.startswith('STAGED_FONT_') else (
                    'M4A_INVALID' if suffix == '.m4a' else
                    media_diagnostic_code(exc) if suffix == '.avif' else
                    'STAGED_MEDIA_INVALID'
                )
                raise PublicationError("staged media is malformed or its extension is spoofed", reason,
                                       context={'error_class': getattr(exc, 'cause_class', None) or type(exc).__name__,
                                                'file': relative, 'format': getattr(exc, 'format_name', None) or suffix[1:]},
                                       phase='font_metadata' if suffix in font_suffixes else 'media_metadata') from exc
        else:
            try:
                if b'\x00' in blob.stdout:
                    raise UnicodeError('binary NUL')
                staged_text = blob.stdout.decode('utf-8', errors='strict')
            except UnicodeError as exc:
                raise PublicationError("staged binary format is unsupported", "STAGED_CONTENT_UNSUPPORTED_BINARY",
                                       context={'error_class': type(exc).__name__}, phase='staged_blob') from exc
        try:
            diff = subprocess.run(
                ['git', '--literal-pathspecs', 'diff', '--cached', '--no-ext-diff', '--no-renames',
                 '--unified=0', '--', relative],
                cwd=root, env=READ_ONLY_GIT_ENV, capture_output=True, timeout=10, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PublicationError("staged diff unavailable for injection context", "STAGED_DIFF_UNAVAILABLE",
                                   context={'error_class': type(exc).__name__}, phase='staged_diff') from exc
        if diff.returncode:
            raise PublicationError("staged diff unavailable for injection context", "STAGED_DIFF_UNAVAILABLE",
                                   phase='staged_diff')
        changed_lines = sorted(added_line_numbers_from_diff(diff.stdout.decode('utf-8', errors='replace')))
        try:
            result = safe_emit(
                sink='git_commit', payload={'staged_blob': staged_text},
                context={'source_path': relative, 'injection_changed_lines': changed_lines}, strict=True,
            )
        except Exception as exc:  # Scanner failures fail closed.
            reason_code = getattr(exc, 'reason_code', 'CONTENT_SCANNER_FAILED')
            raise PublicationError("staged content scanner failed", reason_code,
                                   context={'error_class': type(exc).__name__}, phase='content_scan') from exc
        if result['decision'] in {'BLOCK', 'REVIEW'}:
            return _commit_block(result['findings'], 'staged_blob', relative)
    return safety


def _commit_block(findings: list[dict[str, Any]], source: str, path: str | None) -> dict[str, Any]:
    """Project scanner findings into safe, stable diagnostics with no matched values."""
    code_for = {'SECRET': 'CONTENT_SECRET_BLOCKED', 'PII': 'CONTENT_PII_BLOCKED',
                'INJECTION_SIGNAL': 'CONTENT_INJECTION_BLOCKED'}
    safe_findings = []
    for finding in findings:
        if not isinstance(finding, dict) or finding.get('action') not in {'BLOCK', 'REVIEW'}:
            continue
        reason_code = ('CONTENT_REVIEW_REQUIRED' if finding.get('action') == 'REVIEW'
                       else code_for.get(finding.get('type'), 'CONTENT_SAFETY_BLOCKED'))
        item = {'reason_code': code_for.get(finding.get('type'), 'CONTENT_SAFETY_BLOCKED'),
                'category': finding.get('type') if finding.get('type') in code_for else 'CONTENT',
                'detector': finding.get('detector') if isinstance(finding.get('detector'), str) else 'unknown',
                'source': source}
        item['reason_code'] = reason_code
        for field in ('rule_id', 'finding_fingerprint', 'confidence', 'action'):
            if field in finding and isinstance(finding[field], (str, int, float)):
                item[field] = finding[field]
        if isinstance(finding.get('line'), int) and finding['line'] > 0:
            item['line'] = finding['line']
        if path:
            relative = PurePosixPath(path)
            if (not relative.is_absolute() and '..' not in relative.parts and len(path) <= 200
                    and re.fullmatch(r'[A-Za-z0-9._/-]+', path)
                    and not re.match(r'^[A-Za-z]:', path)):
                try:
                    from content_safety import scan_payload
                    if not any(item.action == 'BLOCK' for item in scan_payload(path, sink='git_commit', strict=True)):
                        item['file'] = path
                except Exception as exc:  # noqa: BLE001 - unsafe path is omitted.
                    logger.debug("Omitting unsafe commit path after %s", type(exc).__name__)
        safe_findings.append(item)
    first = safe_findings[0] if safe_findings else {
        'reason_code': 'CONTENT_SAFETY_BLOCKED', 'category': 'CONTENT', 'detector': 'unknown', 'source': source}
    return {'decision': 'BLOCK', 'reason_code': first['reason_code'], 'phase': 'content_scan',
            'source': source, 'category': first['category'], 'diagnostic_id': str(uuid.uuid4()),
            'retryable': False, 'findings': safe_findings,
            'reason_codes': list(dict.fromkeys(item['reason_code'] for item in safe_findings))}


def _record_publication_diagnostic(diagnostic: dict[str, Any], runtime: str) -> str:
    """Append only allowlisted publication diagnostics to the opt-in existing ledger."""
    try:
        from publication_diagnostics import record_diagnostic
        status = record_diagnostic(diagnostic, runtime)
        if status == 'FAILED':
            logger.warning('Optional publication diagnostic trace failed')
        return status
    except Exception:  # noqa: BLE001 - optional audit must never change the Hook decision.
        logger.warning('Optional publication diagnostic trace failed')
        return 'FAILED'


def _hook_binding(cwd: Path, command: str, mode: str) -> dict[str, str] | None:
    try:
        from publication_commands import shell_commands
        parsed = shell_commands(command)
        if len(parsed) != 1:
            return None
        argv = parsed[0]
        target_ref = ''
        if argv[:2] == ['git', 'push']:
            args = argv[2:]
            while args and args[0].startswith('-'):
                args = args[1:]
            if len(args) == 2 and ':' in args[1]:
                target_ref = args[1].split(':', 1)[1]
        elif argv[:3] == ['gh', 'pr', 'create'] and '--base' in argv:
            target_ref = 'refs/heads/' + argv[argv.index('--base') + 1]
        if not target_ref.startswith('refs/heads/'):
            return None
        head = subprocess.run(['git', 'rev-parse', 'HEAD^{commit}'], cwd=cwd,
                              capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        from publication_authority import runtime_binding
        return runtime_binding(cwd, candidate_sha=head, target_ref=target_ref, mode=mode)
    except Exception:  # noqa: BLE001 - binding is optional evidence; never crash the Hook.
        return None


def deny_hook_input(runtime: str, reason: str, diagnostic: dict[str, Any] | None = None) -> int:
    """Return the runtime's normal deny envelope without echoing input data."""
    reason_messages = {
        "UNSUPPORTED_SHELL_SYNTAX": "AIPS cannot safely parse this shell syntax; simplify the command and retry.",
        "UNSUPPORTED_HEREDOC": "AIPS cannot safely inspect this heredoc form; use a quoted heredoc or a separate command.",
        "DYNAMIC_EXECUTABLE": "AIPS cannot verify a dynamically selected executable; use a literal command name.",
        "DYNAMIC_SUBCOMMAND": "AIPS cannot classify a dynamically selected Git/GitHub command; use a literal subcommand.",
        "DYNAMIC_CLI_OPTION": "AIPS cannot verify a dynamically selected Git/GitHub context option; use a literal option value.",
        "UNSUPPORTED_WRAPPER": "AIPS cannot inspect this Shell wrapper safely; use a literal standalone command.",
        "UNSUPPORTED_INTERPRETER": "AIPS cannot inspect commands read from a Shell file or stdin; use an inspected literal command.",
        "UNSUPPORTED_GIT_PLUMBING": "AIPS blocks this low-level Git publication path; use the exact approved push workflow.",
        "UNKNOWN_GIT_COMMAND": "AIPS cannot classify this Git verb or alias; use a supported built-in command.",
        "UNBOUND_GITHUB_API_MUTATION": "AIPS cannot bind this GitHub API write to an approved operation; use a supported explicit workflow.",
        "AMBIGUOUS_GITHUB_API_REQUEST": "AIPS cannot determine whether this GitHub API request writes data; use an explicit supported request.",
        "UNSUPPORTED_GITHUB_MUTATION": "AIPS requires a separately reviewed workflow for this GitHub mutation.",
        "CONTENT_CANDIDATE_UNAVAILABLE": "AIPS could not inspect the publication content; retry after resolving the local inspection error.",
        "STAGED_CONTENT_UNAVAILABLE": "AIPS could not read a staged file for content inspection; check the index and restage the candidate.",
        "STAGED_INDEX_UNAVAILABLE": "AIPS could not read the staged index; repair the local Git index and rerun the safety diagnosis.",
        "STAGED_BLOB_UNAVAILABLE": "AIPS could not read a staged blob; check the staged file and Git object database, then retry.",
        "MESSAGE_FILE_UNAVAILABLE": "AIPS could not read the commit message file; check the file encoding and access, then retry.",
        "STAGED_CONTENT_TOO_LARGE": "AIPS cannot inspect a staged file above the configured size limit; split or remove that file.",
        "STAGED_CONTENT_UNSUPPORTED_BINARY": "AIPS cannot safely inspect this binary format; convert it to a supported format or remove it from the commit.",
        "STAGED_MEDIA_INVALID": "AIPS could not verify this media file; repair the file or use a supported format with matching contents.",
        "STAGED_FONT_INVALID": "AIPS could not safely parse this font; repair or replace the font file.",
        "STAGED_FONT_FORMAT_MISMATCH": "AIPS found a mismatch between the font extension and its signature; correct the extension or file.",
        "STAGED_FONT_INSPECTOR_UNAVAILABLE": "AIPS font inspection requires fontTools; install the declared dependency.",
        "STAGED_FONT_BROTLI_UNAVAILABLE": "AIPS WOFF2 inspection requires Brotli; install the declared dependency.",
        "STAGED_FONT_RESOURCE_LIMIT": "AIPS font inspection exceeded a bounded resource limit; reduce or replace the font.",
        "CONTENT_SCANNER_FAILED": "AIPS could not complete the content scanner; resolve the local scanner error and retry without bypassing the guard.",
        "CONTENT_SECRET_BLOCKED": "AIPS blocked a possible secret in commit content; remove or rotate it, then scan again.",
        "CONTENT_PII_BLOCKED": "AIPS blocked personal information in commit content; remove it or use an approved redacted value, then scan again.",
        "CONTENT_INJECTION_BLOCKED": "AIPS blocked an instruction-like signal in commit content; revise the content and scan again.",
        "CONTENT_SAFETY_BLOCKED": "AIPS blocked commit content; inspect the safe finding categories and rescan after correction.",
        "M4A_TOO_LARGE": "AIPS cannot publish M4A files above 8 MiB; use Git LFS or external asset storage and keep the repository pointer/documentation here.",
        "M4A_INVALID": "AIPS could not verify this .m4a as a valid M4A audio file; use a correctly encoded file with matching extension.",
        "CONTENT_INSPECTION_UNAVAILABLE": "AIPS content inspection could not complete; check the local scanner and Git state.",
    }
    detail = reason_messages.get(reason, "AIPS blocked this command during a required safety check.")
    detail += " [" + reason + "]"
    if diagnostic is None:
        diagnostic = PublicationError("", reason).diagnostic()
    trace_status = _record_publication_diagnostic(diagnostic, runtime)
    safe_fields = {key: diagnostic.get(key) for key in
                   ("diagnostic_id", "reason_code", "detail_code", "phase", "category", "detail", "detail_zh",
                    "blocking_rule", "blocking_rule_id", "source", "retryable", "recovery_mode", "next_step", "next_step_zh",
                    "findings")}
    if diagnostic.get('binding'):
        safe_fields['binding'] = diagnostic['binding']
    safe_fields.update({"authorization_status": "DENIED", "execution_status": "NOT_EXECUTED",
                        "authorized": False, "executed": False, "trace_status": trace_status})
    detail += " [phase=" + str(safe_fields.get("phase") or "unknown") + \
              "; diagnostic_id=" + str(safe_fields.get("diagnostic_id") or "unavailable") + "]"
    context = "AIPS diagnostic: " + json.dumps(safe_fields, ensure_ascii=False, separators=(",", ":"))
    if runtime == "claude-code":
        result = {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": detail,
            "additionalContext": context,
        }}
    else:
        result = {"decision": "deny", "reason": detail, "diagnostic": safe_fields}
    print(json.dumps(result))
    return 0


def retryable_doctor_observation(cwd: Path) -> dict[str, Any]:
    """Run one bounded, read-only Doctor and keep only its safe diagnostic fields."""
    try:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/publish_preflight.py"), "doctor",
             "--project-root", str(cwd), "--format", "json"],
            cwd=cwd, capture_output=True, text=True, timeout=60, check=False,
        )
        payload = json.loads(proc.stdout) if proc.stdout else None
        if not isinstance(payload, dict):
            raise TypeError("invalid doctor output")
        diagnostics = []
        for item in payload.get("diagnostics", []):
            if not isinstance(item, dict):
                continue
            diagnostics.append({key: item.get(key) for key in
                ("reason_code", "phase", "category", "retryable", "next_step")
                if isinstance(item.get(key), (str, bool))})
        return {"status": payload.get("status") if payload.get("status") in {"READY", "BLOCKED"} else "UNKNOWN",
                "required_check_state": ((payload.get("policy") or {}).get("required_check_state")
                    if isinstance(payload.get("policy"), dict) else None),
                "diagnostics": diagnostics[:8], "read_only": payload.get("read_only") is True,
                "authorized": False, "executed": False, "api_write_performed": False}
    except (OSError, ValueError, TypeError, subprocess.TimeoutExpired):
        return {"status": "UNAVAILABLE", "diagnostics": [], "read_only": True,
                "authorized": False, "executed": False, "api_write_performed": False}


def hook(runtime: str) -> int:
    mode = 'unknown'
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.warning("Hook input could not be parsed as JSON")
        return deny_hook_input(runtime, "invalid_json")
    if not isinstance(payload, dict):
        logger.warning("Hook input must be a JSON object")
        return deny_hook_input(runtime, "invalid_payload")
    if payload.get("hook_event_name") == "PostToolUseFailure":
        if runtime != "claude-code":
            print("{}")
            return 0
        error = payload.get("error")
        error_text = error[:20000] if isinstance(error, str) else ""
        exit_match = re.search(r"\bexit(?:ed)?\s+(?:with\s+)?code\s*[:=]?\s*(\d+)\b", error_text, re.IGNORECASE)
        exit_code = int(exit_match.group(1)) if exit_match and int(exit_match.group(1)) <= 255 else None
        folded = error_text.casefold()
        category = ("NETWORK_ERROR" if any(word in folded for word in ("timed out", "timeout", "connection refused", "network is unreachable"))
                    else "AUTHENTICATION_ERROR" if any(word in folded for word in ("authentication failed", "permission denied", "not authorized"))
                    else "NATIVE_TOOL_ERROR")
        if payload.get("tool_name") != "Bash":
            print("{}")
            return 0
        safe = {"status": "FAILED", "execution_status": "FAILED", "phase": "native_tool_execution", "tool": "Bash",
                "error_category": category, "observed": True, "authorized": False, "executed": True}
        if exit_code is not None:
            safe["exit_code"] = exit_code
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUseFailure",
            "additionalContext": "AIPS observed a native Bash tool failure after execution started: " +
                json.dumps(safe, ensure_ascii=False, separators=(",", ":")) +
                ". The host error text is omitted; inspect the native tool result and correct the command before retrying."
        }}))
        return 0
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
                reason = ("AIPS runtime policy " + str(decision.get("decision")) + " ["
                          + str(decision.get("reason_code")) + "; trace=" + str(decision.get("trace_id")) + "]: "
                          + str((decision.get("recovery") or {}).get("action") or "請檢查授權與安全限制。"))
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
    except Exception as exc:
        from publication_commands import CommandError
        if isinstance(exc, CommandError):
            if exc.reason_code == "UNSUPPORTED_SHELL_SYNTAX":
                return deny_hook_input(runtime, "COMMAND_FORM_UNSUPPORTED",
                                       PublicationError("", "COMMAND_FORM_UNSUPPORTED",
                                                        detail_code=exc.detail_code).diagnostic())
            return deny_hook_input(runtime, exc.reason_code)
        if isinstance(exc, (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, ImportError, subprocess.TimeoutExpired)):
            return deny_hook_input(runtime, "UNSUPPORTED_SHELL_SYNTAX")
        raise
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
            except PublicationError as exc:
                return deny_hook_input(runtime, exc.reason_code, exc.diagnostic())
            except OSError as exc:
                reason = "STAGED_CONTENT_UNAVAILABLE" if exc.errno in {errno.ENOENT, errno.EACCES, errno.EPERM} else "CONTENT_INSPECTION_UNAVAILABLE"
                return deny_hook_input(runtime, reason)
            except (ValueError, TypeError, KeyError, IndexError, AttributeError, ImportError, subprocess.TimeoutExpired):
                return deny_hook_input(runtime, "CONTENT_INSPECTION_UNAVAILABLE")
            if safety["decision"] == "BLOCK":
                reason = safety.get('reason_code') or 'CONTENT_SAFETY_BLOCKED'
                diagnostic = PublicationError('', reason, phase=safety.get('phase') or 'content_scan').diagnostic()
                diagnostic.update({key: safety[key] for key in ('diagnostic_id', 'source', 'category', 'retryable', 'findings') if key in safety})
                return deny_hook_input(runtime, reason, diagnostic)
    ok = False
    hook_diagnostic = None
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
                publication_mode,
                validate_personal_action,
            )
            mode = publication_mode()
            if mode == 'personal':
                from publication_commands import shell_commands
                parsed = shell_commands(command)
                if len(parsed) != 1 or len(approval_operations) != 1:
                    raise PublicationError('one standalone publication operation required', reason_code='COMMAND_FORM_UNSUPPORTED')
                publication = validate_personal_action(cwd, approval_operations[0], parsed[0])
                if approval_operations[0] == 'gh_pr_merge':
                    merge_confirmation = publication.get('merge_confirmation')
                    if not merge_confirmation:
                        raise PublicationError('merge confirmation binding unavailable', reason_code='AUTHORITY_VALIDATION_MISSING')
                    names = ', '.join(merge_confirmation['required_checks']) or 'none reported'
                    reason = (
                        f"GitHub will enable auto-merge for PR #{merge_confirmation['pr_number']} in {publication['github_repo']} "
                        if merge_confirmation.get('auto_merge') else
                        f"Confirm PR merge #{merge_confirmation['pr_number']} in {publication['github_repo']} "
                    ) + (
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
        except Exception as exc:  # noqa: BLE001 - unexpected hook failures must deny with a redacted diagnostic.
            logger.warning("Approval verification failed closed: %s", type(exc).__name__)
            if isinstance(exc, ValueError) and hasattr(exc, 'diagnostic'):
                diagnostic = exc.diagnostic()
            else:
                diagnostic = PublicationError(
                    'unclassified publication authorization failure', 'INTERNAL_DIAGNOSTIC_GAP',
                    context={'error_class': type(exc).__name__}, phase='hook_authorization').diagnostic()
            binding = _hook_binding(cwd, command, mode)
            if binding:
                diagnostic['binding'] = binding
            hook_diagnostic = diagnostic
            if (runtime == "claude-code" and diagnostic.get("retryable") is True and
                    diagnostic.get("category") in {"NETWORK", "RATE_LIMITED", "GITHUB_SERVER_ERROR"}):
                hook_diagnostic["doctor_observation"] = retryable_doctor_observation(cwd)
            reason = diagnostic['reason_code'] + ': ' + diagnostic['detail'] + ' ' + diagnostic['next_step']

    if hook_diagnostic:
        hook_diagnostic['trace_status'] = _record_publication_diagnostic(hook_diagnostic, runtime)
    success_binding = _hook_binding(cwd, command, mode) if ok and approval_operations else None
    if runtime == "claude-code":
        claude_auto_merge = bool(merge_confirmation and merge_confirmation.get('auto_merge'))
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask" if ok and merge_confirmation and not claude_auto_merge else "allow" if ok else "deny",
            "permissionDecisionReason": ("AIPS " + reason if ok else "AIPS blocked protected publication: " + reason) +
                (" [phase=" + str(hook_diagnostic.get("phase")) + "; diagnostic_id=" +
                 str(hook_diagnostic.get("diagnostic_id")) + "]" if hook_diagnostic else ""),
            **({"additionalContext": "AIPS diagnostic: " + json.dumps({key: hook_diagnostic.get(key) for key in
                ("diagnostic_id", "reason_code", "phase", "category", "error_class", "detail", "detail_zh",
                 "blocking_rule", "blocking_rule_id", "source", "retryable",
                 "recovery_mode", "next_step", "next_step_zh", "doctor_observation",
                 "binding", "trace_status")}, ensure_ascii=False, separators=(",", ":")) +
                "; authorization_status=DENIED; execution_status=NOT_EXECUTED"} if hook_diagnostic else
               {"additionalContext": "AIPS publication: " + json.dumps({
                   'status': 'AUTHORIZED', 'authorized': True,
                   'host_decision': 'NOT_EVALUATED', 'execution_status': 'NOT_EXECUTED',
                   'executed': False, 'binding': success_binding,
               }, ensure_ascii=False, separators=(",", ":"))} if ok and approval_operations else {}),
        }}))
    else:
        result = {"decision": "allow" if ok else "deny"}
        if ok and approval_operations:
            result['publication'] = {
                'status': 'AUTHORIZED', 'authorized': True,
                'host_decision': 'NOT_EVALUATED', 'execution_status': 'NOT_EXECUTED',
                'executed': False, 'binding': success_binding,
            }
        if ok and merge_confirmation:
            result['systemMessage'] = 'AIPS per-merge confirmation: ' + reason
        if not ok:
            result["reason"] = "AIPS blocked protected publication: " + reason
            if hook_diagnostic:
                result["diagnostic"] = {key: hook_diagnostic.get(key) for key in
                    ("diagnostic_id", "reason_code", "phase", "category", "detail", "retryable",
                     "recovery_mode", "next_step")}
                result["diagnostic"].update(authorized=False, executed=False)
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
