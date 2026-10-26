from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import project_intelligence as pi
import project_intelligence_seed as seed


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def init_repo(path: Path) -> None:
    path.mkdir(parents=True)
    git(path, "init", "-q")
    git(path, "branch", "-m", "main")
    git(path, "config", "user.email", "aips" + chr(64) + "example.invalid")
    git(path, "config", "user.name", "AIPS Test")
    (path / "src").mkdir()
    (path / "src" / "app.py").write_text("print('a')\n", encoding="utf-8")
    (path / "README.md").write_text("# demo\n", encoding="utf-8")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "initial")


def commit_file(path: Path, rel: str, text: str) -> None:
    target = path / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", f"change {rel}")


def store_of(root: Path) -> Path:
    return pi.intelligence_store(root)[0]


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def dump(path: Path, data: dict) -> None:
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )


def mark_ready(root: Path) -> None:
    """Make a bootstrapped store a READY seed source with one watched topic (no re-analysis)."""
    manifest = store_of(root) / "PROJECT_INTELLIGENCE.yaml"
    intel = load(manifest)
    intel["state"]["readiness"] = "READY"
    intel["topics"] = {"modules": {"watch": ["src/**"]}}
    dump(manifest, intel)


def store_digests(store: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(store.rglob("*")):
        if path.is_file():
            result[str(path.relative_to(store))] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    return result


class WorktreeSeedTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name).resolve()
        self.config = self.base / "config"
        self.config.mkdir()
        self.env = mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.config)})
        self.env.start()
        self.primary = self.base / "main"
        init_repo(self.primary)
        self.secondary = self.base / "wt-one"
        git(
            self.primary,
            "worktree",
            "add",
            "-q",
            str(self.secondary),
            "-b",
            "feature-one",
        )

    def tearDown(self) -> None:
        self.env.stop()
        self._tmp.cleanup()

    def bootstrap_ready_primary(self) -> None:
        pi.bootstrap(self.primary)
        mark_ready(self.primary)


class SeedFromPrimaryTests(WorktreeSeedTestBase):
    def test_new_worktree_is_seeded_from_primary_and_stays_current(self) -> None:
        self.bootstrap_ready_primary()
        source_store = store_of(self.primary)
        before = store_digests(source_store)

        result = pi.bootstrap(self.secondary)

        self.assertEqual(result["status"], "SEEDED")
        self.assertEqual(result["seeded_from"]["selection"], "primary_worktree")
        self.assertEqual(
            result["seeded_from"]["project_id"], pi.intelligence_store(self.primary)[2]
        )
        self.assertEqual(result["freshness"], "CURRENT")
        self.assertEqual(result["reasons"], [])
        self.assertNotIn(str(self.primary), json.dumps(result))

        fr = pi.freshness(self.secondary)
        self.assertEqual(fr["status"], "CURRENT")
        self.assertNotIn("worktree_identity_changed", fr["reasons"])
        self.assertIn(
            "worktree_identity_seeded_from_same_repository", fr["observations"]
        )

        manifest = load(store_of(self.secondary) / "PROJECT_INTELLIGENCE.yaml")
        self.assertEqual(manifest["project"]["root"], str(self.secondary))
        self.assertEqual(
            manifest["provenance"]["seeded_from"]["git_head"],
            load(source_store / "PROJECT_INTELLIGENCE.yaml")["verified"]["git_head"],
        )
        self.assertEqual(
            manifest["provenance"]["seeded_into"]["worktree_identity"],
            pi.repository_identity(self.secondary)["worktree_id"],
        )
        self.assertEqual(
            store_digests(source_store),
            before,
            "seeding must never write into the source store",
        )

    def test_only_watched_changes_make_seeded_store_stale(self) -> None:
        self.bootstrap_ready_primary()
        pi.bootstrap(self.secondary)

        commit_file(self.secondary, "docs/notes.md", "unrelated\n")
        unrelated = pi.freshness(self.secondary)
        self.assertEqual(unrelated["status"], "CURRENT")

        commit_file(self.secondary, "src/app.py", "print('b')\n")
        changed = pi.freshness(self.secondary)
        self.assertEqual(changed["status"], "STALE")
        self.assertIn("watched_committed_path_changed:src/app.py", changed["reasons"])
        self.assertEqual(changed["affected_topics"], ["modules"])

    def test_primary_store_is_preferred_over_newer_secondary(self) -> None:
        self.bootstrap_ready_primary()
        pi.bootstrap(self.secondary)
        mark_ready(self.secondary)
        third = self.base / "wt-two"
        git(self.primary, "worktree", "add", "-q", str(third), "-b", "feature-two")

        result = pi.bootstrap(third)

        self.assertEqual(result["seeded_from"]["selection"], "primary_worktree")
        self.assertEqual(
            result["seeded_from"]["project_id"], pi.intelligence_store(self.primary)[2]
        )

    def test_most_recent_ready_secondary_is_used_when_primary_is_not_ready(
        self,
    ) -> None:
        pi.bootstrap(self.primary)  # PARTIAL: not a seed source
        pi.bootstrap(self.secondary)
        mark_ready(self.secondary)
        third = self.base / "wt-two"
        git(self.primary, "worktree", "add", "-q", str(third), "-b", "feature-two")

        result = pi.bootstrap(third)

        self.assertEqual(result["status"], "SEEDED")
        self.assertEqual(result["seeded_from"]["selection"], "most_recent_ready_store")
        self.assertEqual(
            result["seeded_from"]["project_id"],
            pi.intelligence_store(self.secondary)[2],
        )


