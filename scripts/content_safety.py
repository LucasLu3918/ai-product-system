#!/usr/bin/env python3
"""AIPS sink-aware Runtime Content Safety Boundary."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

try:
    from check_secret_leakage import (
        ASSIGNMENT,
        PATTERNS,
        scan_text,
    )
except ModuleNotFoundError:  # imported as a repository module
    from scripts.check_secret_leakage import (
        ASSIGNMENT,
        PATTERNS,
        scan_text,
    )


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/content-safety.yaml"
DEFAULT_EXCEPTIONS = ROOT / "config/content-safety-exceptions.yaml"
GIT_DIFF_METADATA = re.compile(
    r"(?:index [0-9a-f]{4,64}\.\.[0-9a-f]{4,64}(?: [0-7]{6})?"
    r"|(?:old|new|deleted file|new file) mode [0-7]{6}"
    r"|(?:dis)?similarity index \d{1,3}%)\Z"
)


def git_diff_payload(diff: str) -> list[str]:
    """Exclude numeric Git headers; paths, added, removed and context lines remain scanned.

    Hunk lines retain their prefix, so body text resembling metadata is not excluded.
    """
    return [line for line in diff.splitlines() if not GIT_DIFF_METADATA.fullmatch(line)]


def git_diff_payload_with_added_lines(diff: str) -> tuple[str, set[int]]:
    """Return the complete diff for secret/PII checks and its added-line indexes for injection checks."""
    payload: list[str] = []
    added_lines: set[int] = set()
    in_hunk = False
    for line in diff.splitlines():
        if GIT_DIFF_METADATA.fullmatch(line):
            continue
        payload.append(line)
        if line.startswith("diff --git "):
            in_hunk = False
        elif line.startswith("@@ "):
            in_hunk = True
        elif in_hunk and line.startswith("+") and not line.startswith("+++"):
            added_lines.add(len(payload))
    return "\n".join(payload), added_lines


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+886[- ]?|0)9\d{2}[- ]?\d{3}[- ]?\d{3}(?!\d)")
# Do not treat the numeric prefix of a hexadecimal Git SHA as a payment card.
# A card candidate must be delimited from hexadecimal characters as well as
# decimal digits; real card numbers in prose remain unchanged.
CARD_RE = re.compile(r"(?<![0-9A-Fa-f])(?:\d[ -]?){13,19}(?![0-9A-Fa-f])")
TAIWAN_ID_RE = re.compile(r"(?<![A-Z0-9])[A-Z][12]\d{8}(?![A-Z0-9])", re.IGNORECASE)
INJECTION_RULES = (
    ("injection.override.v2", re.compile(
        r"(?i)\b(?:ignore|disregard|override|bypass)\b.{0,80}"
        r"\b(?:previous|prior|system|developer)\s+instructions?\b"
    )),
    ("injection.exfiltration.v2", re.compile(
        r"(?i)\b(?:reveal|disclose|print|show|upload|exfiltrate|send)\b.{0,80}"
        r"\b(?:system\s+prompt|secrets?|credentials?|tokens?|passwords?)\b"
    )),
    ("injection.agent_execution.v2", re.compile(
        r"(?i)\b(?:agent|assistant|model|copilot|claude|gpt)\b.{0,60}"
        r"\b(?:execute|run|push|send)\b.{0,80}"
        r"\b(?:commands?|repositories|secrets?|credentials?|tokens?|passwords?|data)\b"
    )),
    ("injection.ambiguous.v2", re.compile(
        r"(?i)\b(?:please|must|should|do\s+not|don't)\b.{0,40}"
        r"\b(?:execute|run|push|send)\b.{0,80}"
        r"\b(?:commands?|repositories|secrets?|credentials?|tokens?|passwords?|data)\b"
    )),
)
STRONG_INJECTION_RULES = frozenset({
    "injection.override.v2", "injection.exfiltration.v2", "injection.agent_execution.v2",
})
DURABLE_SINKS = frozenset({"git_commit", "github_pr", "release_notes", "source_artifact"})
DIFF_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


class ContentSafetyExceptionError(ValueError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True)
class Finding:
    type: str
    detector: str
    location: str
    fingerprint: str
    length: int
    action: str
    confidence: float
    line: int | None = None
    rule_id: str | None = None
    finding_fingerprint: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _fingerprint(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]


def _stable_finding_fingerprint(rule_id: str, value: str, source_path: str) -> str:
    normalized = " ".join(value.casefold().split())
    identity = "\0".join((rule_id, source_path.replace("\\", "/"), normalized))
    return "sha256:" + hashlib.sha256(identity.encode("utf-8", errors="replace")).hexdigest()


def added_line_numbers_from_diff(diff: str) -> set[int]:
    """Return new-file line numbers introduced by a unified Git diff."""
    added: set[int] = set()
    new_line: int | None = None
    for line in diff.splitlines():
        hunk = DIFF_HUNK_RE.match(line)
        if hunk:
            new_line = int(hunk.group(1))
            continue
        if line.startswith(("+++", "---")):
            continue
        if new_line is None:
            continue
        if line.startswith("+"):
            added.add(new_line)
            new_line += 1
        elif line.startswith(" "):
            new_line += 1
        elif line.startswith("-"):
            continue
    return added


def _validate_exceptions(path: Path, *, today: dt.date | None = None) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ContentSafetyExceptionError("CONTENT_EXCEPTION_INVALID", "content safety exception policy is invalid") from exc
    if not isinstance(document, dict) or document.get("version") != 1 or not isinstance(document.get("exceptions"), list):
        raise ContentSafetyExceptionError(
            "CONTENT_EXCEPTION_INVALID", "content safety exception policy must be a version 1 mapping with an exceptions list"
        )
    today = today or dt.datetime.now(dt.UTC).date()
    allowed_sinks = {"git_commit", "github_pr", "release_notes"}
    for index, item in enumerate(document["exceptions"]):
        if not isinstance(item, dict):
            raise ContentSafetyExceptionError("CONTENT_EXCEPTION_INVALID", f"content safety exception {index} must be a mapping")
        rule_id, path_value = item.get("rule_id"), item.get("path")
        fingerprint, sink, expires = item.get("finding_fingerprint"), item.get("sink"), item.get("expires_on")
        approval = item.get("approval_reference")
        approver = item.get("approved_by")
        if not isinstance(rule_id, str) or not re.fullmatch(r"injection\.(?:override|exfiltration|agent_execution|ambiguous)\.v2", rule_id):
            raise ContentSafetyExceptionError("CONTENT_EXCEPTION_INVALID", f"content safety exception {index} has an invalid rule_id")
        if (not isinstance(path_value, str) or not path_value or len(path_value) > 240
                or path_value.startswith("/") or ".." in Path(path_value).parts or "\\" in path_value):
            raise ContentSafetyExceptionError("CONTENT_EXCEPTION_INVALID", f"content safety exception {index} has an invalid repository-relative path")
        if not re.fullmatch(r"[A-Za-z0-9._/-]+", path_value) or path_value in {".", ".."}:
            raise ContentSafetyExceptionError("CONTENT_EXCEPTION_INVALID", f"content safety exception {index} has an invalid repository-relative path")
        if not isinstance(fingerprint, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", fingerprint):
            raise ContentSafetyExceptionError("CONTENT_EXCEPTION_INVALID", f"content safety exception {index} has an invalid finding fingerprint")
        if sink not in allowed_sinks:
            raise ContentSafetyExceptionError("CONTENT_EXCEPTION_INVALID", f"content safety exception {index} has an invalid sink")
        try:
            expiry = dt.date.fromisoformat(str(expires))
        except ValueError as exc:
            raise ContentSafetyExceptionError("CONTENT_EXCEPTION_INVALID", f"content safety exception {index} has an invalid expiry") from exc
        if expiry <= today:
            raise ContentSafetyExceptionError("CONTENT_EXCEPTION_EXPIRED", f"content safety exception {index} is expired")
        if not isinstance(approval, str) or not approval.strip() or not isinstance(approver, str) or not approver.strip():
            raise ContentSafetyExceptionError("CONTENT_EXCEPTION_INVALID", f"content safety exception {index} requires human approval evidence")
    return document["exceptions"]


def _exception_applies(exceptions: list[dict[str, Any]], *, rule_id: str, path: str, sink: str,
                       finding_fingerprint: str) -> bool:
    return any(
        item["rule_id"] == rule_id and item["path"] == path and item["sink"] == sink
        and item["finding_fingerprint"] == finding_fingerprint
        for item in exceptions
    )


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


def _finding(kind: str, detector: str, location: str, value: str, config: dict[str, Any], sink: str,
             line: int | None = None, *, rule_id: str | None = None, action: str | None = None,
             confidence: float | None = None, source_path: str = "<root>") -> Finding:
    rule = _policy(config, sink, kind)
    identity_rule = rule_id or (f"{kind.lower()}.{detector}.v1" if kind in {"SECRET", "PII"} else None)
    matched_rule = config.get("injection_rules", {}).get(identity_rule, {}) if identity_rule else {}
    rule_actions = matched_rule.get("actions") or {}
    selected_action = (action or rule_actions.get(sink) or rule_actions.get("default")
                       or matched_rule.get("action") or rule.get("action", "ALLOW"))
    if rule_id in STRONG_INJECTION_RULES and sink in DURABLE_SINKS:
        selected_action = "BLOCK"
    selected_confidence = confidence or matched_rule.get("confidence") or rule.get("confidence", 1.0)
    return Finding(kind, detector, location, _fingerprint(value), len(value), str(selected_action),
                   float(selected_confidence), line, identity_rule,
                   _stable_finding_fingerprint(identity_rule, value, source_path) if identity_rule else None)


def _walk(value: Any, prefix: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{prefix}[{index}]")
    elif isinstance(value, str):
        yield prefix or "<root>", value


def scan_payload(payload: Any, *, sink: str, config: dict[str, Any] | None = None,
                 context: dict[str, Any] | None = None, strict: bool = False) -> list[Finding]:
    config = config or load_config()
    context = context or {}
    source_path = str(context.get("source_path") or "<root>")
    changed_lines_value = context.get("injection_changed_lines")
    changed_lines = set(changed_lines_value) if isinstance(changed_lines_value, (set, list, tuple)) else None
    findings: list[Finding] = []
    for location, text in _walk(payload):
        for item in scan_text(text, location, strict=strict):
            rule = _policy(config, sink, "SECRET")
            secret_rule_id = f"secret.{item['detector']}.v1"
            findings.append(Finding(
                "SECRET", item["detector"], location, str(item["fingerprint"]), int(item["secret_length"]),
                str(rule.get("action", "ALLOW")), float(rule.get("confidence", 1.0)), int(item.get("line", 1)),
                secret_rule_id,
                _stable_finding_fingerprint(secret_rule_id, str(item["fingerprint"]), source_path),
            ))
        for match in EMAIL_RE.finditer(text):
            findings.append(_finding("PII", "email", location, match.group(0), config, sink, text.count("\n", 0, match.start()) + 1))
        for match in PHONE_RE.finditer(text):
            findings.append(_finding("PII", "phone", location, match.group(0), config, sink, text.count("\n", 0, match.start()) + 1))
        for match in CARD_RE.finditer(text):
            candidate = match.group(0)
            if _luhn(candidate):
                findings.append(_finding("PII", "credit-card-luhn", location, candidate, config, sink, text.count("\n", 0, match.start()) + 1))
        for match in TAIWAN_ID_RE.finditer(text):
            if _taiwan_id(match.group(0)):
                findings.append(_finding("PII", "taiwan-id-checksum", location, match.group(0), config, sink, text.count("\n", 0, match.start()) + 1))
        exceptions = _validate_exceptions(DEFAULT_EXCEPTIONS) if sink in {"git_commit", "github_pr", "release_notes"} else []
        for rule_id, pattern in INJECTION_RULES:
            for match in pattern.finditer(text):
                first_line = text.count("\n", 0, match.start()) + 1
                last_line = text.count("\n", 0, match.end()) + 1
                if changed_lines is not None and not any(first_line <= line <= last_line for line in changed_lines):
                    continue
                action = "REVIEW" if rule_id == "injection.ambiguous.v2" else None
                finding = _finding("INJECTION_SIGNAL", rule_id, location, match.group(0), config, sink,
                                   first_line, rule_id=rule_id, action=action, source_path=source_path)
                if (sink in {"git_commit", "github_pr", "release_notes"} and source_path != "<root>"
                        and _exception_applies(exceptions, rule_id=rule_id, path=source_path, sink=sink,
                                               finding_fingerprint=finding.finding_fingerprint or "")):
                    finding = Finding(finding.type, finding.detector, finding.location, finding.fingerprint,
                                      finding.length, "ALLOW", finding.confidence, finding.line,
                                      finding.rule_id, finding.finding_fingerprint)
                findings.append(finding)
    trust = context.get("trust") or context.get("source", {}).get("trust")
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
        replacement = _replacement(finding.type)
        pattern = PATTERNS_BY_DETECTOR.get(finding.detector)
        if pattern:
            result = pattern.sub(replacement, result)
        elif finding.detector == "generic-secret-assignment":
            result = ASSIGNMENT.sub(
                lambda match, value=replacement: match.group(0).replace(match.group(2), value), result
            )
        elif finding.detector == "email":
            result = EMAIL_RE.sub(replacement, result)
        elif finding.detector == "phone":
            result = PHONE_RE.sub(replacement, result)
        elif finding.detector == "credit-card-luhn":
            result = CARD_RE.sub(
                lambda match, value=replacement: value if _luhn(match.group(0)) else match.group(0), result
            )
        elif finding.detector == "taiwan-id-checksum":
            result = TAIWAN_ID_RE.sub(
                lambda match, value=replacement: value if _taiwan_id(match.group(0)) else match.group(0), result
            )
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


def safe_emit(*, sink: str, payload: Any, context: dict[str, Any] | None = None,
              config: dict[str, Any] | None = None, strict: bool = False) -> dict[str, Any]:
    config = config or load_config()
    findings = scan_payload(payload, sink=sink, config=config, context=context, strict=strict)
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
