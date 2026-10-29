from __future__ import annotations

import os
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from project_intelligence import (
    traverse_architecture_impact_graph,
    validate_impact_document,
    validate_traversal_evidence,
)
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

    def test_same_name_callers_are_path_filtered_before_edge_budget(self) -> None:
        self.write(
            "src/scanner.py",
            "def git():\n    return None\n\n"
            "def scan_candidate():\n    return git()\n",
        )
        self.write("src/noise.py", "def git():\n    return None\n")
        noise_calls = "from src.noise import git\n\n"
        noise_calls += "\n".join(
            f"def unrelated_{index}():\n    return git()"
            for index in range(350)
        )
        self.write("src/noise_users.py", noise_calls + "\n")
        self.write(
            "src/target_user.py",
            "from src.scanner import git\n\n"
            "def publish_candidate():\n    return git()\n",
        )
        self.git("add", "-A")
        self.git("-c", "user.name=AIPS Test", "-c", "user.email=" + chr(64) + "example.invalid", "commit", "-qm", "same-name caller fanout")
        index_repository(self.repo, self.store, force=True)

        report = traverse_change_impact(
            self.repo,
            self.store,
            [{"symbol": "git", "path": "src/scanner.py"}],
            "private_leaf",
            directions=["callers"],
            max_depth=2,
            max_edges=300,
        )

        self.assertEqual(report["status"], "COMPLETE")
        self.assertFalse(report["truncated"])
        self.assertLessEqual(report["caller_candidates_scanned"], 2)
        self.assertLessEqual(
            report["caller_candidates_scanned"],
            report["limits"]["caller_candidates"] + 1,
        )
        caller_paths = {
            node.get("path") for node in report["nodes"] if node.get("kind") == "caller"
        }
        self.assertIn("src/target_user.py", caller_paths)
        self.assertNotIn("src/noise_users.py", caller_paths)

    def test_exact_target_path_callers_survive_noise_before_candidate_budget(self) -> None:
        self.write("src/scanner.py", "def git():\n    return None\n")
        self.write("src/noise.py", "def git():\n    return None\n")
        noise_calls = "from src.noise import git\n\n"
        noise_calls += "\n".join(
            f"def unrelated_{index}():\n    return git()"
            for index in range(15)
        )
        self.write("src/noise_users.py", noise_calls + "\n")
        self.write(
            "src/target_user.py",
            "from src.scanner import git\n\n"
            "def publish_candidate():\n    return git()\n",
        )
        self.git("add", "-A")
        self.git("-c", "user.name=AIPS Test", "-c", "user.email=" + chr(64) + "example.invalid", "commit", "-qm", "exact target path before scan budget")
        index_repository(self.repo, self.store, force=True)

        report = traverse_change_impact(
            self.repo,
            self.store,
            [{"symbol": "git", "path": "src/scanner.py"}],
            "private_leaf",
            directions=["callers"],
            max_depth=2,
            max_edges=1,
        )

        self.assertEqual(report["status"], "COMPLETE")
        self.assertFalse(report["truncated"])
        caller_paths = {
            node.get("path") for node in report["nodes"] if node.get("kind") == "caller"
        }
        self.assertEqual(caller_paths, {"src/target_user.py"})

    def test_caller_candidate_scan_budget_overflow_fails_closed(self) -> None:
        self.write("src/scanner.py", "def git():\n    return None\n")
        self.write("src/noise.py", "def git():\n    return None\n")
        noise_calls = "\n".join(
            f"def unrelated_{index}():\n    return git()"
            for index in range(20)
        )
        self.write("src/noise_users.py", noise_calls + "\n")
        self.git("add", "-A")
        self.git("-c", "user.name=AIPS Test", "-c", "user.email=" + chr(64) + "example.invalid", "commit", "-qm", "caller scan budget")
        index_repository(self.repo, self.store, force=True)

        report = traverse_change_impact(
            self.repo,
            self.store,
            [{"symbol": "git", "path": "src/scanner.py"}],
            "private_leaf",
            directions=["callers"],
            max_depth=2,
            max_edges=1,
        )

        self.assertEqual(report["status"], "TRUNCATED")
        self.assertTrue(report["truncated"])
        self.assertEqual(report["stop_reason"], "caller_candidate_limit")
        self.assertEqual(
            report["caller_candidates_scanned"],
            report["limits"]["caller_candidates"],
        )

    def test_pathless_candidate_overflow_counter_stays_within_hard_cap(self) -> None:
        self.write("src/scanner.py", "def git():\n    return None\n")
        callers = "\n".join(
            f"def unresolved_{index}():\n    return git()"
            for index in range(20)
        )
        self.write("src/unresolved_users.py", callers + "\n")
        self.git("add", "-A")
        self.git("-c", "user.name=AIPS Test", "-c", "user.email=" + chr(64) + "example.invalid", "commit", "-qm", "pathless caller scan budget")
        index_repository(self.repo, self.store, force=True)

        report = traverse_change_impact(
            self.repo,
            self.store,
            [{"symbol": "git"}],
            "private_leaf",
            directions=["callers"],
            max_depth=2,
            max_edges=1,
        )

        self.assertEqual(report["status"], "TRUNCATED")
        self.assertEqual(report["stop_reason"], "caller_candidate_limit")
        self.assertEqual(
            report["caller_candidates_scanned"],
            report["limits"]["caller_candidates"],
        )

    def test_exact_caller_edge_budget_overflow_fails_closed(self) -> None:
        self.write("src/scanner.py", "def git():\n    return None\n")
        callers = "from src.scanner import git\n\n"
        callers += "\n".join(
            f"def publish_{index}():\n    return git()"
            for index in range(5)
        )
        self.write("src/publishers.py", callers + "\n")
        self.git("add", "-A")
        self.git("-c", "user.name=AIPS Test", "-c", "user.email=" + chr(64) + "example.invalid", "commit", "-qm", "exact caller edge budget")
        index_repository(self.repo, self.store, force=True)

        report = traverse_change_impact(
            self.repo,
            self.store,
            [{"symbol": "git", "path": "src/scanner.py"}],
            "private_leaf",
            directions=["callers"],
            max_depth=2,
            max_edges=1,
        )

        self.assertEqual(report["status"], "TRUNCATED")
        self.assertTrue(report["truncated"])
        self.assertEqual(report["stop_reason"], "max_edges")

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

    def test_seed_scoped_coverage_does_not_upgrade_global_partial_coverage(self) -> None:
        graph = {
            "nodes": {"isolation_resolver": {"type": "module", "source": "scripts/execution_isolation.py"}},
            "edges": [],
            "coverage": {"api": "partial", "data": "partial", "events": "partial", "consumers": "unknown"},
            "coverage_scopes": [{
                "id": "execution-isolation-boundary",
                "seed_ids": ["isolation_resolver"],
                "coverage": {"api": "complete", "data": "complete", "events": "complete", "consumers": "complete"},
                "evidence": ["scripts/execution_isolation.py:204-251", "tests/validation/conformance_isolation.py"],
            }],
        }
        report = traverse_architecture_impact_graph(
            graph, [{"symbol": "isolation_resolver"}], [], ["callers", "consumers"], 2, 10, 10, []
        )
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["coverage_scope_ids"], ["execution-isolation-boundary"])
        self.assertEqual(graph["coverage"]["consumers"], "unknown")

    def test_seed_scoped_coverage_requires_matching_seeds_and_evidence(self) -> None:
        graph = {
            "nodes": {"other": {"type": "module", "source": "src/other.py"}},
            "edges": [],
            "coverage": {"api": "partial", "data": "partial", "events": "partial", "consumers": "unknown"},
            "coverage_scopes": [{
                "id": "unrelated",
                "seed_ids": ["isolation_resolver"],
                "coverage": {"api": "complete", "data": "complete", "events": "complete", "consumers": "complete"},
                "evidence": ["tests/fixture.py"],
            }],
        }
        report = traverse_architecture_impact_graph(
            graph, [{"symbol": "other"}], [], ["consumers"], 1, 10, 10, []
        )
        self.assertEqual(report["status"], "BOUNDED_WITH_UNKNOWNS")
        self.assertEqual(report["coverage_scope_ids"], [])
        self.assertIn("architecture_graph_coverage", {item.get("kind") for item in report["unresolved"]})

    def test_seed_scoped_coverage_rejects_malformed_evidence(self) -> None:
        graph = {
            "nodes": {"isolation_resolver": {"type": "module", "source": "scripts/execution_isolation.py"}},
            "edges": [],
            "coverage": {"api": "partial", "data": "partial", "events": "partial", "consumers": "unknown"},
            "coverage_scopes": [{
                "id": "malformed",
                "seed_ids": ["isolation_resolver"],
                "coverage": {"api": "complete", "data": "complete", "events": "complete", "consumers": "complete"},
                "evidence": "tests/fixture.py",
            }],
        }
        report = traverse_architecture_impact_graph(
            graph, [{"symbol": "isolation_resolver"}], [], ["consumers"], 2, 10, 10, []
        )
        self.assertEqual(report["status"], "BOUNDED_WITH_UNKNOWNS")
        self.assertEqual(report["coverage_scope_ids"], [])

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

    def test_python_consumer_walk_ignores_annotations_variables_and_attribute_calls(self) -> None:
        self.write(
            "src/service.py",
            "from typing import Any\n"
            "from src.api import get_products\n"
            "def load_products(query: Any) -> dict[str, Any]:\n"
            "    message = 'cache.get(query)'\n"
            "    cache.get(query)\n"
            "    return get_products()\n",
        )
        self.git("add", "-A")
        self.git("-c", "user.name=AIPS Test", "-c", "user.email=" + chr(64) + "example.invalid", "commit", "-qm", "python call extraction")
        index_repository(self.repo, self.store)
        report = traverse_change_impact(
            self.repo,
            self.store,
            [{"symbol": "load_products", "path": "src/service.py"}],
            "private_leaf",
            directions=["consumers"],
            max_depth=1,
        )
        self.assertEqual(report["status"], "COMPLETE")
        consumers = {node.get("path") for node in report["nodes"] if node.get("kind") == "consumer"}
        self.assertEqual(consumers, {"src/api.py"})
        self.assertFalse(report["unresolved"])

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

    def test_file_names_containing_dispatch_terms_are_not_dynamic_calls(self) -> None:
        self.write(
            "src/helper_list.py",
            'helpers = ("harness_resolve.py", "retrieval_intelligence.py")\n',
        )
        self.git("add", "-A")
        self.git("-c", "user.name=AIPS Test", "-c", "user.email=" + chr(64) + "example.invalid", "commit", "-qm", "static helper list")
        index_repository(self.repo, self.store)
        report = traverse_change_impact(
            self.repo,
            self.store,
            [{"symbol": "retrieval_intelligence.py", "path": "src/api.py"}],
            "private_leaf",
            directions=["callers"],
            max_depth=1,
            changed_paths=["src/api.py"],
        )
        self.assertNotIn("dynamic_relationship", {item.get("kind") for item in report["unresolved"]})

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
        missing_disposition = {
            **valid,
            "traversal": {
                **valid["traversal"],
                "nodes": [{"kind": "caller", "path": "src/api.py", "impact_status": "affected_and_changed"}],
            },
        }
        errors = validate_traversal_evidence(missing_disposition, ["src/api.py"])
        self.assertTrue(any("reviewed_safe, requires_change or unknown" in error for error in errors))
        self.assertTrue(any("aips intelligence impact-validate" in error for error in errors))
        broken = {**valid, "traversal": {**valid["traversal"], "status": "TRUNCATED", "truncated": True}}
        self.assertTrue(validate_traversal_evidence(broken, ["src/api.py"]))

    def test_directional_reports_accept_only_exact_human_reviewed_unknowns(self) -> None:
        def digest(value: object) -> str:
            encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            return "sha256:" + hashlib.sha256(encoded).hexdigest()

        scope_id = "scanner-boundary"
        unresolved = {
            "callers": [{"kind": "ambiguous_target", "path": "tests/test_cli.py", "line": 14, "symbol": "run"}],
            "consumers": [{"kind": "dynamic_relationship", "path": "scripts/consumer.py", "line": 22, "symbol": "dispatch"}],
        }

        def report(direction: str) -> dict:
            return {
                "policy_version": 1,
                "policy": "risk-adaptive-bounded",
                "risk_class": "security_boundary",
                "status": "BOUNDED_WITH_UNKNOWNS",
                "seeds": [{"symbol": "scanner", "path": "scripts/scanner.py"}],
                "directions": [direction],
                "required_depth": {direction: 2},
                "reached_depth": {direction: 3},
                "max_depth": 6,
                "limits": {"nodes": 150, "edges": 300, "depth": 6, "caller_candidates": 3000},
                "visited_nodes": 4,
                "visited_edges": 3,
                "caller_candidates_scanned": 8 if direction == "callers" else 0,
                "truncated": False,
                "unresolved": unresolved[direction],
                "nodes": [{
                    "kind": "caller" if direction == "callers" else "consumer",
                    "symbol": "affected_entry",
                    "path": f"scripts/{direction}_entry.py",
                    "line": 5,
                    "depth": 1,
                    "impact_status": "affected_but_unchanged",
                    "disposition": "pending_review",
                }],
                "architecture_graph": {"status": "COMPLETE", "coverage_scope_ids": [scope_id]},
            }

        reports = {direction: report(direction) for direction in ("callers", "consumers")}
        node_reviews = [
            {
                "direction": direction,
                "report_sha256": digest(reports[direction]),
                "node_sha256": digest(reports[direction]["nodes"][0]),
                "disposition": "reviewed_safe",
            }
            for direction in ("callers", "consumers")
        ]
        unknowns = []
        for direction, entries in unresolved.items():
            for index, item in enumerate(entries):
                unknowns.append({
                    "id": f"traversal-{direction}-{index}",
                    "description": "Reviewed unresolved relationship in bounded traversal.",
                    "disposition": "ACCEPTED_LIMITATION",
                    "resolution": "Human review found the relationship does not expand the approved scanner scope.",
                    "evidence": [{"kind": "repository_file", "path": "scripts/project_intelligence.py", "sha256": "sha256:" + "a" * 64}],
                    "review": {"status": "APPROVED", "reviewer": "human", "approval_reference": "user-approval", "reviewed_at": "2026-10-29T00:00:00Z"},
                    "traversal_review": {
                        "direction": direction,
                        "report_sha256": digest(reports[direction]),
                        "unresolved_sha256": digest(item),
                        "disposition": "reviewed_safe",
                    },
                })
        doc = {
            "change": {"risk_class": "security_boundary", "target_paths": []},
            "unknowns": unknowns,
            "traversal": {
                "policy_version": 2,
                "policy": "risk-adaptive-bounded",
                "mode": "directional_reviewed_scope",
                "scope_id": scope_id,
                "directions": ["callers", "consumers"],
                "reports": reports,
                "node_reviews": node_reviews,
            },
        }
        self.assertEqual(validate_traversal_evidence(doc, []), [])
        implementation_approved = {
            **doc,
            "status": "IMPLEMENTATION_APPROVED",
            "scope_review": {"status": "APPROVED", "approval_reference": "scope", "approved_at": "2026-10-29"},
            "unknowns": [],
        }
        approval_errors = validate_impact_document(implementation_approved).get("errors", [])
        self.assertTrue(any("unresolved relationship lacks exactly one reviewed disposition" in error
                            for error in approval_errors))

        missing_review = {**doc, "unknowns": unknowns[:-1]}
        self.assertTrue(any("unresolved relationship lacks exactly one reviewed disposition" in error
                            for error in validate_traversal_evidence(missing_review, [])))

        missing_node_review = json.loads(json.dumps(doc))
        missing_node_review["traversal"]["node_reviews"].pop()
        self.assertTrue(any("affected traversal node lacks exactly one scoped review" in error
                            for error in validate_traversal_evidence(missing_node_review, [])))

        stale_fingerprint = json.loads(json.dumps(doc))
        stale_fingerprint["unknowns"][0]["traversal_review"]["unresolved_sha256"] = "sha256:" + "0" * 64
        self.assertTrue(any("does not match an exact unresolved record" in error
                            for error in validate_traversal_evidence(stale_fingerprint, [])))

        over_budget = json.loads(json.dumps(doc))
        over_budget["traversal"]["reports"]["callers"]["visited_edges"] = 301
        self.assertTrue(any("exceeds the approved edge limit" in error
                            for error in validate_traversal_evidence(over_budget, [])))

        truncated = json.loads(json.dumps(doc))
        truncated["traversal"]["reports"]["consumers"]["truncated"] = True
        self.assertTrue(any("truncated directional traversal cannot establish scoped evidence" in error
                            for error in validate_traversal_evidence(truncated, [])))

        unknown_truncation = json.loads(json.dumps(doc))
        unknown_truncation["traversal"]["reports"]["consumers"].pop("truncated")
        self.assertTrue(any("truncated directional traversal cannot establish scoped evidence" in error
                            for error in validate_traversal_evidence(unknown_truncation, [])))

        malformed_direction = json.loads(json.dumps(doc))
        malformed_direction["traversal"]["directions"] = [{"unexpected": "mapping"}]
        self.assertTrue(validate_traversal_evidence(malformed_direction, []))

        malformed_scope_graph = json.loads(json.dumps(doc))
        malformed_scope_graph["traversal"]["reports"]["callers"]["architecture_graph"] = []
        self.assertTrue(validate_traversal_evidence(malformed_scope_graph, []))

    def test_legacy_artifact_without_risk_profile_remains_compatible(self) -> None:
        self.assertEqual(validate_traversal_evidence({"change": {}}, []), [])


if __name__ == "__main__":
    unittest.main()
