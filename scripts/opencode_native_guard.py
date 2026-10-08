"""Deterministic, narrow OpenCode action classification and path guard."""
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

WRITE_TOOLS = {"write", "edit", "patch", "apply_patch"}
ASSET_SUFFIXES = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif"}
READ_ONLY_COMMANDS = {"pwd", "ls", "cat", "head", "tail", "sed", "rg", "grep", "find", "git", "stat", "file", "wc"}
SAFE_AIPS_COMMANDS = {("doctor",), ("harness", "status"), ("intelligence", "status"), ("creative", "discover"), ("creative", "preflight"), ("creative", "next-version"), ("creative", "trace"), ("project", "check")}
SHELL_META = re.compile(r"[;&|><`$\n\r]")
FIND_SIDE_EFFECTS = {"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprint0", "-fprintf", "-fls"}
SENSITIVE_OPTIONS = {"-c", "--config-env", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config", "--files0-from", "--pre", "--pre-glob"}


def inside_root(path: str, root: str) -> tuple[bool, str]:
    base = Path(root).resolve(strict=True)
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = base / candidate
    # strict=False resolves every existing symlink while allowing a new leaf.
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(base)
    except ValueError:
        return False, "target escapes project root"
    return True, str(resolved)


def is_git_project(root: Path) -> bool:
    result = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=3, check=False)
    return result.returncode == 0


def evaluate_write(*, tool: str, resources: list[str], root: str, manifest: dict[str, Any]) -> dict[str, Any]:
    """Return a direct-action decision; this does not inspect Shell/MCP effects."""
    if tool == "external_action":
        return {"decision": "DENY", "level": "L3", "reason": "external actions require the existing Human approval gate"}
    if tool not in WRITE_TOOLS:
        return {"decision": "UNSUPPORTED", "level": "L0", "reason": "operation is outside the supported native write tools"}
    if not resources or any(not isinstance(item, str) or not item.strip() for item in resources):
        return {"decision": "DENY", "level": "L2", "reason": "native write target is missing or ambiguous"}
    targets: list[Path] = []
    for raw in resources:
        safe, resolved = inside_root(raw, root)
        if not safe:
            return {"decision": "DENY", "level": "L2", "reason": resolved}
        targets.append(Path(resolved))

    task = manifest.get("task") if isinstance(manifest.get("task"), dict) else {}
    classification = task.get("classification") if isinstance(task.get("classification"), dict) else {}
    intelligence = manifest.get("intelligence") if isinstance(manifest.get("intelligence"), dict) else {}
    freshness = manifest.get("freshness") if isinstance(manifest.get("freshness"), dict) else {}
    fail_policy = manifest.get("fail_policy") if isinstance(manifest.get("fail_policy"), dict) else {}
    instructions = manifest.get("instruction_resolution") if isinstance(manifest.get("instruction_resolution"), dict) else {}

    root_path = Path(root).resolve(strict=True)
    git_project = is_git_project(root_path)
    creative_intent = (
        tool in {"write", "edit"}
        and classification.get("domain") == "creative"
        and classification.get("intent") == "create"
    )
    if creative_intent and git_project:
        return {"decision": "DENY", "level": "L2", "reason": "creative asset writes inside Git workspaces require current Project Intelligence"}
    if creative_intent:
        if classification.get("creative_medium") == "raster" and any(target.suffix.lower() == ".svg" for target in targets):
            return {"decision": "DENY", "level": "L1", "reason_code": "creative_medium_mismatch", "reason": "Requested raster artwork cannot silently fall back to SVG"}
        if all(target.suffix.lower() in ASSET_SUFFIXES and not target.exists() for target in targets):
            return {"decision": "ALLOW", "level": "L1", "reason": "new local creative asset in a non-Git workspace; confined target only"}
        reason = "creative output target already exists" if any(target.exists() for target in targets) else "creative output target must use a supported asset extension"
        return {"decision": "DENY", "level": "L2", "reason": reason}

    reasons = []
    if intelligence.get("readiness") != "READY":
        reasons.append("Project Intelligence readiness is not READY")
    if freshness.get("status") != "CURRENT":
        reasons.append("Project Intelligence freshness is not CURRENT")
    if fail_policy.get("mode") == "closed":
        reasons.extend(str(item) for item in fail_policy.get("reasons", []) if item)
    if instructions.get("requires_resolution") is True:
        reasons.append("project instruction authority conflict requires resolution")
    if reasons:
        return {"decision": "DENY", "level": "L2", "reason": "; ".join(dict.fromkeys(reasons))}
    return {"decision": "ALLOW", "level": "L2", "reason": "current Project Intelligence and confined native target"}


def _option_path(value: str) -> bool:
    """Whether an argument is a path-bearing option that needs confinement."""
    return value in {"-f", "--file", "--exclude-from", "--include-from", "--label"} or value.startswith(("--file=", "--exclude-from=", "--include-from="))


