#!/usr/bin/env python3
"""Provider-neutral optional semantic signal contract; it grants no authority."""
from __future__ import annotations

from typing import Any

def validate_signal(signal: dict[str, Any], *, expected_action_digest: str) -> dict[str, str]:
    if not isinstance(signal, dict):
        raise ValueError("semantic signal must be a mapping")
    if signal.get("action_digest") != expected_action_digest:
        raise ValueError("semantic signal action digest mismatch")
    if signal.get("decision") not in {"ALLOW", "DENY", "ESCALATE"}:
        raise ValueError("semantic signal decision is invalid")
    provider = signal.get("provider")
    if not isinstance(provider, str) or not provider.strip():
        raise ValueError("semantic signal provider is required")
    return {"decision": signal["decision"], "provider": provider}
