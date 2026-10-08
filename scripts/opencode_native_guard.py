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
SHELL_META = re.compile(r"[;&|><`$\n\r]")


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
    new_creative_assets = (
        tool == "write"
        and
        not git_project
        and classification.get("domain") == "creative"
        and classification.get("intent") == "create"
        and all(target.suffix.lower() in ASSET_SUFFIXES and not target.exists() for target in targets)
    )
    if new_creative_assets:
        return {"decision": "ALLOW", "level": "L1", "reason": "new local creative asset in a non-Git workspace; confined target only"}

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


def evaluate_shell(*, command: str, cwd: str, root: str) -> dict[str, Any]:
    """Allow only a bounded, metacharacter-free read-only shell subset."""
    safe_cwd, normalized = inside_root(cwd, root)
    if not safe_cwd:
        return {"decision": "DENY", "level": "L2", "reason": "Shell working directory escapes project root"}
    if SHELL_META.search(command):
        return {"decision": "DENY", "level": "L2", "reason": "Shell operators and substitutions are unsupported"}
    try:
        words = shlex.split(command)
    except ValueError:
        words = []
    if not words or Path(words[0]).name not in READ_ONLY_COMMANDS:
        return {"decision": "DENY", "level": "L2", "reason": "Shell command is outside the bounded read-only allowlist"}
    if Path(words[0]).name == "find" and any(item in {"-delete", "-exec", "-execdir", "-ok", "-okdir"} for item in words[1:]):
        return {"decision": "DENY", "level": "L2", "reason": "Find actions that can execute or remove are unsupported"}
    if Path(words[0]).name == "sed" and any(item == "-i" or item.startswith("-i") for item in words[1:]):
        return {"decision": "DENY", "level": "L2", "reason": "in-place Sed edits are outside the read-only allowlist"}
    if Path(words[0]).name == "git" and (len(words) < 2 or words[1] not in {"status", "log", "diff", "show", "branch", "rev-parse"}):
        return {"decision": "DENY", "level": "L2", "reason": "Git command is outside the bounded read-only allowlist"}
    # Constrain explicit path operands (including git -C and absolute paths) to
    # the project. This is deliberately conservative for slash-containing
    # arguments such as grep patterns: ambiguous inputs are denied.
    root_path = Path(root).resolve(strict=True)
    for word in words[1:]:
        if word.startswith("-"):
            continue
        candidate = Path(word).expanduser()
        if candidate.is_absolute() or word.startswith(("./", "../", "~/")) or "/" in word:
            if not candidate.is_absolute():
                candidate = Path(normalized) / candidate
            resolved = candidate.resolve(strict=False)
            try:
                resolved.relative_to(root_path)
            except ValueError:
                return {"decision": "DENY", "level": "L2", "reason": "Shell path operand escapes project root"}
    return {"decision": "ALLOW", "level": "L1", "reason": "bounded read-only Shell command", "cwd": normalized}


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
    except (OSError, ValueError, TypeError, subprocess.SubprocessError) as exc:
        result = {"decision": "DENY", "level": "L2", "reason": f"guard unavailable: {type(exc).__name__}"}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("decision") == "ALLOW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
