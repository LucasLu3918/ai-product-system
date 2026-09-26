#!/usr/bin/env python3
"""Project, replay, or export one run as opt-in OTLP/HTTP JSON traces."""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import sys
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

import yaml
from telemetry_projection import build_projection

MAX_CONFIG_BYTES = 64 * 1024
MAX_PAYLOAD_BYTES = 8 * 1024 * 1024


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _endpoint_allowed(endpoint: str) -> bool:
    parsed = urlsplit(endpoint)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        return False
    if parsed.scheme == "https" and parsed.hostname:
        return True
    if parsed.scheme != "http" or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _load_config(path: Path) -> dict:
    if path.stat().st_size > MAX_CONFIG_BYTES:
        raise ValueError("telemetry config exceeds 64 KiB")
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or set(doc) - {"version", "enabled", "endpoint", "authorization_env", "timeout_seconds", "max_payload_bytes"}:
        raise ValueError("telemetry config has an invalid shape")
    if doc.get("version") != 1 or not isinstance(doc.get("enabled"), bool):
        raise ValueError("telemetry config requires version: 1 and an explicit enabled boolean")
    endpoint = doc.get("endpoint")
    if not isinstance(endpoint, str) or not _endpoint_allowed(endpoint):
        raise ValueError("endpoint must use HTTPS or HTTP loopback")
    timeout = doc.get("timeout_seconds", 3)
    max_bytes = doc.get("max_payload_bytes", MAX_PAYLOAD_BYTES)
    if not isinstance(timeout, (int, float)) or not 0.1 <= timeout <= 10:
        raise ValueError("timeout_seconds must be between 0.1 and 10")
    if not isinstance(max_bytes, int) or not 1024 <= max_bytes <= MAX_PAYLOAD_BYTES:
        raise ValueError("max_payload_bytes must be between 1024 and 8388608")
    env_name = doc.get("authorization_env")
    if env_name is not None and (not isinstance(env_name, str) or not env_name.isidentifier() or not env_name.startswith(("AIPS_OTLP_", "OTEL_EXPORTER_OTLP_"))):
        raise ValueError("authorization_env must name a host environment variable")
    return {**doc, "timeout_seconds": timeout, "max_payload_bytes": max_bytes}


def _traces_url(endpoint: str) -> str:
    endpoint = endpoint.rstrip("/")
    return endpoint if endpoint.endswith("/v1/traces") else endpoint + "/v1/traces"


def export(args) -> dict:
    result = build_projection(args.project, args.run_id)
    raw = json.dumps(result["otlp"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(raw) > MAX_PAYLOAD_BYTES:
        raise ValueError("projected OTLP payload exceeds the 8 MiB limit")
    result_summary = {k: result[k] for k in ("schema_version", "run_id", "event_count", "span_count", "status", "issues", "mapping_profile")}
    if args.output:
        out_path = Path(args.output).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(out_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as out:
            out.write(raw)
        result_summary["output"] = str(out_path)
    if args.send:
        if not args.config:
            raise ValueError("--send requires --config")
        config = _load_config(Path(args.config).expanduser())
        if not config["enabled"]:
            raise ValueError("telemetry export is disabled by config")
        if result["span_count"] == 0:
            result_summary["export_status"] = "TELEMETRY_DEGRADED"
            result_summary["failure_class"] = "NoCompletedSpans"
            return result_summary, 0
        if len(raw) > config["max_payload_bytes"]:
            raise ValueError("projected payload exceeds configured max_payload_bytes")
        headers = {"Content-Type": "application/json"}
        env_name = config.get("authorization_env")
        credential = os.environ.get(env_name, "") if env_name else ""
        if credential:
            if "\r" in credential or "\n" in credential:
                raise ValueError("authorization credential contains invalid header characters")
            headers["Authorization"] = credential
        req = Request(_traces_url(config["endpoint"]), data=raw, headers=headers, method="POST")
        try:
            with build_opener(NoRedirect()).open(req, timeout=config["timeout_seconds"]) as response:
                if not 200 <= response.status < 300:
                    raise OSError(f"OTLP endpoint returned HTTP {response.status}")
                response.read(1024)
        except (HTTPError, HTTPException, OSError, TimeoutError, URLError, ValueError) as exc:
            # Do not emit exception text: endpoints may echo URLs or headers.
            result_summary["export_status"] = "TELEMETRY_DEGRADED"
            result_summary["failure_class"] = type(exc).__name__
            return result_summary, 0
        result_summary["export_status"] = "EXPORTED"
    elif not args.output:
        raise ValueError("choose --output for offline projection or --send for OTLP export")
    if result["status"] == "DEGRADED":
        result_summary["export_status"] = "TELEMETRY_DEGRADED"
    else:
        result_summary.setdefault("export_status", "PROJECTED")
    return result_summary, 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("export", "replay"):
        q = sub.add_parser(name)
        q.add_argument("--project", default=os.getcwd())
        q.add_argument("--run-id", required=True)
        q.add_argument("--config")
        q.add_argument("--send", action="store_true")
        q.add_argument("--output")
    args = p.parse_args()
    try:
        result, code = export(args)
    except (OSError, RuntimeError, ValueError, yaml.YAMLError) as exc:
        print(json.dumps({"export_status": "TELEMETRY_DEGRADED", "failure_class": type(exc).__name__}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
