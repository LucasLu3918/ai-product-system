"""Protected AIPS install and profile paths for agent write checks (PR3).

Protected write targets:
- the installed AIPS system checkout (default XDG/HOME data path and AIPS_INSTALL_DIR);
- AIPS user profile settings under the config home (profile*.yaml/yml and profiles/).

Reads are never classified. This is best-effort, not complete enforcement: interpreters
(python -c, node -e), dynamically built paths and unparsed syntax are not classified.
The recorded system-dir file is intentionally not used, because a development checkout
can be recorded there and must stay writable.
"""
from __future__ import annotations

import os
import re
import shlex
from pathlib import Path

REASON_CODE = "PROTECTED_PATH_WRITE"
FILE_EDIT_TOOLS = {"Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
CONTROL_TOKENS = {";", "&", "&&", "|", "||", "|&", "(", ")", ";;", "\n"}
REDIRECT_TOKENS = {">", ">>", ">|", ">&", ">>&", "&>", "&>>"}
ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SED_INPLACE_RE = re.compile(r"^-[A-Za-z]*i|^--in-place")
MAX_WRAPPER_DEPTH = 3
ALL_ARG_WRITE_COMMANDS = {"tee", "rm", "unlink", "touch", "mkdir", "rmdir", "truncate", "chmod", "chown", "chgrp", "shred"}
DEST_LAST_COMMANDS = {"cp", "install", "ln", "rsync"}
MOVE_COMMANDS = {"mv"}
SHELL_WRAPPERS = {"bash", "sh", "zsh", "dash", "ksh"}
TRANSPARENT_WRAPPERS = {"env", "sudo", "command", "nohup", "time", "exec", "builtin", "nice", "stdbuf", "xargs"}
# Git verbs that only read repository state; every other verb is treated as a write.
GIT_READ_VERBS = {
    "status", "log", "diff", "show", "rev-parse", "ls-files", "ls-tree", "cat-file", "grep", "blame",
    "describe", "shortlog", "rev-list", "for-each-ref", "show-ref", "help", "version",
}


def _home() -> Path:
    return Path.home()


def config_home() -> Path:
    """Same resolution as scripts/aips_cli.sh: XDG_CONFIG_HOME (when set) or ~/.config, plus aips."""
    return Path(os.environ.get("XDG_CONFIG_HOME") or (_home() / ".config")) / "aips"


def profile_settings_path() -> Path:
    """Profile settings file introduced by PR10; defined here so the guard protects it from the start."""
    return config_home() / "profile.yaml"


def installed_system_roots() -> list[Path]:
    roots = [
        Path(os.environ.get("XDG_DATA_HOME") or (_home() / ".local" / "share")) / "aips" / "system",
        _home() / ".local" / "share" / "aips" / "system",
    ]
    override = os.environ.get("AIPS_INSTALL_DIR")
    if override:
        roots.append(Path(override))
    return [Path(os.path.realpath(os.path.expanduser(str(root)))) for root in roots]


def _within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def protected_category(path: Path) -> str | None:
    """Return the protected category for a canonical path, or None."""
    for root in installed_system_roots():
        if _within(path, root):
            return "installed_system"
    config = Path(os.path.realpath(config_home()))
    if path == config:
        return "profile_settings"
    if path.parent == config and path.name.startswith("profile"):
        return "profile_settings"
    if _within(path, config / "profiles"):
        return "profile_settings"
    return None


def _expand(raw: str) -> str:
    home = str(_home())
    expanded = raw.replace("${HOME}", home).replace("$HOME", home)
    if expanded == "~" or expanded.startswith("~/"):
        expanded = home + expanded[1:]
    return expanded


def resolve_path(raw: str, base: Path) -> Path:
    """Resolve symlinks and '..' without requiring the target to exist. May raise ValueError/OSError."""
    candidate = Path(_expand(raw))
    if not candidate.is_absolute():
        candidate = base / candidate
    return Path(os.path.realpath(candidate))


def _protected_raw(raw: str, base: Path) -> bool:
    if not raw or raw == "-" or raw.isdigit():
        return False
    expanded = _expand(raw)
    if "$" in expanded or "`" in expanded:
        # Unresolvable runtime expansion: best-effort guard does not classify it.
        return False
    try:
        return protected_category(resolve_path(raw, base)) is not None
    except (OSError, ValueError, RuntimeError):
        return False


def file_tool_write_is_protected(tool_name: str, tool_input: dict, cwd: Path) -> bool:
    """Edit/Write/NotebookEdit/MultiEdit targets. Resolution failures deny only plausible AIPS paths."""
    key = FILE_EDIT_TOOLS.get(tool_name)
    if key is None:
        return False
    raw = tool_input.get(key)
    if not isinstance(raw, str) or not raw:
        return False
    try:
        return protected_category(resolve_path(raw, cwd)) is not None
    except (OSError, ValueError, RuntimeError):
        return "aips" in raw.lower()


def _tokens(command: str) -> list[str]:
    # Newlines outside quotes separate commands; inside quotes the extra spaces are harmless data.
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _positional(args: list[str]) -> list[str]:
    return [arg for arg in args if arg and not arg.startswith("-")]


def _git_write_targets(args: list[str], env: dict[str, str], base: Path) -> list[Path] | None:
    """Return the repository directories a git write would touch, or None for a read-only verb."""
    directory = base
    git_dirs: list[str] = []
    index = 0
    verb = None
    while index < len(args):
        arg = args[index]
        if arg == "-C" and index + 1 < len(args):
            directory = resolve_path(args[index + 1], directory)
            index += 2
            continue
        if arg in {"-c", "--namespace", "--super-prefix"} and index + 1 < len(args):
            index += 2
            continue
        if arg.startswith(("--git-dir=", "--work-tree=")):
            git_dirs.append(arg.split("=", 1)[1])
        elif arg in {"--git-dir", "--work-tree"} and index + 1 < len(args):
            git_dirs.append(args[index + 1])
            index += 2
            continue
        elif not arg.startswith("-"):
            verb = arg
            break
        index += 1
    if verb is None or verb in GIT_READ_VERBS:
        return None
    targets = [directory]
    for raw in git_dirs + [env[key] for key in ("GIT_DIR", "GIT_WORK_TREE") if key in env]:
        targets.append(resolve_path(raw, directory))
    return targets


def _segment_writes_protected(words: list[str], state: dict, depth: int) -> bool:
    env: dict[str, str] = {}
    while words and ASSIGNMENT_RE.match(words[0]):
        key, _, value = words.pop(0).partition("=")
        env[key] = value
    redirects: list[str] = []
    args: list[str] = []
    index = 0
    while index < len(words):
        if words[index] in REDIRECT_TOKENS and index + 1 < len(words):
            redirects.append(words[index + 1])
            index += 2
            continue
        args.append(words[index])
        index += 1
    base: Path = state["cwd"]
    if any(_protected_raw(raw, base) for raw in redirects):
        return True
    while args and os.path.basename(args[0]) in TRANSPARENT_WRAPPERS:
        args = args[1:]
        while args and args[0].startswith("-"):
            args = args[1:]
    if not args:
        return False
    verb = os.path.basename(args[0])
    rest = args[1:]
    if verb == "cd":
        target = rest[0] if rest and rest[0] != "-" else "~"
        try:
            state["cwd"] = resolve_path(target, base)
        except (OSError, ValueError, RuntimeError):
            state["cwd"] = base
        return False
    if verb in SHELL_WRAPPERS and "-c" in rest and rest.index("-c") + 1 < len(rest):
        return _command_writes_protected(rest[rest.index("-c") + 1], state, depth + 1)
    if verb == "eval" and rest:
        return _command_writes_protected(" ".join(rest), state, depth + 1)
    if verb == "git":
        git_targets = _git_write_targets(rest, env, base)
        return bool(git_targets) and any(protected_category(target) is not None for target in git_targets)
    targets: list[str] = []
    if verb in ALL_ARG_WRITE_COMMANDS:
        targets = _positional(rest)
    elif verb in DEST_LAST_COMMANDS:
        if "-t" in rest and rest.index("-t") + 1 < len(rest):
            targets = [rest[rest.index("-t") + 1]]
        elif "-d" in rest or "--directory" in rest:
            targets = _positional(rest)
        else:
            positional = _positional(rest)
            targets = positional[-1:]
    elif verb in MOVE_COMMANDS or (verb == "sed" and any(SED_INPLACE_RE.match(arg) for arg in rest)):
        targets = _positional(rest)
    elif verb == "dd":
        targets = [arg[3:] for arg in rest if arg.startswith("of=")]
    return any(_protected_raw(raw, base) for raw in redirects + targets)


def _command_writes_protected(command: str, state: dict, depth: int) -> bool:
    if depth > MAX_WRAPPER_DEPTH:
        return True
    try:
        tokens = _tokens(command)
    except ValueError:
        return bool(re.search(r"aips|\.local/share|\.config", command, re.IGNORECASE))
    segment: list[str] = []
    for token in tokens + [";"]:
        if token in CONTROL_TOKENS:
            if segment and _segment_writes_protected(segment, state, depth):
                return True
            segment = []
        else:
            segment.append(token)
    return False


def bash_command_writes_protected(command: str, cwd: Path) -> bool:
    """Best-effort check for common Shell write forms that target protected paths."""
    if not command:
        return False
    try:
        return _command_writes_protected(command, {"cwd": cwd}, 0)
    except (OSError, ValueError, RuntimeError):
        return True
