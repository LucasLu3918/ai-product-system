from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import governance_audit


class GovernanceAuditDiagnosticLookupTest(unittest.TestCase):
    def test_lookup_returns_allowlisted_event_and_verified_chain_status(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = Path(temp) / 'audit.jsonl'
            event = governance_audit.append_event(ledger, {
                'event_type': 'PUBLICATION_DIAGNOSTIC',
                'occurred_at': datetime.now(UTC).isoformat(),
                'diagnostic_id': 'd2fd1f72-9781-4a52-b220-d474b7e94b2f',
                'reason_code': 'PUSH_TARGET_BRANCH_MISMATCH',
                'phase': 'push_validation',
                'source': 'AIPS_PUBLICATION',
                'blocking_rule': 'ENGINEERING_BRANCH_BINDING',
                'authorized': False,
                'executed': False,
                'raw_command': 'must never be stored',
            })
            result = governance_audit.find_diagnostic(ledger, event['diagnostic_id'])
            self.assertEqual(result['status'], 'FOUND')
            self.assertEqual(result['integrity']['status'], 'PASS')
            self.assertEqual(result['event']['reason_code'], 'PUSH_TARGET_BRANCH_MISMATCH')
            self.assertNotIn('raw_command', result['event'])

    def test_lookup_reports_not_found_without_exposing_ledger_contents(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = Path(temp) / 'audit.jsonl'
            result = governance_audit.find_diagnostic(ledger, 'd2fd1f72-9781-4a52-b220-d474b7e94b2f')
            self.assertEqual(result['status'], 'NOT_FOUND')
            self.assertIsNone(result['event'])


if __name__ == '__main__':
    unittest.main()
