from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from project_intelligence import validate_traversal_evidence
from project_intelligence import traverse_architecture_impact_graph
from retrieval_intelligence import (
    index_repository,
    risk_adaptive_policy,
    traverse_change_impact,
)


class ChangeImpactTraversalLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="aips-impact-traversal-")
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.repo = base / "repo"
        self.repo.mkdir()
        self.store = base / "intelligence"
        self.store.mkdir()
        (self.store / "TEMPORAL_ASSERTIONS.yaml").write_text(
            "schema:\n  version: 1\nassertions: []\n", encoding="utf-8"
        )
        (self.store / "IMPACT_GRAPH.yaml").write_text(
            """version: 1
nodes:
  api_products: {type: api, path: src/api.py}
  product_service: {type: module, path: src/service.py}
  product_controller: {type: consumer, path: src/controller.py}
  product_page: {type: consumer, path: src/ProductPage.vue}
edges:
  - {id: api-service, from: api_products, to: product_service, relation: calls, provenance: {source_id: fixture}}
  - {id: service-controller, from: product_service, to: product_controller, relation: consumes, provenance: {source_id: fixture}}
  - {id: service-page, from: product_service, to: product_page, relation: consumes, provenance: {source_id: fixture}}
coverage: {api: complete, data: complete, events: complete, consumers: complete}
unknowns: []
""",
            encoding="utf-8",
        )
        self.cache = base / "cache"
        self.cache.mkdir()
        self.write("src/api.py", "def get_products():\n    return []\n")
        self.write(
            "src/service.py",
            "from src.api import get_products\n\ndef load_products():\n    return get_products()\n",
        )
        self.write(
            "src/controller.py",
            "from src.service import load_products\n\ndef show_products():\n    return load_products()\n",
        )
        self.write(
            "src/ProductPage.vue",
            "<script>\nfunction render_products() {\n  const products = load_products()\n  return products.map((product) => product.id)\n}\n</script>\n",
        )
        self.write(".env", "get_products()\n")
        self.git("init", "-q", "-b", "main")
        self.git("add", "-A")
        self.git("-c", "user.name=AIPS Test", "-c", "user.email=" + chr(64) + "example.invalid", "commit", "-qm", "fixture")
        self.cache_patch = patch.dict(os.environ, {"XDG_CACHE_HOME": str(self.cache)})
        self.cache_patch.start()
        self.addCleanup(self.cache_patch.stop)
        indexed = index_repository(self.repo, self.store, force=True)
        self.assertEqual(indexed["status"], "READY")

    def write(self, rel: str, text: str) -> None:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True)

    def traverse(self, **kwargs):
        return traverse_change_impact(
            self.repo,
            self.store,
            [{"symbol": "get_products", "path": "src/api.py"}],
            "return_shape",
            directions=["callers", "consumers"],
            max_depth=2,
            changed_paths=["src/api.py"],
            **kwargs,
        )

    def test_risk_policy_does_not_force_multihop_for_docs_or_tests(self) -> None:
        self.assertEqual(risk_adaptive_policy("docs_style_test")["required_depth"], 0)
        self.assertEqual(risk_adaptive_policy("private_leaf")["required_depth"], 1)
        self.assertEqual(risk_adaptive_policy("api_contract")["required_depth"], 2)

    def test_finds_two_hop_callers_and_unchanged_map_consumer(self) -> None:
        report = self.traverse()
        self.assertEqual(report["status"], "COMPLETE")
        self.assertFalse(report["truncated"])
        self.assertGreaterEqual(report["reached_depth"]["callers"], 2)
        paths = {node.get("path") for node in report["nodes"]}
        self.assertIn("src/controller.py", paths)
        self.assertIn("src/ProductPage.vue", paths)
        page = next(node for node in report["nodes"] if node.get("path") == "src/ProductPage.vue")
        self.assertEqual(page["impact_status"], "affected_but_unchanged")
        self.assertEqual(page["consumer_hints"][0]["kind"], "map_call")

    def test_candidate_improves_unchanged_consumer_recall_over_diff_only_baseline(self) -> None:
        expected = {"src/service.py", "src/controller.py", "src/ProductPage.vue"}
        baseline_changed_files = {"src/api.py"}
        report = self.traverse()
        candidate = {
            str(node.get("path")) for node in report["nodes"]
            if node.get("kind") != "seed" and node.get("path")
        }
        baseline_recall = len(expected & baseline_changed_files) / len(expected)
        candidate_recall = len(expected & candidate) / len(expected)
        candidate_precision = len(expected & candidate) / max(1, len(candidate))
        self.assertEqual(baseline_recall, 0.0)
        self.assertEqual(candidate_recall, 1.0)
        self.assertEqual(candidate_precision, 1.0)

    def test_cycles_terminate_without_false_depth_truncation(self) -> None:
        self.write("src/cycle_a.py", "def cycle_a():\n    return cycle_b()\n")
        self.write("src/cycle_b.py", "def cycle_b():\n    return cycle_a()\n")
        self.git("add", "-A")
        self.git("-c", "user.name=AIPS Test", "-c", "user.email=" + chr(64) + "example.invalid", "commit", "-qm", "cycle")
        index_repository(self.repo, self.store)
        report = traverse_change_impact(
            self.repo, self.store, [{"symbol": "cycle_a", "path": "src/cycle_a.py"}],
            "private_leaf", directions=["callers"],
        )
        self.assertFalse(report["truncated"])
        self.assertEqual(report["status"], "COMPLETE")
        self.assertLessEqual(report["visited_nodes"], 3)

    def test_history_is_attached_only_for_policy_or_unresolved_cases(self) -> None:
        self.write("docs/change.md", "get_products response shape changed\n")
        self.git("add", "-A")
        self.git("-c", "user.name=AIPS Test", "-c", "user.email=" + chr(64) + "example.invalid", "commit", "-qm", "get_products response shape compatibility")
        index_repository(self.repo, self.store)
        high_risk = self.traverse()
        low_risk = traverse_change_impact(
            self.repo, self.store, [{"symbol": "get_products", "path": "src/api.py"}],
            "private_leaf", directions=["callers"], max_depth=1,
        )
        self.assertTrue(high_risk["history_evidence"])
        self.assertEqual(low_risk["history_evidence"], [])

    def test_architecture_graph_finds_event_subscribers_and_two_hop_consumers(self) -> None:
        graph = {
            "nodes": {
                "products_event": {"type": "event", "source": "events/products.yaml"},
                "worker_a": {"type": "consumer", "source": "workers/a.py"},
                "worker_b": {"type": "consumer", "source": "workers/b.py"},
            },
            "edges": [
                {"id": "event-a", "from": "products_event", "to": "worker_a", "relation": "subscribes", "provenance": {"source_id": "fixture"}},
                {"id": "a-b", "from": "worker_a", "to": "worker_b", "relation": "calls", "provenance": {"source_id": "fixture"}},
            ],
            "coverage": {"api": "complete", "data": "complete", "events": "complete", "consumers": "complete"},
        }
        report = traverse_architecture_impact_graph(
            graph, [{"symbol": "products_event"}], [], ["consumers"], 2, 10, 10, []
        )
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["reached_depth"]["consumers"], 2)
        self.assertEqual({node["symbol"] for node in report["nodes"]}, {"products_event", "worker_a", "worker_b"})

    def test_code_consumer_direction_walks_outgoing_relations(self) -> None:
        report = traverse_change_impact(
            self.repo,
            self.store,
            [{"symbol": "load_products", "path": "src/service.py"}],
            "private_leaf",
            directions=["consumers"],
            max_depth=1,
            changed_paths=["src/service.py"],
        )
        self.assertEqual(report["status"], "COMPLETE")
        self.assertGreaterEqual(report["reached_depth"]["consumers"], 1)
        self.assertIn("src/api.py", {node.get("path") for node in report["nodes"]})

    def test_comments_strings_and_secret_paths_do_not_create_relation_edges(self) -> None:
        report = self.traverse()
        self.assertNotIn(".env", {node.get("path") for node in report["nodes"]})
        self.write("src/decoy.py", "# get_products()\nmessage = 'get_products()'\n")
        self.git("add", "-A")
        self.git("-c", "user.name=AIPS Test", "-c", "user.email=" + chr(64) + "example.invalid", "commit", "-qm", "decoy")
        index_repository(self.repo, self.store)
        report = self.traverse()
        self.assertNotIn("src/decoy.py", {node.get("path") for node in report["nodes"]})

    def test_dynamic_string_dispatch_is_reported_as_unknown(self) -> None:
        self.write("src/registry.py", "def load():\n    return container.resolve('get_products')\n")
        self.git("add", "-A")
        self.git("-c", "user.name=AIPS Test", "-c", "user.email=" + chr(64) + "example.invalid", "commit", "-qm", "dynamic")
        index_repository(self.repo, self.store)
        report = self.traverse()
        self.assertIn("dynamic_relationship", {item.get("kind") for item in report["unresolved"]})
        self.assertEqual(report["status"], "BOUNDED_WITH_UNKNOWNS")

    def test_budget_exhaustion_and_stale_index_are_truthful(self) -> None:
        limited = self.traverse(max_edges=1)
        self.assertTrue(limited["truncated"])
        self.assertEqual(limited["status"], "TRUNCATED")
        self.write("src/new.py", "def unrelated():\n    return 1\n")
        stale = self.traverse()
        self.assertEqual(stale["index_status"], "STALE")
        self.assertEqual(stale["stop_reason"], "retrieval_index_stale")

    def test_high_risk_readiness_requires_complete_dispositions(self) -> None:
        valid = {
            "change": {"risk_class": "api_contract", "target_paths": ["src/api.py"]},
            "traversal": {
                "policy_version": 1,
                "policy": "risk-adaptive-bounded",
                "status": "COMPLETE",
                "required_depth": {"callers": 2},
                "truncated": False,
                "unresolved": [],
                "nodes": [{"kind": "caller", "path": "src/api.py", "impact_status": "affected_and_changed", "disposition": "reviewed_safe"}],
            },
        }
        self.assertEqual(validate_traversal_evidence(valid, ["src/api.py"]), [])
        broken = {**valid, "traversal": {**valid["traversal"], "status": "TRUNCATED", "truncated": True}}
        self.assertTrue(validate_traversal_evidence(broken, ["src/api.py"]))

    def test_legacy_artifact_without_risk_profile_remains_compatible(self) -> None:
        self.assertEqual(validate_traversal_evidence({"change": {}}, []), [])


if __name__ == "__main__":
    unittest.main()
