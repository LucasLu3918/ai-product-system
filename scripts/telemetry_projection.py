#!/usr/bin/env python3
"""Build a deterministic privacy-safe OTLP/HTTP JSON trace projection from one AIPS run."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from aips_identity import project_root, repository_identity
from run_state import load_yaml, run_store

OTEL_GENAI_REVISION = "0c87594975195608dc91b3f702e250a7b240c151"
MAX_EVENTS = 10000
MAX_EVENT_FILE_BYTES = 8 * 1024 * 1024
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")
SAFE_VALUE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,127}$")
SECRET_VALUE = re.compile(r"(?i)(bearer[\s_-]+|gh[pousr]_[A-Za-z0-9]{12,}|sk-[A-Za-z0-9]{16,}|(?:api[_-]?key|secret|token)[=:])")
ALLOWED_TELEMETRY_KEYS = {
    "operation_id", "parent_operation_id", "related_operation_id", "name",
    "provider", "model", "input_tokens", "output_tokens", "status",
}
EVENT_RE = re.compile(r"^aips\.telemetry\.(phase|gate|model|tool)\.(started|waiting|resumed|completed)$")


def _stable_id(value: str, length: int) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def _nanos(value: str) -> int:
    stamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("event timestamp must include a timezone")
    return int(stamp.timestamp() * 1_000_000_000)


def _attribute(key: str, value: Any) -> dict:
    if isinstance(value, bool):
        wrapped = {"boolValue": value}
    elif isinstance(value, int):
        wrapped = {"intValue": str(value)}
    elif isinstance(value, float):
        wrapped = {"doubleValue": value}
    else:
        wrapped = {"stringValue": str(value)}
    return {"key": key, "value": wrapped}


def _span_id(run_id: str, kind: str, op_id: str) -> str:
    return _stable_id(f"aips-span\0{run_id}\0{kind}\0{op_id}", 16)


def _read_event_records(events_path: Path) -> tuple[list[dict], list[str]]:
    if not events_path.exists():
        return [], []
    if events_path.stat().st_size > MAX_EVENT_FILE_BYTES:
        raise ValueError("EVENTS.jsonl exceeds the 8 MiB telemetry projection limit")
    events: list[dict] = []
    issues: list[str] = []
    for line_number, line in enumerate(events_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        if len(events) >= MAX_EVENTS:
            raise ValueError("EVENTS.jsonl exceeds the 10000 event telemetry projection limit")
        try:
            doc = json.loads(line)
        except json.JSONDecodeError:
            issues.append(f"invalid_json_line:{line_number}")
            continue
        if not isinstance(doc, dict):
            issues.append(f"non_object_line:{line_number}")
            continue
        if not EVENT_RE.fullmatch(str(doc.get("event") or "")):
            continue
        attrs = doc.get("telemetry")
        if not isinstance(attrs, dict) or set(attrs) - ALLOWED_TELEMETRY_KEYS:
            issues.append(f"invalid_telemetry_attributes:{line_number}")
            continue
        if not SAFE_ID.fullmatch(str(attrs.get("operation_id") or "")):
            issues.append(f"invalid_operation_id:{line_number}")
            continue
        kind, action = EVENT_RE.fullmatch(str(doc["event"])).groups()
        allowed_actions = {
            "phase": {"started", "completed"},
            "gate": {"started", "waiting", "resumed", "completed"},
            "model": {"started", "completed"},
            "tool": {"started", "completed"},
        }
        if action not in allowed_actions[kind]:
            issues.append(f"invalid_action:{line_number}")
            continue
        name = attrs.get("name")
        allowed_names = {
            "phase": {"planning", "implementation", "review", "validation"},
            "gate": {"requirement", "core_change", "integration", "security", "janitor", "publish"},
            "model": {"chat", "generate_content", "text_completion", "embeddings", "execute_tool"},
        }
        if kind in allowed_names and name not in allowed_names[kind]:
            issues.append(f"invalid_name:{line_number}")
            continue
        if kind == "tool" and (not isinstance(name, str) or not SAFE_VALUE.fullmatch(name)):
            issues.append(f"invalid_name:{line_number}")
            continue
        if kind == "gate" and action == "waiting" and attrs.get("parent_operation_id"):
            issues.append(f"invalid_gate_parent:{line_number}")
            continue
        if action == "completed" and attrs.get("status") not in {"OK", "ERROR"} and kind in {"model", "tool"}:
            issues.append(f"invalid_outcome:{line_number}")
            continue
        if kind != "model" and any(k in attrs for k in ("provider", "model", "input_tokens", "output_tokens")):
            issues.append(f"invalid_model_fields:{line_number}")
            continue
        if kind == "model" and (not SAFE_VALUE.fullmatch(str(attrs.get("provider") or "")) or not SAFE_VALUE.fullmatch(str(attrs.get("model") or ""))):
            issues.append(f"invalid_model_identity:{line_number}")
            continue
        if any(k in attrs and (isinstance(attrs[k], bool) or not isinstance(attrs[k], int) or not 0 <= attrs[k] <= 1_000_000_000) for k in ("input_tokens", "output_tokens")):
            issues.append(f"invalid_token_count:{line_number}")
            continue
        if any(k in attrs and not SAFE_ID.fullmatch(str(attrs[k])) for k in ("parent_operation_id", "related_operation_id")):
            issues.append(f"invalid_correlation_id:{line_number}")
            continue
        timestamp = doc.get("timestamp")
        try:
            _nanos(str(timestamp))
        except (TypeError, ValueError, OverflowError):
            issues.append(f"invalid_timestamp:{line_number}")
            continue
        for key in ("provider", "model"):
            if key in attrs and (not SAFE_VALUE.fullmatch(str(attrs[key])) or SECRET_VALUE.search(str(attrs[key]))):
                issues.append(f"invalid_{key}:{line_number}")
                break
        else:
            events.append(doc)
    return events, issues


def _build_spans(run_id: str, events: list[dict], issues: list[str]) -> list[dict]:
    grouped: dict[tuple[str, str], dict[str, dict]] = {}
    for event in events:
        match = EVENT_RE.fullmatch(event["event"])
        kind, action = match.groups()
        attrs = event["telemetry"]
        op = attrs["operation_id"]
        slot = grouped.setdefault((kind, op), {})
        if action in slot:
            issues.append(f"duplicate_lifecycle_marker:{kind}:{op}:{action}")
            continue
        slot[action] = event

    spans: list[dict] = []
    for (kind, op), pair in sorted(grouped.items()):
        begin = pair.get("started") or pair.get("waiting")
        if kind == "gate":
            end = pair.get("completed") if pair.get("started") else pair.get("resumed")
        else:
            end = pair.get("completed")
        if begin is None or end is None:
            issues.append(f"incomplete_lifecycle:{kind}:{op}")
            continue
        start_ns, end_ns = _nanos(begin["timestamp"]), _nanos(end["timestamp"])
        if end_ns < start_ns:
            issues.append(f"negative_duration:{kind}:{op}")
            continue
        first, last = begin["telemetry"], end["telemetry"]
        if kind == "model" and (first.get("provider") != last.get("provider") or first.get("model") != last.get("model")):
            issues.append(f"model_identity_changed:{op}")
            continue
        name = str(first.get("name") or "unknown")
        span_name = {
            "phase": f"aips.phase.{name}",
            "gate": f"aips.gate.{name}",
            "model": f"{name} {first.get('model', '')}".strip(),
            "tool": f"aips.tool.{name}",
        }[kind]
        span_id = _span_id(run_id, kind, op)
        span_attrs = [
            _attribute("aips.run.id", run_id if SAFE_ID.fullmatch(run_id) else _stable_id(run_id, 32)),
            _attribute("aips.operation.id", op),
            _attribute("aips.operation.kind", kind),
        ]
        if kind == "phase":
            span_attrs.append(_attribute("aips.phase.name", name))
        elif kind == "gate":
            span_attrs.append(_attribute("aips.gate.id", name))
            if begin["event"].endswith(".waiting"):
                span_attrs.append(_attribute("aips.gate.wait", True))
        elif kind == "model":
            # Mapping profile is pinned to the OTel GenAI semantic-convention snapshot above.
            span_attrs.extend([
                _attribute("gen_ai.operation.name", name),
                _attribute("gen_ai.provider.name", first["provider"]),
                _attribute("gen_ai.request.model", first["model"]),
            ])
            if "input_tokens" in last:
                span_attrs.append(_attribute("gen_ai.usage.input_tokens", last["input_tokens"]))
            if "output_tokens" in last:
                span_attrs.append(_attribute("gen_ai.usage.output_tokens", last["output_tokens"]))
        elif kind == "tool":
            span_attrs.append(_attribute("aips.tool.name", name))
        parent = first.get("parent_operation_id")
        related = first.get("related_operation_id")
        span = {
            "traceId": _stable_id(f"aips-trace\0{run_id}", 32),
            "spanId": span_id,
            "name": span_name,
            "kind": 3 if kind == "model" else 1,
            "startTimeUnixNano": str(start_ns),
            "endTimeUnixNano": str(end_ns),
            "attributes": span_attrs,
            "status": {"code": 2 if last.get("status") == "ERROR" else 1},
        }
        if parent:
            span["parentSpanId"] = _span_id(run_id, "phase", parent)
        if related:
            span["links"] = [{"traceId": _stable_id(f"aips-trace\0{run_id}", 32), "spanId": _span_id(run_id, "phase", related)}]
        spans.append(span)

        # A Gate may have a separate waiting/resumed pair. Export it separately
        # from the full gate lifecycle so waiting time remains directly queryable.
        if kind == "gate" and pair.get("waiting") and pair.get("resumed") and pair.get("started"):
            wait_start = _nanos(pair["waiting"]["timestamp"])
            wait_end = _nanos(pair["resumed"]["timestamp"])
            if wait_end >= wait_start:
                wait_op = op + ".wait"
                wait_attrs = [
                    _attribute("aips.run.id", run_id if SAFE_ID.fullmatch(run_id) else _stable_id(run_id, 32)),
                    _attribute("aips.operation.id", op),
                    _attribute("aips.operation.kind", "gate_wait"),
                    _attribute("aips.gate.id", name),
                ]
                spans.append({
                    "traceId": _stable_id(f"aips-trace\0{run_id}", 32),
                    "spanId": _span_id(run_id, "gate_wait", wait_op),
                    "name": f"aips.gate.{name}.wait",
                    "kind": 1,
                    "startTimeUnixNano": str(wait_start),
                    "endTimeUnixNano": str(wait_end),
                    "attributes": wait_attrs,
                    "status": {"code": 1},
                })

    if spans:
        start_ns = min(int(s["startTimeUnixNano"]) for s in spans)
        end_ns = max(int(s["endTimeUnixNano"]) for s in spans)
        root_attrs = [
            _attribute("aips.run.id", run_id if SAFE_ID.fullmatch(run_id) else _stable_id(run_id, 32)),
            _attribute("aips.telemetry.coverage", "observed_lifecycle_only"),
        ]
        root_span_id = _stable_id(f"aips-root\0{run_id}", 16)
        for span in spans:
            span.setdefault("parentSpanId", root_span_id)
        spans.append({
            "traceId": _stable_id(f"aips-trace\0{run_id}", 32),
            "spanId": root_span_id,
            "name": "aips.run",
            "kind": 1,
            "startTimeUnixNano": str(start_ns),
            "endTimeUnixNano": str(end_ns),
            "attributes": root_attrs,
            "status": {"code": 1},
        })
    return spans


def build_projection(project: str | Path, run_id: str) -> dict:
    if not SAFE_ID.fullmatch(run_id):
        raise ValueError("run-id must be a 1-64 character opaque identifier")
    root = project_root(Path(project))
    store, mode = run_store(root, run_id)
    checkpoint = load_yaml(store / "CHECKPOINT.yaml", {})
    if not checkpoint or str(checkpoint.get("run_id")) != run_id:
        raise ValueError("matching CHECKPOINT.yaml is required for telemetry export")
    records, issues = _read_event_records(store / "EVENTS.jsonl")
    spans = _build_spans(run_id, records, issues)
    repo = repository_identity(root)
    version_path = Path(__file__).resolve().parents[1] / "VERSION"
    resource_attrs = [
        _attribute("service.name", "aips"),
        _attribute("service.version", version_path.read_text(encoding="utf-8").strip()),
        _attribute("aips.repository.id", str(repo.get("repository_id") or "unknown")),
        _attribute("aips.workspace.mode", mode),
    ]
    if spans:
        payload = {"resourceSpans": [{
            "resource": {"attributes": resource_attrs},
            "scopeSpans": [{
                "scope": {"name": "aips.telemetry", "version": version_path.read_text(encoding="utf-8").strip()},
                "spans": spans,
            }],
        }]}
    else:
        payload = {"resourceSpans": []}
    return {
        "schema_version": 1,
        "run_id": run_id,
        "source": str(store),
        "event_count": len(records),
        "span_count": len(spans),
        "status": "DEGRADED" if issues else "COMPLETE",
        "issues": sorted(set(issues)),
        "mapping_profile": {"name": "otel-genai-inference-v1", "repository": "open-telemetry/semantic-conventions-genai", "revision": OTEL_GENAI_REVISION},
        "otlp": payload,
    }
