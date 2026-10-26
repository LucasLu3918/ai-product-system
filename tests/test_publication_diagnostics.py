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
        self.assertEqual(result["status"], "READY", result)
        self.assertEqual(result["policy"]["status"], "UNAVAILABLE")
        self.assertEqual(result["policy"]["required_check_state"], "UNKNOWN_PERMISSION")
        self.assertNotIn("protection_evidence_unavailable", result["blockers"])
        diagnosis = next(item for item in result["diagnostics"]
                         if item["reason_code"] == "REQUIRED_CHECKS_POLICY_PERMISSION")
        self.assertFalse(diagnosis["retryable"])
        self.assertEqual(diagnosis["category"], "PERMISSION")
        self.assertEqual(result["next_steps"], [item["next_step"] for item in result["diagnostics"]])
        self.assertNotIn("private detail", str(result))

        with patch.dict(os.environ, {"AIPS_ENFORCE_REQUIRED_CHECKS": "1"}), \
                patch("publication_diagnostics.subprocess.run", side_effect=run), \
                patch("publication_authority._remote_default_branch", return_value="main"), \
                patch("publication_planning._prs", return_value=[]):
            strict = diagnostics.doctor(self.root)
        self.assertEqual(strict["status"], "BLOCKED", strict)
        self.assertIn("protection_evidence_unavailable", strict["blockers"])

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
        diagnostic = json.loads(context.removeprefix("AIPS diagnostic: ").split("; authorization_status=", 1)[0])
        self.assertEqual(diagnostic["phase"], "publication_candidate_remote_and_evidence_validation")
        self.assertGreaterEqual(diagnostic["elapsed_ms"], 0)
        self.assertNotIn("private token detail", output.getvalue())

    def test_generic_git_reads_do_not_query_github(self):
        from contextlib import redirect_stdout
        from io import StringIO

        real_run = subprocess.run
        observed = []

        def run(argv, *args, **kwargs):
            observed.append(list(argv))
            self.assertNotEqual(Path(argv[0]).name, "gh")
            return real_run(argv, *args, **kwargs)

        for command in ("git status --short", "git diff --stat"):
            output = StringIO()
            payload = {"cwd": str(self.root), "tool_input": {"command": command}}
            with patch("governance_guard.subprocess.run", side_effect=run), \
                    patch.object(governance_guard.sys, "stdin", StringIO(json.dumps(payload))), \
                    redirect_stdout(output):
                governance_guard.hook("claude-code")
            self.assertEqual(output.getvalue().strip(), "{}")
        self.assertFalse(any(Path(call[0]).name == "gh" for call in observed))

    def test_hook_deadline_denial_reports_phase_and_elapsed_time(self):
        import time
        from contextlib import redirect_stdout
        from io import StringIO

        output = StringIO()

        def slow_hook(_runtime):
            governance_guard._HOOK_PHASE = "content_safety"
            time.sleep(0.05)

        with patch.object(governance_guard, "_hook_impl", side_effect=slow_hook), \
                patch.object(governance_guard, "HOOK_DEADLINE_SECONDS", 0.01), \
                patch.object(governance_guard, "_record_publication_diagnostic", return_value="NOT_CONFIGURED"), \
                redirect_stdout(output):
            governance_guard.hook("claude-code")
        payload = json.loads(output.getvalue())["hookSpecificOutput"]
        self.assertEqual(payload["permissionDecision"], "deny")
        self.assertIn("HOOK_DEADLINE_EXCEEDED", payload["permissionDecisionReason"])
        context = json.loads(payload["additionalContext"].removeprefix("AIPS diagnostic: ").split("; authorization_status=", 1)[0])
        self.assertEqual(context["phase"], "content_safety")
        self.assertGreaterEqual(context["elapsed_ms"], 1)

    def test_post_tool_timeout_is_not_misclassified_as_network_failure(self):
        from contextlib import redirect_stdout
        from io import StringIO

        output = StringIO()
        payload = {"hook_event_name": "PostToolUseFailure", "tool_name": "Bash",
                   "error": "command timed out while running"}
        with patch.object(governance_guard.sys, "stdin", StringIO(json.dumps(payload))), \
                redirect_stdout(output):
            governance_guard.hook("claude-code")
        rendered = json.loads(output.getvalue())["hookSpecificOutput"]["additionalContext"]
        self.assertIn('"error_category":"TIMEOUT_OBSERVED"', rendered)

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
            patch.object(governance_guard, 'operations_for', return_value=['git_push']),
            patch.object(governance_guard, 'safe_emit', return_value={'decision': 'ALLOW'}),
            patch('publication_commands.shell_commands', return_value=[['git', 'push', 'origin',
                head + ':refs/heads/codex/wrong-target']]),
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

    def test_claude_native_tool_failure_reports_only_safe_execution_evidence(self):
        from contextlib import redirect_stdout
        from io import StringIO

        sentinel = 'PRIVATE_NATIVE_ERROR_SENTINEL'
        payload = {
            'hook_event_name': 'PostToolUseFailure', 'tool_name': 'Bash',
            'tool_input': {'command': 'git push ' + sentinel},
            'error': f'Command failed with exit code 17: {sentinel}',
        }
        output = StringIO()
        with patch('sys.stdin', StringIO(json.dumps(payload))), redirect_stdout(output):
            governance_guard.hook('claude-code')
        text = output.getvalue()
        self.assertNotIn(sentinel, text)
        hook = json.loads(text)['hookSpecificOutput']
        self.assertEqual(hook['hookEventName'], 'PostToolUseFailure')
        self.assertIn('"phase":"native_tool_execution"', hook['additionalContext'])
        self.assertIn('"exit_code":17', hook['additionalContext'])
        self.assertIn('"execution_status":"FAILED"', hook['additionalContext'])

    def test_pretool_denial_is_not_reported_as_native_execution_failure(self):
        from contextlib import redirect_stdout
        from io import StringIO

        payload = {'hook_event_name': 'PreToolUse', 'tool_name': 'Bash',
                   'tool_input': {'command': ''}}
        output = StringIO()
        with patch('sys.stdin', StringIO(json.dumps(payload))), redirect_stdout(output):
            governance_guard.hook('claude-code')
        self.assertNotIn('native_tool_execution', output.getvalue())
        self.assertEqual(output.getvalue().strip(), '{}')

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

    def test_claude_hook_does_not_run_doctor_inline_for_retryable_remote_failure(self):
        from contextlib import redirect_stdout
        from io import StringIO

        from publication_authority import PublicationError

        command = "gh pr merge 7 --repo fixture/repo --squash --match-head-commit " + "a" * 40
        calls = []
        def run(argv, **kwargs):
            calls.append(argv)
            raise AssertionError("Doctor must not run inside the synchronous PreToolUse hook")

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
        self.assertEqual(calls, [])
        payload = json.loads(output.getvalue())["hookSpecificOutput"]
        self.assertEqual(payload["permissionDecision"], "deny")
        self.assertIn("aips publish doctor --worktree . --format json", payload["permissionDecisionReason"])
        self.assertNotIn('"doctor_observation"', payload["additionalContext"])
        self.assertIn("authorization_status=DENIED", payload["additionalContext"])
        self.assertIn("execution_status=NOT_EXECUTED", payload["additionalContext"])

    def test_claude_hook_timeout_returns_safe_diagnosis_without_command_text(self):
        from contextlib import redirect_stdout
        from io import StringIO

        secret_command = "git ls-remote PRIVATE_ENDPOINT PRIVATE_TOKEN"
        command = "git push origin " + "a" * 40 + ":refs/heads/codex/fixture"
        output = StringIO()
        with patch.object(governance_guard, "operations_for", return_value=["git_push"]), \
                patch.object(governance_guard, "safe_emit", return_value={"decision": "ALLOW"}), \
                patch("publication_authority.publication_mode", return_value="personal"), \
                patch("publication_commands.shell_commands", return_value=[["git", "push", "origin"]]), \
                patch("publication_authority.validate_personal_action",
                      side_effect=subprocess.TimeoutExpired(secret_command, 15)), \
                patch.dict(os.environ, {'AIPS_GOVERNANCE_AUDIT_LEDGER': ''}), \
                patch.object(governance_guard.sys, "stdin", StringIO(json.dumps({
                    "cwd": str(self.root), "tool_input": {"command": command}}))), \
                redirect_stdout(output):
            self.assertEqual(governance_guard.hook("claude-code"), 0)
        response = output.getvalue()
        payload = json.loads(response)["hookSpecificOutput"]
        self.assertEqual(payload["permissionDecision"], "deny")
        self.assertIn('"reason_code":"REMOTE_OBSERVATION_FAILED"', payload["additionalContext"])
        self.assertIn('"detail_code":"REMOTE_OBSERVATION_TIMEOUT"', payload["additionalContext"])
        self.assertIn('"phase":"remote_observation"', payload["additionalContext"])
        self.assertIn('"error_class":"TimeoutExpired"', payload["additionalContext"])
        self.assertIn("aips publish doctor --worktree . --format json", response)
        self.assertNotIn("PRIVATE_ENDPOINT", response)
        self.assertNotIn("PRIVATE_TOKEN", response)
        self.assertIn("authorization_status=DENIED", payload["additionalContext"])

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

    def test_prepare_and_diagnose_cli_json_errors_are_structured_and_redacted(self):
        import errno
        from contextlib import redirect_stderr, redirect_stdout
        from io import StringIO

        import publication_planning as planning
        import publish_preflight as preflight

        cases = (
            ("prepare", "prepare", PermissionError(errno.EACCES, "Permission denied", "/private/secret/path"),
             "LOCAL_PERMISSION_DENIED", "EACCES", "PERMISSION"),
            ("diagnose", "diagnose", preflight.PreflightError("private endpoint token=super-secret"),
             "PREFLIGHT_VALIDATION_ERROR", None, "INTERNAL"),
            ("diagnose", "diagnose", ValueError("private body input"),
             "INVALID_PUBLICATION_INPUT", None, "INVALID_ARGUMENT"),
        )
        for command, target, error, reason_code, error_code, category in cases:
            with self.subTest(command=command):
                output, errors = StringIO(), StringIO()
                argv = ["publish_preflight.py", command, "--worktree", str(self.root)]
                if command == "prepare":
                    argv.extend(["--title", "Candidate", "--body-file", str(self.root / "body.md")])
                else:
                    argv.extend(["--command", "git push origin candidate"])
                argv.extend(["--format", "json"])
                with patch.object(planning, target, side_effect=error), \
                        patch.object(sys, "argv", argv), \
                        redirect_stdout(output), redirect_stderr(errors):
                    exit_code = preflight.main()

                self.assertEqual(exit_code, 2)
                payload = json.loads(output.getvalue())
                self.assertEqual(payload["status"], "BLOCKED")
                self.assertFalse(payload["authorized"])
                self.assertFalse(payload["executed"])
                self.assertEqual(payload["diagnostics"][0]["error_class"], type(error).__name__)
                self.assertEqual(payload["diagnostics"][0]["reason_code"], reason_code)
                self.assertEqual(payload["diagnostics"][0]["category"], category)
                if error_code:
                    self.assertEqual(payload["diagnostics"][0]["error_code"], error_code)
                self.assertTrue(payload["diagnostics"][0]["redacted"])
                self.assertNotIn("super-secret", output.getvalue())
                self.assertNotIn("/private/secret/path", output.getvalue())
                self.assertEqual(errors.getvalue(), "")

    def test_cli_text_exception_output_remains_compatible(self):
        from contextlib import redirect_stderr, redirect_stdout
        from io import StringIO

        import publication_planning as planning
        import publish_preflight as preflight

        output, errors = StringIO(), StringIO()
        argv = ["publish_preflight.py", "diagnose", "--worktree", str(self.root),
                "--command", "git push origin candidate"]
        with patch.object(planning, "diagnose", side_effect=preflight.PreflightError("legacy failure")), \
                patch.object(sys, "argv", argv), redirect_stdout(output), redirect_stderr(errors):
            exit_code = preflight.main()
        self.assertEqual(exit_code, 2)
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(errors.getvalue(), "PUBLISH PREFLIGHT ERROR: legacy failure\n")


if __name__ == "__main__":
    unittest.main()
