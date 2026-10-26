from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import project_intelligence as pi
import project_intelligence_gc as gc
import turn_context_hook as hook

STALE = {"status": "STALE", "affected_topics": ["testing"]}


class TaskRefreshRequirementTests(unittest.TestCase):
    def test_not_stale_needs_no_refresh(self) -> None:
        plan = pi.task_refresh_requirement({"status": "CURRENT"}, "READY", ["a"], {"status": "CURRENT"})
        self.assertFalse(plan["refresh_required"])
        self.assertFalse(plan["advisory"])
        self.assertEqual(plan["targeted_refresh"], [])

    def test_stale_not_ready_keeps_store_wide_refresh(self) -> None:
        plan = pi.task_refresh_requirement(STALE, "PARTIAL", [], {"status": "STALE"})
        self.assertEqual(plan, {"refresh_required": True, "targeted_refresh": ["testing"], "advisory": False,
                                "reason": "stale_not_ready"})

    def test_ready_stale_without_task_topics_is_advisory(self) -> None:
        plan = pi.task_refresh_requirement(STALE, "READY", [], {"status": "STALE"})
        self.assertFalse(plan["refresh_required"])
        self.assertTrue(plan["advisory"])
        self.assertEqual(plan["reason"], "no_task_relevant_topics")

    def test_ready_stale_unaffected_task_topics_is_advisory(self) -> None:
        plan = pi.task_refresh_requirement(STALE, "READY", ["/s/topics/modules.md"], {"status": "CURRENT"})
        self.assertFalse(plan["refresh_required"])
        self.assertEqual(plan["reason"], "task_topics_not_affected")

    def test_ready_stale_affected_task_topics_require_only_those(self) -> None:
        plan = pi.task_refresh_requirement(
            {"status": "STALE", "affected_topics": ["modules", "testing"]}, "READY", ["/s/topics/modules.md"],
            {"status": "STALE", "affected_selected_topics": ["modules"]},
        )
        self.assertTrue(plan["refresh_required"])
        self.assertTrue(plan["advisory"])
        self.assertEqual(plan["targeted_refresh"], ["modules"])

    def test_unproven_relevance_falls_back_to_all_affected(self) -> None:
        plan = pi.task_refresh_requirement(STALE, "READY", ["/s/topics/modules.md"], {"status": "STALE"})
        self.assertTrue(plan["refresh_required"])
        self.assertEqual(plan["targeted_refresh"], ["testing"])
        self.assertEqual(plan["reason"], "task_relevance_unproven")


class RetrievalNeedTests(unittest.TestCase):
    def test_rule(self) -> None:
        self.assertFalse(pi.retrieval_needed_for_task("", True, ["modules"]))
        self.assertFalse(pi.retrieval_needed_for_task("Explain dictionaries", False, []))
        self.assertTrue(pi.retrieval_needed_for_task("Fix the bug", True, []))
        self.assertTrue(pi.retrieval_needed_for_task("Review the API handler", False, ["architecture"]))


class HookRenderingTests(unittest.TestCase):
    def test_advisory_without_refresh_has_no_instruction(self) -> None:
        req = {"refresh_required": False, "freshness_advisory": True, "refresh_reason": "task_topics_not_affected",
               "targeted_refresh": []}
        lines = hook.freshness_lines({"freshness": "STALE"}, req)
        self.assertEqual(len(lines), 1)
        self.assertIn("no refresh needed", lines[0])

    def test_required_refresh_lists_topics(self) -> None:
        req = {"refresh_required": True, "freshness_advisory": True, "refresh_reason": "task_topics_affected",
               "targeted_refresh": ["modules"]}
        self.assertIn("targeted_refresh=modules", hook.freshness_lines({"freshness": "STALE"}, req))

    def test_legacy_manifest_keeps_targeted_refresh(self) -> None:
        self.assertEqual(hook.freshness_lines({"freshness": "STALE"}, {"targeted_refresh": ["modules"]}),
                         ["targeted_refresh=modules"])

    def test_next_step_mutation_keeps_change_impact(self) -> None:
        line = hook.next_step_line({"task": {"mutation_likely": True}}, {"change_impact_required": True}, {}, {"mode": "soft"})
        self.assertIn("resolve Change Impact", line)
        self.assertNotIn("refresh", line)

    def test_next_step_closed_policy_names_reasons(self) -> None:
        line = hook.next_step_line(
            {"task": {"mutation_likely": True}},
            {"initialize_intelligence": True, "semantic_enrichment_required": True, "change_impact_required": True},
            {}, {"mode": "closed", "reasons": ["intelligence_missing"]},
        )
        self.assertTrue(line.startswith("Mutation blocked until fail_closed_reasons=intelligence_missing"))
        self.assertIn("initialize Intelligence", line)
        self.assertIn("resolve Change Impact", line)

    def test_next_step_read_only(self) -> None:
        line = hook.next_step_line({"task": {"mutation_likely": False}}, {"change_impact_required": False}, {}, {"mode": "soft"})
        self.assertTrue(line.startswith("Read-only turn"))

    def test_compact_context_read_only_missing_index(self) -> None:
        data = {
            "project": {"root": "/p", "mode": "EPHEMERAL", "intelligence_store": "/s"},
            "task": {"mutation_likely": False},
            "intelligence": {"readiness": "READY", "freshness": "STALE"},
            "requirements": {"retrieval_needed": False, "retrieval_index_required": False, "refresh_required": False,
                             "freshness_advisory": True, "refresh_reason": "no_task_relevant_topics",
                             "targeted_refresh": [], "change_impact_required": False},
            "context": {"layers": {"core": {}, "recall": {}, "telemetry": {"hard_budget_tokens": 7600}},
                        "retrieval": {"status": "INDEX_MISSING", "results": []}},
            "fail_policy": {"mode": "soft"},
        }
        rendered = hook.compact_context(data)
        self.assertIn("retrieval_index=MISSING (not needed for this task", rendered)
        self.assertNotIn("retrieval_index_required=True", rendered)
        self.assertNotIn("targeted_refresh=", rendered)


class IntelligenceGcTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name).resolve()
        self.projects = self.base / "config" / "aips" / "projects"
        self.projects.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def store(self, workspace: str, root: object) -> Path:
        store = self.projects / workspace / "intelligence"
        (store / "topics").mkdir(parents=True)
        (store / "PROJECT_INTELLIGENCE.yaml").write_text(yaml.safe_dump({"project": {"root": root}}), encoding="utf-8")
        return store

    def test_dry_run_lists_without_deleting(self) -> None:
        live = self.base / "live"
        live.mkdir()
        kept = self.store("a-live", str(live))
        orphan = self.store("b-gone", str(self.base / "gone"))
        result = gc.collect(self.projects)
        self.assertEqual(result["status"], "DRY_RUN")
        self.assertEqual([item["store"] for item in result["orphaned"]], [str(orphan)])
        self.assertEqual([item["store"] for item in result["kept"]], [str(kept)])
        self.assertTrue(orphan.is_dir())
        self.assertEqual(result["removed"], [])

    def test_apply_removes_only_orphans_and_preserves_other_workspace_data(self) -> None:
        live = self.base / "live"
        live.mkdir()
        kept = self.store("a-live", str(live))
        orphan = self.store("b-gone", str(self.base / "gone"))
        (self.projects / "b-gone" / "runs").mkdir()
        empty_orphan = self.store("c-gone", str(self.base / "gone2"))
        result = gc.collect(self.projects, apply=True)
        self.assertEqual(result["status"], "APPLIED")
        self.assertEqual(sorted(item["store"] for item in result["removed"]), sorted([str(orphan), str(empty_orphan)]))
        self.assertTrue(kept.is_dir())
        self.assertFalse(orphan.exists())
        self.assertTrue((self.projects / "b-gone" / "runs").is_dir())
        self.assertFalse((self.projects / "c-gone").exists())

    def test_unverifiable_or_unrecorded_roots_are_never_deleted(self) -> None:
        relative = self.store("a-relative", "relative/path")
        unrecorded = self.store("b-none", None)
        missing_manifest = self.projects / "c-missing" / "intelligence"
        missing_manifest.mkdir(parents=True)
        broken_link = self.base / "broken"
        broken_link.symlink_to(self.base / "nowhere")
        dangling = self.store("d-dangling", str(broken_link))
        result = gc.collect(self.projects, apply=True)
        self.assertEqual(result["removed"], [])
        for path in (relative, unrecorded, missing_manifest, dangling):
            self.assertTrue(path.is_dir())
        reasons = {item["workspace_id"]: item["reason"] for item in result["skipped"]}
        self.assertEqual(reasons["a-relative"], "project_root_not_absolute")
        self.assertEqual(reasons["b-none"], "project_root_unrecorded")
        self.assertEqual(reasons["c-missing"], "manifest_missing")
        self.assertEqual([item["workspace_id"] for item in result["kept"]], ["d-dangling"])

    def test_symlinks_cannot_escape_projects_dir(self) -> None:
        outside = self.base / "outside"
        outside_store = outside / "intelligence"
        (outside_store / "topics").mkdir(parents=True)
        (outside_store / "PROJECT_INTELLIGENCE.yaml").write_text(
            yaml.safe_dump({"project": {"root": str(self.base / "gone")}}), encoding="utf-8")
        (self.projects / "a-workspace-link").symlink_to(outside, target_is_directory=True)
        real = self.projects / "b-store-link"
        real.mkdir()
        (real / "intelligence").symlink_to(outside_store, target_is_directory=True)
        result = gc.collect(self.projects, apply=True)
        self.assertEqual(result["removed"], [])
        self.assertTrue(outside_store.is_dir())
        reasons = {item["workspace_id"]: item["reason"] for item in result["skipped"]}
        self.assertEqual(reasons, {"a-workspace-link": "workspace_is_symlink", "b-store-link": "store_is_symlink"})

    def test_symlinked_projects_dir_is_refused(self) -> None:
        link = self.base / "projects-link"
        link.symlink_to(self.projects, target_is_directory=True)
        self.store("a-gone", str(self.base / "gone"))
        result = gc.collect(link, apply=True)
        self.assertEqual(result["status"], "REFUSED")
        self.assertTrue((self.projects / "a-gone" / "intelligence").is_dir())

    def test_missing_projects_dir(self) -> None:
        self.assertEqual(gc.collect(self.base / "absent")["status"], "NO_STORES")

    def test_reappearing_root_is_not_deleted(self) -> None:
        gone = self.base / "gone"
        orphan = self.store("a-gone", str(gone))
        original = gc._path_present
        calls = {"n": 0}

        def flaky(path: str) -> bool | None:
            calls["n"] += 1
            if calls["n"] > 1:
                gone.mkdir(exist_ok=True)
            return original(path)

        gc._path_present = flaky
        try:
            result = gc.collect(self.projects, apply=True)
        finally:
            gc._path_present = original
        self.assertEqual(result["removed"], [])
        self.assertTrue(orphan.is_dir())
        self.assertEqual(result["skipped"][0]["reason"], "changed_before_removal")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    unittest.main()
