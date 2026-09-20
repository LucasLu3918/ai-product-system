#!/usr/bin/env python3
"""Provider-neutral Evolution Radar evidence utilities.

The collector performs bounded public-source retrieval and deterministic normalization.
It never infers that a signal is suitable for AIPS. When no semantic analyzer is
available, recommendations remain ANALYSIS_PENDING.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import ipaddress
import json
from pathlib import Path
import re
import socket
import ssl
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/evolution-sources.yaml"
ALLOWED_STATES = {"COVERED", "HOLD", "ASSESS", "TRIAL", "ADOPT", "ANALYSIS_PENDING"}
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
DEFAULT_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
DEFAULT_MAX_REDIRECTS = 3


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def canonical_url(value: str) -> str:
    parsed = urllib.parse.urlsplit((value or "").strip())
    if not parsed.scheme or not parsed.netloc:
        return (value or "").strip()
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query = [(k, v) for k, v in query if not k.lower().startswith("utm_")]
    return urllib.parse.urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", urllib.parse.urlencode(query), "")
    )


def signal_fingerprint(title: str, url: str) -> str:
    basis = f"{normalize_text(title).casefold()}\n{canonical_url(url)}".encode("utf-8")
    return "sha256:" + hashlib.sha256(basis).hexdigest()


def _is_global_ip(value: str) -> bool:
    candidate = value.split("%", 1)[0]
    try:
        return ipaddress.ip_address(candidate).is_global
    except ValueError:
        return False


def validate_public_url_syntax(url: str) -> urllib.parse.SplitResult:
    value = (url or "").strip()
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ValueError("public source URL must use https and include a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("public source URL must not contain userinfo or credentials")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("public source URL has an invalid port") from exc
    if port is not None and not (1 <= port <= 65535):
        raise ValueError("public source URL has an invalid port")

    hostname = parsed.hostname.rstrip(".")
    if not hostname or hostname.casefold() == "localhost" or hostname.casefold().endswith(".localhost"):
        raise ValueError("public source URL must not target localhost")

    try:
        literal = ipaddress.ip_address(hostname.split("%", 1)[0])
    except ValueError:
        pass
    else:
        if not literal.is_global:
            raise ValueError("public source URL must use a globally routable address")
    return parsed


def resolve_public_destination(url: str) -> tuple[urllib.parse.SplitResult, list[str]]:
    parsed = validate_public_url_syntax(url)
    hostname = (parsed.hostname or "").rstrip(".")
    port = parsed.port or 443
    try:
        infos = socket.getaddrinfo(
            hostname,
            port,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
    except socket.gaierror as exc:
        raise ValueError("public source hostname resolution failed") from exc

    addresses: list[str] = []
    for _, _, _, _, sockaddr in infos:
        address = str(sockaddr[0]).split("%", 1)[0]
        if not _is_global_ip(address):
            raise ValueError("public source hostname resolved to a non-public address")
        if address not in addresses:
            addresses.append(address)
    if not addresses:
        raise ValueError("public source hostname resolved to no usable addresses")
    return parsed, addresses


def _bounded_read(response: http.client.HTTPResponse, max_response_bytes: int) -> bytes:
    length = response.getheader("Content-Length")
    if length:
        try:
            declared = int(length)
        except ValueError:
            declared = None
        if declared is not None and declared > max_response_bytes:
            raise ValueError("public source response exceeds configured size limit")
    body = response.read(max_response_bytes + 1)
    if len(body) > max_response_bytes:
        raise ValueError("public source response exceeds configured size limit")
    return body


def _request_once(
    parsed: urllib.parse.SplitResult,
    addresses: list[str],
    *,
    timeout: float,
    max_response_bytes: int,
) -> tuple[int, dict[str, str], bytes]:
    hostname = (parsed.hostname or "").rstrip(".")
    port = parsed.port or 443
    target = urllib.parse.urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
    headers = {
        "User-Agent": "AIPS-Evolution-Radar/1",
        "Accept": "application/rss+xml, application/atom+xml, application/json, text/xml;q=0.9, */*;q=0.1",
        "Connection": "close",
    }
    last_error: BaseException | None = None
    for address in addresses:
        context = ssl.create_default_context()
        conn = http.client.HTTPSConnection(hostname, port=port, timeout=timeout, context=context)
        raw_socket = None
        try:
            raw_socket = socket.create_connection((address, port), timeout=timeout)
            conn.sock = context.wrap_socket(raw_socket, server_hostname=hostname)
            raw_socket = None
            conn.request("GET", target, headers=headers)
            response = conn.getresponse()
            try:
                status = int(response.status)
                response_headers = {k.lower(): v for k, v in response.getheaders()}
                if status in REDIRECT_STATUSES:
                    return status, response_headers, b""
                if not 200 <= status < 300:
                    raise ValueError(f"public source returned HTTP status {status}")
                return status, response_headers, _bounded_read(response, max_response_bytes)
            finally:
                response.close()
        except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
            last_error = exc
        finally:
            if raw_socket is not None:
                raw_socket.close()
            conn.close()
    if last_error is not None:
        raise last_error
    raise OSError("public source connection failed")


def fetch_bytes(
    url: str,
    timeout: float,
    *,
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
) -> bytes:
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if max_response_bytes < 1:
        raise ValueError("max_response_bytes must be positive")
    if max_redirects < 0:
        raise ValueError("max_redirects must be non-negative")

    current = (url or "").strip()
    visited: set[str] = set()
    redirects = 0
    while True:
        parsed, addresses = resolve_public_destination(current)
        normalized = canonical_url(current)
        if normalized in visited:
            raise ValueError("public source redirect loop detected")
        visited.add(normalized)

        status, headers, body = _request_once(
            parsed,
            addresses,
            timeout=timeout,
            max_response_bytes=max_response_bytes,
        )
        if status not in REDIRECT_STATUSES:
            return body

        location = headers.get("location")
        if not location:
            raise ValueError("public source redirect is missing Location")
        if redirects >= max_redirects:
            raise ValueError("public source redirect limit exceeded")
        next_url = urllib.parse.urljoin(current, location)
        validate_public_url_syntax(next_url)
        current = next_url
        redirects += 1


def _rss_items(data: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(data)
    items: list[dict[str, Any]] = []
    for node in root.findall(".//item"):
        title = normalize_text(node.findtext("title") or "")
        link = normalize_text(node.findtext("link") or "")
        date = normalize_text(node.findtext("pubDate") or "") or None
        if title and link:
            items.append({"title": title, "url": link, "published_at": date})
    if items:
        return items
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for node in root.findall(".//atom:entry", ns):
        title = normalize_text(node.findtext("atom:title", default="", namespaces=ns))
        link_node = node.find("atom:link", ns)
        link = normalize_text(link_node.attrib.get("href", "") if link_node is not None else "")
        date = normalize_text(node.findtext("atom:updated", default="", namespaces=ns)) or None
        if title and link:
            items.append({"title": title, "url": link, "published_at": date})
    return items


def collect_source(
    source: dict[str, Any],
    max_items: int,
    timeout: float,
    *,
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
) -> list[dict[str, Any]]:
    kind = source.get("kind")
    url = source.get("url")
    role = str(source.get("role") or "legacy")
    fetch_options = {
        "max_response_bytes": max_response_bytes,
        "max_redirects": max_redirects,
    }
    if kind == "rss":
        raw = _rss_items(fetch_bytes(url, timeout, **fetch_options))[:max_items]
    elif kind == "json" and source.get("item_url_template"):
        ids = json.loads(fetch_bytes(url, timeout, **fetch_options).decode("utf-8"))[:max_items]
        raw = []
        for item_id in ids:
            item_url = source["item_url_template"].format(id=item_id)
            item = json.loads(fetch_bytes(item_url, timeout, **fetch_options).decode("utf-8"))
            if item.get("title"):
                raw.append({
                    "title": normalize_text(item.get("title", "")),
                    "url": item.get("url") or f"https://news.ycombinator.com/item?id={item_id}",
                    "published_at": item.get("time"),
                })
    else:
        raise ValueError(f"unsupported source kind: {kind!r}")

    out: list[dict[str, Any]] = []
    for item in raw[:max_items]:
        url_value = canonical_url(str(item.get("url") or ""))
        title = normalize_text(str(item.get("title") or ""))
        if not title or not url_value:
            continue
        out.append({
            "fingerprint": signal_fingerprint(title, url_value),
            "title": title,
            "canonical_url": url_value,
            "source_id": source["id"],
            "source_role": role,
            "published_at": item.get("published_at"),
        })
    return out

def _policy_int(policy: dict[str, Any], key: str, default: int, errors: list[str]) -> int:
    try:
        return int(policy.get(key, default))
    except (TypeError, ValueError):
        errors.append(f"{key} must be an integer")
        return default


def validate_config(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    policy = doc.get("policy") or {}
    sources = [s for s in (doc.get("sources") or []) if s.get("enabled", True)]
    minimum = _policy_int(policy, "minimum_sources_when_available", 5, errors)
    minimum_community = _policy_int(policy, "minimum_community_sources_when_available", 5, errors)
    target_community = _policy_int(policy, "target_community_sources", 6, errors)
    maximum = _policy_int(policy, "max_items_per_source", 8, errors)
    max_raw_signals = _policy_int(policy, "max_raw_signals", 50, errors)
    max_response_bytes = _policy_int(policy, "max_response_bytes", DEFAULT_MAX_RESPONSE_BYTES, errors)
    max_redirects = _policy_int(policy, "max_redirects", DEFAULT_MAX_REDIRECTS, errors)

    if minimum < 1:
        errors.append("minimum_sources_when_available must be >= 1")
    if minimum_community < 1:
        errors.append("minimum_community_sources_when_available must be >= 1")
    if target_community < minimum_community:
        errors.append("target_community_sources must be >= minimum_community_sources_when_available")
    if maximum < 1 or maximum > 25:
        errors.append("max_items_per_source must be between 1 and 25")
    if max_raw_signals < maximum or max_raw_signals > 250:
        errors.append("max_raw_signals must be between max_items_per_source and 250")
    quality = policy.get("evidence_quality") or {}
    expected_levels = {
        "discovery_only": 0,
        "multi_community": 1,
        "primary_source": 2,
        "primary_corroborated": 3,
        "multi_primary_corroborated": 4,
    }
    if quality.get("adopt_minimum_level") != 2:
        errors.append("evidence_quality.adopt_minimum_level must be 2")
    if quality.get("levels") != expected_levels:
        errors.append("evidence_quality.levels must match the deterministic 0-4 contract")
    if max_response_bytes < 1024 or max_response_bytes > 10 * 1024 * 1024:
        errors.append("max_response_bytes must be between 1024 and 10485760")
    if max_redirects < 0 or max_redirects > 10:
        errors.append("max_redirects must be between 0 and 10")
    if policy.get("public_only") is not True:
        errors.append("public_only must be true")
    if policy.get("credentials_in_repository") is not False:
        errors.append("credentials_in_repository must be false")

    ids = [s.get("id") for s in sources]
    if len(ids) != len(set(ids)) or any(not x for x in ids):
        errors.append("enabled source ids must be unique and non-empty")
    if len(sources) < minimum:
        errors.append(f"configured enabled sources {len(sources)} is below minimum {minimum}")

    communities = [s for s in sources if s.get("role") == "community"]
    if len(communities) < target_community:
        errors.append(
            f"configured community sources {len(communities)} is below target {target_community}"
        )

    for source in sources:
        source_id = source.get("id")
        role = source.get("role")
        if role not in {"community", "primary"}:
            errors.append(f"source {source_id} role must be community or primary")
        if "best_effort" in source and not isinstance(source.get("best_effort"), bool):
            errors.append(f"source {source_id} best_effort must be boolean")
        for field in ("url", "item_url_template"):
            value = source.get(field)
            if value is None:
                continue
            try:
                validate_public_url_syntax(str(value).format(id=1) if field == "item_url_template" else str(value))
            except (KeyError, ValueError) as exc:
                errors.append(f"source {source_id} {field} must be a credential-free public https URL: {exc}")
        if source.get("kind") not in {"rss", "json"}:
            errors.append(f"source {source_id} has unsupported kind")
        if source.get("kind") == "json" and not source.get("item_url_template"):
            errors.append(f"source {source_id} json source requires item_url_template")
    return errors

def evidence_quality_metadata(provenance: list[dict[str, str]]) -> dict[str, Any]:
    normalized = sorted(
        {
            (str(item.get("source_id") or ""), str(item.get("role") or "legacy"))
            for item in provenance
            if str(item.get("source_id") or "")
        }
    )
    primary = sorted(source_id for source_id, role in normalized if role == "primary")
    community = sorted(source_id for source_id, role in normalized if role == "community")
    if len(primary) >= 2:
        level, strength = 4, "VERY_HIGH"
    elif primary and community:
        level, strength = 3, "HIGH"
    elif primary:
        level, strength = 2, "MEDIUM"
    elif len(community) >= 2:
        level, strength = 1, "LOW"
    else:
        level, strength = 0, "DISCOVERY"
    return {
        "evidence_level": level,
        "evidence_strength": strength,
        "primary_source_count": len(primary),
        "community_source_count": len(community),
    }


def deduplicate(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for signal in signals:
        fp = signal["fingerprint"]
        source_id = str(signal.get("source_id") or "")
        source_role = str(signal.get("source_role") or "legacy")
        if fp not in seen:
            item = dict(signal)
            item["recurrence_count"] = 1
            item["duplicate_of"] = None
            item["source_ids"] = [source_id] if source_id else []
            item["source_roles"] = [source_role]
            item["source_provenance"] = (
                [{"source_id": source_id, "role": source_role}] if source_id else []
            )
            seen[fp] = item
        else:
            seen[fp]["recurrence_count"] += 1
            if source_id and source_id not in seen[fp]["source_ids"]:
                seen[fp]["source_ids"].append(source_id)
            if source_role not in seen[fp]["source_roles"]:
                seen[fp]["source_roles"].append(source_role)
            provenance = seen[fp].setdefault("source_provenance", [])
            candidate = {"source_id": source_id, "role": source_role}
            if source_id and candidate not in provenance:
                provenance.append(candidate)

    for item in seen.values():
        item["source_ids"] = sorted(item["source_ids"])
        item["source_roles"] = sorted(item["source_roles"])
        item["source_provenance"] = sorted(
            item.get("source_provenance") or [],
            key=lambda value: (str(value.get("source_id") or ""), str(value.get("role") or "")),
        )
        roles = set(item["source_roles"])
        if "primary" in roles and "community" in roles:
            item["verification_status"] = "PRIMARY_CORROBORATED"
        elif "primary" in roles:
            item["verification_status"] = "PRIMARY_SOURCE"
        elif "community" in roles:
            item["verification_status"] = "DISCOVERY_ONLY"
        else:
            item["verification_status"] = "LEGACY_UNVERIFIED"
        item.update(evidence_quality_metadata(item["source_provenance"]))
    return list(seen.values())


def bound_signals_by_source(
    signals: list[dict[str, Any]],
    source_order: list[str],
    max_total: int,
) -> list[dict[str, Any]]:
    """Apply a deterministic global cap without letting early sources monopolize the budget."""
    buckets: dict[str, list[dict[str, Any]]] = {source_id: [] for source_id in source_order}
    for signal in signals:
        buckets.setdefault(str(signal.get("source_id") or ""), []).append(signal)

    bounded: list[dict[str, Any]] = []
    index = 0
    while len(bounded) < max_total:
        progressed = False
        for source_id in source_order:
            bucket = buckets.get(source_id) or []
            if index < len(bucket):
                bounded.append(bucket[index])
                progressed = True
                if len(bounded) >= max_total:
                    break
        if not progressed:
            break
        index += 1
    return bounded

def build_evidence(config: dict[str, Any], *, mode: str, timeout: float = 8.0) -> dict[str, Any]:
    if mode not in {"weekly", "monthly"}:
        raise ValueError("mode must be weekly or monthly")
    config_errors = validate_config(config)
    if config_errors:
        raise ValueError("; ".join(config_errors))

    policy = config["policy"]
    maximum = int(policy["max_items_per_source"])
    max_raw_signals = int(policy["max_raw_signals"])
    minimum_community = int(policy["minimum_community_sources_when_available"])
    target_community = int(policy["target_community_sources"])
    max_response_bytes = int(policy["max_response_bytes"])
    max_redirects = int(policy["max_redirects"])
    enabled = [s for s in config["sources"] if s.get("enabled", True)]
    source_order = [str(s["id"]) for s in enabled]
    attempted: list[str] = []
    successful: list[str] = []
    successful_community: list[str] = []
    failures: list[dict[str, str]] = []
    collected: list[dict[str, Any]] = []

    for source in enabled:
        source_id = str(source["id"])
        attempted.append(source_id)
        try:
            items = collect_source(
                source,
                maximum,
                timeout,
                max_response_bytes=max_response_bytes,
                max_redirects=max_redirects,
            )
            if not items:
                failures.append({"source_id": source_id, "error": "EmptySource"})
                continue
            successful.append(source_id)
            if source.get("role") == "community":
                successful_community.append(source_id)
            collected.extend(items)
        except (OSError, ValueError, ET.ParseError, json.JSONDecodeError, http.client.HTTPException) as exc:
            failures.append({"source_id": source_id, "error": type(exc).__name__})

    bounded = bound_signals_by_source(collected, source_order, max_raw_signals)
    unique = deduplicate(bounded)
    recommendations = [
        {
            "signal_fingerprint": signal["fingerprint"],
            "state": "ANALYSIS_PENDING",
            "aips_current_state": "",
            "benefit": "",
            "cost_complexity": "",
            "reliability_security": "",
            "confidence": None,
            "uncertainty": "Semantic analyzer unavailable; no suitability conclusion inferred.",
            "example": "",
            "reuse_extension_path": [],
            "architecture_diagram_review_if_adopted": False,
        }
        for signal in unique
    ]
    community_coverage = {
        "required": minimum_community,
        "target": target_community,
        "successful": len(successful_community),
        "status": "HEALTHY" if len(successful_community) >= minimum_community else "DEGRADED",
    }
    return {
        "version": 1,
        "run": {
            "mode": mode,
            "generated_at": utc_now(),
            "repository_revision": None,
            "analyzer": {"status": "unavailable", "provider": None, "model": None},
        },
        "sources": {
            "configured": source_order,
            "roles": {str(s["id"]): str(s.get("role") or "legacy") for s in enabled},
            "attempted": attempted,
            "successful": successful,
            "successful_community": successful_community,
            "community_coverage": community_coverage,
            "failures": failures,
        },
        "signals": unique,
        "recommendations": recommendations,
        "summary": {
            "collected_before_global_limit": len(collected),
            "signal_count": len(bounded),
            "global_signal_limit": max_raw_signals,
            "global_signal_limit_applied": len(collected) > len(bounded),
            "adopt_minimum_evidence_level": int(policy["evidence_quality"]["adopt_minimum_level"]),
            "deduplicated_count": len(unique),
            "recommendation_count": len(recommendations),
            "actionable_count": 0,
            "zero_recommendations_valid": True,
        },
        "authority": {
            "code_change_authorized": False,
            "branch_or_pr_authorized": False,
            "merge_authorized": False,
            "release_authorized": False,
            "human_decision_required": True,
        },
    }

def validate_evidence(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("version") != 1:
        errors.append("version must be 1")
    mode = (doc.get("run") or {}).get("mode")
    if mode not in {"weekly", "monthly", "quarterly"}:
        errors.append("run.mode must be weekly, monthly or quarterly")
    analyzer = (doc.get("run") or {}).get("analyzer") or {}
    if analyzer.get("status") not in {"available", "unavailable"}:
        errors.append("run.analyzer.status must be available or unavailable")
    sources = doc.get("sources") or {}
    configured = sources.get("configured") or []
    attempted = sources.get("attempted") or []
    if not configured or set(attempted) - set(configured):
        errors.append("attempted sources must be configured")
    successful = sources.get("successful")
    if successful is not None and set(successful) - set(attempted):
        errors.append("successful sources must be attempted")
    successful_community = sources.get("successful_community")
    if successful_community is not None and set(successful_community) - set(successful or []):
        errors.append("successful community sources must be successful sources")
    coverage = sources.get("community_coverage")
    if coverage is not None:
        if coverage.get("status") not in {"HEALTHY", "DEGRADED"}:
            errors.append("community coverage status must be HEALTHY or DEGRADED")
        for key in ("required", "target", "successful"):
            if not isinstance(coverage.get(key), int) or isinstance(coverage.get(key), bool) or coverage.get(key) < 0:
                errors.append(f"community coverage {key} must be a non-negative integer")
        if isinstance(coverage.get("required"), int) and isinstance(coverage.get("target"), int) and coverage["target"] < coverage["required"]:
            errors.append("community coverage target must be >= required")

    signals = doc.get("signals") or []
    fingerprints = [s.get("fingerprint") for s in signals]
    if len(fingerprints) != len(set(fingerprints)) or any(not fp for fp in fingerprints):
        errors.append("signals must have unique non-empty fingerprints")
    allowed_roles = {"community", "primary", "legacy"}
    allowed_verification = {"DISCOVERY_ONLY", "PRIMARY_SOURCE", "PRIMARY_CORROBORATED", "LEGACY_UNVERIFIED"}
    for signal in signals:
        if not signal.get("title") or not signal.get("canonical_url") or not signal.get("source_id"):
            errors.append("each signal requires title, canonical_url and source_id")
        if signal.get("recurrence_count", 0) < 1:
            errors.append("signal recurrence_count must be >= 1")
        roles = signal.get("source_roles")
        if roles is not None:
            if not isinstance(roles, list) or not roles or not set(roles).issubset(allowed_roles):
                errors.append("signal source_roles must contain only community/primary/legacy")
        verification = signal.get("verification_status")
        if verification is not None and verification not in allowed_verification:
            errors.append("signal verification_status is invalid")
        provenance = signal.get("source_provenance")
        if provenance is not None:
            if not isinstance(provenance, list) or not provenance:
                errors.append("signal source_provenance must be a non-empty list when present")
            elif any(
                not isinstance(item, dict)
                or not str(item.get("source_id") or "")
                or item.get("role") not in allowed_roles
                for item in provenance
            ):
                errors.append("signal source_provenance entries must bind source_id and valid role")
        level = signal.get("evidence_level")
        strength = signal.get("evidence_strength")
        if level is not None and (not isinstance(level, int) or isinstance(level, bool) or not 0 <= level <= 4):
            errors.append("signal evidence_level must be an integer from 0 to 4")
        if strength is not None and strength not in {"DISCOVERY", "LOW", "MEDIUM", "HIGH", "VERY_HIGH"}:
            errors.append("signal evidence_strength is invalid")
        for key in ("primary_source_count", "community_source_count"):
            value = signal.get(key)
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                errors.append(f"signal {key} must be a non-negative integer")

    recs = doc.get("recommendations") or []
    signal_set = set(fingerprints)
    for rec in recs:
        if rec.get("signal_fingerprint") not in signal_set:
            errors.append("recommendation must reference an existing signal")
        if rec.get("state") not in ALLOWED_STATES:
            errors.append("recommendation has invalid state")
    if analyzer.get("status") == "unavailable" and any(r.get("state") != "ANALYSIS_PENDING" for r in recs):
        errors.append("unavailable analyzer may only emit ANALYSIS_PENDING")
    authority = doc.get("authority") or {}
    for key in ("code_change_authorized", "branch_or_pr_authorized", "merge_authorized", "release_authorized"):
        if authority.get(key) is not False:
            errors.append(f"authority.{key} must be false")
    if authority.get("human_decision_required") is not True:
        errors.append("authority.human_decision_required must be true")
    summary = doc.get("summary") or {}
    if summary.get("deduplicated_count") != len(signals):
        errors.append("summary.deduplicated_count must match signals")
    if summary.get("recommendation_count") != len(recs):
        errors.append("summary.recommendation_count must match recommendations")
    adopt_minimum = summary.get("adopt_minimum_evidence_level")
    if adopt_minimum is not None and adopt_minimum != 2:
        errors.append("summary.adopt_minimum_evidence_level must remain 2")
    if summary.get("zero_recommendations_valid") is not True:
        errors.append("zero recommendations must remain valid")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    collect = sub.add_parser("collect")
    collect.add_argument("--config", default=str(DEFAULT_CONFIG))
    collect.add_argument("--mode", choices=("weekly", "monthly"), default="weekly")
    collect.add_argument("--output")
    collect.add_argument("--timeout", type=float, default=8.0)
    validate = sub.add_parser("validate")
    validate.add_argument("evidence")
    config_check = sub.add_parser("validate-config")
    config_check.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()

    if args.command == "validate-config":
        doc = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")) or {}
        errors = validate_config(doc)
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 1
    if args.command == "collect":
        config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")) or {}
        evidence = build_evidence(config, mode=args.mode, timeout=args.timeout)
        text = yaml.safe_dump(evidence, sort_keys=False, allow_unicode=True)
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0
    evidence = yaml.safe_load(Path(args.evidence).read_text(encoding="utf-8")) or {}
    errors = validate_evidence(evidence)
    print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
