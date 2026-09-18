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


def run(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, env=env, capture_output=True, text=True)


def json_run(args: list[str], env: dict[str, str]) -> dict:
    result = run(args, env)
    require(result.returncode == 0, f"command failed: {args}: {result.stdout} {result.stderr}")
    return json.loads(result.stdout)


def git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, capture_output=True, text=True)


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
        git(project, "config", "user.name", "AIPS Evidence")

        files = {
            "orders/refund_service.py": (
                "class RefundService:\n"
                "    def refund_order(self, order_id, inventory):\n"
                "        inventory.restore(order_id)\n"
                "        return 'refunded'\n"
            ),
            "orders/order_repository.py": (
                "class OrderRepository:\n"
                "    def mark_refunded(self, order_id):\n"
                "        return order_id\n"
            ),
            "tests/test_refund_service.py": (
                "def test_refund_retry_restores_inventory_once():\n"
                "    assert 'inventory compensation'\n"
            ),
            "admin/dashboard.py": "def render_dashboard():\n    return 'unrelated admin metrics'\n",
            "docs/architecture.md": "# Orders\nRefunds restore inventory and must be idempotent.\n",
            "config/credentials.json": '{"token":"super-secret-fixture"}\n',
        }
        for rel, body in files.items():
            path = project / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        git(project, "add", "-A")
        git(project, "commit", "-qm", "add refund flow")

        refund = project / "orders/refund_service.py"
        refund.write_text(
            "class RefundService:\n"
            "    def refund_order(self, order_id, inventory):\n"
            "        # retry guard prevents duplicate inventory compensation\n"
            "        inventory.restore_once(order_id)\n"
            "        return 'refunded'\n",
            encoding="utf-8",
        )
        git(project, "add", "orders/refund_service.py")
        git(project, "commit", "-qm", "fix refund retry inventory compensation")

        env = dict(os.environ)
        env["HOME"] = str(home)
        env["XDG_CONFIG_HOME"] = str(config)
        env["XDG_CACHE_HOME"] = str(cache)

        boot = json_run([
            sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json",
        ], env)
        store = Path(boot["store"])

        index = json_run([
            sys.executable, str(PI), "index", "--project", str(project), "--format", "json",
        ], env)
        require(index.get("status") == "READY", "retrieval index must become READY")
        require(index.get("coverage", {}).get("files", 0) >= 5, "expected repository files to be indexed")
        require((store / "RETRIEVAL_INDEX.yaml").is_file(), "retrieval metadata must live with Project Intelligence")

        meta = yaml.safe_load((store / "RETRIEVAL_INDEX.yaml").read_text(encoding="utf-8")) or {}
        require((meta.get("cache") or {}).get("canonical") is False, "retrieval DB must be rebuildable cache, not canonical truth")
        semantic = ((meta.get("providers") or {}).get("semantic") or {})
        require(semantic.get("status") == "NOT_CONFIGURED", "semantic provider absence must be truthful")
        require(semantic.get("required") is False, "semantic provider must remain optional")

        query = json_run([
            sys.executable, str(PI), "retrieve",
            "--project", str(project),
            "--prompt", "modify refund retry inventory compensation",
            "--token-budget", "1200",
            "--limit", "8",
            "--format", "json",
        ], env)
        require(query.get("status") == "READY", "retrieval query must succeed")
        require(query.get("estimated_tokens", 99999) <= 1200, "retrieval must honor token budget")
        structural = query.get("structural") or {}
        ranking = query.get("ranking") or {}
        require(structural.get("status") == "READY", "structural retrieval must be READY by default")
        require(structural.get("default_enabled") is True, "structural retrieval must be adopted as default")
        require(structural.get("enabled") is True, "default retrieval must enable structural lane")
        require(structural.get("selection") == "default", "default structural selection must be explicit in evidence")
        require("structural_reference_graph" in (ranking.get("lanes") or []),
                "default retrieval ranking must include structural relation graph")
        results = query.get("results") or []
        require(results, "retrieval must return evidence")

        code_results = [r for r in results if r.get("path") == "orders/refund_service.py"]
        test_results = [r for r in results if r.get("path") == "tests/test_refund_service.py"]
        history_results = [r for r in results if r.get("type") == "history"]
        require(code_results, "target refund implementation must be retrieved")
        require(test_results, "related refund test must be retrieved")
        require(any("fix refund retry inventory compensation" in str(r.get("subject")) for r in history_results),
                "relevant prior commit must be retrieved")
        require(not any(r.get("path") == "admin/dashboard.py" for r in results),
                "unrelated admin module must be excluded from bounded result set")
        require(not any("super-secret-fixture" in str(r.get("snippet")) for r in results),
                "secret-like credential file must never enter retrieval output")
        for result in results:
            require(bool(result.get("content_hash")), "every retrieval result must carry content provenance")
            revision = result.get("revision") or {}
            require(bool(revision.get("git_head")), "every retrieval result must bind git revision")

        no_structural = json_run([
            sys.executable, str(PI), "retrieve",
            "--project", str(project),
            "--prompt", "modify refund retry inventory compensation RefundService",
            "--token-budget", "1200",
            "--limit", "8",
            "--no-structural",
            "--format", "json",
        ], env)
        no_structural_doc = no_structural.get("structural") or {}
        no_structural_ranking = no_structural.get("ranking") or {}
        require(no_structural_doc.get("enabled") is False, "--no-structural must disable structural expansion")
        require(no_structural_doc.get("selection") == "explicit", "opt-out must be recorded as explicit selection")
        require("structural_reference_graph" not in (no_structural_ranking.get("lanes") or []),
                "opt-out ranking must exclude structural lane")

        # Dirty current workspace content must supersede the indexed committed revision.
        refund.write_text(
            refund.read_text(encoding="utf-8")
            + "\n# current workspace retry_guard_v2 evidence\n",
            encoding="utf-8",
        )
        dirty_query = json_run([
            sys.executable, str(PI), "retrieve",
            "--project", str(project),
            "--prompt", "refund retry_guard_v2",
            "--token-budget", "900",
            "--limit", "5",
            "--format", "json",
        ], env)
        dirty_results = dirty_query.get("results") or []
        require(any("retry_guard_v2" in str(r.get("snippet")) for r in dirty_results),
                "dirty workspace content must be incrementally re-indexed before retrieval")
        update = dirty_query.get("index_update") or {}
        require("orders/refund_service.py" in (update.get("changed_paths") or []),
                "incremental index update must identify the changed refund file")

        context = json_run([
            sys.executable, str(PI), "context",
            "--project", str(project),
            "--runtime", "codex",
            "--prompt", "modify refund retry_guard_v2",
            "--format", "json",
        ], env)
        retrieval = (context.get("context") or {}).get("retrieval") or {}
        require(retrieval.get("status") == "READY", "Turn Context must expose Retrieval Intelligence")
        require(retrieval.get("results"), "Turn Context must carry bounded retrieval evidence")
        context_structural = retrieval.get("structural") or {}
        context_ranking = retrieval.get("ranking") or {}
        require(context_structural.get("enabled") is True, "Turn Context must use adopted structural retrieval")
        require(context_structural.get("selection") == "default", "Turn Context structural selection must be default")
        require("structural_reference_graph" in (context_ranking.get("lanes") or []),
                "Turn Context ranking must expose structural relation graph")

    print("retrieval_intelligence_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
