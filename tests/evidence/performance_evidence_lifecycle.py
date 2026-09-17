#!/usr/bin/env python3
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from urllib.request import urlopen

import yaml


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(project: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=project, capture_output=True, text=True, timeout=5)
    require(result.returncode == 0, result.stderr or result.stdout)
    return result.stdout.strip()


def load_helper(path: Path):
    spec = importlib.util.spec_from_file_location("performance_evidence", path)
    require(spec is not None and spec.loader is not None, "Unable to load performance_evidence.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BenchmarkServer(ThreadingHTTPServer):
    request_queue_size = 64
    daemon_threads = True

    def __init__(self, address, handler):
        super().__init__(address, handler)
        self.phase_delays_ms: dict[str, float] = {}
        self.profile_rows: list[dict[str, float]] = []
        self.profile_lock = threading.Lock()

    def configure(self, delays_ms: dict[str, float]) -> None:
        self.phase_delays_ms = dict(delays_ms)
        with self.profile_lock:
            self.profile_rows.clear()

    def record(self, row: dict[str, float]) -> None:
        with self.profile_lock:
            self.profile_rows.append(row)


class OrdersHandler(BaseHTTPRequestHandler):
    server: BenchmarkServer

    def log_message(self, format: str, *args) -> None:
        return

    def do_GET(self) -> None:
        if self.path != "/orders":
            self.send_response(404)
            self.end_headers()
            return

        row: dict[str, float] = {}
        for component in ("sql_query", "cache_refresh", "serialization"):
            started = time.perf_counter()
            time.sleep(self.server.phase_delays_ms[component] / 1000.0)
            row[component] = (time.perf_counter() - started) * 1000.0

        self.server.record(row)
        body = b'{"orders":[{"id":1,"status":"ready"}]}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def one_request(url: str) -> float:
    started = time.perf_counter()
    with urlopen(url, timeout=10) as response:
        body = response.read()
        require(response.status == 200, f"unexpected HTTP status: {response.status}")
        require(b'"orders"' in body, "orders response payload missing")
    return (time.perf_counter() - started) * 1000.0


def benchmark(url: str, requests: int, concurrency: int) -> list[float]:
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(one_request, url) for _ in range(requests)]
        return [future.result(timeout=15) for future in futures]


