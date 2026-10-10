"""Bounded shell AST extraction; unsupported syntax is a denial, never a bypass."""
from __future__ import annotations

import re
import shlex
from typing import Any


class CommandError(ValueError):
    pass


def _unquoted_expansion(raw: str) -> bool:
    quote = None
    escaped = False
    for index, char in enumerate(raw):
        if escaped:
            if char == '\n':
                return True  # Shell removes continuation; shlex must not change the inspected value.
            escaped = False
            continue
        if char == '\\' and quote != "'":
            escaped = True
        elif quote:
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
        elif char in '*?[{' or char == '~' and index == 0:
            return True
    return False


def _mask_heredocs(source: str) -> str:
    lines = source.splitlines(keepends=True)
    result: list[str] = []
    index = 0
    quote = None
    while index < len(lines):
        line = lines[index]
        pending = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == "\\" and quote != "'":
                i += 2
                continue
            if quote:
                if ch == quote:
                    quote = None
            elif ch in "'\"":
                quote = ch
            elif line[i:i + 2] == "<<" and line[i:i + 3] != "<<<":
                match = re.match(r"<<(-?)\s*('([^']+)'|\"([^\"]+)\"|(\\?)([A-Za-z_][A-Za-z0-9_]*))", line[i:])
                if not match:
                    raise CommandError("unsupported heredoc delimiter")
                delimiter = match[3] or match[4] or match[6]
                quoted = bool(match[3] or match[4] or match[5])
                pending.append((delimiter, quoted, bool(match[1])))
                end = i + len(match[0])
                line = line[:i] + " " * (end - i) + line[end:]
                i = end
                continue
            i += 1
        result.append(line)
        index += 1
        for delimiter, quoted, tabs in pending:
            while index < len(lines):
                body = lines[index]
                candidate = body.rstrip("\r\n")
                if tabs:
                    candidate = candidate.lstrip("\t")
                result.append("\n" if body.endswith("\n") else "")
                index += 1
                if candidate == delimiter:
                    break
                if not quoted and ("$" in body or "`" in body):
                    raise CommandError("executable or variable expansion in heredoc requires separate commands")
            else:
                raise CommandError("unterminated heredoc")
    return "".join(result)


def shell_commands(source: str) -> list[list[str]]:
    """Return executable command nodes, including command/process substitutions."""
    import bashlex

    if not source.strip():
        return []
    normalized = _mask_heredocs(source)
    try:
        trees = bashlex.parse(normalized)
    except (ValueError, NotImplementedError, bashlex.errors.ParsingError) as exc:
        raise CommandError("unsupported or malformed shell syntax") from exc
    commands: list[list[str]] = []

    def walk(node: Any) -> None:
        if not hasattr(node, "kind"):
            return
        if node.kind == "command":
            words = [part for part in node.parts if part.kind in {"word", "assignment"}]
            argv = []
            for word in words:
                raw = normalized[word.pos[0]:word.pos[1]]
                # Dynamic executable/arguments cannot bind an exact publication action.
                if _unquoted_expansion(raw):
                    argv.append('\0shell-expansion:' + raw)
                elif getattr(word, "parts", None):
                    argv.append(raw)
                else:
                    try:
                        values = shlex.split(raw)
                    except ValueError as exc:
                        raise CommandError("malformed command word") from exc
                    argv.append(values[0] if len(values) == 1 else raw)
            commands.append(argv)
        for value in vars(node).values():
            if isinstance(value, list):
                for child in value:
                    walk(child)
            elif hasattr(value, "kind"):
                walk(value)

    for tree in trees:
        walk(tree)
    return commands
