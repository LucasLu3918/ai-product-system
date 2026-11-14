"""Behavior contracts for the registry-derived Skill Explorer output."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import skill_catalog


class SkillCatalogRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import yaml

        cls.registry = yaml.safe_load(skill_catalog.REGISTRY.read_text(encoding="utf-8"))
        cls.source = json.loads(skill_catalog.SOURCE.read_text(encoding="utf-8"))
        cls.cards, cls.categories, cls.catalog = skill_catalog.build_cards(cls.registry, cls.source)

    def test_catalog_preserves_source_status_and_installability_separately(self):
        by_id = {item["id"]: item for item in self.catalog}
        canonical = next(iter(self.registry["skills"]))
        self.assertEqual(by_id[canonical]["source"], "aips")
        self.assertFalse(by_id[canonical]["installable"])
        self.assertEqual(by_id[canonical]["status"], "enabled")

        distinct_upstream = next(item for item in self.catalog if item["source"] == "upstream" and item["installable"])
        self.assertTrue(distinct_upstream["upstream_commit"])
        self.assertTrue(distinct_upstream["source_path"])
        self.assertNotEqual(distinct_upstream["status"], "enabled")

    def test_static_compatibility_page_and_machine_data_are_generated(self):
        self.assertIn('<article class="card"', self.cards)
        self.assertIn('id="cards"', skill_catalog.render())
        self.assertIn("AIPS canonical Skill", self.cards)
        self.assertEqual(len(self.catalog), len(self.registry["skills"]) + len(self.source["skills"]))
        data = json.loads(skill_catalog.render_catalog())
        self.assertEqual(data["source_commit"], self.source["source"]["commit"])
        self.assertEqual(len(data["skills"]), len(self.catalog))

    def test_generated_output_contains_no_fixed_inventory_total(self):
        output = skill_catalog.render()
        self.assertIn(f">{len(self.catalog)}<", output)
        self.assertIn('data-status="enabled"', output)


if __name__ == "__main__":
    unittest.main()
