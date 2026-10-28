from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import governance_guard as guard
import project_governance_mode as modes


class ProjectGovernanceModeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        subprocess.run(["git", "-C", str(self.root), "init", "-q"], check=True)
        subprocess.run(
            ["git", "-C", str(self.root), "remote", "add", "origin", "https://github.com/example/project.git"],
            check=True,
        )
        self.xdg = Path(self.temp.name) / "config"
        self.env = patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.xdg)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_missing_project_configuration_defaults_to_off_without_writes(self) -> None:
        result = modes.resolve(self.root)

        self.assertEqual(result["mode"], "off")
        self.assertEqual(result["enforce_scope"], [])
        self.assertFalse((self.root / ".ai").exists())
        self.assertFalse((self.root / ".aips").exists())
        self.assertFalse(self.xdg.exists())

    def test_opt_in_mode_is_stored_outside_repository_with_private_permissions(self) -> None:
        result = modes.set_mode(self.root, "assist")

        self.assertEqual(result["mode"], "assist")
        self.assertEqual(result["enforce_scope"], [])
        self.assertTrue(result["config_path"].is_relative_to(self.xdg.resolve()))
        self.assertTrue(result["config_path"].is_file())
        self.assertEqual(result["config_path"].stat().st_mode & 0o777, 0o600)
        self.assertEqual(result["config_path"].parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(modes.resolve(self.root)["mode"], "assist")

    def test_enforce_requires_a_nonempty_allowlisted_scope(self) -> None:
        with self.assertRaises(modes.ModeConfigError):
            modes.set_mode(self.root, "enforce")
        with self.assertRaises(modes.ModeConfigError):
            modes.set_mode(self.root, "enforce", ["git push"])

        result = modes.set_mode(self.root, "enforce", ["git_push", "gh_pr_merge"])

        self.assertEqual(result["mode"], "enforce")
        self.assertEqual(result["enforce_scope"], ["gh_pr_merge", "git_push"])

    def test_unknown_mode_and_scope_are_rejected_without_changing_existing_config(self) -> None:
        modes.set_mode(self.root, "observe")
        with self.assertRaises(modes.ModeConfigError):
            modes.set_mode(self.root, "relaxed")
        with self.assertRaises(modes.ModeConfigError):
            modes.set_mode(self.root, "assist", ["git_push"])

        self.assertEqual(modes.resolve(self.root)["mode"], "observe")

    def test_symlinked_config_is_rejected(self) -> None:
        path = modes.config_path(self.root)
        path.parent.mkdir(parents=True, mode=0o700)
        target = Path(self.temp.name) / "outside.yaml"
        target.write_text("schema_version: 1\nmode: enforce\n")
        path.symlink_to(target)

        with self.assertRaises(modes.ModeConfigError):
            modes.resolve(self.root)

    def test_corrupt_or_wrong_identity_config_is_not_treated_as_off(self) -> None:
        path = modes.config_path(self.root)
        path.parent.mkdir(parents=True, mode=0o700)
        path.write_text("schema_version: [bad]\n")
        with self.assertRaises(modes.ModeConfigError):
            modes.resolve(self.root)

        modes.set_mode(self.root, "assist")
        with path.open("a", encoding="utf-8") as stream:
            stream.write("unexpected: true\n")
        with self.assertRaises(modes.ModeConfigError):
            modes.resolve(self.root)

        modes.set_mode(self.root, "assist")
        path = modes.config_path(self.root)
        content = path.read_text().replace(modes.repository_id(self.root), "0" * 20)
        path.write_text(content)
        with self.assertRaises(modes.ModeConfigError):
            modes.resolve(self.root)

    def test_mode_selection_never_writes_to_project_git_tree(self) -> None:
        modes.set_mode(self.root, "observe")

        status = subprocess.run(
            ["git", "-C", str(self.root), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertEqual(status, "")

    def test_project_cli_can_set_and_show_a_mode(self) -> None:
        cli = ROOT / "scripts" / "aips_cli.sh"
        env = dict(os.environ, XDG_CONFIG_HOME=str(self.xdg))
        set_result = subprocess.run(
            ["bash", str(cli), "project", "mode", "set", "enforce", "--project", str(self.root),
             "--scope", "gh_pr_merge,git_push", "--format", "json"],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        show_result = subprocess.run(
            ["bash", str(cli), "project", "mode", "show", "--project", str(self.root), "--format", "json"],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        status_result = subprocess.run(
            ["bash", str(cli), "status", str(self.root)],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertEqual(json.loads(set_result.stdout)["mode"], "enforce")
        shown = json.loads(show_result.stdout)
        self.assertEqual(shown["mode"], "enforce")
        self.assertEqual(shown["enforce_scope"], ["gh_pr_merge", "git_push"])
        self.assertIn("Optional governance mode: enforce", status_result.stdout)

    def run_guard(
        self,
        mode: dict[str, object],
        publication_mode: str = "personal",
        safety_decision: str = "BLOCK",
    ) -> dict[str, object]:
        payload = {
            "cwd": str(self.root),
            "tool_name": "Bash",
            "tool_input": {"command": "git push origin main"},
        }
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps(payload))), patch("sys.stdout", output), \
                patch("runtime_policy.action_from_hook", return_value=None), \
                patch.object(guard, "operations_for", return_value=["git_push"]), \
                patch.object(guard, "bash_command_writes_protected", return_value=False), \
                patch.object(guard, "file_tool_write_is_protected", return_value=False), \
                patch("project_governance_mode.resolve", return_value=mode), \
                patch("publication_authority.publication_mode", return_value=publication_mode), \
                patch.object(guard, "safe_emit", return_value={"decision": safety_decision, "reason_code": "CONTENT_SECRET_BLOCKED"}):
            self.assertEqual(guard._hook_impl("claude-code"), 0)
        return json.loads(output.getvalue())

    def test_off_mode_skips_project_only_guard(self) -> None:
        response = self.run_guard({"mode": "off", "enforce_scope": []}, safety_decision="ALLOW")

        self.assertEqual(response, {})

    def test_off_mode_does_not_bypass_hard_content_safety(self) -> None:
        response = self.run_guard({"mode": "off", "enforce_scope": []})

        self.assertEqual(response["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("CONTENT_SECRET_BLOCKED", response["hookSpecificOutput"]["permissionDecisionReason"])

    def test_off_mode_does_not_block_unclassifiable_commands_without_global_high_assurance(self) -> None:
        payload = {"cwd": str(self.root), "tool_name": "Bash", "tool_input": {"command": "complex shell"}}
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps(payload))), patch("sys.stdout", output), \
                patch("runtime_policy.action_from_hook", return_value=None), \
                patch.object(guard, "bash_command_writes_protected", return_value=False), \
                patch.object(guard, "file_tool_write_is_protected", return_value=False), \
                patch.object(guard, "operations_for", side_effect=ValueError("unclassified")), \
                patch("project_governance_mode.resolve", return_value={"mode": "off", "enforce_scope": []}), \
                patch("publication_authority.publication_mode", return_value="personal"):
            self.assertEqual(guard._hook_impl("claude-code"), 0)

        self.assertEqual(json.loads(output.getvalue()), {})

    def test_unclassifiable_commands_remain_blocked_by_global_high_assurance(self) -> None:
        payload = {"cwd": str(self.root), "tool_name": "Bash", "tool_input": {"command": "complex shell"}}
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps(payload))), patch("sys.stdout", output), \
                patch("runtime_policy.action_from_hook", return_value=None), \
                patch.object(guard, "bash_command_writes_protected", return_value=False), \
                patch.object(guard, "file_tool_write_is_protected", return_value=False), \
                patch.object(guard, "operations_for", side_effect=ValueError("unclassified")), \
                patch("project_governance_mode.resolve", return_value={"mode": "off", "enforce_scope": []}), \
                patch("publication_authority.publication_mode", return_value="high_assurance"):
            self.assertEqual(guard._hook_impl("claude-code"), 0)

        self.assertEqual(json.loads(output.getvalue())["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_assist_reports_advice_without_blocking_or_granting_host_permission(self) -> None:
        response = self.run_guard({"mode": "assist", "enforce_scope": []}, safety_decision="ALLOW")
        hook_output = response["hookSpecificOutput"]

        self.assertNotIn("permissionDecision", hook_output)
        self.assertIn("assist", hook_output["additionalContext"])
        self.assertIn("REMOTE_BRANCH_UNAVAILABLE", hook_output["additionalContext"])

    def test_assist_does_not_downgrade_hard_content_safety(self) -> None:
        response = self.run_guard({"mode": "assist", "enforce_scope": []}, safety_decision="BLOCK")

        self.assertEqual(response["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("CONTENT_SECRET_BLOCKED", response["hookSpecificOutput"]["permissionDecisionReason"])

    def test_external_assist_configuration_is_consumed_by_the_real_hook_resolver(self) -> None:
        modes.set_mode(self.root, "assist")
        payload = {
            "cwd": str(self.root),
            "tool_name": "Bash",
            "tool_input": {"command": "git push origin main"},
        }
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps(payload))), patch("sys.stdout", output), \
                patch("runtime_policy.action_from_hook", return_value=None), \
                patch.object(guard, "bash_command_writes_protected", return_value=False), \
                patch.object(guard, "file_tool_write_is_protected", return_value=False), \
                patch("publication_authority.publication_mode", return_value="personal"), \
                patch.object(guard, "safe_emit", return_value={"decision": "ALLOW"}):
            self.assertEqual(guard._hook_impl("claude-code"), 0)

        hook_output = json.loads(output.getvalue())["hookSpecificOutput"]
        self.assertNotIn("permissionDecision", hook_output)
        self.assertIn('"mode":"assist"', hook_output["additionalContext"])

    def test_observe_records_only_safe_action_metadata_without_blocking(self) -> None:
        response = self.run_guard({"mode": "observe", "enforce_scope": []}, safety_decision="ALLOW")
        context = response["hookSpecificOutput"]["additionalContext"]

        self.assertNotIn("permissionDecision", response["hookSpecificOutput"])
        self.assertIn('"mode":"observe"', context)
        self.assertIn('"operations":["git_push"]', context)

    def test_gemini_before_tool_advisory_uses_neutral_output_without_decision(self) -> None:
        payload = {
            "cwd": str(self.root),
            "tool_name": "run_shell_command",
            "tool_input": {"command": "git push origin main"},
        }
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps(payload))), patch("sys.stdout", output), \
                patch("runtime_policy.action_from_hook", return_value=None), \
                patch.object(guard, "operations_for", return_value=["git_push"]), \
                patch.object(guard, "bash_command_writes_protected", return_value=False), \
                patch.object(guard, "file_tool_write_is_protected", return_value=False), \
                patch("project_governance_mode.resolve", return_value={"mode": "observe", "enforce_scope": []}), \
                patch("publication_authority.publication_mode", return_value="personal"):
            self.assertEqual(guard._hook_impl("gemini-cli"), 0)

        response = json.loads(output.getvalue())
        self.assertNotIn("decision", response)
        self.assertIn("observe", response["systemMessage"])
        self.assertIn("native host permission", response["systemMessage"])

    def test_enforce_does_not_block_actions_outside_its_explicit_scope(self) -> None:
        response = self.run_guard({"mode": "enforce", "enforce_scope": ["git_commit"]}, safety_decision="ALLOW")

        self.assertNotIn("permissionDecision", response.get("hookSpecificOutput", {}))
        self.assertIn("scope", response.get("hookSpecificOutput", {}).get("additionalContext", ""))

    def test_enforce_blocks_a_scoped_action_when_a_required_check_fails(self) -> None:
        response = self.run_guard({"mode": "enforce", "enforce_scope": ["git_push"]}, safety_decision="ALLOW")

        self.assertEqual(response["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_off_mode_cannot_override_global_high_assurance(self) -> None:
        response = self.run_guard({"mode": "off", "enforce_scope": []}, publication_mode="high_assurance", safety_decision="ALLOW")
        hook_output = response["hookSpecificOutput"]

        self.assertEqual(hook_output["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
