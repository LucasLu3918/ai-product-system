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
            "cases": [
                {
                    "id": "refund-retry",
                    "query": "refund retry inventory compensation RefundService",
                    "relevant_paths": [
                        "orders/refund_service.py",
                        "tests/test_refund_service.py",
                    ],
                    "relevant_history_terms": ["fix refund retry inventory compensation"],
                    "baseline_context_files": ["intelligence:topics/refund.md"],
                },
                {
                    "id": "auth-token-expiry",
                    "query": "auth token expiry validation TokenValidator",
                    "relevant_paths": [
                        "auth/token_validator.py",
                        "tests/test_token_validator.py",
                    ],
                    "relevant_history_terms": ["harden auth token expiry validation"],
                    "baseline_context_files": ["intelligence:topics/auth.md"],
                },
                {
                    "id": "refund-status-migration",
                    "query": "refund status migration repository RefundRepository",
                    "relevant_paths": [
                        "billing/refund_repository.py",
                        "billing/migrations/004_add_refund_status.sql",
                        "tests/test_refund_repository.py",
                    ],
                    "relevant_history_terms": ["add refund status migration"],
                    "baseline_context_files": ["intelligence:topics/billing.md"],
                },
            ],
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
        require(aggregate.get("cases") == 3 and aggregate.get("failed") == 0, "all fixture cases must pass")
        require(float(aggregate.get("macro_recall_at_k") or 0) >= 0.66, "macro recall below contract")
        require(float(aggregate.get("macro_precision_at_k") or 0) >= 0.40, "macro precision below contract")
        require(float(aggregate.get("macro_mrr") or 0) >= 0.50, "macro MRR below contract")
        require(float(aggregate.get("token_reduction_ratio") or 0) > 0.50, "bounded retrieval should use materially fewer fixture tokens")

        for case in report.get("cases") or []:
            require(case.get("status") == "PASS", f"case failed: {case.get('id')}")
            baseline = case.get("baseline") or {}
            retrieval = case.get("retrieval") or {}
            metrics = retrieval.get("metrics") or {}
            require(baseline.get("reference_recall") == 1.0, "baseline fixture must retain path-reference signal")
            require(baseline.get("direct_source_recall") == 0.0, "static topic context must not be misrepresented as direct source evidence")
            require(float(metrics.get("recall_at_k") or 0) >= 0.66, "retrieval direct-source recall too low")
            require(int(metrics.get("estimated_tokens") or 0) <= int(retrieval.get("token_budget") or 0), "token budget not enforced")
            require(retrieval.get("semantic_status") == "NOT_CONFIGURED", "evaluation must remain truthful without semantic provider")
            require("latency_ms_observed" in retrieval, "latency observation missing")

        decision = report.get("decision") or {}
        require(decision.get("automatic_provider_enablement") is False, "evaluation must not enable providers")
        require(decision.get("automatic_rank_weight_change") is False, "evaluation must not mutate ranking")
        require(decision.get("automatic_architecture_change") is False, "evaluation must not select architecture automatically")
        require(decision.get("human_review_required_for_next_optimization") is True, "next optimization must require Human review")
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
