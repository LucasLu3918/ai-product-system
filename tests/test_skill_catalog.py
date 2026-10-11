"""Integration tests for Strategy B skill intake and the Human Skill Explorer."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from scripts.skill_catalog import OUTPUT, TEMPLATE, records, render

ROOT = Path(__file__).resolve().parents[1]


def test_one_page_catalog_deterministic_and_complete():
    items = records(ROOT)
    ids = [entry["id"] for entry in items]
    assert len(ids) == len(set(ids)) == 45
    assert ids == sorted(ids)
    assert render(ROOT) == (ROOT / OUTPUT).read_text(encoding="utf-8")
    markup = render(ROOT)
    assert "__AIPS_SKILL_DATA__" not in markup
    assert "__AIPS_SKILL_COUNT__" not in markup
    assert 'id="search"' in markup and 'id="category"' in markup
    assert 'id="origin"' in markup and 'id="cards"' in markup
    assert 'navigator.clipboard' in markup
    assert "<script src=" not in markup
    assert 'rel="noopener noreferrer"' in markup
    match = re.search(r'<script id="skill-data" type="application/json">(.*?)</script>', markup, re.DOTALL)
    assert match
    data = json.loads(match.group(1))
    assert [x["id"] for x in data] == ids
    assert all(x["example"] and x["name_zh"] and x["triggers"] for x in data)


def test_upstream_all_38_dispositions_and_no_extra_beta():
    intake = yaml.safe_load((ROOT / "references/external-skills/mattpocock-2026-10-11.yaml").read_text(encoding="utf-8"))
    assert intake["upstream"]["commit"] == "49dd158d1076134a641b33efb035946536778336"
    entries = intake["entries"]
    sources = [e["source"] for e in entries]
    assert len(sources) == len(set(sources)) == 38
    assert all(e["action"] in {"new", "merge", "workflow", "optional", "excluded", "reference"} for e in entries)
    assert len([e for e in entries if e["action"] == "new"]) == 4
    assert {e["source"] for e in entries if e["source"].startswith("in-progress/") and e["action"] != "excluded"} == {
        "in-progress/writing-fragments", "in-progress/writing-beats", "in-progress/writing-shape"
    }
    assert not any(e["source"].startswith("misc/") and e["action"] == "new" for e in entries)
    assert intake["policy"]["beta_trials"] == "disabled"
    assert intake["policy"]["writing_workflow"] == "opt_in"


def test_no_skill_identity_collision_and_explicit_writing():
    index = yaml.safe_load((ROOT / "skills/INDEX.yaml").read_text(encoding="utf-8"))["skills"]
    new = {"rapid-prototyping", "technical-research", "human-guided-wizard", "technical-teaching", "creative-writing-workflow"}
    assert new <= set(index)
    assert len(index) == 45
    assert {"code-review", "tdd", "systematic-debugging", "domain-driven-design", "delivery-planning"} <= set(index)
    assert index["creative-writing-workflow"]["triggers"] == ["explicit_creative_writing_workflow"]
    assert not any(s in index for s in ("chief-of-staff", "claude-handoff", "loop-me", "setup-ts-deep-modules"))
    for item in index.values():
        assert (ROOT / "skills" / item["path"]).exists()


def test_html_generator_only_reads_local_canonical_sources():
    program = (ROOT / "scripts/skill_catalog.py").read_text(encoding="utf-8")
    assert "http" not in program and "requests" not in program
    assert "skills/INDEX.yaml" in program and "docs/human/skill-examples.yaml" in program
    assert "write_text" in program
    assert (ROOT / TEMPLATE).exists()
