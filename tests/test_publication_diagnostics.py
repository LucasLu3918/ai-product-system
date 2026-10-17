from __future__ import annotations

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
import governance_audit
import governance_guard
import publication_authority as authority
import publication_diagnostics as diagnostics
import repository_governance_snapshot as governance_snapshot


class PublicationDiagnosticsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        subprocess.run(["git", "init", "-b", "main"], cwd=self.root, check=True,
                       capture_output=True, text=True)
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/fixture/repo.git"],
                       cwd=self.root, check=True, capture_output=True, text=True)

    def test_doctor_reports_policy_and_checks_without_side_effects(self):
        real_run = subprocess.run
        calls = []

        def run(argv, *args, **kwargs):
            if Path(argv[0]).name != "gh":
                return real_run(argv, *args, **kwargs)
            calls.append(list(argv))
            if argv[1:3] == ["auth", "status"]:
                return subprocess.CompletedProcess(argv, 0, "", "")
            endpoint = argv[-1]
            if endpoint == "repos/fixture/repo":
                data = {"allow_squash_merge": True, "allow_merge_commit": False,
                        "allow_rebase_merge": True}
            elif endpoint.endswith("/rules/branches/main"):
                data = []
            elif endpoint.endswith("/branches/main"):
                data = {"name": "main", "protected": True}
            elif endpoint.endswith("/rulesets?includes_parents=true&per_page=100"):
                data = []
            elif endpoint.endswith("/branches/main/protection"):
                data = {"required_status_checks": {"contexts": ["repository"]}}
            else:
                raise AssertionError("unexpected GitHub read")
            return subprocess.CompletedProcess(argv, 0, json.dumps(data), "")

        with patch("publication_diagnostics.subprocess.run", side_effect=run), \
                patch("publication_authority._remote_default_branch", return_value="main"), \
                patch("publication_planning._prs", return_value=[]):
            result = diagnostics.doctor(self.root)
        self.assertEqual(result["status"], "READY", result)
        self.assertFalse(result["authorized"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["api_write_performed"])
        self.assertEqual(result["version"], 2)
        self.assertEqual(result["worktree"]["status"], "CLEAN")
        self.assertTrue(any(item["phase"] == "worktree_validation" for item in result["phases"]))
        self.assertEqual(result["merge_methods"], ["rebase", "squash"])
        self.assertEqual(result["policy"]["required_checks"], ["repository"])
        self.assertFalse(result["policy"]["api_write_performed"])
        self.assertTrue(all(call[:2] != ["gh", "api"] or " -X " not in " ".join(call) for call in calls))

    def test_incomplete_protection_visibility_stays_blocked_unknown(self):
        real_run = subprocess.run

        def run(argv, *args, **kwargs):
            if Path(argv[0]).name != "gh":
                return real_run(argv, *args, **kwargs)
            if argv[1:3] == ["auth", "status"]:
                return subprocess.CompletedProcess(argv, 0, "", "")
            if argv[-1] == "repos/fixture/repo":
                data = {"allow_squash_merge": True}
                return subprocess.CompletedProcess(argv, 0, json.dumps(data), "")
            if "branches/main" in argv[-1] and "protection" not in argv[-1]:
                if "/rules/branches/" in argv[-1]:
                    return subprocess.CompletedProcess(argv, 1, "", "HTTP 403 private detail")
                return subprocess.CompletedProcess(argv, 0, json.dumps({"name": "main", "protected": True}), "")
            if "rulesets?" in argv[-1]:
                return subprocess.CompletedProcess(argv, 0, "[]", "")
            return subprocess.CompletedProcess(argv, 1, "", "HTTP 403 private detail")

        with patch("publication_diagnostics.subprocess.run", side_effect=run), \
                patch("publication_authority._remote_default_branch", return_value="main"), \
                patch("publication_planning._prs", return_value=[]):
            result = diagnostics.doctor(self.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["policy"]["status"], "UNAVAILABLE")
        diagnosis = next(item for item in result["diagnostics"]
                         if item["reason_code"] == "REQUIRED_CHECKS_POLICY_PERMISSION")
        self.assertFalse(diagnosis["retryable"])
        self.assertEqual(diagnosis["category"], "PERMISSION")
        self.assertEqual(result["next_steps"], [item["next_step"] for item in result["diagnostics"]])
        self.assertNotIn("private detail", str(result))

    def test_policy_permission_and_transient_failures_keep_distinct_safe_categories(self):
        base = {"source_complete": False, "sources": {"branch_protection": {
            "status": "UNKNOWN_PERMISSION", "endpoint": "repos/fixture/repo/branches/main/protection",
            "http_status": 403, "error_class": "PERMISSION", "error_message": "private"}},
            "branch_protection": {}, "rulesets": []}
        permission = diagnostics.required_checks_policy(base)
        self.assertEqual((permission["status"], permission["category"], permission["retryable"]),
                         ("UNKNOWN_PERMISSION", "PERMISSION", False))
        for category in ("NETWORK", "RATE_LIMITED", "GITHUB_SERVER_ERROR"):
            snapshot = {**base, "sources": {"branch_protection": {
                "status": "UNKNOWN", "endpoint": "repos/fixture/repo/branches/main/protection",
                "http_status": None, "error_class": category}}}
            observed = diagnostics.required_checks_policy(snapshot)
            self.assertEqual(observed["category"], category)
            self.assertTrue(observed["retryable"])
        self.assertEqual(diagnostics.remote_failure("HTTP 429 secondary rate limit"), "RATE_LIMITED")
        self.assertEqual(diagnostics.remote_failure("HTTP 503 service unavailable"), "GITHUB_SERVER_ERROR")

    def test_doctor_observes_remote_default_policy_branch_separately(self):
        subprocess.run(["git", "checkout", "-b", "codex/source"], cwd=self.root, check=True,
                       capture_output=True, text=True)
        real_run = subprocess.run

        def run(argv, *args, **kwargs):
            if Path(argv[0]).name != "gh":
                return real_run(argv, *args, **kwargs)
            if argv[1:3] == ["auth", "status"]:
                return subprocess.CompletedProcess(argv, 0, "", "")
            if argv[-1] == "repos/fixture/repo":
                return subprocess.CompletedProcess(argv, 0, json.dumps({"allow_squash_merge": True}), "")
            raise AssertionError("doctor should use the shared structured API observer")

        payloads = {
            "rules/branches/main": [],
            "branches/main": {"name": "main", "protected": True},
            "rulesets?includes_parents=true&per_page=100": [],
            "branches/main/protection": {"required_status_checks": {"contexts": ["ci"]}},
        }

        def query(_root, endpoint):
            return {"returncode": 0, "http_status": 200,
                    "payload": next(value for suffix, value in payloads.items() if endpoint.endswith(suffix)),
                    "endpoint": endpoint, "error_class": None, "error_message": None}

        with patch("publication_diagnostics.subprocess.run", side_effect=run), \
                patch("publication_authority._remote_default_branch", return_value="main"), \
                patch("repository_governance_snapshot.query_github_api", side_effect=query), \
                patch("publication_planning._prs", return_value=[]):
            result = diagnostics.doctor(self.root)
        self.assertEqual(result["candidate_branch"], "codex/source")
        self.assertEqual(result["policy_branch"], "main")
        self.assertEqual(result["governance"]["branch"], "main")
        self.assertEqual(result["status"], "READY", result)

    def test_doctor_branch_option_overrides_remote_default_policy_target(self):
        subprocess.run(["git", "checkout", "-b", "codex/source"], cwd=self.root, check=True,
                       capture_output=True, text=True)
        real_run = subprocess.run

        def run(argv, *args, **kwargs):
            if Path(argv[0]).name != "gh":
                return real_run(argv, *args, **kwargs)
            if argv[1:3] == ["auth", "status"]:
                return subprocess.CompletedProcess(argv, 0, "", "")
            if argv[-1] == "repos/fixture/repo":
                return subprocess.CompletedProcess(argv, 0, json.dumps({"allow_squash_merge": True}), "")
            raise AssertionError("no PR is expected")

        observed = {"branch_protection": {"required_checks": ["ci"]}, "source_complete": True,
                    "protection_state": "PROTECTED", "evidence_level": "EFFECTIVE_RULES_CONFIRMED",
                    "sources": {}, "rulesets": []}
        with patch("publication_diagnostics.subprocess.run", side_effect=run), \
                patch("publication_authority._remote_default_branch", return_value="main"), \
                patch("repository_governance_snapshot.build_snapshot", return_value=observed) as build, \
                patch("publication_planning._prs", return_value=[]):
            result = diagnostics.doctor(self.root, branch="release")
        self.assertEqual(result["candidate_branch"], "codex/source")
        self.assertEqual(result["policy_branch"], "release")
        self.assertEqual(build.call_args.args[1], "release")

    def test_github_http_authentication_and_permission_are_distinct(self):
        token = "ghp_" + "abcdefghijklmnopqrst" + "uvwxyz1234567890"
        auth = governance_snapshot.parse_gh_response(
            "repos/fixture/repo", 1,
            "HTTP/2 401\r\ncontent-type: application/json\r\n\r\n{\"message\":\"bad token\"}")
        permission = governance_snapshot.parse_gh_response(
            "repos/fixture/repo", 1,
            "HTTP/2 403\r\ncontent-type: application/json\r\n\r\n" +
            json.dumps({"message": "token " + token + " leaked?"}))
        self.assertEqual(auth["error_class"], "AUTHENTICATION")
        self.assertEqual(permission["error_class"], "PERMISSION")
        self.assertNotIn(token, str(permission))
        limited = governance_snapshot.parse_gh_response(
            "repos/fixture/repo", 1,
            "HTTP/2 403\r\nretry-after: 30\r\ncontent-type: application/json\r\n\r\n{\"message\":\"rate limited\"}")
        self.assertEqual(limited["error_class"], "RATE_LIMITED")

    def test_claude_hook_denial_includes_bounded_diagnostic_not_command(self):
        from contextlib import redirect_stdout
        from io import StringIO

        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(governance_guard.deny_hook_input(
                "claude-code", "REMOTE_OBSERVATION_FAILED"), 0)
        payload = json.loads(output.getvalue())["hookSpecificOutput"]
        self.assertEqual(payload["permissionDecision"], "deny")
        self.assertIn("diagnostic_id=", payload["permissionDecisionReason"])
        self.assertIn("phase=", payload["permissionDecisionReason"])
        context = payload["additionalContext"]
        self.assertIn('"reason_code":"REMOTE_OBSERVATION_FAILED"', context)
        self.assertIn('"authorized":false', context)
        self.assertIn('"executed":false', context)
        self.assertIn('"authorization_status":"DENIED"', context)
        self.assertIn('"source":"AIPS_PUBLICATION"', context)
        self.assertNotIn("command", context)

    def test_internal_hook_failure_exposes_only_safe_error_class(self):
        from contextlib import redirect_stdout
        from io import StringIO

        command = "git push origin " + "a" * 40 + ":refs/heads/codex/fixture"
        output = StringIO()
        with patch.object(governance_guard, "operations_for", return_value=["git_push"]), \
                patch.object(governance_guard, "safe_emit", return_value={"decision": "ALLOW"}), \
                patch("publication_authority.publication_mode", return_value="personal"), \
                patch("publication_commands.shell_commands", return_value=[["git", "push", "origin", "a" * 40 + ":refs/heads/codex/fixture"]]), \
                patch("publication_authority.validate_personal_action", side_effect=RuntimeError("private token detail")), \
                patch.dict(os.environ, {'AIPS_GOVERNANCE_AUDIT_LEDGER': ''}), \
                patch.object(governance_guard.sys, "stdin", StringIO(json.dumps({
                    "cwd": str(self.root), "tool_input": {"command": command}}))), \
                redirect_stdout(output):
            governance_guard.hook("claude-code")
        payload = json.loads(output.getvalue())["hookSpecificOutput"]
        self.assertEqual(payload["permissionDecision"], "deny")
        context = payload["additionalContext"]
        self.assertIn('"error_class":"RuntimeError"', context)
        self.assertNotIn("private token detail", output.getvalue())

    def test_diagnostic_ledger_records_only_allowlisted_error_class(self):
        ledger = self.root / "diagnostics.jsonl"
        with patch.dict(os.environ, {'AIPS_GOVERNANCE_AUDIT_LEDGER': str(ledger)}):
            status = diagnostics.record_diagnostic({
                "diagnostic_id": "d2fd1f72-9781-4a52-b220-d474b7e94b2f",
                "reason_code": "INTERNAL_DIAGNOSTIC_GAP", "phase": "hook_authorization",
                "source": "AIPS_PUBLICATION", "blocking_rule_id": "INTERNAL_DIAGNOSTIC_GAP",
                "error_class": "RuntimeError"}, "claude-code")
            unsafe_status = diagnostics.record_diagnostic({
                "diagnostic_id": "9f02fdb5-b2ae-4ef0-89ca-34d102bb93f0",
                "reason_code": "INTERNAL_DIAGNOSTIC_GAP", "phase": "hook_authorization",
                "source": "AIPS_PUBLICATION", "blocking_rule_id": "INTERNAL_DIAGNOSTIC_GAP",
                "error_class": "RuntimeError: secret"}, "claude-code")
        events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(status, "RECORDED")
        self.assertEqual(unsafe_status, "RECORDED")
        self.assertEqual(events[0]["error_class"], "RuntimeError")
        self.assertNotIn("error_class", events[1])

    def test_hook_optional_trace_failure_never_changes_block_decision(self):
        from contextlib import redirect_stdout
        from io import StringIO

        output = StringIO()
        with (
            patch.dict(os.environ, {'AIPS_GOVERNANCE_AUDIT_LEDGER': '/unwritable/ledger.jsonl'}),
            patch('governance_audit.append_event', side_effect=OSError('private path')),
            redirect_stdout(output),
        ):
            governance_guard.deny_hook_input('claude-code', 'REMOTE_OBSERVATION_FAILED')
        payload = json.loads(output.getvalue())['hookSpecificOutput']
        self.assertEqual(payload['permissionDecision'], 'deny')
        self.assertIn('"trace_status":"FAILED"', payload['additionalContext'])

    def test_pretool_hook_denial_preserves_specific_reason_and_binding(self):
        from contextlib import redirect_stdout
        from io import StringIO

        (self.root / 'candidate.txt').write_text('candidate\n')
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True, capture_output=True)
        subprocess.run(['git', '-c', 'user.name=Fixture',
                        '-c', 'user.email=fixture',
                        'commit', '-m', 'fixture'], cwd=self.root, check=True, capture_output=True)
        head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=self.root, check=True,
                              capture_output=True, text=True).stdout.strip()
        command = 'git push origin ' + head + ':refs/heads/codex/wrong-target'
        payload = {'cwd': str(self.root), 'tool_input': {'command': command}}
        output = StringIO()
        hook_env = dict(os.environ)
        for key in list(hook_env):
            if key.startswith('GIT_CONFIG_') or key in {'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE'}:
                hook_env.pop(key, None)
        with (
            patch('sys.stdin', StringIO(json.dumps(payload))),
            patch.dict(os.environ, hook_env, clear=True),
            patch.dict(os.environ, {'AIPS_GOVERNANCE_AUDIT_LEDGER': ''}),
            patch('publication_authority.publication_mode', return_value='personal'),
            patch('publication_authority.validate_personal_action', side_effect=
                  authority.PublicationError(
                      'personal mode permits only the current engineering branch',
                      'PUSH_TARGET_BRANCH_MISMATCH', phase='push_validation')),
            redirect_stdout(output),
        ):
            governance_guard.hook('claude-code')
        hook = json.loads(output.getvalue())['hookSpecificOutput']
        self.assertEqual(hook['permissionDecision'], 'deny')
        self.assertIn('PUSH_TARGET_BRANCH_MISMATCH', hook['permissionDecisionReason'])
        context = hook['additionalContext']
        self.assertIn('"candidate_sha":"' + head + '"', context)
        self.assertIn('"target_ref":"refs/heads/codex/wrong-target"', context)
        self.assertIn('"runtime_version":"0.83.0"', context)
        self.assertIn('authorization_status=DENIED', context)

    def test_diagnostic_lookup_is_explicitly_unconfigured_by_default(self):
        with patch.dict(os.environ, {'AIPS_GOVERNANCE_AUDIT_LEDGER': ''}):
            result = diagnostics.lookup_diagnostic('d2fd1f72-9781-4a52-b220-d474b7e94b2f')
        self.assertEqual(result['status'], 'NOT_CONFIGURED')
        self.assertIn('不會自動建立 ledger', result['next_step_zh'])

    def test_diagnostic_id_cli_reads_allowlisted_existing_ledger_event(self):
        ledger = self.root / 'diagnostics.jsonl'
        diagnostic_id = 'd2fd1f72-9781-4a52-b220-d474b7e94b2f'
        governance_audit.append_event(ledger, {
            'event_type': 'PUBLICATION_DIAGNOSTIC',
            'occurred_at': '2026-10-14T00:00:00Z',
            'diagnostic_id': diagnostic_id,
            'reason_code': 'PUSH_TARGET_BRANCH_MISMATCH',
            'phase': 'push_validation',
            'source': 'AIPS_PUBLICATION',
            'blocking_rule_id': 'PUSH_TARGET_BRANCH_MISMATCH',
            'raw_command': 'must not be returned',
        })
        env = dict(os.environ, AIPS_GOVERNANCE_AUDIT_LEDGER=str(ledger))
        result = subprocess.run([
            sys.executable, str(ROOT / 'scripts/publish_preflight.py'), 'diagnose',
            '--diagnostic-id', diagnostic_id, '--format', 'json'],
            cwd=ROOT, env=env, capture_output=True, text=True, check=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['status'], 'FOUND')
        self.assertEqual(payload['integrity']['status'], 'PASS')
        self.assertEqual(payload['event']['reason_code'], 'PUSH_TARGET_BRANCH_MISMATCH')
        self.assertNotIn('raw_command', payload['event'])

    def test_claude_hook_runs_one_read_only_doctor_only_for_retryable_remote_failure(self):
        from contextlib import redirect_stdout
        from io import StringIO

        from publication_authority import PublicationError

        command = "gh pr merge 7 --repo fixture/repo --squash --match-head-commit " + "a" * 40
        doctor_payload = {"status": "BLOCKED", "read_only": True,
                          "policy": {"required_check_state": "UNAVAILABLE"},
                          "diagnostics": [{"reason_code": "REQUIRED_CHECKS_POLICY_NETWORK",
                              "phase": "protection_policy_evidence", "category": "NETWORK",
                              "retryable": True, "next_step": "Retry safely."}],
                          "authorized": False, "executed": False, "api_write_performed": False}
        calls = []
        def run(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 2, json.dumps(doctor_payload), "sensitive raw output")

        output = StringIO()
        with patch.object(governance_guard, "operations_for", return_value=["gh_pr_merge"]), \
                patch.object(governance_guard, "safe_emit", return_value={"decision": "ALLOW"}), \
                patch("publication_authority.publication_mode", return_value="personal"), \
                patch("publication_commands.shell_commands", return_value=[["gh", "pr", "merge", "7"]]), \
                patch("publication_authority.validate_personal_action", side_effect=PublicationError(
                    "private details", "REQUIRED_CHECKS_POLICY_NETWORK", phase="protection_policy_evidence")), \
                patch.object(governance_guard.subprocess, "run", side_effect=run), \
                patch.dict(os.environ, {'AIPS_GOVERNANCE_AUDIT_LEDGER': ''}), \
                patch.object(governance_guard.sys, "stdin", StringIO(json.dumps({"cwd": str(self.root),
                    "tool_input": {"command": command}}))), \
                redirect_stdout(output):
            self.assertEqual(governance_guard.hook("claude-code"), 0)
        self.assertEqual(len(calls), 1)
        self.assertIn("doctor", calls[0])
        payload = json.loads(output.getvalue())["hookSpecificOutput"]
        self.assertEqual(payload["permissionDecision"], "deny")
        self.assertIn('"doctor_observation"', payload["additionalContext"])
        self.assertNotIn("sensitive raw output", output.getvalue())
        self.assertIn('"authorized":false', payload["additionalContext"])

    def test_aips_cli_routes_doctor_to_non_aips_git_project(self):
        project = self.root / "customer-project"
        project.mkdir()
        subprocess.run(["git", "init", "-b", "main"], cwd=project, check=True,
                       capture_output=True, text=True)
        env = dict(os.environ)
        env["AIPS_VALIDATION_PYTHON"] = sys.executable
        result = subprocess.run([str(ROOT / "bin/aips"), "publish", "doctor", "--project-root",
                                 str(project), "--format", "json"], cwd=ROOT, env=env,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertNotIn("not an AIPS repository", result.stderr)
        self.assertIn("REMOTE_OBSERVATION_FAILED", result.stdout)


if __name__ == "__main__":
    unittest.main()