def profile_means(rows: list[dict[str, float]]) -> dict[str, float]:
    require(rows, "server-side profile rows missing")
    names = sorted(rows[0])
    return {
        name: sum(row[name] for row in rows) / len(rows)
        for name in names
    }


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    helper_path = root / "scripts" / "performance_evidence.py"
    performance_skill = root / "skills" / "performance" / "performance-profiling" / "SKILL.md"
    sql_skill = root / "skills" / "database" / "sql-performance" / "SKILL.md"
    for required in (helper_path, performance_skill, sql_skill):
        require(required.is_file(), f"required performance artifact missing: {required}")
    helper = load_helper(helper_path)

    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "orders-service"
        project.mkdir()
        artifact = project / "performance-benchmark.json"
        evidence_path = project / "PERFORMANCE_EVIDENCE.yaml"

        conditions = {
            "requests": 12,
            "concurrency": 12,
            "dataset": "orders-fixture-200",
            "environment": "localhost-threaded-http",
            "provider": "python-stdlib-http",
        }
        baseline_delays = {
            "sql_query": 10.0,
            "cache_refresh": 2050.0,
            "serialization": 5.0,
        }
        after_delays = {
            "sql_query": 10.0,
            "cache_refresh": 25.0,
            "serialization": 5.0,
        }

        config_path = project / "service_config.yaml"
        config_path.write_text(
            yaml.safe_dump({"delays_ms": baseline_delays}, sort_keys=False),
            encoding="utf-8",
        )
        git(project, "init", "-q")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Performance Evidence")
        git(project, "config", "commit.gpgsign", "false")
        git(project, "add", ".")
        git(project, "commit", "-qm", "fixture baseline")
        baseline_revision = git(project, "rev-parse", "HEAD")

        loaded_skills: list[str] = []
        performance_text = performance_skill.read_text(encoding="utf-8")
        require("Do not guess the bottleneck" in performance_text, "performance profiling boundary missing")
        loaded_skills.append("performance-profiling")

        server = BenchmarkServer(("127.0.0.1", 0), OrdersHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_address[1]}/orders"

        try:
            server.configure(baseline_delays)
            baseline_samples = benchmark(
                url, conditions["requests"], conditions["concurrency"]
            )
            baseline_profile = profile_means(list(server.profile_rows))
            dominant = max(baseline_profile, key=baseline_profile.get)
            category = "sql" if dominant == "sql_query" else "cache"
            profile = {
                "component_mean_ms": baseline_profile,
                "bottleneck": {"name": dominant, "category": category},
                "method": "server-side phase timing with time.perf_counter",
            }

            routed = helper.route_specialist_skills(profile)
            require(routed == ["performance-profiling"], f"unexpected non-SQL routing: {routed}")
            require("sql-performance" not in loaded_skills, "SQL skill loaded before SQL evidence")

            baseline_p95 = helper.percentile_nearest_rank(baseline_samples, 0.95)
            require(baseline_p95 >= 2000.0, f"baseline p95 unexpectedly below target: {baseline_p95:.3f}ms")

            config_path.write_text(
                yaml.safe_dump({"delays_ms": after_delays}, sort_keys=False),
                encoding="utf-8",
            )
            git(project, "add", "service_config.yaml")
            git(project, "commit", "-qm", "optimize cache refresh path")
            after_revision = git(project, "rev-parse", "HEAD")

            server.configure(after_delays)
            after_samples = benchmark(
                url, conditions["requests"], conditions["concurrency"]
            )
            after_profile = profile_means(list(server.profile_rows))
            after_p95 = helper.percentile_nearest_rank(after_samples, 0.95)
            require(after_p95 < 2000.0, f"optimized p95 did not meet target: {after_p95:.3f}ms")
            require(after_p95 < baseline_p95, "optimization did not improve measured p95")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        sql_profile = {
            "component_mean_ms": {"sql_query": 400.0, "serialization": 5.0},
            "bottleneck": {"name": "sql_query", "category": "sql"},
        }
        sql_routed = helper.route_specialist_skills(sql_profile)
        require(
            sql_routed == ["performance-profiling", "sql-performance"],
            f"SQL evidence must route sql-performance: {sql_routed}",
        )
        sql_text = sql_skill.read_text(encoding="utf-8")
        require(
            "Load only after evidence implicates database/SQL" in sql_text,
            "SQL performance skill evidence boundary missing",
        )

        artifact_payload = {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "conditions": conditions,
            "baseline": {
                "source_revision": baseline_revision,
                "samples_ms": baseline_samples,
                "p95_ms": baseline_p95,
                "profile": profile,
            },
            "after": {
                "source_revision": after_revision,
                "samples_ms": after_samples,
                "p95_ms": after_p95,
                "profile": {
                    "component_mean_ms": after_profile,
                    "method": "server-side phase timing with time.perf_counter",
                },
            },
        }
        artifact.write_text(
            json.dumps(artifact_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        evidence = {
            "version": 1,
            "status": "PASS",
            "target": {
                "endpoint": "/orders",
                "metric": "p95_response_time_ms",
                "threshold_ms": 2000,
            },
            "conditions": conditions,
            "baseline": artifact_payload["baseline"],
            "optimization": {
                "root_cause": dominant,
                "mechanism": "reduce synchronous cache refresh delay on the shared orders path",
                "loaded_skills": loaded_skills,
            },
            "after": artifact_payload["after"],
            "evidence": {
                "benchmark_artifact": artifact.name,
            },
        }
        evidence_path.write_text(yaml.safe_dump(evidence, sort_keys=False), encoding="utf-8")

        checked = helper.validate(evidence, project)
        require(checked["valid"] is True, json.dumps(checked, indent=2))
        require(checked["target_met"] is True, json.dumps(checked, indent=2))
        require(checked["sql_implicated"] is False, json.dumps(checked, indent=2))
        require(
            checked["success_inferred_without_measurement"] is False,
            "validator must never infer success without raw measurements",
        )

        cli_checked = subprocess.run(
            [
                sys.executable,
                str(helper_path),
                str(evidence_path),
                "--project",
                str(project),
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        require(cli_checked.returncode == 0, cli_checked.stdout + cli_checked.stderr)

        no_measurements = yaml.safe_load(yaml.safe_dump(evidence))
        no_measurements["baseline"].pop("samples_ms", None)
        missing = helper.validate(no_measurements, project)
        require(missing["valid"] is False, "PASS without baseline measurements must fail closed")
        require(
            any("baseline.samples_ms" in error for error in missing["errors"]),
            f"missing measurement failure was not explicit: {missing}",
        )

        false_sql = yaml.safe_load(yaml.safe_dump(evidence))
        false_sql["optimization"]["loaded_skills"].append("sql-performance")
        false_sql_result = helper.validate(false_sql, project)
        require(false_sql_result["valid"] is False, "SQL skill without SQL evidence must fail closed")
        require(
            any("must not be loaded" in error for error in false_sql_result["errors"]),
            f"false SQL routing failure was not explicit: {false_sql_result}",
        )

        failed_target = yaml.safe_load(yaml.safe_dump(evidence))
        failed_target["after"]["samples_ms"] = [2100.0] * conditions["requests"]
        failed_target["after"]["p95_ms"] = 2100.0
        target_result = helper.validate(failed_target, project)
        require(target_result["valid"] is False, "PASS above p95 target must fail closed")
        require(
            any("strictly below" in error for error in target_result["errors"]),
            f"target failure was not explicit: {target_result}",
        )

    print("PERFORMANCE EVIDENCE LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
