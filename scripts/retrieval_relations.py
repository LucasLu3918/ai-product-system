"""Bounded lexical relation extraction primitives for Retrieval Intelligence."""

from __future__ import annotations

import re
from typing import Any

_CALL_KEYWORDS = {
    "if", "for", "while", "switch", "catch", "with", "function", "def", "class",
    "return", "new", "typeof", "sizeof", "nameof", "select", "where", "when",
    "lock", "using", "import", "require", "assert", "print", "async",
}
_CALL_PATTERN = re.compile(r"(?<![\w$])([A-Za-z_$][A-Za-z0-9_$]*)\s*\(")
_REFERENCE_PATTERN = re.compile(r"(?<![\w$])([A-Za-z_$][A-Za-z0-9_$]*)(?![\w$])")


def code_without_comments_or_strings(text: str) -> str:
    """Mask comments and quoted strings while preserving line and column offsets."""
    out = list(text)
    i = 0
    state = "code"
    quote = ""
    while i < len(text):
        char = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if state == "line":
            if char == "\n":
                state = "code"
            else:
                out[i] = " "
            i += 1
            continue
        if state == "block":
            if char == "*" and nxt == "/":
                out[i] = out[i + 1] = " "
                i += 2
                state = "code"
                continue
            if char != "\n":
                out[i] = " "
            i += 1
            continue
        if state == "string":
            if char == "\\":
                if char != "\n":
                    out[i] = " "
                if i + 1 < len(text):
                    if text[i + 1] != "\n":
                        out[i + 1] = " "
                    i += 2
                    continue
            if text.startswith(quote, i):
                for offset in range(len(quote)):
                    if text[i + offset] != "\n":
                        out[i + offset] = " "
                i += len(quote)
                state = "code"
                continue
            if char != "\n":
                out[i] = " "
            i += 1
            continue

        if char == "/" and nxt == "/":
            out[i] = out[i + 1] = " "
            i += 2
            state = "line"
            continue
        if char == "/" and nxt == "*":
            out[i] = out[i + 1] = " "
            i += 2
            state = "block"
            continue
        if char == "#" or (char == "-" and nxt == "-"):
            out[i] = " "
            if nxt == "-":
                out[i + 1] = " "
                i += 2
            else:
                i += 1
            state = "line"
            continue
        if char in "'\"`":
            quote = char * 3 if text.startswith(char * 3, i) else char
            for offset in range(len(quote)):
                if text[i + offset] != "\n":
                    out[i + offset] = " "
            i += len(quote)
            state = "string"
            continue
        i += 1
    return "".join(out)


def relation_rows(
    masked_text: str,
    definitions: list[tuple[str, str, int]],
    *,
    max_rows: int,
) -> list[dict[str, Any]]:
    """Build bounded lexical call/reference rows from masked source text."""
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(masked_text.splitlines(), start=1):
        owner_name = "@file"
        owner_line = 0
        for name, _kind, definition_line in definitions:
            if definition_line > line_no:
                break
            owner_name, owner_line = name, definition_line
        if owner_name != "@file" and any(
            definition_line == line_no and name == owner_name
            for name, _kind, definition_line in definitions
        ):
            continue
        call_names = {
            match.group(1) for match in _CALL_PATTERN.finditer(line)
            if match.group(1).lower() not in _CALL_KEYWORDS
        }
        names = set(_REFERENCE_PATTERN.findall(line))
        for name in sorted(names):
            if name.lower() in _CALL_KEYWORDS:
                continue
            relation = "calls" if name in call_names else "references"
            rows.append({
                "source_name": owner_name,
                "source_definition_line": owner_line,
                "target_name": name,
                "source_line": line_no,
                "relation": relation,
            })
            if len(rows) >= max_rows:
                return rows
    return rows