def _check_operand_path(word: str, *, cwd: Path, root: Path) -> bool:
    candidate = Path(word).expanduser()
    if not candidate.is_absolute():
        candidate = cwd / candidate
    try:
        candidate.resolve(strict=False).relative_to(root)
    except ValueError:
        return False
    return True


def _aips_read_only(words: list[str], *, cwd: Path, root: Path) -> tuple[bool, str, str]:
    """Allow only fixed, read-only AIPS diagnostics; this is not a general CLI exemption."""
    command = tuple(words[1:3]) if len(words) >= 3 and words[1] in {"harness", "intelligence", "creative", "project"} else tuple(words[1:2])
    if command not in SAFE_AIPS_COMMANDS:
        return False, "shell_aips_command_unsupported", "AIPS command is outside the bounded read-only diagnostic allowlist"
    if command == ("project", "check"):
        if len(words) != 4 or not _check_operand_path(words[3], cwd=cwd, root=root):
            return False, "shell_aips_arguments_unsupported", "AIPS project check accepts one confined path"
        return True, "shell_aips_readonly", "bounded read-only AIPS diagnostic"
    command_options = {
        ("creative", "discover"): {"--project"},
        ("creative", "preflight"): {"--project", "--bundle"},
        ("creative", "next-version"): {"--project", "--target"},
        ("creative", "trace"): {"--limit"},
    }
    allowed_options = command_options.get(command, set())
    values: dict[str, str] = {}
    index = 1 + len(command)
    while index < len(words):
        option = words[index]
        if option not in allowed_options or index + 1 >= len(words) or words[index + 1].startswith("-"):
            return False, "shell_aips_arguments_unsupported", "AIPS diagnostic accepts only its bounded path and format arguments"
        value = words[index + 1]
        if option in {"--project", "--bundle", "--target"} and not _check_operand_path(value, cwd=cwd, root=root):
            return False, "shell_path_escape", "AIPS diagnostic path escapes the project root"
        if option == "--limit" and (not value.isdigit() or not 1 <= int(value) <= 100):
            return False, "shell_aips_arguments_unsupported", "AIPS trace limit must be between 1 and 100"
        if option in values:
            return False, "shell_aips_arguments_unsupported", "AIPS diagnostic path option was repeated"
        values[option] = value
        index += 2
    required = {
        ("creative", "preflight"): {"--project", "--bundle"},
        ("creative", "next-version"): {"--project", "--target"},
        ("project", "check"): set(),
    }.get(command, set())
    if not required.issubset(values):
        return False, "shell_aips_arguments_unsupported", "AIPS diagnostic is missing a required bounded path"
    if command == ("creative", "trace") and any(option != "--limit" for option in values):
        return False, "shell_aips_arguments_unsupported", "AIPS creative trace accepts only --limit"
    return True, "shell_aips_readonly", "bounded read-only AIPS diagnostic"


def _shell_reason_code(reason: str, decision: str) -> str:
    if decision == "ALLOW":
        return "shell_readonly_allow"
    lowered = reason.lower()
    if "working directory escapes" in lowered or "path escapes" in lowered or "path operand escapes" in lowered:
        return "shell_path_escape"
    if "operators and substitutions" in lowered:
        return "shell_operators_unsupported"
    if "outside the bounded read-only allowlist" in lowered:
        return "shell_command_unsupported"
    if "find actions" in lowered:
        return "shell_find_effect_unsupported"
    if "sed" in lowered:
        return "shell_sed_effect_unsupported"
    if "git" in lowered:
        return "shell_git_command_unsupported"
    if "option" in lowered:
        return "shell_option_unsupported"
    return "shell_policy_denied"


