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
import signal
import subprocess
import sys
import time
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
try:
    from protected_paths import REASON_CODE as PROTECTED_PATH_REASON
    from protected_paths import (
        bash_command_writes_protected,
        file_tool_write_is_protected,
    )
except ModuleNotFoundError:  # imported as a repository module
    from scripts.protected_paths import REASON_CODE as PROTECTED_PATH_REASON
    from scripts.protected_paths import (
        bash_command_writes_protected,
        file_tool_write_is_protected,
    )

PROTECTED = ("git_push", "git_tag", "gh_pr_create", "gh_pr_merge", "gh_release_create", "publish_ship")
CONTENT_SENSITIVE = ("git_commit", *PROTECTED)
logger = logging.getLogger(__name__)
HOOK_DEADLINE_SECONDS = 8.0
_HOOK_STARTED_AT: float | None = None
_HOOK_PHASE = "input_validation"
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
# A dynamic path prefix is acceptable only when its literal basename cannot reach Git/GitHub publication.
CLASSIFIED_EXECUTABLES = {"bash", "sh", "zsh", "dash", "ksh", "fish", "env", "sudo", "command", "eval", "exec"}
# git-lfs subcommands that only read, or change local files/config; lfs push and history rewrites stay denied.
GIT_LFS_LOCAL = {"checkout", "env", "ext", "fetch", "fsck", "install", "locks", "logs", "ls-files", "pointer",
                 "prune", "pull", "status", "track", "uninstall", "untrack", "version"}
GIT_ALIAS_MAX_DEPTH = 5
# Dynamic values for these options can redefine what a built-in Git verb executes.
DYNAMIC_FORBIDDEN_OPTIONS = {"-c", "--config-env", "--exec-path"}
GH_API_WRITE_FLAGS = ("-f", "-F", "--field", "--raw-field", "--input")


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


def _direct_operations(tokens: list[str], cwd: Path | None = None, depth: int = 0) -> list[str]:
    tokens = _unwrap(tokens)
    if not tokens:
        return []
    from publication_commands import publish_ship_arguments
    if publish_ship_arguments(tokens) is not None:
        # One Bash command = one protected operation; the CLI's child git/gh calls are not agent Bash calls.
        return ["publish_ship"]
    exe = Path(tokens[0]).name

    if exe in {"bash", "sh", "zsh"}:
        for i, token in enumerate(tokens[1:], start=1):
            if token == "-c" and i + 1 < len(tokens):
                return operations_for(tokens[i + 1], cwd, depth)
            if re.fullmatch(r'-[A-Za-z]*c[A-Za-z]*', token) and i + 1 < len(tokens):
                return operations_for(tokens[i + 1], cwd, depth)
        from publication_commands import CommandError
        raise CommandError('interpreter file/stdin execution cannot be classified; use literal standalone commands', 'UNSUPPORTED_INTERPRETER')

    if exe == "eval" and len(tokens) > 1:
        return operations_for(" ".join(tokens[1:]), cwd, depth)

    if exe == "git":
        return _git_operations(tokens, cwd, depth)

    if exe == "gh":
        args = _strip_options(tokens[1:], GH_GLOBAL_WITH_VALUE)
        if args and args[0] == 'api':
            _check_gh_api_read(args[1:])
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


def _check_gh_api_read(args: list[str]) -> None:
    """Allow only GitHub API reads: default/explicit GET without request fields or an input body."""
    from publication_commands import CommandError
    method = None
    writes = False
    i = 0
    while i < len(args):
        token = args[i]
        value = None
        if token in {'-X', '--method'}:
            if i + 1 >= len(args):
                raise CommandError('GitHub API method value is missing', 'AMBIGUOUS_GITHUB_API_REQUEST')
            value = args[i + 1]
            i += 1
        elif token.startswith('--method='):
            value = token.split('=', 1)[1]
        elif token.startswith('-X') and len(token) > 2:
            value = token[2:]
        elif token in GH_API_WRITE_FLAGS or token.startswith(('--field=', '--raw-field=', '--input=')) \
                or re.fullmatch(r'-[fF].+', token):
            writes = True
        if value is not None:
            if method is not None or _dynamic_word(value):
                raise CommandError('ambiguous GitHub API request is unsupported', 'AMBIGUOUS_GITHUB_API_REQUEST')
            method = value
        i += 1
    # gh api switches to POST when fields or an input body are present, so any of them is a write.
    if writes or (method is not None and method.upper() != 'GET'):
        raise CommandError('unbound GitHub API mutation is unsupported', 'UNBOUND_GITHUB_API_MUTATION')


