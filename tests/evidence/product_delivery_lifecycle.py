#!/usr/bin/env python3
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import yaml

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "product_delivery_evidence.py"
READINESS = ROOT / "scripts" / "check_release_readiness.py"

APP = '''#!/usr/bin/env python3
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = int(os.environ["PORT"])
VERSION = os.environ.get("APP_VERSION", "unknown")
LOG_PATH = Path(os.environ["LOG_PATH"])
UNHEALTHY = os.environ.get("FORCE_UNHEALTHY") == "1"

class Handler(BaseHTTPRequestHandler):
    def emit(self, status, payload):
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"path": self.path, "status": status, "version": VERSION}) + "\\n")
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self.emit(503 if UNHEALTHY else 200, {"status": "unhealthy" if UNHEALTHY else "ok", "version": VERSION})
        elif self.path == "/smoke":
            self.emit(200, {"smoke": "pass", "version": VERSION})
        elif self.path == "/version":
            self.emit(200, {"version": VERSION})
        else:
            self.emit(404, {"error": "not_found"})

    def log_message(self, format, *args):
        return

ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
'''


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request(port: int, route: str) -> tuple[int, dict]:
    try:
        with urlopen(f"http://127.0.0.1:{port}{route}", timeout=2) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def start_service(script: Path, log_path: Path, version: str, unhealthy: bool = False) -> tuple[subprocess.Popen, int]:
    port = free_port()
    env = dict(os.environ)
    env.update({"PORT": str(port), "APP_VERSION": version, "LOG_PATH": str(log_path)})
    if unhealthy:
        env["FORCE_UNHEALTHY"] = "1"
    process = subprocess.Popen(
        [sys.executable, str(script)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(f"service exited early: {process.stderr.read() if process.stderr else ''}")
        try:
            request(port, "/health")
            return process, port
        except (URLError, ConnectionError, TimeoutError):
            time.sleep(0.05)
    process.terminate()
    raise AssertionError("service did not become reachable")


def stop_service(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


def verify_service(port: int, version: str, expect_healthy: bool = True) -> dict:
    health_code, health = request(port, "/health")
    smoke_code, smoke = request(port, "/smoke")
    version_code, version_doc = request(port, "/version")
    if expect_healthy:
        require(health_code == 200 and health.get("status") == "ok", "health check must PASS")
    else:
        require(health_code == 503 and health.get("status") == "unhealthy", "failure injection must make health fail")
    require(smoke_code == 200 and smoke.get("smoke") == "pass", "smoke endpoint must be reachable")
    require(version_code == 200 and version_doc.get("version") == version, "deployed version must match exact RC")
    return {"health": health, "smoke": smoke, "version": version_doc}


def load_validator():
    spec = importlib.util.spec_from_file_location("aips_product_delivery_evidence", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load product_delivery_evidence.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def event(name: str) -> dict:
    return {"name": name, "at": datetime.now(timezone.utc).isoformat()}


def main() -> int:
    module = load_validator()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "workspace" / "apps" / "api" / "app.py"
        source.parent.mkdir(parents=True)
        source.write_text(APP, encoding="utf-8")
        source_revision = sha256(source)
        candidate_hash = source_revision
        version = "rc-028.1"
        events: list[dict] = [event("planning_complete")]

        product_path = root / "PRODUCT.yaml"
        product = {
            "version": 1,
            "status": "active",
            "product": {"name": "scenario-028-fixture", "version": version},
            "workspace": {"strategy": "monorepo", "root": "."},
            "deployment_units": [{"id": "api", "source": "workspace/apps/api", "deployable": True}],
            "environments": {
                "local": {"required": True, "entry_command": "python app.py"},
                "staging": {"required": True},
                "production": {"requested": True, "required": True},
            },
            "delivery": {
                "status": "implementing",
                "production_enablement_requested": True,
                "release_readiness": "RELEASE_READINESS.yaml",
                "rollback": "restore exact verified RC",
                "runbook": "RUNBOOK.md",
            },
            "observability": {"requirements": {"structured_logs": "required", "health_check": "required"}},
        }
        write_yaml(product_path, product)
        (root / "RUNBOOK.md").write_text("# Runbook\nDeploy exact RC, verify health/smoke/logs, rollback on failure.\n", encoding="utf-8")

        # LOCAL_COMPLETE: run the implemented source and verify real behavior before creating the RC artifact.
        local_log = root / "local.log"
        proc, port = start_service(source, local_log, version)
        try:
            local_result = verify_service(port, version)
        finally:
            stop_service(proc)
        require(local_log.exists() and local_log.stat().st_size > 0, "local structured logs required")
        (root / "local-evidence.json").write_text(json.dumps(local_result, indent=2), encoding="utf-8")
        events.append(event("local_verified"))

        artifact = root / "release" / "app.py"
        artifact.parent.mkdir(parents=True)
        shutil.copyfile(source, artifact)
        require(sha256(artifact) == candidate_hash, "RC artifact must bind verified local source bytes")
        events.append(event("release_candidate_created"))

        # Staging must deploy the exact immutable RC bytes and pass verification.
        staging_app = root / "staging" / "app.py"
        staging_app.parent.mkdir()
        shutil.copyfile(artifact, staging_app)
        require(sha256(staging_app) == candidate_hash, "staging candidate drift")
        staging_log = root / "staging.log"
        proc, port = start_service(staging_app, staging_log, version)
        try:
            staging_result = verify_service(port, version)
        finally:
            stop_service(proc)
        require(staging_log.exists() and staging_log.stat().st_size > 0, "staging structured logs required")
        (root / "staging-evidence.json").write_text(json.dumps(staging_result, indent=2), encoding="utf-8")
        events.append(event("staging_verified"))

        readiness_path = root / "RELEASE_READINESS.yaml"
        readiness = {
            "version": 1,
            "status": "READY",
            "release": {"version": version, "candidate": candidate_hash, "target_environment": "production"},
            "staging": {"status": "PASS", "evidence": "staging-evidence.json", "comparable": True},
            "smoke": {"status": "PASS", "evidence": "staging-evidence.json"},
            "security": {
                "effective_sal": 2,
                "deterministic_checks": "pass",
                "independent_review": "pass",
                "unresolved_critical": 0,
                "unresolved_high": 0,
            },
            "observability": {"structured_logs": "PASS", "health_check": "PASS"},
            "recovery": {"runbook": "RUNBOOK.md", "rollback": "restore exact verified RC"},
            "blockers": [],
            "evidence": ["local-evidence.json", "staging-evidence.json", "RUNBOOK.md"],
        }
        write_yaml(readiness_path, readiness)
        checked = subprocess.run(
            [sys.executable, str(READINESS), str(readiness_path)], capture_output=True, text=True, timeout=10
        )
        require(checked.returncode == 0, f"Release Readiness must PASS: {checked.stdout} {checked.stderr}")
        require(json.loads(checked.stdout).get("status") == "pass", "readiness helper did not report pass")
        events.append(event("release_readiness_ready"))

        approval_path = root / "PROMOTION_APPROVAL.yaml"
        approval = {
            "version": 1,
            "status": "APPROVED",
            "scope": "product-production-promotion",
            "candidate_sha256": candidate_hash,
            "target_environment": "production",
            "actor": "scenario-fixture-explicit-human-authority",
        }
        write_yaml(approval_path, approval)
        events.append(event("promotion_approved"))

        # Production promotion occurs only after READY + explicit exact-candidate approval.
        require(readiness["status"] == "READY", "production must not deploy without READY")
        require(approval["status"] == "APPROVED" and approval["candidate_sha256"] == candidate_hash, "production approval missing/stale")
        production_app = root / "production" / "app.py"
        production_app.parent.mkdir()
        shutil.copyfile(artifact, production_app)
        require(sha256(production_app) == candidate_hash, "production candidate drift")
        events.append(event("production_deployed"))

        production_log = root / "production.log"
        proc, port = start_service(production_app, production_log, version)
        try:
            production_result = verify_service(port, version)
        finally:
            stop_service(proc)
        require(production_log.exists() and production_log.stat().st_size > 0, "production structured logs required")
        require('"path": "/health"' in production_log.read_text(encoding="utf-8"), "production health log evidence missing")
        (root / "production-evidence.json").write_text(json.dumps(production_result, indent=2), encoding="utf-8")
        events.append(event("production_verified"))

        # Exercise controlled recovery: operational health failure, then restore the same verified RC bytes.
        failure_log = root / "production-failure.log"
        proc, port = start_service(production_app, failure_log, version, unhealthy=True)
        try:
            failed_result = verify_service(port, version, expect_healthy=False)
        finally:
            stop_service(proc)
        (root / "recovery-trigger.json").write_text(json.dumps(failed_result, indent=2), encoding="utf-8")
        events.append(event("recovery_triggered"))

        shutil.copyfile(artifact, production_app)
        require(sha256(production_app) == candidate_hash, "rollback must restore exact verified RC")
        recovery_log = root / "recovery.log"
        proc, port = start_service(production_app, recovery_log, version)
        try:
            recovered_result = verify_service(port, version)
        finally:
            stop_service(proc)
        (root / "recovery-evidence.json").write_text(json.dumps(recovered_result, indent=2), encoding="utf-8")
        events.append(event("recovery_completed"))

        product["delivery"]["status"] = "PRODUCTION_VERIFIED"
        product["delivery"]["local_complete_evidence"] = ["local-evidence.json"]
        write_yaml(product_path, product)

        evidence_path = root / "PRODUCT_DELIVERY_EVIDENCE.yaml"
        evidence = {
            "version": 1,
            "mode": "representative_isolated_lifecycle",
            "status": "PASS",
            "external_production_claimed": False,
            "product": {"product_yaml": "PRODUCT.yaml", "delivery_state": "PRODUCTION_VERIFIED"},
            "release_candidate": {"id": version, "source_revision": source_revision, "artifact": "release/app.py", "sha256": candidate_hash},
            "environments": {
                "local": {"status": "PASS", "isolated": True, "candidate_sha256": candidate_hash, "evidence": "local-evidence.json"},
                "staging": {"status": "PASS", "isolated": True, "candidate_sha256": candidate_hash, "evidence": "staging-evidence.json"},
                "production": {"status": "PASS", "isolated": True, "candidate_sha256": candidate_hash, "evidence": "production-evidence.json"},
            },
            "gates": {
                "local_complete": {"status": "PASS", "evidence": "local-evidence.json"},
                "release_readiness": {"status": "READY", "evidence": "RELEASE_READINESS.yaml"},
                "promotion_approval": {"status": "APPROVED", "candidate_sha256": candidate_hash, "target_environment": "production", "evidence": "PROMOTION_APPROVAL.yaml"},
            },
            "post_deploy": {"health": "PASS", "smoke": "PASS", "structured_logs_observed": True, "evidence": "production-evidence.json"},
            "recovery": {"exercised": True, "trigger": "production_health_failure", "restored_candidate_sha256": candidate_hash, "restored_health": "PASS", "evidence": "recovery-evidence.json"},
            "events": events,
            "notes": ["This CI fixture proves lifecycle gates in isolated representative environments; it does not claim deployment to an external customer production platform."],
        }
        write_yaml(evidence_path, evidence)

        result = module.validate(evidence_path)
        require(result["status"] == "PASS", f"valid end-to-end evidence must PASS: {result}")
        require(result["external_production_inferred"] is False, "validator must never infer external production")
        require(result["production_gate_inferred_from_readiness_alone"] is False, "READY must not imply promotion approval")

        cli = subprocess.run(
            [sys.executable, str(VALIDATOR), str(evidence_path), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        require(cli.returncode == 0 and json.loads(cli.stdout).get("status") == "PASS", "validator CLI must PASS valid lifecycle")

        # Fail-closed negative cases protect the gates that make Scenario 028 meaningful.
        bad_approval = copy.deepcopy(evidence)
        bad_approval["gates"]["promotion_approval"]["status"] = "MISSING"
        write_yaml(root / "bad-approval.yaml", bad_approval)
        require(module.validate(root / "bad-approval.yaml")["status"] == "FAIL", "missing promotion approval must fail")

        drift = copy.deepcopy(evidence)
        drift["environments"]["production"]["candidate_sha256"] = "different-candidate"
        write_yaml(root / "candidate-drift.yaml", drift)
        require(module.validate(root / "candidate-drift.yaml")["status"] == "FAIL", "candidate drift must fail")

        no_recovery = copy.deepcopy(evidence)
        no_recovery["recovery"]["exercised"] = False
        write_yaml(root / "no-recovery.yaml", no_recovery)
        require(module.validate(root / "no-recovery.yaml")["status"] == "FAIL", "unexercised recovery must fail")

        wrong_order = copy.deepcopy(evidence)
        approval_index = next(i for i, item in enumerate(wrong_order["events"]) if item["name"] == "promotion_approved")
        deploy_index = next(i for i, item in enumerate(wrong_order["events"]) if item["name"] == "production_deployed")
        wrong_order["events"][approval_index], wrong_order["events"][deploy_index] = wrong_order["events"][deploy_index], wrong_order["events"][approval_index]
        write_yaml(root / "wrong-order.yaml", wrong_order)
        require(module.validate(root / "wrong-order.yaml")["status"] == "FAIL", "production-before-approval ordering must fail")

        false_external_claim = copy.deepcopy(evidence)
        false_external_claim["external_production_claimed"] = True
        write_yaml(root / "false-external-claim.yaml", false_external_claim)
        require(module.validate(root / "false-external-claim.yaml")["status"] == "FAIL", "fixture must not claim external production")

    print("PRODUCT DELIVERY LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
