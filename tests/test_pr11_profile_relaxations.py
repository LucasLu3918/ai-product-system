"""PR11 profile-gated relaxations: Claude co-author trailer and post-merge background refresh.

Every switch is off by default. No literal address appears in this file; the separator is built at runtime.
Temporary directories only: the real ~/.config/aips is never read or written.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import aips_profile as ap
import publish_preflight as publish
import turn_context_hook as hook

AT = chr(64)
CLAUDE = f"Co-Authored-By: Claude Sonnet 5.5 <noreply{AT}anthropic.com>"
ON = {"claude_coauthor_trailer": True}
HEAD = "a" * 40


def scan(text: str) -> str:
    return publish.safe_emit(sink="git_commit", payload=text)["decision"]


class ClaudeCoauthorTrailerTests(unittest.TestCase):
    def policy(self, values):
        return publish.git_identity_policy(values)

    def mask(self, message: str, values=ON, author: str = "human-author") -> str:
        return publish.mask_trailer_identities(message, author, self.policy(values))

    def test_switch_is_registered_and_off_by_default(self):
        self.assertIn("claude_coauthor_trailer", ap.SWITCHES)
        self.assertFalse(ap.SWITCHES["claude_coauthor_trailer"].default)
        self.assertTrue(ap.SWITCHES["claude_coauthor_trailer"].implication_zh)
        self.assertTrue(ap.SWITCHES["claude_coauthor_trailer"].implication_en)

    def test_exact_trailer_is_allowed_when_enabled(self):
        message = "feat: change\n\nbody text\n\n" + CLAUDE
        masked = self.mask(message)
        self.assertEqual(scan(message), "BLOCK")
        self.assertEqual(scan(masked), "ALLOW")
        self.assertNotIn(AT, masked)

    def test_switch_off_keeps_blocking(self):
        message = "feat: change\n\nbody\n\n" + CLAUDE
        for values in ({}, {"claude_coauthor_trailer": False}):
            self.assertEqual(self.mask(message, values), message)
            self.assertEqual(scan(self.mask(message, values)), "BLOCK")

    def test_default_loading_without_profile_file_is_off(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
                ap, "profile_settings_path", return_value=Path(directory) / "missing.yaml"):
            policy = publish.git_identity_policy()
        message = "subject\n\n" + CLAUDE
        self.assertEqual(publish.mask_trailer_identities(message, "x", policy), message)

    def test_wrong_domain_or_look_alike_is_blocked(self):
        for line in (
            f"Co-Authored-By: Claude Sonnet 5.5 <noreply{AT}anthropic.org>",
            f"Co-Authored-By: Claude Sonnet 5.5 <noreply{AT}anthropic.com.evil.test>",
            f"Co-Authored-By: Claude Sonnet 5.5 <noreply{AT}ANTHROPIC.com>",
            f"Co-Authored-By: Claude Sonnet 5.5 <someone{AT}anthropic.com>",
            f"Co-Authored-By: Claude Sonnet 5.5 <noreply{AT}anthropic.com >",
            f"Co-Authored-By: Claude Sonnet 5.5 <noreply{AT}gmail.com>",
            f"Co-Authored-By: Claude Sonnet 5.5 <noreply{AT}anthropic.com><other{AT}example.net>",
        ):
            message = "subject\n\n" + line
            self.assertEqual(self.mask(message), message, line)
            self.assertEqual(scan(self.mask(message)), "BLOCK", line)

    def test_other_names_and_keys_are_blocked(self):
        for line in (
            f"Co-Authored-By: Someone Else <noreply{AT}anthropic.com>",
            f"Co-Authored-By: Claude <noreply{AT}anthropic.com>",
            f"Co-Authored-By: Claude Sonnet! <noreply{AT}anthropic.com>",
            f"Co-Authored-By: Claude  Sonnet <noreply{AT}anthropic.com>",
            f"Co-authored-by: Claude Sonnet 5.5 <noreply{AT}anthropic.com>",
            f"Signed-off-by: Claude Sonnet 5.5 <noreply{AT}anthropic.com>",
            f"Reviewed-by: Claude Sonnet 5.5 <noreply{AT}anthropic.com>",
        ):
            message = "subject\n\n" + line
            self.assertEqual(self.mask(message), message, line)

    def test_email_in_body_stays_blocked(self):
        body_email = "subject\n\ncontact person" + AT + "example.net for details\n\n" + CLAUDE
        masked = self.mask(body_email)
        self.assertIn(AT + "example.net", masked)
        self.assertEqual(scan(masked), "BLOCK")
        in_body = "subject\n\n" + CLAUDE + "\n\nfinal words"
        self.assertEqual(self.mask(in_body), in_body)
        self.assertEqual(scan(in_body), "BLOCK")
        self.assertEqual(self.mask(CLAUDE), CLAUDE)

    def test_multiple_trailers(self):
        other = f"Co-Authored-By: Pat Example <pat{AT}example.net>"
        mixed = "subject\n\nbody\n\n" + CLAUDE + "\n" + other
        masked = self.mask(mixed)
        self.assertIn("pat" + AT + "example.net", masked)
        self.assertEqual(scan(masked), "BLOCK")
        claude_with_plain_trailer = "subject\n\nbody\n\nChange-Id: I1234\n" + CLAUDE
        self.assertEqual(scan(self.mask(claude_with_plain_trailer)), "ALLOW")
        non_trailer_line = "subject\n\nbody\n\n" + CLAUDE + "\nthanks"
        self.assertEqual(self.mask(non_trailer_line), non_trailer_line)

    def test_other_gate_checks_are_not_relaxed(self):
        fake_token = "ghp_" + "A" * 40
        message = "subject\n\n" + fake_token + "\n\n" + CLAUDE
        self.assertEqual(scan(self.mask(message)), "BLOCK")

    def test_malformed_profile_entry_fails_closed(self):
        bad = {"identity": {"allowed_email_patterns": ["^x$"],
                            "profile_trailer_identities": {"claude_coauthor_trailer": {"key": "Co-Authored-By"}}}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.yaml"
            path.write_text(yaml.safe_dump(bad), encoding="utf-8")
            with patch.object(publish, "GIT_PUBLICATION_POLICY", path), self.assertRaises(publish.GitIdentityPolicyError):
                publish.git_identity_policy(ON)

    def test_profile_helper_returns_empty_on_failure(self):
        with patch.object(ap, "load_profile", side_effect=RuntimeError("boom")):
            self.assertEqual(publish._profile_values(), {})


def stale_ready_manifest(root: Path, store: Path, reason: str = "task_topics_affected") -> dict:
    return {
        "project": {"root": str(root), "intelligence_store": str(store)},
        "intelligence": {"readiness": "READY", "freshness": "STALE"},
        "requirements": {"refresh_required": reason == "task_topics_affected", "freshness_advisory": True,
                         "refresh_reason": reason},
    }


class PostMergeRefreshTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(os.path.realpath(tmp.name)) / "project"
        self.store = self.root / ".ai" / "intelligence"
        self.store.mkdir(parents=True)

    def enabled(self, value: bool = True):
        state = ap.ProfileState("LOADED", {"post_merge_refresh": value}, {"post_merge_refresh": "file"}, None)
        return patch.object(hook, "load_profile", return_value=state)

    def git_head(self, head: str = HEAD):
        return patch.object(hook.subprocess, "run", return_value=MagicMock(stdout=head + "\n"))

    def test_switch_registered_and_off_by_default(self):
        self.assertIn("post_merge_refresh", ap.SWITCHES)
        self.assertFalse(ap.SWITCHES["post_merge_refresh"].default)

    def test_off_starts_nothing(self):
        popen = MagicMock()
        with self.enabled(False), self.git_head():
            self.assertFalse(hook.maybe_start_post_merge_refresh(stale_ready_manifest(self.root, self.store), popen))
        popen.assert_not_called()
        self.assertEqual(list(self.store.iterdir()), [])

    def test_enabled_starts_one_detached_refresh_per_head(self):
        popen = MagicMock()
        manifest = stale_ready_manifest(self.root, self.store)
        with self.enabled(), self.git_head():
            self.assertTrue(hook.maybe_start_post_merge_refresh(manifest, popen))
            self.assertFalse(hook.maybe_start_post_merge_refresh(manifest, popen))
        popen.assert_called_once()
        command = popen.call_args.args[0]
        self.assertEqual(command[1:3], ["intelligence", "refresh"])
        self.assertEqual(command[-1], str(self.root))
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        self.assertEqual([item.name for item in self.store.iterdir()], [f".post-merge-refresh-{HEAD}.lock"])

    def test_new_head_starts_again_and_drops_old_lock(self):
        popen = MagicMock()
        manifest = stale_ready_manifest(self.root, self.store)
        with self.enabled():
            with self.git_head():
                self.assertTrue(hook.maybe_start_post_merge_refresh(manifest, popen))
            with self.git_head("b" * 40):
                self.assertTrue(hook.maybe_start_post_merge_refresh(manifest, popen))
        self.assertEqual(popen.call_count, 2)
        self.assertEqual([item.name for item in self.store.iterdir()], [f".post-merge-refresh-{'b' * 40}.lock"])

    def test_only_when_task_topics_are_affected(self):
        popen = MagicMock()
        with self.enabled(), self.git_head():
            for reason in ("task_topics_not_affected", "no_task_relevant_topics"):
                self.assertFalse(hook.maybe_start_post_merge_refresh(stale_ready_manifest(self.root, self.store, reason), popen))
            partial = stale_ready_manifest(self.root, self.store)
            partial["intelligence"]["readiness"] = "PARTIAL"
            self.assertFalse(hook.maybe_start_post_merge_refresh(partial, popen))
            current = stale_ready_manifest(self.root, self.store)
            current["intelligence"]["freshness"] = "CURRENT"
            self.assertFalse(hook.maybe_start_post_merge_refresh(current, popen))
        popen.assert_not_called()

    def test_missing_store_or_bad_head_or_errors_never_raise(self):
        popen = MagicMock(side_effect=OSError("spawn failed"))
        with self.enabled():
            with self.git_head("not-a-sha"):
                self.assertFalse(hook.maybe_start_post_merge_refresh(stale_ready_manifest(self.root, self.store), popen))
            with self.git_head():
                missing = stale_ready_manifest(self.root, self.root / "absent")
                self.assertFalse(hook.maybe_start_post_merge_refresh(missing, popen))
                self.assertFalse(hook.maybe_start_post_merge_refresh(stale_ready_manifest(self.root, self.store), popen))
            self.assertFalse(hook.maybe_start_post_merge_refresh({}, popen))

    def test_profile_import_failure_is_off(self):
        with patch.object(hook, "load_profile", None):
            self.assertFalse(hook.maybe_start_post_merge_refresh(stale_ready_manifest(self.root, self.store), MagicMock()))


if __name__ == "__main__":
    unittest.main()
