"""Bounded ComfyUI capability discovery and private, non-authoritative cache."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from creative_errors import Blocked

MAX_OBJECT_INFO_BYTES = 12 * 1024 * 1024
MAX_OBJECT_INFO_NODES = 10_000


def parse_object_info(raw: bytes) -> tuple[dict[str, Any], str]:
    if not isinstance(raw, bytes) or len(raw) > MAX_OBJECT_INFO_BYTES:
        raise Blocked("COMFY_SCHEMA_TOO_LARGE", "ComfyUI node schema exceeds the configured byte limit.", phase="creative.capabilities", source="comfyui")
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise Blocked("COMFY_SCHEMA_INVALID", "ComfyUI returned invalid node schema JSON.", phase="creative.capabilities", source="comfyui") from exc
    if not isinstance(data, dict) or not data or len(data) > MAX_OBJECT_INFO_NODES:
        raise Blocked("COMFY_SCHEMA_INVALID", "ComfyUI node schema has an unsupported shape or node count.", phase="creative.capabilities", source="comfyui")
    for name, metadata in data.items():
        if not isinstance(name, str) or not name or len(name) > 128 or not isinstance(metadata, dict):
            raise Blocked("COMFY_SCHEMA_INVALID", "ComfyUI node schema contains an invalid node entry.", phase="creative.capabilities", source="comfyui")
    return data, "sha256:" + hashlib.sha256(raw).hexdigest()


def input_choices(spec: Any) -> list[Any] | None:
    if not isinstance(spec, list) or not spec:
        return None
    choices = spec[0]
    return choices if isinstance(choices, list) else None


def node_model_candidates(metadata: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    inputs = metadata.get("input") or {}
    if not isinstance(inputs, dict):
        return result
    for group in ("required", "optional"):
        fields = inputs.get(group) or {}
        if not isinstance(fields, dict):
            continue
        for field, spec in fields.items():
            if not isinstance(field, str) or not any(token in field.casefold() for token in ("model", "ckpt", "unet", "clip", "vae", "lora", "embedding", "upscale")):
                continue
            choices = input_choices(spec)
            if choices is not None and all(isinstance(value, str) for value in choices):
                result[field] = choices[:500]
    return result


def record_private_snapshot(base_url: str, comfy_version: str, schema_sha256: str, workflow_sha256: str) -> dict[str, str]:
    """Record fingerprints only; never cache prompts, model filenames, or workflow contents."""
    cache_root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")).expanduser()
    directory = cache_root / "aips" / "comfyui-capabilities"
    key_source = "\0".join((base_url, comfy_version[:128], schema_sha256, workflow_sha256))
    key = hashlib.sha256(key_source.encode("utf-8")).hexdigest()
    target = directory / f"{key}.json"
    try:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(directory, 0o700)
        body = json.dumps({"version": 1, "key": key, "schema_sha256": schema_sha256,
                           "workflow_sha256": workflow_sha256,
                           "observed_at": datetime.now(UTC).isoformat()}, sort_keys=True) + "\n"
        fd, temporary = tempfile.mkstemp(prefix=".comfy-capability-", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(body)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)
        return {"status": "RECORDED", "cache_key": key, "cache_scope": "private_fingerprints_only"}
    except OSError:
        return {"status": "UNAVAILABLE", "cache_scope": "private_fingerprints_only"}
