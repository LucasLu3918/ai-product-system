from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import docs_only_review


class DocsOnlyReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture" + "@" + "users.noreply.github.com")
        (self.root / "README.md").write_text("base\n", encoding="utf-8")
        (self.root / ".gitignore").write_text("workspace/captures/RUNLOG.md\n", encoding="utf-8")
        self.git("add", "README.md", ".gitignore")
        self.git("commit", "-qm", "base")

    def git(self, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=self.root, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_requires_explicit_opt_in_and_derives_classification_from_git_diff(self) -> None:
        self.assertEqual(docs_only_review.review(self.root)["reason_code"], "OPT_IN_REQUIRED")
        (self.root / "README.md").write_text("updated\n", encoding="utf-8")
        (self.root / "workspace/captures").mkdir(parents=True)
        (self.root / "workspace/captures/RUNLOG.md").write_text("ignored record\n", encoding="utf-8")

        report = docs_only_review.review(self.root, opt_in=True)
        self.assertEqual(report["classification"], "DOCS_ONLY")
        self.assertEqual(report["changed_files"], ["README.md"])
        self.assertEqual(report["ignored_paths"], ["workspace/captures/RUNLOG.md"])
        self.assertNotIn("tests_not_applicable", report)
        self.assertIn("secret_scan", report["required_checks"])
        self.assertIn("git_diff_check", report["required_checks"])
        self.assertIn("approval_and_reconciliation", report["required_checks"])
        self.assertEqual(report["status"], "DOCS_ONLY_REVIEW_ONLY")

    def test_claude_settings_and_aips_security_paths_are_never_docs_only(self) -> None:
        settings = self.root / ".claude/settings.json"
        settings.parent.mkdir()
        settings.write_text("{}\n", encoding="utf-8")
        self.git("add", ".claude/settings.json")
        report = docs_only_review.review(self.root, opt_in=True)
        self.assertFalse(report["docs_only"])
        self.assertEqual(report["classification"], "NOT_DOCS_ONLY")
        self.assertIn(".claude/settings.json", report["rejected_paths"])

    def test_symlink_escape_is_rejected(self) -> None:
        outside = Path(self.temp.name) / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        (self.root / "docs").mkdir()
        (self.root / "docs/escape.md").symlink_to(outside)
        self.git("add", "-f", "docs/escape.md")
        report = docs_only_review.review(self.root, opt_in=True)
        self.assertFalse(report["docs_only"])
        self.assertEqual(report["reason_code"], "PATH_OUTSIDE_REPOSITORY")

    def test_empty_diff_does_not_claim_docs_only(self) -> None:
        report = docs_only_review.review(self.root, opt_in=True)
        self.assertFalse(report["docs_only"])
        self.assertEqual(report["reason_code"], "NO_CHANGES")


if __name__ == "__main__":
    unittest.main()
