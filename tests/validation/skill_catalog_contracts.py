"""One owning validation for the registry-backed Skill Explorer and source intake."""

import json
import subprocess
import sys
from collections import Counter

import yaml

from .static_contracts import ROOT, errors

manifest_path = ROOT / "skills/integrations/matt-pocock-skills.json"
registry_path = ROOT / "skills/INDEX.yaml"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
records = manifest.get("skills", [])
expected_counts = {"engineering": 20, "productivity": 7, "in-progress": 7, "misc": 4}
counts = Counter(record.get("category") for record in records)

if manifest.get("source", {}).get("commit") != "49dd158d1076134a641b33efb035946536778336":
    errors.append("Matt Pocock source commit must remain pinned")
if len(records) != 38 or counts != expected_counts:
    errors.append(f"upstream Skill disposition inventory mismatch: {len(records)} / {dict(counts)}")
if len({record.get("id") for record in records}) != len(records):
    errors.append("upstream Skill ids must be unique")
if len({record.get("path") for record in records}) != len(records):
    errors.append("upstream Skill paths must be unique")

registry = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
active = registry.get("skills", {})
required = {
    "prototype", "technical-research", "human-guided-wizard",
    "technical-teaching", "issue-triage", "writing-fragments",
    "writing-beats", "writing-shape",
}
if not required.issubset(active):
    errors.append("all admitted optional and selected Writing Skills must be registered")
if len(active) != 48:
    errors.append(f"expected 48 current AIPS Skill cards, found {len(active)}")

by_id = {record.get("id"): record for record in records}
for identifier in ("writing-fragments", "writing-beats", "writing-shape"):
    record = by_id.get(identifier)
    if not record or record.get("disposition") != "adopted_optional":
        errors.append(f"{identifier} must remain an explicitly selected optional Skill")
    source = active.get(identifier) or {}
    if not source.get("triggers") or any(not trigger.startswith("explicit_") for trigger in source["triggers"]):
        errors.append(f"{identifier} must only use explicit request triggers")
for identifier in ("chief-of-staff", "claude-handoff", "loop-me", "setup-ts-deep-modules"):
    record = by_id.get(identifier) or {}
    if record.get("disposition") in {"adopted", "adopted_optional"}:
        errors.append(f"excluded or untested Beta Skill was activated: {identifier}")

for identifier in required:
    skill_path = ROOT / "skills" / active[identifier]["path"]
    if not skill_path.is_file():
        errors.append(f"registered Skill source is missing: {skill_path.relative_to(ROOT)}")

generator = ROOT / "scripts/skill_catalog.py"
if generator.is_file():
    result = subprocess.run(
        [sys.executable, str(generator), "--check"],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode:
        errors.append("Skill catalog generation check failed: " + result.stdout + result.stderr)
else:
    errors.append("Skill catalog generator is missing")

scenario = ROOT / "tests/scenarios/259-matt-pocock-skill-integration.md"
if not scenario.is_file():
    errors.append("Scenario 259 is missing")

skills_cli = ROOT / "scripts/skills_cli.py"
if skills_cli.is_file():
    for include_upstream, expected in ((False, 48), (True, 86)):
        args = [sys.executable, str(skills_cli), "list", "--format", "json"]
        if include_upstream:
            args.append("--include-upstream")
        result = subprocess.run(args, cwd=ROOT, capture_output=True, check=False, text=True)
        try:
            listing = json.loads(result.stdout)
        except json.JSONDecodeError:
            errors.append(f"AIPS Skill list did not emit valid JSON: {result.stderr}")
            continue
        if result.returncode or len(listing) != expected:
            errors.append(f"AIPS Skill list returned an unexpected inventory count: {len(listing)}")
        if not all(item.get("locale") == "zh-TW" and item.get("description") for item in listing):
            errors.append("AIPS Skill list must provide nonempty Traditional Chinese descriptions by default")
        if include_upstream and not any(item.get("id") == "grill-me" and item.get("source") == "upstream" and item.get("status") == "workflow" for item in listing):
            errors.append("upstream grill-me must be listed with its workflow disposition")
else:
    errors.append("AIPS Skill list CLI is missing")

localization = json.loads((ROOT / "skills/locale/zh-TW.json").read_text(encoding="utf-8"))
missing_locales = (set(active) | {record.get("id") for record in records}) - set(localization)
if missing_locales:
    errors.append("Traditional Chinese Skill descriptions missing: " + ", ".join(sorted(missing_locales)))
