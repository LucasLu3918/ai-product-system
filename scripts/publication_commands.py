"""Bounded shell AST extraction; unsupported syntax is a denial, never a bypass."""
from __future__ import annotations

import re
import shlex
from typing import Any


class CommandError(ValueError):
    def __init__(self, message: str, reason_code: str = "UNSUPPORTED_SHELL_SYNTAX", *, detail_code: str | None = None):
        super().__init__(message)
        self.reason_code = reason_code
        aliases = {
            "UNSUPPORTED_SHELL_SYNTAX": "SHELL_SYNTAX_UNSUPPORTED",
            "UNSUPPORTED_WRAPPER": "COMMAND_WRAPPER_UNSUPPORTED",
            "UNSUPPORTED_INTERPRETER": "COMMAND_WRAPPER_UNSUPPORTED",
        }
        self.detail_code = detail_code or aliases.get(reason_code, reason_code)


def command_form_detail(source: str) -> str:
    """Return a stable, input-free classification for a compound shell form."""
    import bashlex

    try:
        trees = bashlex.parse(source)
    except (ValueError, NotImplementedError, bashlex.errors.ParsingError):
        return "SHELL_SYNTAX_UNSUPPORTED"
    kinds: set[str] = set()

    def visit(node: Any) -> None:
        kind = getattr(node, "kind", None)
        if kind:
            kinds.add(kind)
        for value in vars(node).values() if hasattr(node, "__dict__") else ():
            if isinstance(value, list):
                for child in value:
                    visit(child)
            elif hasattr(value, "kind"):
                visit(value)

    for tree in trees:
        visit(tree)
    if "pipeline" in kinds or "pipe" in kinds:
        return "PIPE_UNSUPPORTED"
    if "list" in kinds:
        return "MULTI_COMMAND_UNSUPPORTED"
    if len(trees) > 1:
        return "MULTI_COMMAND_UNSUPPORTED"
    if kinds & {"commandsubstitution", "processsubstitution"}:
        return "PUBLICATION_ARGUMENT_DYNAMIC"
    try:
        _normalized, expansions = _mask_heredocs(inline_literal_heredocs(source))
    except CommandError:
        return "UNSUPPORTED_HEREDOC"
    if expansions:
        # An unquoted heredoc expands variables and substitutions, so its text cannot be bound.
        return "PUBLICATION_ARGUMENT_DYNAMIC"
    return "COMMAND_WRAPPER_UNSUPPORTED"


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


# Claude Code's standard commit-message form. A quoted delimiter keeps the body literal, so the
# substitution is exactly the body without trailing newlines.
_LITERAL_HEREDOC_SUBSTITUTION = re.compile(
    r"\"\$\(cat[ \t]+<<(?P<tabs>-?)[ \t]*'(?P<delim>[A-Za-z_][A-Za-z0-9_]*)'[ \t]*\n"
    r"(?P<body>.*?)\n(?P<indent>\t*)(?P=delim)\n\)\"", re.DOTALL)


def inline_literal_heredocs(source: str) -> str:
    """Replace `"$(cat <<'EOF' ... EOF\n)"` with the equivalent single-quoted literal word.

    Only a prefix of plain words and quotes is scanned; any expansion, backtick, comment or other
    heredoc before a candidate stops inlining, because quoting there cannot be tracked exactly.
    A body line equal to the delimiter would end the heredoc early, so that candidate is left as is.
    """
    parts: list[str] = []
    copied = 0
    i = 0
    quote = None
    while i < len(source):
        char = source[i]
        if quote == "'":
            if char == "'":
                quote = None
            i += 1
            continue
        if quote is None and char == '"':
            match = _LITERAL_HEREDOC_SUBSTITUTION.match(source, i)
            if match:
                tabs = bool(match['tabs'])
                lines = match['body'].split('\n')
                if tabs:
                    lines = [line.lstrip('\t') for line in lines]
                if (not tabs and match['indent']) or match['delim'] in lines:
                    break
                parts.extend([source[copied:i], shlex.quote('\n'.join(lines).rstrip('\n'))])
                copied = i = match.end()
                continue
        if char == '\\':
            i += 2
            continue
        if char == '`' or (char == '#' and quote is None) or source.startswith(('$(', '${', "$'", '<<'), i):
            break
        if char == '"':
            quote = None if quote == '"' else '"'
        elif char == "'" and quote is None:
            quote = "'"
        i += 1
    return ''.join(parts) + source[copied:]


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


def shell_commands(source: str, *, mark_dynamic: bool = False) -> list[list[str]]:
    """Return executable command nodes, including command/process substitutions.

    With ``mark_dynamic`` every word that Bash would expand is prefixed with NUL, so callers can
    tell a literal ``$`` or backtick inside single quotes from a real expansion.
    """
    import bashlex

    if not source.strip():
        return []
    normalized, heredoc_expansions = _mask_heredocs(inline_literal_heredocs(source))
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
                elif getattr(word, "parts", None) or (mark_dynamic and raw.startswith(("$'", '$"'))):
                    argv.append('\0' + raw if mark_dynamic else raw)
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
