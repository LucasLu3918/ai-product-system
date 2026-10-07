"""Bounded lexical relation extraction primitives for Retrieval Intelligence."""

from __future__ import annotations

import ast
import builtins
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
    call_names_by_line: dict[int, set[str]] | None = None,
) -> list[dict[str, Any]]:
    """Build bounded call/reference rows from masked source text.

    Python callers may supply AST-derived call names so annotations, attributes,
    and local identifiers are not mistaken for function calls. Other languages
    retain the bounded lexical candidate behavior.
    """
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
        call_names = (
            call_names_by_line.get(line_no, set())
            if call_names_by_line is not None
            else {
                match.group(1) for match in _CALL_PATTERN.finditer(line)
                if match.group(1).lower() not in _CALL_KEYWORDS
            }
        )
        names = set(_REFERENCE_PATTERN.findall(line)) | set(call_names)
        for name in sorted(names):
            if name.lower() in _CALL_KEYWORDS:
                continue
            relation = "calls" if name in call_names else "references"
            row = {
                "source_name": owner_name,
                "source_definition_line": owner_line,
                "target_name": name,
                "source_line": line_no,
                "relation": relation,
            }
            if len(rows) < max_rows:
                rows.append(row)
                continue
            if call_names_by_line is None:
                return rows
            if relation != "calls":
                continue
            reference_index = next(
                (index for index, existing in enumerate(rows) if existing["relation"] == "references"),
                None,
            )
            if reference_index is not None:
                rows.pop(reference_index)
                rows.append(row)
    return rows


def python_call_names_by_line(source: str) -> dict[int, set[str]] | None:
    """Return statically named Python calls, or None when parsing fails.

    Only direct ``name(...)`` calls are indexed. Attribute calls such as
    ``mapping.get(...)`` remain references because they do not identify a
    repository function without type or dispatch resolution. Builtins are
    excluded because they cannot be repository consumers.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    calls: dict[int, set[str]] = {}
    builtin_names = vars(builtins)
    imported_names: dict[str, str] = {}
    imported_modules: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_names[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.asname or alias.name.split(".", 1)[0])
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            name = imported_names.get(node.func.id, node.func.id)
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id in imported_modules:
            name = node.func.attr
        else:
            continue
        if name in builtin_names:
            continue
        calls.setdefault(node.lineno, set()).add(name)
    return calls
