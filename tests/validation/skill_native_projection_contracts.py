"""Contract checks for AIPS native Agent Skill installations."""

from __future__ import annotations

import yaml

from .static_contracts import ROOT, errors

module = ROOT / "scripts/native_skill_projection.py"
commands = ROOT / "scripts/portable_commands.py"
registry = ROOT / "harness/commands/REGISTRY.yaml"
for path in (module, commands, registry):
    if not path.is_file():
        errors.append(f"Native Skill installation artifact missing: {path.relative_to(ROOT)}")

if module.is_file():
    source = module.read_text(encoding="utf-8")
    for expected in ("ALREADY_PRESENT_UNOWNED", "CONFLICT_PRESERVED", "RETAINED_SHARED", "source_digest", "project_root"):
        if expected not in source:
            errors.append(f"Native Skill ownership contract is missing {expected}")
if commands.is_file():
    source = commands.read_text(encoding="utf-8")
    if "native_skill_projection" not in source or "portable-command" not in source:
        errors.append("Portable Commands do not route through the native Skill ownership manifest")
if registry.is_file():
    source = registry.read_text(encoding="utf-8")
    try:
        hosts = (yaml.safe_load(source) or {}).get("hosts", {})
    except yaml.YAMLError as exc:
        hosts = {}
        errors.append(f"Portable Command registry YAML is invalid: {exc}")
    for host, path in (("codex", "~/.agents/skills"), ("claude", "~/.claude/skills"), ("gemini", "~/.agents/skills")):
        if hosts.get(host, {}).get("renderer") != "markdown-skill" or hosts.get(host, {}).get("placement") != path:
            errors.append(f"{host} does not declare its native Skill discovery path")

evidence = ROOT / "tests/evidence/skills_cli_lifecycle.py"
if not evidence.is_file():
    errors.append("Native Skill installation lifecycle evidence is missing")
