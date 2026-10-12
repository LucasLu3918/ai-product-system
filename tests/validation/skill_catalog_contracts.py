"""One owning validation for the registry-backed Skill Explorer and source intake."""

import hashlib
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
    "writing-beats", "writing-shape", "grill-with-docs",
}
if not required.issubset(active):
    errors.append("all admitted optional and selected Writing Skills must be registered")
if len(active) != 49:
    errors.append(f"expected 49 current AIPS Skill cards, found {len(active)}")

by_id = {record.get("id"): record for record in records}
canonical_duplicates = [record for record in records if record.get("id") in active]
installable_upstream = [record for record in records if record.get("id") not in active]
if len(canonical_duplicates) != 7 or len(installable_upstream) != 31:
    errors.append("all 31 distinct upstream Skills must be installable and seven canonical IDs protected")
allowed_dispositions = {"merged", "adopted", "adopted_optional", "workflow", "auto_routed", "experimental_optional"}
if any(record.get("disposition") not in allowed_dispositions for record in records):
    errors.append("every upstream Skill must be AIPS-integrated, auto-routed, or experimental/optional")
for identifier in ("writing-fragments", "writing-beats", "writing-shape"):
    record = by_id.get(identifier)
    if not record or record.get("disposition") != "adopted_optional":
        errors.append(f"{identifier} must remain an explicitly selected optional Skill")
    source = active.get(identifier) or {}
    if not source.get("triggers") or any(not trigger.startswith("explicit_") for trigger in source["triggers"]):
        errors.append(f"{identifier} must only use explicit request triggers")
for identifier in ("chief-of-staff", "claude-handoff", "loop-me", "setup-ts-deep-modules"):
    record = by_id.get(identifier) or {}
    if record.get("disposition") != "experimental_optional":
        errors.append(f"overlapping in-progress Skill must remain experimental/optional: {identifier}")
for identifier in ("migrate-to-shoehorn", "scaffold-exercises", "setup-pre-commit"):
    record = by_id.get(identifier) or {}
    if record.get("disposition") != "auto_routed" or not record.get("aips_targets"):
        errors.append(f"distinct repo/tool Skill must have an automatic AIPS route: {identifier}")
route_triggers = {
    "migrate-to-shoehorn": ("tdd", "typescript_test_fixture_migration"),
    "scaffold-exercises": ("technical-teaching", "exercise_scaffold_setup"),
    "setup-pre-commit": ("tdd", "pre_commit_validation_setup"),
}
for identifier, (target, trigger) in route_triggers.items():
    if target not in active or trigger not in (active.get(target) or {}).get("triggers", []):
        errors.append(f"automatic route for {identifier} is missing canonical target trigger {target}:{trigger}")
for identifier in ("setup-matt-pocock-skills", "git-guardrails-claude-code", "grill-with-docs"):
    record = by_id.get(identifier) or {}
    if record.get("disposition") != "experimental_optional":
        errors.append(f"overlapping upstream Skill must be experimental/optional: {identifier}")
for record in records:
    local_path = record.get("local_path")
    if not local_path:
        errors.append(f"upstream source is not vendored: {record.get('id')}")
        continue
    path = ROOT / local_path
    if not path.is_file():
        errors.append(f"vendored source is missing: {local_path}")
        continue
    if hashlib.sha256(path.read_bytes()).hexdigest() != record.get("sha256"):
        errors.append(f"vendored source digest mismatch: {local_path}")

grill = active.get("grill-with-docs") or {}
grill_source = ROOT / "skills" / grill.get("path", "")
if not grill_source.is_file() or "explicit_grill_with_docs" not in grill.get("triggers", []):
    errors.append("grill-with-docs must be a canonical explicit-invocation Skill")
else:
    openai_policy = grill_source.parent / "agents" / "openai.yaml"
    if not openai_policy.is_file() or "allow_implicit_invocation: false" not in openai_policy.read_text(encoding="utf-8"):
        errors.append("grill-with-docs must disable implicit invocation in its native Codex metadata")

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
    for include_upstream, expected in ((False, 49), (True, 87)):
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
        if include_upstream and not any(item.get("id") == "migrate-to-shoehorn" and item.get("source") == "upstream" and item.get("status") == "auto_routed" and item.get("local_path") for item in listing):
            errors.append("upstream repo/tool Skills must expose their route and vendored source path")
else:
    errors.append("AIPS Skill list CLI is missing")

localization = json.loads((ROOT / "skills/locale/zh-TW.json").read_text(encoding="utf-8"))
missing_locales = (set(active) | {record.get("id") for record in records}) - set(localization)
if missing_locales:
    errors.append("Traditional Chinese Skill descriptions missing: " + ", ".join(sorted(missing_locales)))
