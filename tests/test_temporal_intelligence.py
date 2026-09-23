from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.temporal_intelligence import active_assertions, between, validate_document, why


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


class TemporalIntelligenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "test@example.com")
        git(self.root, "config", "user.name", "Temporal Test")
        (self.root / "README.md").write_text("initial\n", encoding="utf-8")
        git(self.root, "add", "README.md")
        git(self.root, "commit", "-qm", "initial")
        self.c100 = git(self.root, "rev-parse", "HEAD")
        (self.root / "README.md").write_text("service A\n", encoding="utf-8")
        git(self.root, "commit", "-qam", "ADR-001 service A")
        self.c200 = git(self.root, "rev-parse", "HEAD")
        (self.root / "README.md").write_text("service B\n", encoding="utf-8")
        git(self.root, "commit", "-qam", "ADR-009 service B")
        self.c300 = git(self.root, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def doc(self) -> dict:
        return {
            "schema": {"version": 1},
            "assertions": [
                {
                    "id": "payment-service-a",
                    "subject": "payment",
                    "predicate": "routes_through",
                    "object": "service-a",
                    "validity": {"from_revision": self.c200, "to_revision_exclusive": self.c300},
                    "history_quality": "VERIFIED",
                    "provenance": {"source": "ADR-001"},
                },
                {
                    "id": "payment-service-b",
                    "subject": "payment",
                    "predicate": "routes_through",
                    "object": "service-b",
                    "validity": {"from_revision": self.c300, "to_revision_exclusive": None},
                    "history_quality": "VERIFIED",
                    "supersedes": ["payment-service-a"],
                    "superseded_by": None,
                },
            ],
        }

    def test_revision_queries_and_supersession(self) -> None:
        doc = self.doc()
        self.assertEqual(validate_document(doc), [])
        self.assertEqual(active_assertions(self.root, doc, self.c200)["assertions"][0]["object"], "service-a")
        self.assertEqual(active_assertions(self.root, doc, self.c300)["assertions"][0]["object"], "service-b")
        delta = between(self.root, doc, self.c200, self.c300)
        self.assertEqual(delta["added"][0]["id"], "payment-service-b")
        self.assertEqual(delta["ended"][0]["id"], "payment-service-a")
        self.assertEqual(why(doc, "payment-service-b")["supersession_chain"][0]["id"], "payment-service-b")

    def test_unknown_history_is_current_only(self) -> None:
        doc = {
            "schema": {"version": 1},
            "assertions": [{
                "id": "unknown-start", "subject": "x", "predicate": "is", "object": "y",
                "validity": {"from_revision": "UNKNOWN", "to_revision_exclusive": None},
                "history_quality": "PARTIAL",
            }],
        }
        self.assertEqual(len(active_assertions(self.root, doc)["assertions"]), 1)
        historical = active_assertions(self.root, doc, self.c200)
        self.assertEqual(historical["assertions"], [])
        self.assertEqual(historical["excluded"][0]["reason"], "history_start_unknown")

    def test_invalid_interval_fails_closed(self) -> None:
        doc = self.doc()
        doc["assertions"][0]["validity"]["to_revision_exclusive"] = self.c200
        self.assertTrue(any("non-empty" in error for error in validate_document(doc)))


if __name__ == "__main__":
    unittest.main()
