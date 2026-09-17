#!/usr/bin/env python3
"""Provider-neutral Evolution Radar evidence utilities.

The collector performs bounded public-source retrieval and deterministic normalization.
It never infers that a signal is suitable for AIPS. When no semantic analyzer is
available, recommendations remain ANALYSIS_PENDING.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/evolution-sources.yaml"
ALLOWED_STATES = {"COVERED", "HOLD", "ASSESS", "TRIAL", "ADOPT", "ANALYSIS_PENDING"}


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


def fetch_bytes(url: str, timeout: float) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "AIPS-Evolution-Radar/1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 - configured public URLs only
        return response.read()


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


def collect_source(source: dict[str, Any], max_items: int, timeout: float) -> list[dict[str, Any]]:
    kind = source.get("kind")
    url = source.get("url")
    if kind == "rss":
        raw = _rss_items(fetch_bytes(url, timeout))[:max_items]
    elif kind == "json" and source.get("item_url_template"):
        ids = json.loads(fetch_bytes(url, timeout).decode("utf-8"))[:max_items]
        raw = []
        for item_id in ids:
            item_url = source["item_url_template"].format(id=item_id)
            item = json.loads(fetch_bytes(item_url, timeout).decode("utf-8"))
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
            "published_at": item.get("published_at"),
        })
    return out


def validate_config(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    policy = doc.get("policy") or {}
    sources = [s for s in (doc.get("sources") or []) if s.get("enabled", True)]
    minimum = int(policy.get("minimum_sources_when_available", 5))
    maximum = int(policy.get("max_items_per_source", 5))
    if minimum < 1:
        errors.append("minimum_sources_when_available must be >= 1")
    if maximum < 1 or maximum > 25:
        errors.append("max_items_per_source must be between 1 and 25")
    ids = [s.get("id") for s in sources]
    if len(ids) != len(set(ids)) or any(not x for x in ids):
        errors.append("enabled source ids must be unique and non-empty")
    if len(sources) < minimum:
        errors.append(f"configured enabled sources {len(sources)} is below minimum {minimum}")
    for source in sources:
        url = str(source.get("url") or "")
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or not parsed.netloc:
            errors.append(f"source {source.get('id')} must use a public https URL")
        if source.get("kind") not in {"rss", "json"}:
            errors.append(f"source {source.get('id')} has unsupported kind")
    return errors


def deduplicate(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for signal in signals:
        fp = signal["fingerprint"]
        if fp not in seen:
            item = dict(signal)
            item["recurrence_count"] = 1
            item["duplicate_of"] = None
            seen[fp] = item
        else:
            seen[fp]["recurrence_count"] += 1
    return list(seen.values())


def build_evidence(config: dict[str, Any], *, mode: str, timeout: float = 8.0) -> dict[str, Any]:
    if mode not in {"weekly", "monthly"}:
        raise ValueError("mode must be weekly or monthly")
    config_errors = validate_config(config)
    if config_errors:
        raise ValueError("; ".join(config_errors))

    policy = config["policy"]
    maximum = int(policy["max_items_per_source"])
    enabled = [s for s in config["sources"] if s.get("enabled", True)]
    attempted: list[str] = []
    failures: list[dict[str, str]] = []
    collected: list[dict[str, Any]] = []
    for source in enabled:
        attempted.append(source["id"])
        try:
            collected.extend(collect_source(source, maximum, timeout))
        except (OSError, ValueError, ET.ParseError, json.JSONDecodeError, urllib.error.URLError) as exc:
            failures.append({"source_id": source["id"], "error": type(exc).__name__})

    unique = deduplicate(collected)
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
    return {
        "version": 1,
        "run": {
            "mode": mode,
            "generated_at": utc_now(),
            "repository_revision": None,
            "analyzer": {"status": "unavailable", "provider": None, "model": None},
        },
        "sources": {
            "configured": [s["id"] for s in enabled],
            "attempted": attempted,
            "failures": failures,
        },
        "signals": unique,
        "recommendations": recommendations,
        "summary": {
            "signal_count": len(collected),
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
    if mode not in {"weekly", "monthly"}:
        errors.append("run.mode must be weekly or monthly")
    analyzer = (doc.get("run") or {}).get("analyzer") or {}
    if analyzer.get("status") not in {"available", "unavailable"}:
        errors.append("run.analyzer.status must be available or unavailable")
    sources = doc.get("sources") or {}
    configured = sources.get("configured") or []
    attempted = sources.get("attempted") or []
    if not configured or set(attempted) - set(configured):
        errors.append("attempted sources must be configured")
    signals = doc.get("signals") or []
    fingerprints = [s.get("fingerprint") for s in signals]
    if len(fingerprints) != len(set(fingerprints)) or any(not fp for fp in fingerprints):
        errors.append("signals must have unique non-empty fingerprints")
    for signal in signals:
        if not signal.get("title") or not signal.get("canonical_url") or not signal.get("source_id"):
            errors.append("each signal requires title, canonical_url and source_id")
        if signal.get("recurrence_count", 0) < 1:
            errors.append("signal recurrence_count must be >= 1")
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
