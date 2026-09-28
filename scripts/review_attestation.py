"""Verify a runtime receipt against an externally supplied trust anchor."""
from __future__ import annotations

import base64
import binascii
import json
from pathlib import Path
from typing import Any, Callable

import yaml


def verifier_from_store(path: Path) -> Callable[[dict[str, Any]], bool]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict) or doc.get("version") != 1 or not isinstance(doc.get("issuers"), list):
        raise ValueError("invalid independent-review trust store")
    issuers = {}
    for item in doc["issuers"]:
        if not isinstance(item, dict) or not all(isinstance(item.get(key), str) and item[key] for key in ("key_id", "runtime", "public_key_b64")):
            raise ValueError("invalid independent-review issuer")
        if item["key_id"] in issuers:
            raise ValueError("duplicate independent-review issuer")
        issuers[item["key_id"]] = item

    def verify(attestation: dict[str, Any]) -> bool:
        issuer = issuers.get(attestation.get("issuer_key_id"))
        if issuer is None or issuer["runtime"] != attestation.get("runtime"):
            return False
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            from cryptography.exceptions import InvalidSignature
        except ImportError:
            return False
        try:
            public = base64.b64decode(issuer["public_key_b64"], validate=True)
            signature = base64.b64decode(attestation["signature_b64"], validate=True)
            message = json.dumps({key: value for key, value in attestation.items() if key != "signature_b64"},
                                 sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            Ed25519PublicKey.from_public_bytes(public).verify(signature, message)
            return True
        except (ValueError, TypeError, KeyError, binascii.Error, InvalidSignature):
            return False

    return verify
