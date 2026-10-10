"""Bounded shell AST extraction; unsupported syntax is a denial, never a bypass."""
from __future__ import annotations

import re
import shlex
from typing import Any


class CommandError(ValueError):
    def __init__(self, message: str, reason_code: str = "UNSUPPORTED_SHELL_SYNTAX"):
        super().__init__(message)
        self.reason_code = reason_code


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


def _embedded_substitutions(raw: str) -> list[str]:
    """Extract command substitutions hidden inside Bash parameter-expansion nodes."""
    results: list[str] = []
    i = 0
    quote = None
    while i < len(raw):
        char = raw[i]
        if char == "\\" and quote != "'":
            i += 2
            continue
        if quote == "'":
            if char == "'":
                quote = None
            i += 1
            continue
        if char in "'\"":
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
            i += 1
            continue
        active = quote in {None, '"'}
        if active and raw.startswith("$(", i) and not raw.startswith("$((", i):
            depth = 1
            j = i + 2
            nested_quote = None
            while j < len(raw):
                token = raw[j]
                if token == "\\" and nested_quote != "'":
                    j += 2
                    continue
                if nested_quote == "'":
                    if token == "'":
                        nested_quote = None
                    j += 1
                    continue
                if token in "'\"`":
                    if nested_quote == token:
                        nested_quote = None
                    elif nested_quote is None:
                        nested_quote = token
                    j += 1
                    continue
                if token == "(":
                    depth += 1
                elif token == ")":
                    depth -= 1
                    if depth == 0:
                        results.append(raw[i + 2:j])
                        i = j + 1
                        break
                j += 1
            else:
                raise CommandError("unterminated nested command substitution")
            continue
        if active and char == "`":
            j = i + 1
            while j < len(raw):
                if raw[j] == "\\":
                    j += 2
                    continue
                if raw[j] == "`":
                    results.append(raw[i + 1:j])
                    i = j + 1
                    break
                j += 1
            else:
                raise CommandError("unterminated nested backtick substitution")
            continue
        i += 1
    return results


def _mask_heredocs(source: str) -> tuple[str, list[str]]:
    lines = source.splitlines(keepends=True)
    result: list[str] = []
    expansions: list[str] = []
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
                    raise CommandError("unsupported heredoc delimiter", "UNSUPPORTED_HEREDOC")
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
                if not quoted:
                    expansions.append(body.lstrip("\t") if tabs else body)
                result.append("\n" if body.endswith("\n") else "")
                index += 1
                if candidate == delimiter:
                    break
            else:
                raise CommandError("unterminated heredoc", "UNSUPPORTED_HEREDOC")
    return "".join(result), expansions


def shell_commands(source: str) -> list[list[str]]:
    """Return executable command nodes, including command/process substitutions."""
    import bashlex

    if not source.strip():
        return []
    normalized, heredoc_expansions = _mask_heredocs(source)
    try:
        trees = bashlex.parse(normalized)
    except (ValueError, NotImplementedError, bashlex.errors.ParsingError) as exc:
        raise CommandError("unsupported or malformed shell syntax") from exc
    commands: list[list[str]] = []

    def walk(node: Any, source_text: str) -> None:
        if not hasattr(node, "kind"):
            return
        if node.kind == "parameter":
            raw = source_text[node.pos[0]:node.pos[1]]
            for embedded in _embedded_substitutions(raw):
                try:
                    embedded_trees = bashlex.parse(embedded)
                except (ValueError, NotImplementedError, bashlex.errors.ParsingError) as exc:
                    raise CommandError("unsupported nested parameter expansion") from exc
                for embedded_tree in embedded_trees:
                    walk(embedded_tree, embedded)
        if node.kind == "command":
            words = [part for part in node.parts if part.kind in {"word", "assignment"}]
            argv = []
            for word in words:
                raw = source_text[word.pos[0]:word.pos[1]]
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
                    walk(child, source_text)
            elif hasattr(value, "kind"):
                walk(value, source_text)

    for tree in trees:
        walk(tree, normalized)
    # A double-quoted wrapper preserves heredoc text as data while leaving only
    # the heredoc's real $() and backtick expansions active for bashlex to parse.
    # Escaping literal double quotes keeps them from changing the wrapper's parse.
    for body in heredoc_expansions:
        wrapper = 'printf "%s" "' + body.replace('"', '\\"') + '"'
        try:
            expansion_trees = bashlex.parse(wrapper)
        except (ValueError, NotImplementedError, bashlex.errors.ParsingError) as exc:
            raise CommandError("unsupported or malformed heredoc expansion", "UNSUPPORTED_HEREDOC") from exc
        for tree in expansion_trees:
            walk(tree, wrapper)
    return commands
