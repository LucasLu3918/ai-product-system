#!/usr/bin/env python3
"""Exercise safe telemetry recording, projection, replay, and OTLP export."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from telemetry_export import _endpoint_allowed, export
from telemetry_projection import build_projection
from telemetry_record import record


class Receiver(BaseHTTPRequestHandler):
    response_code = 200
    redirect_to: str | None = None
    requests: ClassVar[list[dict]] = []

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        self.__class__.requests.append({"path": self.path, "body": json.loads(body), "authorization": self.headers.get("Authorization")})
        self.send_response(self.response_code)
        if self.response_code in {301, 302, 307, 308} and self.redirect_to:
            self.send_header("Location", self.redirect_to)
        self.end_headers()
        self.wfile.write(b"ignored receiver response")

    def log_message(self, fmt, *args):
        return


def marker(root: Path, run_id: str, kind: str, action: str, operation_id: str, name: str, **extra):
    args = SimpleNamespace(
        project=str(root), run_id=run_id, kind=kind, action=action,
        operation_id=operation_id, parent_operation_id=extra.pop("parent_operation_id", None),
        related_operation_id=extra.pop("related_operation_id", None), name=name,
        provider=extra.pop("provider", None), model=extra.pop("model", None),
        input_tokens=extra.pop("input_tokens", None), output_tokens=extra.pop("output_tokens", None),
        outcome=extra.pop("outcome", "OK"),
    )
    assert not extra, f"unexpected test input keys: {sorted(extra)}"
    return record(args)


def make_run(root: Path, run_id: str) -> Path:
    run_dir = root / ".ai" / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "CHECKPOINT.yaml").write_text(yaml.safe_dump({"version": 3, "run_id": run_id, "status": "COMPLETE"}), encoding="utf-8")
    return run_dir


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="aips-telemetry-test-") as tmp:
        root = Path(tmp)
        (root / ".ai").mkdir()
        run_id = "run-otel-test"
        run_dir = make_run(root, run_id)

        marker(root, run_id, "phase", "started", "plan-op", "planning")
        marker(root, run_id, "phase", "completed", "plan-op", "planning")
        marker(root, run_id, "phase", "started", "review-op", "review", related_operation_id="plan-op")
        marker(root, run_id, "phase", "completed", "review-op", "review", related_operation_id="plan-op")
        marker(root, run_id, "gate", "started", "gate-op", "integration")
        marker(root, run_id, "gate", "waiting", "gate-op", "integration")
        marker(root, run_id, "gate", "resumed", "gate-op", "integration")
        marker(root, run_id, "gate", "completed", "gate-op", "integration")
        marker(root, run_id, "model", "started", "model-op", "chat", provider="openai", model="test-model", parent_operation_id="plan-op")
        marker(root, run_id, "model", "completed", "model-op", "chat", provider="openai", model="test-model", input_tokens=12, output_tokens=7, parent_operation_id="plan-op")
        marker(root, run_id, "tool", "started", "tool-op", "read_file", parent_operation_id="plan-op")
        marker(root, run_id, "tool", "completed", "tool-op", "read_file", parent_operation_id="plan-op")

        first = build_projection(root, run_id)
        second = build_projection(root, run_id)
        assert first == second, "replay projection must be deterministic"
        assert first["status"] == "COMPLETE", first["issues"]
        spans = first["otlp"]["resourceSpans"][0]["scopeSpans"][0]["spans"]
        by_name = {s["name"]: s for s in spans}
        assert "aips.run" in by_name and by_name["aips.run"]["name"] == "aips.run"
        assert "aips.gate.integration.wait" in by_name
        review_span = by_name["aips.phase.review"]
        assert review_span.get("links"), "independent review must correlate through a SpanLink"
        model_attrs = {x["key"]: x["value"] for x in by_name["chat test-model"]["attributes"]}
        assert model_attrs["gen_ai.usage.input_tokens"]["intValue"] == "12"
        assert model_attrs["gen_ai.usage.output_tokens"]["intValue"] == "7"
        payload_text = json.dumps(first["otlp"])
        for forbidden in ("prompt", "private reasoning", "tool arguments", "AIPS_OTLP_AUTHORIZATION"):
            assert forbidden not in payload_text

        events_path = run_dir / "EVENTS.jsonl"
        existing = events_path.read_text(encoding="utf-8")
        rejected = SimpleNamespace(project=str(root), run_id=run_id, kind="model", action="completed", operation_id="bad-op", parent_operation_id=None, related_operation_id=None, name="chat", provider="openai", model="Bearer-secret-value", input_tokens=1, output_tokens=1, outcome="OK")
        try:
            record(rejected)
            raise AssertionError("unsafe model identifier must reject")
        except ValueError:
            pass
        assert events_path.read_text(encoding="utf-8") == existing, "rejected data must not be persisted"

        with events_path.open("a", encoding="utf-8") as out:
            out.write(json.dumps({"sequence": 100, "timestamp": "2026-09-26T00:00:00Z", "event": "aips.telemetry.phase.started", "status": "INFO", "telemetry": {"operation_id": "bad-content", "name": "planning", "prompt": "must-not-leak"}}) + "\n")
        invalid = build_projection(root, run_id)
        assert invalid["status"] == "DEGRADED"
        assert "must-not-leak" not in json.dumps(invalid["otlp"])

        assert _endpoint_allowed("https://telemetry.example/v1/traces")
        assert _endpoint_allowed("http://127.0.0.1:4318")
        assert not _endpoint_allowed("http://telemetry.example")
        assert not _endpoint_allowed("https://user:secret" + chr(64) + "telemetry.example")
        assert not _endpoint_allowed("https://telemetry.example?token=secret")

        Receiver.requests = []
        Receiver.response_code = 200
        server = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        config = root / "telemetry.yaml"
        config.write_text(yaml.safe_dump({
            "version": 1, "enabled": True,
            "endpoint": f"http://127.0.0.1:{server.server_port}",
            "authorization_env": "AIPS_OTLP_AUTHORIZATION",
            "timeout_seconds": 1,
            "max_payload_bytes": 1048576,
        }), encoding="utf-8")
        os.environ["AIPS_OTLP_AUTHORIZATION"] = "Bearer local-test"
        args = SimpleNamespace(project=str(root), run_id=run_id, config=str(config), send=True, output=None)
        try:
            result, code = export(args)
            assert code == 0 and result["export_status"] == "TELEMETRY_DEGRADED", result
            # The deliberately injected invalid event makes the run degraded, but a valid OTLP request is still delivered.
            assert len(Receiver.requests) == 1
            assert Receiver.requests[0]["path"] == "/v1/traces"
            assert Receiver.requests[0]["authorization"] == "Bearer local-test"
            assert "must-not-leak" not in json.dumps(Receiver.requests[0]["body"])

            Receiver.response_code = 503
            result, code = export(args)
            assert code == 0 and result["export_status"] == "TELEMETRY_DEGRADED"
            assert "local-test" not in json.dumps(result)

            before_redirect = len(Receiver.requests)
            Receiver.response_code = 302
            Receiver.redirect_to = "https://example.invalid/collect"
            result, code = export(args)
            assert code == 0 and result["export_status"] == "TELEMETRY_DEGRADED"
            assert len(Receiver.requests) == before_redirect + 1, "exporter must not follow redirects with credential-bearing requests"
        finally:
            os.environ.pop("AIPS_OTLP_AUTHORIZATION", None)
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    print("telemetry-export lifecycle: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
