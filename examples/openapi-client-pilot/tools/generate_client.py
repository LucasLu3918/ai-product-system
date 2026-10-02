#!/usr/bin/env python3
"""Bounded project-local generator for the Widgets reference contract."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

VERSION = "pilot-client-generator 1.0"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--template", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.version:
        print(VERSION)
        return
    if not all((args.spec, args.template, args.output)):
        parser.error("--spec, --template, and --output are required")
    source = args.spec.read_bytes()
    spec = json.loads(source)
    try:
        assert spec["openapi"] == "3.1.0"
        assert spec["paths"]["/widgets"]["post"]["operationId"] == "createWidget"
        assert spec["paths"]["/widgets/{widget_id}"]["get"]["operationId"] == "getWidget"
        assert spec["components"]["securitySchemes"]["bearerAuth"]["scheme"] == "bearer"
        assert spec["components"]["schemas"]["CreateWidget"]["required"] == ["name"]
    except (AssertionError, KeyError, TypeError) as exc:
        raise SystemExit("unsupported pilot contract; review the generator and client semantics") from exc
    template = args.template.read_text(encoding="utf-8")
    result = template.replace("__SPEC_SHA256__", hashlib.sha256(source).hexdigest())
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "client.py").write_text(result, encoding="utf-8")


if __name__ == "__main__":
    main()