class IsolationAndCopySetTests(WorktreeSeedTestBase):
    def test_only_allowlisted_artifacts_are_copied(self) -> None:
        self.bootstrap_ready_primary()
        source = store_of(self.primary)
        (source / "RETRIEVAL_INDEX.yaml").write_text(
            "db: /elsewhere/index.sqlite\n", encoding="utf-8"
        )
        (source / "MOBILE_NOTES.md").write_text("ad hoc notes\n", encoding="utf-8")
        (source / ".writer.lock").write_text("pid=1\n", encoding="utf-8")
        (source / "topics").mkdir(exist_ok=True)
        (source / "topics" / "modules.md").write_text("# modules\n", encoding="utf-8")
        (source / "topics" / "scratch.txt").write_text("skip\n", encoding="utf-8")

        pi.bootstrap(self.secondary)

        target = store_of(self.secondary)
        self.assertFalse((target / "RETRIEVAL_INDEX.yaml").exists())
        self.assertFalse((target / "MOBILE_NOTES.md").exists())
        self.assertFalse((target / "topics" / "scratch.txt").exists())
        self.assertTrue((target / "topics" / "modules.md").exists())
        self.assertTrue((target / "DISCOVERY.yaml").exists())
        manifest = load(target / "PROJECT_INTELLIGENCE.yaml")
        # Six top-level artifacts plus topics/modules.md; retrieval metadata, notes, lock, reviews and scratch are excluded.
        self.assertEqual(manifest["provenance"]["copied_artifact_count"], 7)
        self.assertGreaterEqual(manifest["provenance"]["excluded_artifact_count"], 5)

    def test_copy_on_write_source_is_not_changed_by_target_writes(self) -> None:
        self.bootstrap_ready_primary()
        source = store_of(self.primary)
        before = store_digests(source)
        pi.bootstrap(self.secondary)
        target_manifest = store_of(self.secondary) / "PROJECT_INTELLIGENCE.yaml"
        intel = load(target_manifest)
        intel["state"]["readiness"] = "PARTIAL"
        dump(target_manifest, intel)
        pi.render_review(self.secondary)
        self.assertEqual(store_digests(source), before)
        self.assertEqual(
            load(source / "PROJECT_INTELLIGENCE.yaml")["state"]["readiness"], "READY"
        )
        self.assertEqual(load(target_manifest)["state"]["readiness"], "PARTIAL")


class SameRepositoryProofTests(WorktreeSeedTestBase):
    def test_forged_repository_identity_is_never_a_source(self) -> None:
        self.bootstrap_ready_primary()
        manifest = store_of(self.primary) / "PROJECT_INTELLIGENCE.yaml"
        intel = load(manifest)
        intel["project"]["repository_id"] = "0" * 20
        dump(manifest, intel)

        result = pi.bootstrap(self.secondary)

        self.assertNotEqual(result.get("status"), "SEEDED")

    def test_store_of_other_repository_is_not_a_source(self) -> None:
        other = self.base / "other-repo"
        init_repo(other)
        pi.bootstrap(other)
        mark_ready(other)
        other_store = store_of(other)
        self.assertTrue(other_store.is_dir())

        # The second repository is never listed as a worktree of the first.
        result = pi.bootstrap(self.secondary)

        self.assertNotEqual(result.get("status"), "SEEDED")
        self.assertNotIn("seeded_from", result)

    def test_no_ready_source_falls_back_without_diagnostic(self) -> None:
        pi.bootstrap(self.primary)  # PARTIAL primary, nothing to seed from

        result = pi.bootstrap(self.secondary)

        self.assertEqual(result["readiness"], "PARTIAL")
        self.assertNotIn("observations", result)