def evaluate_shell(*, command: str, cwd: str, root: str) -> dict[str, Any]:
    """Allow a small, effect-aware read-only Shell subset.

    This is a command policy, not a complete sandbox: a host process may still
    observe ambient filesystem/network permissions or invoke effects through
    mechanisms outside this parsed command string.
    """
    safe_cwd, normalized = inside_root(cwd, root)
    if not safe_cwd:
        return {"decision": "DENY", "level": "L2", "reason": "Shell working directory escapes project root"}
    if SHELL_META.search(command):
        return {"decision": "DENY", "level": "L2", "reason": "Shell operators and substitutions are unsupported"}
    try:
        words = shlex.split(command)
    except ValueError:
        words = []
    if words and Path(words[0]).name == "aips":
        allowed, reason_code, reason = _aips_read_only(words, cwd=Path(normalized), root=Path(root).resolve(strict=True))
        if not allowed:
            return {"decision": "DENY", "level": "L2", "reason_code": reason_code, "reason": reason}
        return {"decision": "ALLOW", "level": "L1", "reason_code": reason_code, "reason": reason, "cwd": normalized}
    if not words or Path(words[0]).name not in READ_ONLY_COMMANDS:
        return {"decision": "DENY", "level": "L2", "reason": "Shell command is outside the bounded read-only allowlist"}
    executable = Path(words[0]).name
    if any(word in SENSITIVE_OPTIONS or word.split("=", 1)[0] in SENSITIVE_OPTIONS for word in words[1:]):
        return {"decision": "DENY", "level": "L2", "reason": "Shell option can change command execution or redirect its search root"}
    if executable == "find" and any(item.split("=", 1)[0] in FIND_SIDE_EFFECTS for item in words[1:]):
        return {"decision": "DENY", "level": "L2", "reason": "Find actions that can execute or remove are unsupported"}
    if executable == "sed" and any(item == "-i" or item.startswith("-i") for item in words[1:]):
        return {"decision": "DENY", "level": "L2", "reason": "in-place Sed edits are outside the read-only allowlist"}
    if executable == "sed":
        scripts = [value[2:] for value in words[1:] if value.startswith("-e") and len(value) > 2]
        scripts.extend(words[index + 1] for index, value in enumerate(words[1:]) if value in {"-e", "--expression"} and index + 2 < len(words))
        # Sed's e/w commands can execute programs or write files. Since parsing
        # the full Sed language is not a security boundary, refuse these forms.
        if any(re.search(r"(?<!\\)(?:^|[;}\n\r])\s*[0-9,$!~,/+*?\[\]().^-]*[ew](?:\s|$|;|})", script) or re.search(r"(?<!\\)/[a-zA-Z0-9_.-]*/(?:e|w)(?:\s|$|;)", script) for script in scripts):
            return {"decision": "DENY", "level": "L2", "reason": "Sed scripts with execute or file-write commands are unsupported"}
    if executable == "git":
        # Parse only explicit, harmless global directory selection. Reject all
        # other global configuration that can alter aliases, hooks or paths.
        git_args = words[1:]
        while git_args and git_args[0] in {"-C", "--literal-pathspecs", "--no-pager"}:
            if git_args[0] == "-C":
                if len(git_args) < 2 or not _check_operand_path(git_args[1], cwd=Path(normalized), root=Path(root).resolve(strict=True)):
                    return {"decision": "DENY", "level": "L2", "reason": "Git directory selection escapes project root"}
                git_args = git_args[2:]
            else:
                git_args = git_args[1:]
        if not git_args or git_args[0] not in {"status", "log", "diff", "show", "branch", "rev-parse"}:
            return {"decision": "DENY", "level": "L2", "reason": "Git command is outside the bounded read-only allowlist"}
    # Path-valued options must be checked along with positional path operands.
    root_path = Path(root).resolve(strict=True)
    cwd_path = Path(normalized)
    skip_value = False
    for word in words[1:]:
        if skip_value:
            if not _check_operand_path(word, cwd=cwd_path, root=root_path):
                return {"decision": "DENY", "level": "L2", "reason": "Shell option path escapes project root"}
            skip_value = False
            continue
        if _option_path(word):
            if "=" in word:
                value = word.split("=", 1)[1]
                if not _check_operand_path(value, cwd=cwd_path, root=root_path):
                    return {"decision": "DENY", "level": "L2", "reason": "Shell option path escapes project root"}
            else:
                skip_value = True
            continue
        if word.startswith("-"):
            continue
        # Refuse ambiguous explicit paths, including options that are joined to
        # their values. Non-path search patterns remain valid for grep/rg.
        if (word.startswith(("./", "../", "~/", "/")) or "/" in word) and not _check_operand_path(
            word, cwd=cwd_path, root=root_path
        ):
            return {"decision": "DENY", "level": "L2", "reason": "Shell path operand escapes project root"}
    if skip_value:
        return {"decision": "DENY", "level": "L2", "reason": "Shell path option is missing its value"}
    return {"decision": "ALLOW", "level": "L1", "reason_code": "shell_readonly_allow", "reason": "bounded read-only command policy; external process effects remain outside the guard", "cwd": normalized}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    write = sub.add_parser("write")
    write.add_argument("--tool", required=True)
    write.add_argument("--resources", required=True)
    write.add_argument("--root", required=True)
    write.add_argument("--manifest", required=True)
    shell = sub.add_parser("shell")
    shell.add_argument("--command", required=True)
    shell.add_argument("--cwd", required=True)
    shell.add_argument("--root", required=True)
    args = parser.parse_args()
    try:
        if args.command == "write":
            result = evaluate_write(tool=args.tool, resources=json.loads(args.resources), root=args.root, manifest=json.loads(args.manifest))
        else:
            result = evaluate_shell(command=args.command, cwd=args.cwd, root=args.root)
            result.setdefault("reason_code", _shell_reason_code(str(result.get("reason", "")), str(result.get("decision", "DENY"))))
    except (OSError, ValueError, TypeError, subprocess.SubprocessError) as exc:
        result = {"decision": "DENY", "level": "L2", "reason": f"guard unavailable: {type(exc).__name__}"}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("decision") == "ALLOW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