def _git_alias(global_options: list[str], verb: str, cwd: Path | None) -> str | None:
    """Read one alias definition from the caller's repository configuration.

    Any global option (-C, -c, --git-dir, --work-tree, --config-env, ...) can change which
    configuration defines the alias, so aliases are resolved only for plain `git <alias>`.
    """
    if global_options or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', verb):
        return None
    proc = subprocess.run(['git', 'config', '--get', 'alias.' + verb], cwd=cwd,
                          env=READ_ONLY_GIT_ENV, capture_output=True, text=True, timeout=5, check=False)
    value = proc.stdout.strip()
    return value if proc.returncode == 0 and value else None


def _alias_publication_error():
    from publication_commands import CommandError
    return CommandError('Git alias resolves to a guarded publication command; run the literal command',
                        'GIT_ALIAS_PUBLICATION_UNSUPPORTED')


def _git_operations(tokens: list[str], cwd: Path | None, depth: int) -> list[str]:
    from publication_commands import CommandError
    args = _strip_options(tokens[1:], GIT_GLOBAL_WITH_VALUE)
    if not args:
        return []
    global_options = tokens[1:len(tokens) - len(args)]
    if args[0] == "push":
        return ["git_push"]
    if args[0] == "commit":
        return ["git_commit"]
    if args[0] in {'send-pack', 'http-push', 'receive-pack'}:
        raise CommandError('Git remote-ref plumbing is unsupported; use the exact signed push workflow', 'UNSUPPORTED_GIT_PLUMBING')
    if args[0] == "tag":
        query = args[1:]
        read_flags = {"--list", "-l", "--verify", "-v", "--contains", "--no-contains",
                      "--merged", "--no-merged", "--points-at", "--sort", "--format", "--column", "--no-column"}
        if not query or (any(x.split("=")[0] in read_flags or re.fullmatch(r"-n\d*", x) for x in query)
                         and all(not x.startswith("-") or x.split("=")[0] in read_flags or re.fullmatch(r"-n\d*", x) for x in query)):
            return []
        return ["git_tag"]
    if args[0] == "lfs":
        subcommand = next((x for x in args[1:] if not x.startswith("-")), None)
        if subcommand is None or subcommand in GIT_LFS_LOCAL:
            return []
        raise CommandError('git-lfs subcommand may publish or rewrite history', 'UNSUPPORTED_GIT_LFS_COMMAND')
    builtin = subprocess.run(['git', '--list-cmds=builtins'], capture_output=True, text=True, timeout=5, check=False)
    if builtin.returncode == 0 and args[0] in builtin.stdout.split():
        return []
    # A Git alias may run shell code or publish; classify its expansion and allow only read-only results.
    alias = _git_alias(global_options, args[0], cwd) if depth < GIT_ALIAS_MAX_DEPTH else None
    if alias is None:
        raise CommandError('unknown Git verb or alias cannot be classified', 'UNKNOWN_GIT_COMMAND')
    if alias.startswith('!'):
        # Shell aliases receive the remaining arguments positionally; only the body itself is classified.
        expanded_operations = operations_for(alias[1:], cwd, depth + 1)
    else:
        try:
            expanded = shlex.split(alias)
        except ValueError as exc:
            raise CommandError('Git alias cannot be parsed', 'UNKNOWN_GIT_COMMAND') from exc
        expanded_operations = _direct_operations(['git', *expanded, *args[1:]], cwd, depth + 1)
    if expanded_operations:
        raise _alias_publication_error()
    return []


def _dynamic_executable_is_unclassified(word: str) -> bool:
    """True when a dynamic path prefix ends in a literal basename that cannot reach Git/GitHub."""
    if "\0" in word or "/" not in word:
        return False
    name = word.rsplit("/", 1)[1].strip("\"'")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", name):
        return False
    return name not in CLASSIFIED_EXECUTABLES and not name.startswith(("git", "gh"))


def _global_options(tokens: list[str], with_value: set[str]) -> tuple[list[str], bool]:
    """Return the CLI words after global options and whether a context option was dynamic.

    A dynamic directory or repository is acceptable for read-only commands, but a dynamic
    configuration or exec path can redefine what a built-in verb runs, so it always denies.
    """
    from publication_commands import CommandError
    try:
        return _after_global_options(tokens, with_value), False
    except CommandError as exc:
        if exc.reason_code != "DYNAMIC_CLI_OPTION":
            raise
        index = 0
        while index < len(tokens) and tokens[index].startswith("-") and tokens[index] != "-":
            option, _, inline = tokens[index].partition("=")
            value = inline if inline else (tokens[index + 1] if option in with_value and index + 1 < len(tokens) else "")
            if option in DYNAMIC_FORBIDDEN_OPTIONS and (_dynamic_word(tokens[index]) or _dynamic_word(value)):
                raise
            index += 2 if option in with_value and not inline else 1
        return _strip_options(tokens, with_value), True


