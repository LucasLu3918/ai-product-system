#!/usr/bin/env python3
"""Build a bounded review packet from allowlisted repository evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import yaml

from content_safety import scan_payload


ALLOWED_SOURCE_CLASSES = {
    "specification",
    "acceptance_criteria",
    "repository_source",
    "change_boundary",
    "change_impact",
    "diff",
    "test_result",
    "security_evidence",
    "architecture_decision",
    "project_instruction",
}
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
FINGERPRINT_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
MAX_FILE_BYTES = 512 * 1024
MAX_PACKET_BYTES = 2 * 1024 * 1024


class ReviewPacketError(ValueError):
    pass


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_hash(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def safe_source_path(root: Path, value: Any) -> tuple[str, Path]:
    if not isinstance(value, str) or not value.strip():
        raise ReviewPacketError("each evidence source requires a repository-relative path")
    raw = Path(value)
    if raw.is_absolute() or ".." in raw.parts:
        raise ReviewPacketError("evidence source path must stay inside the repository")
    resolved_root = root.resolve()
    resolved = (resolved_root / raw).resolve()
    if not resolved.is_relative_to(resolved_root) or not resolved.is_file():
        raise ReviewPacketError("evidence source is missing or escapes the repository")
    return raw.as_posix(), resolved


def validate_candidate(candidate: Any) -> dict[str, str]:
    if not isinstance(candidate, dict):
        raise ReviewPacketError("candidate must be a mapping")
    result: dict[str, str] = {}
    for key in ("base_sha", "head_sha"):
        value = candidate.get(key)
        if not isinstance(value, str) or not GIT_SHA_RE.fullmatch(value):
            raise ReviewPacketError(f"candidate.{key} must be a full lowercase Git SHA")
        result[key] = value
    changed_hash = candidate.get("changed_files_hash")
    if not isinstance(changed_hash, str) or not FINGERPRINT_RE.fullmatch(changed_hash):
        raise ReviewPacketError("candidate.changed_files_hash must be a sha256 fingerprint")
    result["changed_files_hash"] = changed_hash
    return result


def build_packet(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("version") != 1:
        raise ReviewPacketError("review packet manifest version must be 1")
    candidate = validate_candidate(manifest.get("candidate"))
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ReviewPacketError("review packet requires at least one evidence source")

    normalized: list[dict[str, Any]] = []
    total_bytes = 0
    seen_paths: set[str] = set()
    for item in sources:
        if not isinstance(item, dict):
            raise ReviewPacketError("each evidence source must be a mapping")
        source_class = item.get("class")
        if not isinstance(source_class, str) or source_class not in ALLOWED_SOURCE_CLASSES:
            raise ReviewPacketError("evidence source class is not allowlisted")
        path, resolved = safe_source_path(root, item.get("path"))
        if path in seen_paths:
            raise ReviewPacketError("duplicate evidence source path")
        seen_paths.add(path)
        raw = resolved.read_bytes()
        if len(raw) > MAX_FILE_BYTES:
            raise ReviewPacketError("evidence source exceeds the per-file byte limit")
        total_bytes += len(raw)
        if total_bytes > MAX_PACKET_BYTES:
            raise ReviewPacketError("review packet exceeds the total byte limit")
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ReviewPacketError("review packet sources must be UTF-8 text") from exc
        findings = scan_payload(content, sink="source_artifact")
        if any(item.type in {"SECRET", "PII"} for item in findings):
            raise ReviewPacketError("review packet source failed content-safety checks")
        normalized.append({
            "class": source_class,
            "path": path,
            "sha256": file_hash(raw),
            "bytes": len(raw),
            "content": content,
            "untrusted_content": any(item.type == "INJECTION_SIGNAL" for item in findings),
        })

    normalized.sort(key=lambda item: (item["class"], item["path"]))
    body = {
        "version": 1,
        "candidate": candidate,
        "sources": normalized,
        "context_policy": {
            "inheritance": "none",
            "allowed_classes": sorted({item["class"] for item in normalized}),
            "denied_classes": [
                "implementation_transcript",
                "private_reasoning",
                "scratchpad",
                "raw_model_trace",
            ],
        },
    }
    return {**body, "packet_fingerprint": canonical_hash(body)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8")) or {}
        if not isinstance(manifest, dict):
            raise ReviewPacketError("review packet manifest must be a mapping")
        packet = build_packet(args.root, manifest)
    except (OSError, UnicodeError, yaml.YAMLError, ReviewPacketError) as exc:
        print(f"REVIEW PACKET BLOCKED: {exc}")
        return 2
    rendered = yaml.safe_dump(packet, sort_keys=False, allow_unicode=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
