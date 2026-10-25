from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import publication_scan_evidence as evidence


class PublicationScanEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cache = Path(self.temp.name) / "cache"
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.scope = {
            "repository_id": "a" * 64, "worktree_id": "b" * 64,
            "base_commit": "1" * 40, "candidate_commit": "2" * 40,
            "operations": ["git_push"], "remote": "origin",
            "target_ref": "refs/heads/codex/fixture", "expected_remote_oid": "3" * 40,
            "diff_digest": "sha256:" + "4" * 64,
        }
        self.cache_patch = patch.object(evidence.runtime_cache, "cache_home", return_value=self.cache)
        self.cache_patch.start()
        self.addCleanup(self.cache_patch.stop)

    def test_evidence_is_exact_short_lived_and_integrity_checked(self):
        digest = evidence.store(self.root, self.scope, policy_digest="sha256:" + "5" * 64, now=100)
        self.assertTrue(digest.startswith("sha256:"))
        self.assertTrue(evidence.valid(self.root, self.scope,
                                      policy_digest="sha256:" + "5" * 64, now=101))
        self.assertFalse(evidence.valid(self.root, self.scope,
                                       policy_digest="sha256:" + "5" * 64, now=401))
        for field, value in (("candidate_commit", "6" * 40),
                             ("base_commit", "7" * 40),
                             ("target_ref", "refs/heads/codex/other"),
                             ("expected_remote_oid", "8" * 40),
                             ("diff_digest", "sha256:" + "9" * 64)):
            changed = dict(self.scope, **{field: value})
            self.assertFalse(evidence.valid(self.root, changed,
                                            policy_digest="sha256:" + "5" * 64, now=101), field)
        self.assertFalse(evidence.valid(self.root, self.scope,
                                       policy_digest="sha256:" + "a" * 64, now=101))
        stored = next((self.cache / "aips-publication-scan-evidence").glob("*.json"))
        payload = json.loads(stored.read_text())
        payload["status"] = "BLOCKED"
        stored.write_text(json.dumps(payload))
        self.assertFalse(evidence.valid(self.root, self.scope,
                                       policy_digest="sha256:" + "5" * 64, now=101))

    def test_missing_or_symlinked_evidence_fails_closed(self):
        self.assertFalse(evidence.valid(self.root, self.scope, policy_digest="sha256:" + "5" * 64))
        evidence.store(self.root, self.scope, policy_digest="sha256:" + "5" * 64, now=100)
        stored = next((self.cache / "aips-publication-scan-evidence").glob("*.json"))
        target = stored.with_suffix(".target")
        stored.rename(target)
        stored.symlink_to(target)
        self.assertFalse(evidence.valid(self.root, self.scope,
                                       policy_digest="sha256:" + "5" * 64, now=101))


if __name__ == "__main__":
    unittest.main()