def operations_for(command: str, cwd: Path | None = None, depth: int = 0) -> list[str]:
    from publication_commands import CommandError
    operations: list[str] = []
    for segment in _segments(command):
        effective = _unwrap(segment)
        if effective and _dynamic_word(effective[0]):
            if _dynamic_executable_is_unclassified(effective[0]):
                continue
            raise CommandError('dynamic executable cannot be classified', 'DYNAMIC_EXECUTABLE')
        dynamic_option = False
        if effective and Path(effective[0]).name == 'git':
            args, dynamic_option = _global_options(effective[1:], GIT_GLOBAL_WITH_VALUE)
            if args and _dynamic_word(args[0]):
                raise CommandError('dynamic Git subcommand cannot be classified', 'DYNAMIC_SUBCOMMAND')
        if effective and Path(effective[0]).name == 'gh':
            args, dynamic_option = _global_options(effective[1:], GH_GLOBAL_WITH_VALUE)
            if any(_dynamic_word(word) for word in args[:2]):
                raise CommandError('dynamic GitHub CLI command cannot be classified', 'DYNAMIC_SUBCOMMAND')
        if effective and Path(effective[0]).name in {'bash', 'sh', 'zsh'} and '<<' in command:
            raise CommandError('shell heredoc execution requires an inspected standalone command', 'UNSUPPORTED_HEREDOC')
        try:
            segment_operations = _direct_operations(segment, cwd, depth)
        except CommandError as exc:
            # Alias and verb lookups cannot be trusted when the target repository is dynamic.
            if dynamic_option and exc.reason_code == 'UNKNOWN_GIT_COMMAND':
                raise CommandError('dynamic CLI global option cannot bind a stable target', 'DYNAMIC_CLI_OPTION') from exc
            raise
        # A dynamic repository/directory only matters when it would select a publication target.
        if dynamic_option and segment_operations:
            raise CommandError('dynamic CLI global option cannot bind a stable target', 'DYNAMIC_CLI_OPTION')
        for operation in segment_operations:
            if operation not in operations:
                operations.append(operation)
    return operations


def operation_for(command: str):
    operations = operations_for(command)
    return operations[0] if operations else None


COMMIT_ADD_OPTIONS = {'-A', '--all', '-u', '--update', '-f', '--force', '--'}
COMMIT_FLAG_OPTIONS = {'--allow-empty', '--allow-empty-message', '--no-verify', '--signoff', '-s', '--quiet', '-q'}


def _commit_chain(command: str) -> tuple[list[list[str]], list[str]]:
    """Return literal `git add` commands joined by && before one final `git commit`.

    Words Bash would expand carry a NUL marker, so literal `$` or backticks in quoted text stay allowed.
    """
    import bashlex
    from publication_commands import inline_literal_heredocs, shell_commands
    unsupported = PublicationError("commit must be standalone or follow literal git add commands joined by &&",
                                   reason_code='COMMAND_FORM_UNSUPPORTED', detail_code='COMMIT_FORM_UNSUPPORTED')
    normalized = inline_literal_heredocs(command)
    commands = shell_commands(normalized, mark_dynamic=True)
    if len(commands) == 1:
        if commands[0][:2] != ['git', 'commit']:
            raise unsupported
        return [], commands[0]
    if '<<' in normalized:
        raise unsupported
    try:
        trees = bashlex.parse(normalized)
    except (ValueError, NotImplementedError, bashlex.errors.ParsingError) as exc:
        raise unsupported from exc
    if len(trees) != 1 or trees[0].kind != 'list':
        raise unsupported
    parts = trees[0].parts
    operators = [part.op for part in parts if part.kind == 'operator']
    # Any substitution, pipe or other connector adds commands that the operators cannot account for.
    if (any(part.kind not in {'command', 'operator'} for part in parts) or any(op != '&&' for op in operators)
            or len(operators) != len(commands) - 1):
        raise unsupported
    *adds, commit = commands
    if commit[:2] != ['git', 'commit'] or any(add[:2] != ['git', 'add'] for add in adds):
        raise unsupported
    for add in adds:
        for word in add[2:]:
            if '\0' in word:
                raise PublicationError("git add pathspecs must be literal", reason_code='PUBLICATION_INPUT_UNBOUND')
            if word.startswith('-') and word not in COMMIT_ADD_OPTIONS:
                raise unsupported
    return adds, commit


