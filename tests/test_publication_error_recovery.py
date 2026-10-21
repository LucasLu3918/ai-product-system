"""Contract tests: reason fidelity, Required Checks policy evidence and recovery safety."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from publication_authority import PublicationError
from publication_diagnostics import classify_required_checks
from publication_planning import recovery_guidance


class PublicationRecoveryContractTest(unittest.TestCase):
    def test_specific_merge_errors_not_collapsed_to_generic_rejection(self):
        for code in ("MERGE_HEAD_PIN_REQUIRED", "MERGE_HEAD_MISMATCH",
                     "MERGE_METHOD_REQUIRED", "MERGE_PR_NUMBER_REQUIRED",
                     "MERGE_OPTION_FORBIDDEN"):
            with self.subTest(code=code):
                item = PublicationError("sensitive local detail", code).diagnostic()
                self.assertEqual(item["reason_code"], code)
                self.assertEqual(item["source"], "AIPS_PUBLICATION")
                self.assertNotIn("sensitive local detail", str(item))
                self.assertTrue(item["next_step"])

    def test_absent_required_checks_distinguish_policy_proof(self):
        error = "no required checks reported on feature"
        cases = [
            (None, "UNAVAILABLE", "REQUIRED_CHECKS_POLICY_UNVERIFIED"),
            ([], "UNCONFIGURED", "REQUIRED_CHECKS_UNCONFIGURED"),
            (["repository"], "MISSING", "REQUIRED_CHECKS_MISSING"),
        ]
        for policy, status, code in cases:
            with self.subTest(policy=policy):
                result = classify_required_checks(None, returncode=1, stderr=error,
                                                  required_policy=policy)
                self.assertEqual((result["status"], result["reason_code"]), (status, code))
        self.assertEqual(classify_required_checks([], required_policy=None)["status"],
                         "UNAVAILABLE")

    def test_configured_required_policy_requires_evidence_and_skip_remains_aips_blocked(self):
        missing = classify_required_checks([], required_policy=["verify", "visual-audit"])
        skipped = classify_required_checks([{"name": "verify", "bucket": "skipping"}],
                                           required_policy=["verify"])
        self.assertEqual((missing["status"], missing["checks"]),
                         ("MISSING", ["verify", "visual-audit"]))
        self.assertEqual((skipped["status"], skipped["reason_code"]),
                         ("MISSING", "REQUIRED_CHECKS_MISSING"))
        self.assertEqual((skipped["provider_status"], skipped["github_required_check_outcome"]),
                         ("SKIPPING", "SUCCESSFUL"))

    def test_host_denial_requires_human_and_does_not_execute(self):
        report = {"status": "BLOCKED", "next_step": "REOBSERVE",
                  "diagnostics": [PublicationError("", "HOST_MERGE_WITHOUT_REVIEW").diagnostic()]}
        recovery = recovery_guidance(report)
        self.assertEqual(recovery["state"], "HOST_PERMISSION_REQUIRED")
        self.assertTrue(recovery["requires_human"])
        self.assertFalse(recovery["retry_read_only"])
        self.assertFalse(recovery["authorized"])
        self.assertFalse(recovery["executed"])

    def test_only_read_observation_retries_while_check_pending(self):
        report = {"status": "BLOCKED", "diagnostics": [
            PublicationError("", "REQUIRED_CHECKS_PENDING").diagnostic()]}
        result = recovery_guidance(report)
        self.assertTrue(result["retry_read_only"])
        self.assertTrue(report["diagnostics"][0]["retryable"])
        self.assertFalse(result["authorized"])
        self.assertFalse(result["executed"])

    def test_transient_remote_observation_retries_but_permission_does_not(self):
        unknown_remote = PublicationError("", "REMOTE_OBSERVATION_FAILED").diagnostic()
        transient = recovery_guidance({"status": "BLOCKED", "diagnostics": [{
            **unknown_remote, "category": "NETWORK", "retryable": True}]})
        permission = recovery_guidance({"status": "BLOCKED", "diagnostics": [
            PublicationError("", "REQUIRED_CHECKS_PERMISSION").diagnostic()]})
        self.assertEqual(transient["state"], "READ_OBSERVATION_RETRYABLE")
        self.assertTrue(transient["retry_read_only"])
        self.assertFalse(transient["authorized"])
        self.assertFalse(transient["executed"])
        self.assertEqual(permission["state"], "REPAIR_REQUIRED")
        self.assertFalse(permission["retry_read_only"])
        unknown = recovery_guidance({"status": "BLOCKED", "diagnostics": [unknown_remote]})
        self.assertFalse(unknown["retry_read_only"])
        self.assertFalse(unknown_remote["retryable"])

    def test_timeout_is_a_retryable_read_observation_with_specific_recovery(self):
        item = PublicationError('', 'REMOTE_OBSERVATION_FAILED',
            context={'error_class': 'TimeoutExpired'}, phase='remote_observation',
            detail_code='REMOTE_OBSERVATION_TIMEOUT').diagnostic()
        result = recovery_guidance({'status': 'BLOCKED', 'diagnostics': [item]})
        self.assertEqual(item['reason_code'], 'REMOTE_OBSERVATION_FAILED')
        self.assertEqual(item['detail_code'], 'REMOTE_OBSERVATION_TIMEOUT')
        self.assertEqual(item['error_class'], 'TimeoutExpired')
        self.assertEqual(item['category'], 'TIMEOUT')
        self.assertTrue(result['retry_read_only'])
        self.assertFalse(result['authorized'])
        self.assertFalse(result['executed'])

    def test_merge_confirmation_and_merged_are_separate(self):
        awaiting = recovery_guidance({"status": "PLANNED",
                                     "next_step": "NATIVE_MERGE_CONFIRMATION"})
        merged = recovery_guidance({"status": "COMPLETE",
                                   "next_step": "POST_MERGE_RECONCILIATION"})
        self.assertTrue(awaiting["requires_human"])
        self.assertEqual(merged["state"], "ALREADY_MERGED")
        self.assertFalse(merged["requires_human"])


if __name__ == "__main__":
    unittest.main()
