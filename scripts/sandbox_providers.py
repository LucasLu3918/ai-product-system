#!/usr/bin/env python3
"""Fail-closed capability matching for external sandbox providers."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from aips_identity import config_home, repository_identity


REGISTRY = Path(__file__).resolve().parents[1] / "config" / "sandbox-providers.yaml"


def registry_digest(path: Path | None = None) -> str:
    path = path or REGISTRY
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verification_path(root: Path) -> Path:
    repo_id = repository_identity(root)["repository_id"]
    return config_home() / "sandbox-providers" / repo_id / "verification.json"


def _fresh_record(root: Path, provider: str, cfg: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
    path = verification_path(root)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        verified_at = dt.datetime.fromisoformat(record["verified_at"].replace("Z", "+00:00"))
        age = dt.datetime.now(dt.timezone.utc) - verified_at
        max_age = int((cfg.get("verification") or {}).get("max_age_hours", 24))
        if record.get("status") != "VERIFIED":
            return False, "provider verification is not VERIFIED", record
        if record.get("provider") != provider or record.get("registry_digest") != registry_digest():
            return False, "provider verification does not match the current registry", record
        if age < dt.timedelta(0) or age > dt.timedelta(hours=max_age):
            return False, "provider verification is stale", record
        required = {"create", "execute", "network_deny", "ephemeral", "destroy", "host_fixture_unchanged"}
        observed = record.get("observed_controls") or {}
        if not required.issubset(observed) or any(observed.get(key) is not True for key in required):
            return False, "provider verification is missing required observed controls", record
        return True, "fresh provider verification matches registry", record
    except (OSError, ValueError, KeyError, TypeError):
        return False, "no valid provider verification record", None


def resolve(root: Path, *, data_class: str = "public", minimum_isolation: str = "microvm") -> dict[str, Any]:
    config = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    candidates = []
    reasons = []
    for provider, cfg in sorted((config.get("providers") or {}).items()):
        if not cfg.get("enabled"):
            reasons.append(f"{provider}: provider disabled")
            continue
        if cfg.get("integration_status") != "AVAILABLE":
            reasons.append(f"{provider}: task execution adapter is not enabled")
            continue
        if data_class not in cfg.get("data_classes", []):
            reasons.append(f"{provider}: data class {data_class} is not permitted")
            continue
        assurance = cfg.get("assurance") or {}
        ranks = {"container": 1, "vm": 2, "microvm": 3}
        if minimum_isolation not in ranks or ranks.get(str(assurance.get("isolation_class")), 0) < ranks[minimum_isolation]:
            reasons.append(f"{provider}: runtime class does not meet {minimum_isolation} requirement")
            continue
        valid, reason, record = _fresh_record(root, provider, cfg)
        if not valid:
            reasons.append(f"{provider}: {reason}")
            continue
        candidates.append({"provider": provider, "runtime_class": cfg.get("runtime_class"), "verification": record})
    return {
        "status": "AVAILABLE" if candidates else "BLOCKED",
        "mode": "sandbox",
        "isolated": bool(candidates),
        "provider": candidates[0]["provider"] if candidates else None,
        "runtime_class": candidates[0]["runtime_class"] if candidates else None,
        "verification": candidates[0]["verification"] if candidates else None,
        "reason": "verified provider capability matched" if candidates else "; ".join(reasons) or "no provider registered",
    }
