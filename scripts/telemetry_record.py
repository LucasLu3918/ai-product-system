#!/usr/bin/env python3
"""Record a bounded, privacy-safe telemetry lifecycle marker in AIPS run evidence."""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import os
import re
import sys
from pathlib import Path

from aips_identity import project_root
from run_state import run_store

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")
SAFE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,63}$")
SAFE_PROVIDER_MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,127}$")
SECRET_VALUE = re.compile(r"(?i)(bearer[\s_-]+|gh[pousr]_[A-Za-z0-9]{12,}|sk-[A-Za-z0-9]{16,}|(?:api[_-]?key|secret|token)[=:])")
KINDS = {"phase", "gate", "model", "tool"}
ACTIONS = {
    "phase": {"started", "completed"},
    "gate": {"started", "waiting", "resumed", "completed"},
    "model": {"started", "completed"},
    "tool": {"started", "completed"},
}
PHASES = {"planning", "implementation", "review", "validation"}
GATES = {"requirement", "core_change", "integration", "security", "janitor", "publish"}
MODEL_OPERATIONS = {"chat", "generate_content", "text_completion", "embeddings", "execute_tool"}
ALLOWED_ATTRIBUTES = {
    "operation_id", "parent_operation_id", "related_operation_id", "name",
    "provider", "model", "input_tokens", "output_tokens", "status",
}
MAX_EVENT_BYTES = 4096


def _valid_id(value: str | None, label: str, *, required: bool = False) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise ValueError(f"{label} must be a 1-64 character opaque identifier")
    return value


def _append_event(path: Path, event: dict) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        seq = 1
        if path.exists():
            with path.open("rb") as existing:
                for line in existing:
                    if line.strip():
                        seq += 1
        event["sequence"] = seq
        encoded = json.dumps(event, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
        if len(encoded) > MAX_EVENT_BYTES:
            raise ValueError("telemetry event exceeds the bounded event size")
        fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
        try:
            with os.fdopen(fd, "ab", closefd=True) as out:
                out.write(encoded)
                out.flush()
                os.fsync(out.fileno())
        except BaseException:
            try:
                os.close(fd)
            except OSError:
                pass
            raise
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return seq


def record(args: argparse.Namespace) -> dict:
    if not SAFE_ID.fullmatch(args.run_id):
        raise ValueError("run-id must be a 1-64 character opaque identifier")
    root = project_root(Path(args.project))
    store, mode = run_store(root, args.run_id)
    checkpoint = store / "CHECKPOINT.yaml"
    if not checkpoint.is_file():
        raise ValueError("matching CHECKPOINT.yaml is required before recording telemetry")
    kind, action = args.kind, args.action
    if action not in ACTIONS[kind]:
        raise ValueError(f"unsupported action for {kind}")
    name = args.name
    if kind == "phase" and name not in PHASES:
        raise ValueError("phase name is not in the allowlist")
    if kind == "gate" and name not in GATES:
        raise ValueError("gate name is not in the allowlist")
    if kind == "model" and name not in MODEL_OPERATIONS:
        raise ValueError("model operation is not in the pinned mapping profile")
    if kind == "tool" and (not isinstance(name, str) or not SAFE_NAME.fullmatch(name)):
        raise ValueError("tool name must be a bounded identifier")

    attrs: dict = {"operation_id": _valid_id(args.operation_id, "operation_id", required=True), "name": name}
    attrs["parent_operation_id"] = _valid_id(args.parent_operation_id, "parent_operation_id")
    attrs["related_operation_id"] = _valid_id(args.related_operation_id, "related_operation_id")
    if kind == "model" and action in {"started", "completed"}:
        if not SAFE_PROVIDER_MODEL.fullmatch(args.provider or "") or not SAFE_PROVIDER_MODEL.fullmatch(args.model or ""):
            raise ValueError("model events require bounded provider and model identifiers")
        if SECRET_VALUE.search(args.provider) or SECRET_VALUE.search(args.model):
            raise ValueError("secret-like provider/model identifiers are not allowed")
        attrs["provider"] = args.provider
        attrs["model"] = args.model
        if action == "completed":
            for key, value in (("input_tokens", args.input_tokens), ("output_tokens", args.output_tokens)):
                if value is not None and not 0 <= value <= 1_000_000_000:
                    raise ValueError(f"{key} must be an integer from 0 to 1000000000")
                if value is not None:
                    attrs[key] = value
            attrs["status"] = args.outcome
    elif kind == "tool" and action == "completed":
        attrs["status"] = args.outcome
    elif args.input_tokens is not None or args.output_tokens is not None or args.provider or args.model:
        raise ValueError("provider/model/token values are allowed only on model events")

    attrs = {k: v for k, v in attrs.items() if k in ALLOWED_ATTRIBUTES and v is not None}
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    event = {
        "timestamp": now,
        "event": f"aips.telemetry.{kind}.{action}",
        "status": "INFO" if action != "completed" else attrs.get("status", "OK"),
        "artifact": None,
        "evidence": [],
        "telemetry": attrs,
    }
    sequence = _append_event(store / "EVENTS.jsonl", event)
    return {"mode": mode, "run_id": args.run_id, "sequence": sequence, "event": event["event"]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--run-id", required=True)
    p.add_argument("--kind", choices=sorted(KINDS), required=True)
    p.add_argument("--action", required=True)
    p.add_argument("--operation-id", required=True)
    p.add_argument("--parent-operation-id")
    p.add_argument("--related-operation-id", help="Correlation-only relationship, useful for independent review.")
    p.add_argument("--name", required=True)
    p.add_argument("--provider")
    p.add_argument("--model")
    p.add_argument("--input-tokens", type=int)
    p.add_argument("--output-tokens", type=int)
    p.add_argument("--outcome", choices=["OK", "ERROR"], default="OK")
    args = p.parse_args()
    try:
        result = record(args)
    except (OSError, RuntimeError, ValueError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
