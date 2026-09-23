#!/usr/bin/env python3
"""AIPS sink-aware Runtime Content Safety Boundary."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

import yaml

try:
    from check_secret_leakage import ASSIGNMENT, PATTERNS, entropy, placeholder, scan_text
except ModuleNotFoundError:  # imported as a repository module
    from scripts.check_secret_leakage import ASSIGNMENT, PATTERNS, entropy, placeholder, scan_text


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/content-safety.yaml"
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+886[- ]?|0)9\d{2}[- ]?\d{3}[- ]?\d{3}(?!\d)")
# Do not treat the numeric prefix of a hexadecimal Git SHA as a payment card.
# A card candidate must be delimited from hexadecimal characters as well as
# decimal digits; real card numbers in prose remain unchanged.
CARD_RE = re.compile(r"(?<![0-9A-Fa-f])(?:\d[ -]?){13,19}(?![0-9A-Fa-f])")
TAIWAN_ID_RE = re.compile(r"(?<![A-Z0-9])[A-Z][12]\d{8}(?![A-Z0-9])", re.I)
INJECTION_RE = re.compile(
    r"(?ix)\b(?:ignore|disregard|override|bypass)\b.{0,80}\b(?:previous|prior|system|developer|instructions?)\b"
    r"|\b(?:reveal| disclose|print|show|upload|exfiltrate)\b.{0,80}\b(?:system prompt|secret|credential|token|password)\b"
    r"|\b(?:execute|run|push|send)\b.{0,80}\b(?:command|repository|secret|credential|data)\b"
)


@dataclass(frozen=True)
class Finding:
    type: str
    detector: str
    location: str
    fingerprint: str
    length: int
    action: str
    confidence: float

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _fingerprint(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]


def _luhn(value: str) -> bool:
    digits = [int(c) for c in value if c.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _taiwan_id(value: str) -> bool:
    value = value.upper()
    if not TAIWAN_ID_RE.fullmatch(value):
        return False
    letters = "ABCDEFGHJKLMNPQRSTUVXYWZIO"
    code = letters.index(value[0]) + 10
    digits = [code // 10, code % 10] + [int(c) for c in value[1:]]
    weights = [1, 9, 8, 7, 6, 5, 4, 3, 2, 1, 1]
    return sum(d * w for d, w in zip(digits, weights)) % 10 == 0


def _policy(config: dict[str, Any], sink: str, kind: str) -> dict[str, Any]:
    sinks = config.get("sinks") or {}
    selected = sinks.get(sink) or sinks.get("default") or {}
    policies = selected.get("policies") or {}
    return policies.get(kind) or policies.get("DEFAULT") or {"action": "ALLOW", "confidence": 0.0}


def _finding(kind: str, detector: str, location: str, value: str, config: dict[str, Any], sink: str) -> Finding:
    rule = _policy(config, sink, kind)
    return Finding(kind, detector, location, _fingerprint(value), len(value), str(rule.get("action", "ALLOW")), float(rule.get("confidence", 1.0)))


def _walk(value: Any, prefix: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{prefix}[{index}]")
    elif isinstance(value, str):
        yield prefix or "<root>", value


def scan_payload(payload: Any, *, sink: str, config: dict[str, Any] | None = None, context: dict[str, Any] | None = None) -> list[Finding]:
    config = config or load_config()
    findings: list[Finding] = []
    for location, text in _walk(payload):
        for item in scan_text(text, location):
            rule = _policy(config, sink, "SECRET")
            findings.append(Finding(
                "SECRET", item["detector"], location, str(item["fingerprint"]), int(item["secret_length"]),
                str(rule.get("action", "ALLOW")), float(rule.get("confidence", 1.0)),
            ))
        for match in EMAIL_RE.finditer(text):
            findings.append(_finding("PII", "email", location, match.group(0), config, sink))
        for match in PHONE_RE.finditer(text):
            findings.append(_finding("PII", "phone", location, match.group(0), config, sink))
        for match in CARD_RE.finditer(text):
            candidate = match.group(0)
            if _luhn(candidate):
                findings.append(_finding("PII", "credit-card-luhn", location, candidate, config, sink))
        for match in TAIWAN_ID_RE.finditer(text):
            if _taiwan_id(match.group(0)):
                findings.append(_finding("PII", "taiwan-id-checksum", location, match.group(0), config, sink))
        for match in INJECTION_RE.finditer(text):
            findings.append(_finding("INJECTION_SIGNAL", "instruction-pattern", location, match.group(0), config, sink))
    trust = (context or {}).get("trust") or (context or {}).get("source", {}).get("trust")
    if trust == "UNTRUSTED":
        findings.append(_finding("UNTRUSTED_CONTENT", "provenance", "context", "UNTRUSTED_CONTENT", config, sink))
    return findings


def _replacement(kind: str) -> str:
    return "[REDACTED]" if kind in {"SECRET", "PII"} else "[UNTRUSTED_CONTENT]"


def _redact_text(text: str, findings: list[Finding], location: str) -> str:
    result = text
    for finding in findings:
        if finding.location != location or finding.type not in {"SECRET", "PII", "UNTRUSTED_CONTENT"}:
            continue
        pattern = PATTERNS_BY_DETECTOR.get(finding.detector)
        if pattern:
            result = pattern.sub(_replacement(finding.type), result)
        elif finding.detector == "generic-secret-assignment":
            result = ASSIGNMENT.sub(lambda match: match.group(0).replace(match.group(2), _replacement(finding.type)), result)
        elif finding.detector == "email":
            result = EMAIL_RE.sub(_replacement(finding.type), result)
        elif finding.detector == "phone":
            result = PHONE_RE.sub(_replacement(finding.type), result)
        elif finding.detector == "credit-card-luhn":
            result = CARD_RE.sub(lambda m: _replacement(finding.type) if _luhn(m.group(0)) else m.group(0), result)
        elif finding.detector == "taiwan-id-checksum":
            result = TAIWAN_ID_RE.sub(lambda m: _replacement(finding.type) if _taiwan_id(m.group(0)) else m.group(0), result)
    return result


PATTERNS_BY_DETECTOR = {name: pattern for name, pattern in PATTERNS}


def _sanitize(payload: Any, findings: list[Finding], prefix: str = "") -> Any:
    if isinstance(payload, dict):
        return {key: _sanitize(value, findings, f"{prefix}.{key}" if prefix else str(key)) for key, value in payload.items()}
    if isinstance(payload, list):
        return [_sanitize(value, findings, f"{prefix}[{index}]") for index, value in enumerate(payload)]
    if isinstance(payload, str):
        return _redact_text(payload, findings, prefix or "<root>")
    return payload


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict) or value.get("version") != 1:
        raise ValueError("content safety config must be version 1 mapping")
    return value


def safe_emit(*, sink: str, payload: Any, context: dict[str, Any] | None = None, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    findings = scan_payload(payload, sink=sink, config=config, context=context)
    actions = {finding.action.upper() for finding in findings}
    if "BLOCK" in actions:
        decision = "BLOCK"
        safe_payload = None
    elif "REDACT" in actions:
        decision = "REDACT"
        safe_payload = _sanitize(payload, findings)
    elif "REVIEW" in actions:
        decision = "REVIEW"
        safe_payload = _sanitize(payload, findings)
    else:
        decision = "ALLOW"
        safe_payload = payload
    return {"decision": decision, "safe_payload": safe_payload, "findings": [item.as_dict() for item in findings], "sink": sink}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scan", choices=["scan"])
    parser.add_argument("--sink", required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--text")
    parser.add_argument("--trust", choices=["TRUSTED", "UNTRUSTED"], default="TRUSTED")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8")) if args.input else (args.text or "")
    result = safe_emit(sink=args.sink, payload=payload, context={"trust": args.trust})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["decision"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
