#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
PI = ROOT / "scripts" / "project_intelligence.py"
CORPUS = ROOT / "tests" / "fixtures" / "retrieval_quality_corpus.yaml"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(project: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=project, capture_output=True, text=True)
    require(result.returncode == 0, result.stderr or result.stdout)
    return result.stdout.strip()


def json_run(args: list[str], env: dict[str, str], expected: int = 0) -> dict:
    result = subprocess.run(args, env=env, capture_output=True, text=True)
    require(result.returncode == expected, f"command failed: {args}: {result.stdout} {result.stderr}")
    return json.loads(result.stdout)


def write(project: Path, rel: str, body: str) -> None:
    path = project / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def broad_topic(title: str, references: list[str]) -> str:
    filler = "\n".join(
        f"- broad project architecture note {idx}: shared platform behavior and conventions"
        for idx in range(180)
    )
    refs = "\n".join(f"- evidence pointer: {path}" for path in references)
    return f"# {title}\n{refs}\n{filler}\n"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        project = base / "project"
        home = base / "home"
        config = base / "config"
        cache = base / "cache"
        project.mkdir()
        home.mkdir()

        git(project, "init", "-q")
        git(project, "branch", "-m", "main")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Retrieval Evaluation")

        write(project, "orders/refund_service.py", """class RefundService:
    def refund_order(self, order_id, inventory):
        # refund retry uses inventory compensation once
        inventory.restore_once(order_id)
        return "refunded"
""")
        write(project, "tests/test_refund_service.py", """def test_refund_retry_inventory_compensation_once():
    assert "refund retry inventory compensation"
""")
        write(project, "auth/token_validator.py", """class TokenValidator:
    def validate_expiry(self, token):
        # token expiry validation rejects stale auth tokens
        return token.expires_at > 0
""")
        write(project, "tests/test_token_validator.py", """def test_auth_token_expiry_validation():
    assert "auth token expiry validation"
""")
        write(project, "billing/refund_repository.py", """class RefundRepository:
    def persist_refund_status(self, status):
        return status
""")
        write(project, "billing/migrations/004_add_refund_status.sql", "ALTER TABLE refunds ADD COLUMN refund_status TEXT;\n")
        write(project, "tests/test_refund_repository.py", """def test_refund_status_migration_repository():
    assert "refund status migration repository"
""")
        write(project, "services/receipts/service.go", """package receipts

type ReceiptService struct{}

func (ReceiptService) ReconcileReceipt(receiptID string) string {
    // reconcile receipt retry without duplicating the ledger entry
    return receiptID
}
""")
        write(project, "services/receipts/service_test.go", """package receipts

func TestReconcileReceiptRetry(t *testing.T) {
    _ = "reconcile receipt retry"
}
""")
        write(project, "web/session_refresh.ts", """export class SessionRefreshCoordinator {
  refreshExpiredBrowser(sessionId: string): string {
    return sessionId;
  }
}
""")
        write(project, "web/session_refresh.test.ts", """export function testExpiredBrowserSessionRefresh() {
  return "session refresh expired browser";
}
""")
        write(project, "apps/api/authorization.py", """from shared.security.permission_policy import PermissionPolicy

def authorize_api_request(user, action):
    return PermissionPolicy().authorize(user, action)
""")
        write(project, "shared/security/permission_policy.py", """class PermissionPolicy:
    def authorize(self, user, action):
        return bool(user and action)
""")
        write(project, "tests/api/test_authorization.py", """def test_api_uses_shared_permission_policy():
    assert "api authorization shared permission policy"
""")
        write(project, "accounts/registration_coordinator.py", """class RegistrationCoordinator:
    def enroll(self, account, relay):
        relay.publish_once(account.id, "onboarding.notice")
        return account
""")
        write(project, "messaging/outbox_relay.py", """class OutboxRelay:
    def publish_once(self, key, event_name):
        return (key, event_name)
""")
        write(project, "tests/accounts/test_registration_idempotency.py", """def test_enrollment_event_is_idempotent():
    assert "onboarding notice emitted once"
""")
        write(project, "checkout/coordinator.go", """package checkout

type CheckoutCoordinator struct{}

func (CheckoutCoordinator) PlaceOrder(orderID string, reserve func(string) bool) bool {
    return reserve(orderID)
}
""")
        write(project, "inventory/reservation.go", """package inventory

func ReserveStock(orderID string) bool {
    return orderID != ""
}
""")
        write(project, "checkout/coordinator_test.go", """package checkout

func TestReservationRollback(t *testing.T) {
    _ = "rollback reserved stock"
}
""")
        write(project, "identity/access_epoch.ts", """export class AccessEpoch {
  revokeStaleSessions(subjectId: string): string {
    return subjectId;
  }
}
""")
        write(project, "identity/access_epoch.test.ts", """export function testRevokesStaleSessionsAfterEpochChange() {
  return "revokes stale sessions";
}
""")
        for idx in range(12):
            write(project, f"admin/unrelated_{idx}.py", f"def unrelated_admin_{idx}():\n    return 'dashboard analytics metrics {idx}'\n")

        git(project, "add", "-A")
        git(project, "commit", "-qm", "baseline services")

        refund_path = project / "orders/refund_service.py"
        refund_path.write_text(
            refund_path.read_text(encoding="utf-8")
            + "\n# committed refund retry inventory compensation guard\n",
            encoding="utf-8",
        )
        git(project, "add", "orders/refund_service.py")
        git(project, "commit", "-qm", "fix refund retry inventory compensation")

        auth_path = project / "auth/token_validator.py"
        auth_path.write_text(
            auth_path.read_text(encoding="utf-8")
            + "\n# committed auth token expiry validation guard\n",
            encoding="utf-8",
        )
        git(project, "add", "auth/token_validator.py")
        git(project, "commit", "-qm", "harden auth token expiry validation")

        migration_path = project / "billing/migrations/004_add_refund_status.sql"
        migration_path.write_text(
            migration_path.read_text(encoding="utf-8")
            + "-- committed refund status migration\n",
            encoding="utf-8",
        )
        git(project, "add", "billing/migrations/004_add_refund_status.sql")
        git(project, "commit", "-qm", "add refund status migration")

        history_changes = [
            ("services/receipts/service.go", "// history receipt retry guard\n", "stabilize receipt reconciliation retry"),
            ("web/session_refresh.ts", "// history expired browser session guard\n", "guard expired browser session refresh"),
            ("shared/security/permission_policy.py", "# history centralized policy\n", "centralize api permission policy"),
            ("messaging/outbox_relay.py", "# history idempotent registration event\n", "make registration notification idempotent"),
            ("inventory/reservation.go", "// history checkout rollback linkage\n", "connect checkout coordinator to reservation rollback"),
            ("identity/access_epoch.ts", "// history credential rotation invalidation\n", "invalidate access after credential rotation"),
        ]
        for rel, marker, message in history_changes:
            path = project / rel
            path.write_text(path.read_text(encoding="utf-8") + "\n" + marker, encoding="utf-8")
            git(project, "add", rel)
            git(project, "commit", "-qm", message)

        env = dict(os.environ)
        env["HOME"] = str(home)
        env["XDG_CONFIG_HOME"] = str(config)
        env["XDG_CACHE_HOME"] = str(cache)

        boot = json_run([
            sys.executable, str(PI), "bootstrap",
            "--project", str(project), "--format", "json",
        ], env)
        store = Path(boot["store"])
        topics = store / "topics"
        topics.mkdir(parents=True, exist_ok=True)
        (topics / "refund.md").write_text(
            broad_topic("Refund Architecture", [
                "orders/refund_service.py",
                "tests/test_refund_service.py",
            ]),
            encoding="utf-8",
        )
        (topics / "auth.md").write_text(
            broad_topic("Authentication Architecture", [
                "auth/token_validator.py",
                "tests/test_token_validator.py",
            ]),
            encoding="utf-8",
        )
        (topics / "billing.md").write_text(
            broad_topic("Billing Architecture", [
                "billing/refund_repository.py",
                "billing/migrations/004_add_refund_status.sql",
                "tests/test_refund_repository.py",
            ]),
            encoding="utf-8",
        )
        topic_specs = {
            "receipts.md": ("Receipt Reconciliation", ["services/receipts/service.go", "services/receipts/service_test.go"]),
            "session.md": ("Browser Session Refresh", ["web/session_refresh.ts", "web/session_refresh.test.ts"]),
            "monorepo-auth.md": ("Monorepo Authorization", ["apps/api/authorization.py", "shared/security/permission_policy.py", "tests/api/test_authorization.py"]),
            "registration.md": ("Registration Messaging", ["accounts/registration_coordinator.py", "messaging/outbox_relay.py", "tests/accounts/test_registration_idempotency.py"]),
            "checkout.md": ("Checkout Reservation Flow", ["checkout/coordinator.go", "inventory/reservation.go", "checkout/coordinator_test.go"]),
            "identity.md": ("Identity Session Invalidation", ["identity/access_epoch.ts", "identity/access_epoch.test.ts"]),
        }
        for filename, (title, refs) in topic_specs.items():
            (topics / filename).write_text(broad_topic(title, refs), encoding="utf-8")

        corpus = yaml.safe_load(CORPUS.read_text(encoding="utf-8")) or {}
        require(corpus.get("version") == 1, "retrieval quality corpus version mismatch")
        require(len(corpus.get("cases") or []) == 9, "retrieval quality corpus must contain nine cases")

        suite = {
            "version": 1,
            "name": "fixture-retrieval-quality",
            "defaults": {
                "top_k": 5,
                "result_limit": 8,
                "token_budget": 1200,
                "thresholds": {
                    "recall_at_k_min": 0.66,
                    "precision_at_k_min": 0.40,
                    "mrr_min": 0.50,
                    "history_recall_min": 1.00,
                    "irrelevant_context_rate_max": 0.55,
                    "direct_source_recall_delta_min": 0.60,
                },
            },
            "cases": corpus["cases"],
        }
        # Keep benchmark control data outside indexed product source so the
        # evaluation query cannot retrieve its own expected-answer fixture.
        suite_path = base / "retrieval-evaluation.yaml"
        suite_path.write_text(yaml.safe_dump(suite, sort_keys=False), encoding="utf-8")
        report_path = base / "retrieval-report.json"

        report = json_run([
            sys.executable, str(PI), "evaluate",
            "--project", str(project),
            "--suite", str(suite_path),
            "--output", str(report_path),
            "--format", "json",
        ], env)

        require(report.get("status") == "PASS", f"quality suite must pass: {report}")
        aggregate = report.get("aggregate") or {}
        require(aggregate.get("cases") == 9, "expanded corpus must execute nine cases")
        require(aggregate.get("required_cases") == 6, "expanded corpus must contain six required cases")
        require(aggregate.get("required_failed") == 0, "all required retrieval regression cases must pass")
        require(aggregate.get("diagnostic_cases") == 3, "expanded corpus must contain three diagnostic stress cases")
        require(
            int(aggregate.get("diagnostic_passed") or 0) + int(aggregate.get("diagnostic_gaps") or 0) == 3,
            "diagnostic cases must resolve to pass or explicit gap",
        )
        if int(aggregate.get("diagnostic_gaps") or 0) > 0:
            require(bool(aggregate.get("diagnostic_gaps_by_dimension")), "diagnostic gaps must aggregate dimensions")
        require(float(aggregate.get("macro_recall_at_k") or 0) >= 0.66, "macro recall below contract")
        require(float(aggregate.get("macro_precision_at_k") or 0) >= 0.40, "macro precision below contract")
        require(float(aggregate.get("macro_mrr") or 0) >= 0.50, "macro MRR below contract")
        require(float(aggregate.get("token_reduction_ratio") or 0) > 0.50, "bounded retrieval should use materially fewer fixture tokens")

        for case in report.get("cases") or []:
            enforcement = case.get("enforcement")
            baseline = case.get("baseline") or {}
            retrieval = case.get("retrieval") or {}
            metrics = retrieval.get("metrics") or {}
            require(baseline.get("reference_recall") == 1.0, "baseline fixture must retain path-reference signal")
            require(baseline.get("direct_source_recall") == 0.0, "static topic context must not be misrepresented as direct source evidence")
            require(int(metrics.get("estimated_tokens") or 0) <= int(retrieval.get("token_budget") or 0), "token budget not enforced")
            require(retrieval.get("semantic_status") == "NOT_CONFIGURED", "evaluation must remain truthful without semantic provider")
            require("latency_ms_observed" in retrieval, "latency observation missing")
            if enforcement == "required":
                require(case.get("status") == "PASS", f"required case failed: {case.get('id')}")
                require(float(metrics.get("recall_at_k") or 0) >= 0.66, "required retrieval direct-source recall too low")
            else:
                require(enforcement == "diagnostic", f"unknown case enforcement: {enforcement}")
                require(case.get("dimensions"), "diagnostic case must declare dimensions")

        decision = report.get("decision") or {}
        require(decision.get("automatic_provider_enablement") is False, "evaluation must not enable providers")
        require(decision.get("automatic_rank_weight_change") is False, "evaluation must not mutate ranking")
        require(decision.get("automatic_architecture_change") is False, "evaluation must not select architecture automatically")
        require(decision.get("human_review_required_for_next_optimization") is True, "next optimization must require Human review")
        require(decision.get("diagnostic_gaps_are_evidence_only") is True, "diagnostic gaps must remain evidence-only")
        require(bool(report.get("result_fingerprint")), "evaluation result fingerprint missing")
        scope = report.get("fingerprint_scope") or {}
        require("observed latency" in (scope.get("excludes") or []), "latency must be excluded from deterministic fingerprint")
        require(report_path.is_file(), "requested evaluation report was not written")

        second = json_run([
            sys.executable, str(PI), "evaluate",
            "--project", str(project),
            "--suite", str(suite_path),
            "--format", "json",
        ], env)
        require(
            second.get("result_fingerprint") == report.get("result_fingerprint"),
            "same repository/suite evidence must keep a stable fingerprint across observed latency changes",
        )
        print("retrieval_quality_metrics=" + json.dumps(aggregate, sort_keys=True))

        probe_required = dict(suite["cases"][0])
        probe_required["id"] = "required-probe"
        probe_required["enforcement"] = "required"
        probe_diagnostic = dict(suite["cases"][0])
        probe_diagnostic["id"] = "diagnostic-gap-probe"
        probe_diagnostic["enforcement"] = "diagnostic"
        probe_diagnostic["query"] = "nonexistent semantic relation qzxwvv"
        probe_diagnostic["relevant_history_terms"] = []
        probe_diagnostic["thresholds"] = {
            "recall_at_k_min": 1.0,
            "precision_at_k_min": 1.0,
            "mrr_min": 1.0,
            "history_recall_min": 1.0,
            "irrelevant_context_rate_max": 0.0,
            "direct_source_recall_delta_min": 1.0,
        }
        probe_suite = dict(suite)
        probe_suite["name"] = "diagnostic-enforcement-probe"
        probe_suite["cases"] = [probe_required, probe_diagnostic]
        probe_path = base / "diagnostic-probe.yaml"
        probe_path.write_text(yaml.safe_dump(probe_suite, sort_keys=False), encoding="utf-8")
        probe = json_run([
            sys.executable, str(PI), "evaluate",
            "--project", str(project),
            "--suite", str(probe_path),
            "--format", "json",
        ], env)
        probe_aggregate = probe.get("aggregate") or {}
        require(probe.get("status") == "PASS", "diagnostic-only gap must not fail overall suite")
        require(probe_aggregate.get("required_failed") == 0, "required probe must remain healthy")
        require(probe_aggregate.get("diagnostic_gaps") == 1, "diagnostic failure must be recorded as a gap")
        require("diagnostic-gap-probe" in (probe_aggregate.get("diagnostic_gap_ids") or []), "diagnostic gap id missing")

        invalid = dict(suite)
        invalid["cases"] = [dict(suite["cases"][0]), dict(suite["cases"][0])]
        bad_path = base / "invalid-evaluation.yaml"
        bad_path.write_text(yaml.safe_dump(invalid, sort_keys=False), encoding="utf-8")
        bad = subprocess.run([
            sys.executable, str(PI), "evaluate",
            "--project", str(project),
            "--suite", str(bad_path),
            "--format", "json",
        ], env=env, capture_output=True, text=True)
        require(bad.returncode == 2, "invalid suite must fail validation")
        require("duplicate case id" in bad.stderr, "invalid suite failure must be explicit")

    print("retrieval_quality_evaluation_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
