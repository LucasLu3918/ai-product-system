"""Canonical JSON serialization and SHA-256 fingerprints used by AIPS."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize mappings deterministically without changing Unicode bytes."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def canonical_hash(value: Any, *, prefix: bool = False) -> str:
    """Return the canonical SHA-256 digest, optionally with its public prefix."""
    digest = hashlib.sha256(canonical_json_bytes(value)).hexdigest()
    return f"sha256:{digest}" if prefix else digest


def canonical_digest(value: Any) -> str:
    """Return the canonical digest in the established ``sha256:`` form."""
    return canonical_hash(value, prefix=True)