def _git_add_paths(cwd: Path, add: list[str]) -> tuple[set[str], set[str]]:
    """Resolve what `git add` would stage without writing the index or object database."""
    try:
        proc = subprocess.run(['git', '-c', 'core.quotePath=false', 'add', '--dry-run', *add[2:]], cwd=cwd,
                              env=READ_ONLY_GIT_ENV, capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PublicationError("git add preview unavailable", "CONTENT_INSPECTION_UNAVAILABLE",
                               context={'error_class': type(exc).__name__}, phase='staged_index') from exc
    if proc.returncode:
        raise PublicationError("git add preview failed", "CONTENT_INSPECTION_UNAVAILABLE", phase='staged_index')
    added: set[str] = set()
    removed: set[str] = set()
    for line in proc.stdout.splitlines():
        match = re.fullmatch(r"(add|remove) '(.+)'", line)
        if not match:
            raise PublicationError("git add preview is ambiguous", "CONTENT_INSPECTION_UNAVAILABLE", phase='staged_index')
        (added if match[1] == 'add' else removed).add(match[2])
    return added, removed


def commit_safety(cwd: Path, command: str) -> dict:
    """Scan actual commit messages and candidate content; exempt only final author email metadata."""
    from content_safety import added_line_numbers_from_diff, scan_payload
    from publication_authority import PublicationError
    adds, commit = _commit_chain(command)
    args = commit[2:]
    if any('\0' in word for word in args):
        raise PublicationError("commit message/file must be literal without shell expansion", reason_code='PUBLICATION_INPUT_UNBOUND')
    # Alternate index/worktree environment can change what Git commits.
    if any(os.environ.get(key) for key in ['GIT_INDEX_FILE', 'GIT_DIR', 'GIT_WORK_TREE']):
        raise PublicationError("alternate Git commit environment unsupported", reason_code='ALTERNATE_GIT_ENVIRONMENT')
    messages = []
    commit_all = amend = no_edit = False
    i = 0
    while i < len(args):
        word = args[i]
        if word in {'-m', '--message', '-F', '--file', '-am'}:
            if i + 1 >= len(args):
                raise PublicationError("commit message value missing", reason_code='PUBLICATION_OPTION_INVALID', phase='commit_message')
            value = args[i + 1]
            if word == '-am':
                commit_all = True
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
        elif word in {'-a', '--all'}:
            commit_all = True
            i += 1
        elif word == '--amend':
            amend = True
            i += 1
        elif word == '--no-edit':
            no_edit = True
            i += 1
        elif word in COMMIT_FLAG_OPTIONS:
            i += 1
        else:
            # --only, re-use/editor messages and path selection change the candidate.
            raise PublicationError("unsupported commit option requires an explicit inspected staged commit", reason_code='COMMAND_FORM_UNSUPPORTED')
    if no_edit and not amend:
        raise PublicationError("--no-edit is supported only with --amend", reason_code='COMMAND_FORM_UNSUPPORTED')
    try:
        root_proc = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=cwd, env=READ_ONLY_GIT_ENV,
                                   capture_output=True, text=True, timeout=10, check=False)
        if root_proc.returncode:
            raise OSError('repository root unavailable')
        root = Path(root_proc.stdout.strip())
        if not messages and amend and no_edit:
            # The amended commit keeps HEAD's message; inspect it like an explicit message.
            reused = subprocess.run(['git', 'log', '-1', '--format=%B'], cwd=root, env=READ_ONLY_GIT_ENV,
                                    capture_output=True, text=True, timeout=10, check=False)
            if reused.returncode:
                raise OSError('amended commit message unavailable')
            messages.append(reused.stdout.rstrip('\n'))
    except subprocess.TimeoutExpired as exc:
        raise PublicationError("staged index inspection timed out", "STAGED_INDEX_UNAVAILABLE",
                               context={'error_class': type(exc).__name__}, phase='staged_index') from exc
    except OSError as exc:
        raise PublicationError("repository index unavailable", "STAGED_INDEX_UNAVAILABLE",
                               context={'error_class': type(exc).__name__}, phase='staged_index') from exc
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
    # Commit is the only local injection gate: the push-time candidate scan covers secrets only.
    if safety['decision'] in {'BLOCK', 'REVIEW'}:
        return _commit_block(safety['findings'], 'commit_message', None)
    # Worktree paths whose current file content becomes part of the commit (git add / commit -a).
    worktree_paths: set[str] = set()
    removed_paths: set[str] = set()
    for add in adds:
        added, removed = _git_add_paths(cwd, add)
        worktree_paths |= added
        removed_paths |= removed
    try:
        if commit_all:
            tracked = subprocess.run(['git', 'diff', '--name-only', '-z', '--diff-filter=ACMRT'], cwd=root,
                                     env=READ_ONLY_GIT_ENV, capture_output=True, timeout=10, check=False)
            if tracked.returncode:
                raise OSError('tracked worktree changes unavailable')
            worktree_paths |= {os.fsdecode(name) for name in tracked.stdout.split(b'\0') if name}
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
    candidates = [name for name in staged.stdout.split(b'\0') if name and os.fsdecode(name) not in removed_paths]
    candidates += [os.fsencode(path) for path in sorted(worktree_paths) if os.fsencode(path) not in candidates]
    for name in candidates:
        relative = os.fsdecode(name)
        from_worktree = relative in worktree_paths
        if b'160000' in index_modes.get(name, set()):
            raise PublicationError("staged submodule content cannot be inspected", "STAGED_CONTENT_UNSUPPORTED_BINARY",
                                   phase='staged_blob')
        suffix = PurePosixPath(relative).suffix.lower()
        font_suffixes = {'.ttf', '.otf', '.woff', '.woff2'}
        from media_metadata import MEDIA_SUFFIXES
        media_suffixes = MEDIA_SUFFIXES
        limit = 8 * 1024 * 1024
        too_large = ("M4A_TOO_LARGE" if suffix == '.m4a' else
                     "STAGED_FONT_RESOURCE_LIMIT" if suffix in font_suffixes else
                     "STAGED_MEDIA_RESOURCE_LIMIT" if suffix in media_suffixes else
                     "STAGED_CONTENT_TOO_LARGE")
        if from_worktree:
            path = root / relative
            if not os.path.lexists(path):
                continue  # A deletion adds no content.
            try:
                if path.is_symlink():
                    content = os.fsencode(os.readlink(path))
                elif not path.is_file():
                    raise PublicationError("worktree directory or submodule content cannot be inspected",
                                           "STAGED_CONTENT_UNSUPPORTED_BINARY", phase='staged_blob')
                elif path.stat().st_size > limit:
                    raise PublicationError("worktree file exceeds inspection limit", too_large,
                                           context={'file': relative, 'format': suffix[1:]}, phase='staged_blob')
                else:
                    content = path.read_bytes()
            except OSError as exc:
                raise PublicationError("worktree file unavailable", "STAGED_CONTENT_UNAVAILABLE",
                                       context={'error_class': type(exc).__name__}, phase='staged_blob') from exc
        else:
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
            if blob_size > limit:
                raise PublicationError("staged blob exceeds inspection limit", too_large,
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
            content = blob.stdout
        if len(content) > limit:
            raise PublicationError("staged blob exceeds inspection limit", too_large,
                                   context={'file': relative, 'format': suffix[1:]}, phase='staged_blob')
        if suffix in media_suffixes | font_suffixes:
            from media_metadata import (
                MediaInspectionError,
                extract_metadata,
                media_diagnostic_code,
            )
            try:
                staged_text = extract_metadata(content, suffix)
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
                if b'\x00' in content:
                    raise UnicodeError('binary NUL')
                staged_text = content.decode('utf-8', errors='strict')
            except UnicodeError as exc:
                raise PublicationError("staged binary format is unsupported", "STAGED_CONTENT_UNSUPPORTED_BINARY",
                                       context={'error_class': type(exc).__name__}, phase='staged_blob') from exc
        # Injection context uses the lines this commit adds; worktree content is compared with HEAD.
        diff_args = (['diff', 'HEAD'] if from_worktree else ['diff', '--cached'])
        try:
            diff = subprocess.run(
                ['git', '--literal-pathspecs', *diff_args, '--no-ext-diff', '--no-renames',
                 '--unified=0', '--', relative],
                cwd=root, env=READ_ONLY_GIT_ENV, capture_output=True, timeout=10, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PublicationError("staged diff unavailable for injection context", "STAGED_DIFF_UNAVAILABLE",
                                   context={'error_class': type(exc).__name__}, phase='staged_diff') from exc
        if from_worktree and (diff.returncode or not diff.stdout):
            # New file or no HEAD yet: every line is added by this commit.
            changed_lines = list(range(1, staged_text.count('\n') + 2))
        elif diff.returncode:
            raise PublicationError("staged diff unavailable for injection context", "STAGED_DIFF_UNAVAILABLE",
                                   phase='staged_diff')
        else:
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


def _protected_path_diagnostic(reason: str) -> dict[str, Any]:
    """Static, input-free diagnostic: never echoes the protected path or the command."""
    unavailable = reason == "PROTECTED_PATH_GUARD_UNAVAILABLE"
    return {
        "version": 2, "diagnostic_id": str(uuid.uuid4()), "reason_code": reason,
        "detail": ("AIPS could not verify this write against the protected install or profile paths."
                   if unavailable else
                   "AIPS blocked an agent write to the installed AIPS system or profile settings."),
        "detail_zh": ("AIPS 無法驗證此寫入是否指向受保護的安裝目錄或 profile 設定。" if unavailable else
                      "AIPS 已阻擋代理寫入已安裝的 AIPS 系統目錄或 profile 設定。"),
        "next_step": ("Retry only after the local check can run; do not work around the guard. "
                      "請在本機檢查可執行後再重試，不要繞過 guard。" if unavailable else
                      "Make system and profile changes in the development repository, publish them through a PR, "
                      "and leave the installed copy untouched. 請在開發 repo 修改系統與 profile 內容並透過 PR 發布，不要直接修改已安裝副本。"),
        "next_step_zh": ("本機檢查可執行後再重試；不要繞過 guard。" if unavailable else
                         "在開發 repo 修改，透過 PR 發布；不要改動已安裝副本或 profile 設定。"),
        "phase": "protected_path_guard", "category": "POLICY", "source": "AIPS_GUARD",
        "blocking_rule": "protected_path", "blocking_rule_id": reason, "retryable": unavailable,
        "recovery_mode": "HUMAN_OR_HOST_REQUIRED", "redacted": True,
    }


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
        "GIT_ALIAS_PUBLICATION_UNSUPPORTED": "AIPS blocks Git aliases that expand to commit or publication commands; run the literal command.",
        "UNSUPPORTED_GIT_LFS_COMMAND": "AIPS blocks git-lfs subcommands that can publish, lock remote files or rewrite history.",
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
        "PROTECTED_PATH_WRITE": "AIPS blocked an agent write to the installed AIPS system or profile settings.",
        "PROTECTED_PATH_GUARD_UNAVAILABLE": "AIPS could not verify this write against the protected paths; the write was not allowed.",
    }
    detail = reason_messages.get(reason, "AIPS blocked this command during a required safety check.")
    if diagnostic is None:
        diagnostic = PublicationError("", reason).diagnostic()
    if diagnostic.get("reason_code") == reason and diagnostic.get("next_step"):
        # A static, input-free recipe stops agents from guessing command variants.
        detail += " Next: " + str(diagnostic["next_step"])
    detail += " [" + reason + "]"
    trace_status = ("SKIPPED_DEADLINE" if reason == "HOOK_DEADLINE_EXCEEDED"
                    else _record_publication_diagnostic(diagnostic, runtime))
    safe_fields = {key: diagnostic.get(key) for key in
                   ("diagnostic_id", "reason_code", "detail_code", "phase", "category", "detail", "detail_zh",
                    "blocking_rule", "blocking_rule_id", "source", "retryable", "recovery_mode", "next_step", "next_step_zh",
                    "findings")}
    if diagnostic.get('binding'):
        safe_fields['binding'] = diagnostic['binding']
    if _HOOK_STARTED_AT is not None:
        safe_fields['elapsed_ms'] = max(0, int((time.monotonic() - _HOOK_STARTED_AT) * 1000))
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


def _hook_impl(runtime: str) -> int:
    global _HOOK_PHASE
    _HOOK_PHASE = "input_validation"
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
        category = ("TIMEOUT_OBSERVED" if any(word in folded for word in ("timed out", "timeout"))
                    else "NETWORK_ERROR" if any(word in folded for word in ("connection refused", "network is unreachable"))
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
        _HOOK_PHASE = "runtime_policy"
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
    # Protected install/profile writes are denied before publication classification (PR3, best-effort).
    _HOOK_PHASE = "protected_path_guard"
    try:
        guard_cwd = Path(str(payload.get("cwd") or os.getcwd())).resolve()
        protected_write = (
            (runtime == "claude-code" and file_tool_write_is_protected(
                str(payload.get("tool_name") or ""), tool_input or {}, guard_cwd))
            or bash_command_writes_protected(command, guard_cwd)
        )
    except Exception as exc:  # noqa: BLE001 - an unverifiable path check must fail closed.
        logger.warning("Protected path guard failed closed: %s", type(exc).__name__)
        return deny_hook_input(runtime, "PROTECTED_PATH_GUARD_UNAVAILABLE",
                               _protected_path_diagnostic("PROTECTED_PATH_GUARD_UNAVAILABLE"))
    if protected_write:
        return deny_hook_input(runtime, PROTECTED_PATH_REASON, _protected_path_diagnostic(PROTECTED_PATH_REASON))
    try:
        _HOOK_PHASE = "command_classification"
        operations = operations_for(command, Path(str(payload.get("cwd") or os.getcwd())).resolve())
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
            _HOOK_PHASE = "content_safety"
            sink = {
                "git_commit": "git_commit",
                "git_push": "source_artifact",
                "git_tag": "source_artifact",
                "gh_pr_create": "github_pr",
                "gh_pr_merge": "github_pr",
                "gh_release_create": "release_notes",
                "publish_ship": "github_pr",
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
    ship_binding = None
    approval_operations = [operation for operation in operations if operation in PROTECTED]
    if not approval_operations:
        ok = True
        reason = "content safety passed; no publish approval required"
    else:
        try:
            _HOOK_PHASE = "publication_validation"
            if len(approval_operations) != 1:
                raise PublicationError('one protected publication operation per invocation required',
                                       'COMMAND_FORM_UNSUPPORTED', phase='command_validation',
                                       detail_code='MULTI_COMMAND_UNSUPPORTED')
            from publication_authority import (
                publication_mode,
                validate_personal_action,
            )
            mode = publication_mode()
            if mode == 'personal':
                from publication_commands import command_form_detail, shell_commands
                # Marked words let quoted literal `$`/backticks (for example a quoted heredoc PR
                # body) through while every real expansion still carries a NUL marker and denies.
                parsed = shell_commands(command, mark_dynamic=True)
                if len(parsed) != 1 or len(approval_operations) != 1:
                    raise PublicationError('one standalone publication operation required', reason_code='COMMAND_FORM_UNSUPPORTED',
                                           detail_code=command_form_detail(command))
                _HOOK_PHASE = "publication_candidate_remote_and_evidence_validation"
                if approval_operations[0] == 'publish_ship':
                    from publication_commands import publish_ship_arguments
                    from publication_ship import validate_for_hook
                    ship_args = publish_ship_arguments(parsed[0])
                    if ship_args is None:
                        raise PublicationError('use the single supported ship command', 'COMMAND_FORM_UNSUPPORTED',
                                               detail_code='SHIP_FORM_UNSUPPORTED')
                    ship = validate_for_hook(cwd, ship_args)
                    ship_binding = ship['binding']
                    publication = {}
                else:
                    publication = validate_personal_action(
                        cwd, approval_operations[0], parsed[0], require_scan_evidence=True, literal_marked=True)
                if approval_operations[0] == 'publish_ship':
                    reason = 'personal publish ship checks passed; scan ' + ship['scan']
                elif approval_operations[0] == 'gh_pr_merge':
                    merge_confirmation = publication.get('merge_confirmation')
                    if not merge_confirmation:
                        raise PublicationError('merge confirmation binding unavailable', reason_code='AUTHORITY_VALIDATION_MISSING')
                    checks_enabled = merge_confirmation.get('required_checks_enforced', False)
                    names = ', '.join(merge_confirmation['required_checks']) or ('none' if checks_enabled else 'not enforced by AIPS')
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
                if approval_operations[0] == 'publish_ship':
                    raise PublicationError('publish ship is available only in personal publication mode',
                                           'ASSURANCE_MODE_BLOCKED', phase='authority_validation')
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
            elif isinstance(exc, subprocess.TimeoutExpired):
                diagnostic = PublicationError(
                    'remote observation timed out', 'REMOTE_OBSERVATION_FAILED',
                    context={'error_class': 'TimeoutExpired'}, phase='remote_observation',
                    detail_code='REMOTE_OBSERVATION_TIMEOUT').diagnostic()
            else:
                diagnostic = PublicationError(
                    'unclassified publication authorization failure', 'INTERNAL_DIAGNOSTIC_GAP',
                    context={'error_class': type(exc).__name__}, phase=_HOOK_PHASE).diagnostic()
            binding = _hook_binding(cwd, command, mode)
            if binding:
                diagnostic['binding'] = binding
            hook_diagnostic = diagnostic
            reason = hook_diagnostic['reason_code'] + ': ' + hook_diagnostic['detail'] + ' ' + hook_diagnostic['next_step']
            if (runtime == "claude-code" and diagnostic.get("retryable") is True and
                    diagnostic.get("category") in {"NETWORK", "RATE_LIMITED", "GITHUB_SERVER_ERROR", "TIMEOUT"}):
                hook_diagnostic["next_step"] = (
                    "Manual read-only diagnostic command in this candidate worktree: `aips publish doctor --worktree . --format json`; "
                    "to inspect the safe remote-observation failure, then re-observe before publication."
                )
                hook_diagnostic["next_step_zh"] = (
                    "此候選工作樹的唯讀診斷命令：`aips publish doctor --worktree . --format json`； "
                    "檢查遠端觀測失敗原因；重新確認目前候選前不可發布。"
                )
                reason = hook_diagnostic['reason_code'] + ': ' + hook_diagnostic['detail'] + ' ' + hook_diagnostic['next_step']

    if hook_diagnostic:
        hook_diagnostic['elapsed_ms'] = max(
            0, int((time.monotonic() - (_HOOK_STARTED_AT or time.monotonic())) * 1000))
        _HOOK_PHASE = "diagnostic_recording"
        hook_diagnostic['trace_status'] = _record_publication_diagnostic(hook_diagnostic, runtime)
    success_binding = ship_binding or (_hook_binding(cwd, command, mode) if ok and approval_operations else None)
    if runtime == "claude-code":
        claude_auto_merge = bool(merge_confirmation and merge_confirmation.get('auto_merge'))
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask" if ok and merge_confirmation and not claude_auto_merge else "allow" if ok else "deny",
            "permissionDecisionReason": ("AIPS " + reason if ok else "AIPS blocked protected publication: " + reason) +
                (" [phase=" + str(hook_diagnostic.get("phase")) + "; diagnostic_id=" +
                 str(hook_diagnostic.get("diagnostic_id")) + "]" if hook_diagnostic else ""),
            **({"additionalContext": "AIPS diagnostic: " + json.dumps({key: hook_diagnostic.get(key) for key in
                ("diagnostic_id", "reason_code", "detail_code", "phase", "category", "error_class", "elapsed_ms", "detail", "detail_zh",
                 "blocking_rule", "blocking_rule_id", "source", "retryable",
                "recovery_mode", "next_step", "next_step_zh",
                 "binding", "trace_status")}, ensure_ascii=False, separators=(",", ":")) +
                "; authorization_status=DENIED; execution_status=NOT_EXECUTED"} if hook_diagnostic else
               {"additionalContext": "AIPS publication: " + json.dumps({
                   'status': 'AUTHORIZED', 'authorized': True,
                   'host_decision': 'NOT_EVALUATED', 'execution_status': 'NOT_EXECUTED',
                   'executed': False, 'binding': success_binding,
                   'elapsed_ms': max(0, int((time.monotonic() - (_HOOK_STARTED_AT or time.monotonic())) * 1000)),
                   'phase': _HOOK_PHASE,
               }, ensure_ascii=False, separators=(",", ":"))} if ok and approval_operations else {}),
        }}))
    else:
        result = {"decision": "allow" if ok else "deny"}
        if ok and approval_operations:
            result['publication'] = {
                'status': 'AUTHORIZED', 'authorized': True,
                'host_decision': 'NOT_EVALUATED', 'execution_status': 'NOT_EXECUTED',
                'executed': False, 'binding': success_binding,
                'elapsed_ms': max(0, int((time.monotonic() - (_HOOK_STARTED_AT or time.monotonic())) * 1000)),
                'phase': _HOOK_PHASE,
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


class _HookDeadlineExceeded(BaseException):
    pass


def _hook_deadline_handler(_signum, _frame):
    raise _HookDeadlineExceeded()


def hook(runtime: str) -> int:
    """Run one Hook under a hard, fail-closed wall-clock budget."""
    global _HOOK_STARTED_AT, _HOOK_PHASE
    previous_started, previous_phase = _HOOK_STARTED_AT, _HOOK_PHASE
    _HOOK_STARTED_AT = time.monotonic()
    _HOOK_PHASE = "input_validation"
    old_handler = None
    old_timer = (0.0, 0.0)
    timer_active = False
    try:
        if hasattr(signal, "setitimer"):
            import threading
            if threading.current_thread() is threading.main_thread():
                old_handler = signal.getsignal(signal.SIGALRM)
                old_timer = signal.getitimer(signal.ITIMER_REAL)
                signal.signal(signal.SIGALRM, _hook_deadline_handler)
                signal.setitimer(signal.ITIMER_REAL, HOOK_DEADLINE_SECONDS)
                timer_active = True
        return _hook_impl(runtime)
    except _HookDeadlineExceeded:
        elapsed = max(0, int((time.monotonic() - (_HOOK_STARTED_AT or time.monotonic())) * 1000))
        diagnostic = PublicationError(
            "Hook exceeded its bounded execution deadline", "HOOK_DEADLINE_EXCEEDED",
            phase=_HOOK_PHASE).diagnostic()
        diagnostic["elapsed_ms"] = elapsed
        return deny_hook_input(runtime, "HOOK_DEADLINE_EXCEEDED", diagnostic)
    finally:
        if timer_active:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)
            if old_timer[0] > 0:
                remaining = max(0.001, old_timer[0] - (time.monotonic() - (_HOOK_STARTED_AT or time.monotonic())))
                signal.setitimer(signal.ITIMER_REAL, remaining, old_timer[1])
        _HOOK_STARTED_AT, _HOOK_PHASE = previous_started, previous_phase


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