class SymlinkRefusalTests(WorktreeSeedTestBase):
    def test_symlink_inside_source_store_refuses_seed(self) -> None:
        self.bootstrap_ready_primary()
        outside = self.base / "outside-secret.txt"
        outside.write_text("do-not-copy\n", encoding="utf-8")
        link = store_of(self.primary) / "NOTES.md"
        os.symlink(outside, link)

        result = pi.bootstrap(self.secondary)

        self.assertEqual(
            result["observations"],
            ["intelligence_seed_fallback:source_contains_symlink"],
        )
        target = store_of(self.secondary)
        self.assertFalse((target / "NOTES.md").exists())
        self.assertNotIn(
            "do-not-copy",
            "".join(
                p.read_text(encoding="utf-8", errors="ignore")
                for p in target.rglob("*")
                if p.is_file()
            ),
        )

    def test_symlinked_projects_entry_is_never_followed(self) -> None:
        self.bootstrap_ready_primary()
        source_dir = store_of(self.primary).parent
        elsewhere = self.base / "elsewhere"
        shutil.move(str(source_dir), str(elsewhere))
        os.symlink(elsewhere, source_dir)

        result = pi.bootstrap(self.secondary)

        self.assertNotEqual(result.get("status"), "SEEDED")
        self.assertNotIn("seeded_from", result)

    def test_symlinked_target_store_refuses_seed(self) -> None:
        self.bootstrap_ready_primary()
        decoy = self.base / "decoy"
        decoy.mkdir()
        target_parent = store_of(self.secondary).parent
        target_parent.mkdir(parents=True, exist_ok=True)
        os.symlink(decoy, target_parent / "intelligence")

        attempt = seed.seed_worktree_store(
            self.secondary, store_of(self.secondary), schema_version=pi.SCHEMA_VERSION
        )

        self.assertEqual(
            attempt, {"status": "REFUSED", "reason_code": "target_store_is_symlink"}
        )
        self.assertEqual(list(decoy.iterdir()), [])


class FallbackTests(WorktreeSeedTestBase):
    def test_copy_error_falls_back_to_normal_initialization_without_partial_store(
        self,
    ) -> None:
        self.bootstrap_ready_primary()

        with mock.patch(
            "project_intelligence_seed.shutil.copyfile",
            side_effect=OSError("disk full"),
        ):
            result = pi.bootstrap(self.secondary)

        self.assertEqual(
            result["observations"], ["intelligence_seed_fallback:seed_error"]
        )
        self.assertIn("readiness", result)
        target_parent = store_of(self.secondary).parent
        self.assertEqual(list(target_parent.glob(".intelligence-seed-*")), [])
        manifest = load(store_of(self.secondary) / "PROJECT_INTELLIGENCE.yaml")
        self.assertNotIn("provenance", manifest)
        self.assertEqual(manifest["state"]["readiness"], "PARTIAL")

    def test_non_empty_target_without_manifest_is_refused_and_untouched(self) -> None:
        self.bootstrap_ready_primary()
        target = store_of(self.secondary)
        target.mkdir(parents=True)
        (target / "hand-written.md").write_text("keep me\n", encoding="utf-8")

        attempt = seed.seed_worktree_store(
            self.secondary, target, schema_version=pi.SCHEMA_VERSION
        )

        self.assertEqual(
            attempt, {"status": "REFUSED", "reason_code": "target_store_not_empty"}
        )
        self.assertEqual(
            (target / "hand-written.md").read_text(encoding="utf-8"), "keep me\n"
        )

    def test_existing_manifest_is_preserved_and_never_reseeded(self) -> None:
        self.bootstrap_ready_primary()
        pi.bootstrap(self.secondary)
        first = store_digests(store_of(self.secondary))

        result = pi.bootstrap(self.secondary)

        self.assertEqual(result["status"], "PRESERVED_EXISTING")
        self.assertEqual(store_digests(store_of(self.secondary)), first)


class FreshnessProvenanceTests(WorktreeSeedTestBase):
    def test_unproven_worktree_identity_change_remains_stale(self) -> None:
        pi.bootstrap(self.secondary)
        manifest = store_of(self.secondary) / "PROJECT_INTELLIGENCE.yaml"
        intel = load(manifest)
        intel["project"]["worktree_identity"] = "f" * 16
        dump(manifest, intel)

        fr = pi.freshness(self.secondary)

        self.assertEqual(fr["status"], "STALE")
        self.assertIn("worktree_identity_changed", fr["reasons"])

    def test_store_copied_into_another_worktree_is_not_proven(self) -> None:
        self.bootstrap_ready_primary()
        pi.bootstrap(self.secondary)
        third = self.base / "wt-two"
        git(self.primary, "worktree", "add", "-q", str(third), "-b", "feature-two")
        third_store = store_of(third)
        third_store.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(store_of(self.secondary), third_store)

        fr = pi.freshness(third)

        self.assertEqual(fr["status"], "STALE")
        self.assertIn("worktree_identity_changed", fr["reasons"])


if __name__ == "__main__":
    unittest.main()
