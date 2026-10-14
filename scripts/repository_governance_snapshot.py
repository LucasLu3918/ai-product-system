#!/usr/bin/env python3
"""Capture read-only GitHub ruleset and branch-protection evidence."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from aips_common import canonical_digest as _aips_canonical_digest

ROOT = Path(__file__).resolve().parents[1]


def canonical_digest(value: Any) -> str:
    return _aips_canonical_digest(value)


def repository_slug(remote: str) -> str | None:
    match = re.search(r"(?:github\.com[:/])([^/]+/[^/.]+?)(?:\.git)?$", remote.strip())
    return match.group(1) if match else None


def _required_checks(protection: dict[str, Any]) -> list[str]:
    checks = protection.get("required_status_checks") or {}
    contexts = {str(item) for item in checks.get("contexts") or []}
    contexts.update({str(item.get("context")) for item in checks.get("checks") or [] if item.get("context")})
    return sorted(contexts)


_HTTP_STATUS = re.compile(r"^HTTP/\S+\s+(\d{3})\b", re.MULTILINE)
_SAFE_TOKEN = re.compile(r"(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")
_BEARER = re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s,;]+")
_CREDENTIAL_URL = re.compile(r"https?://[^\s/@:]+:[^\s/@]+@", re.IGNORECASE)


def _safe_message(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    message = value.replace("\r", " ").replace("\n", " ")
    message = _SAFE_TOKEN.sub("[REDACTED]", message)
    message = _BEARER.sub(r"\1[REDACTED]", message)
    message = _CREDENTIAL_URL.sub("https://[REDACTED]@", message)
    return message[:500]


def parse_gh_response(endpoint: str, returncode: int, output: str, stderr: str = "") -> dict[str, Any]:
    """Extract bounded API evidence from `gh api --include` without retaining headers."""
    status_match = _HTTP_STATUS.search(output or "")
    http_status = int(status_match.group(1)) if status_match else None
    body = output or ""
    headers = ""
    if status_match:
        pieces = re.split(r"\r?\n\r?\n", body, maxsplit=1)
        headers = pieces[0] if pieces else ""
        body = pieces[1] if len(pieces) == 2 else ""
        # A paginated response can contain another status line after a body.
        body = re.split(r"\r?\nHTTP/\S+\s+\d{3}\b", body, maxsplit=1)[0]
    try:
        payload = json.loads(body) if body.strip() else None
    except json.JSONDecodeError:
        payload = None
    if returncode == 0 and http_status in (None, 200):
        return {"returncode": 0, "http_status": http_status, "payload": payload,
                "endpoint": endpoint, "error_class": None, "error_message": None}
    message = payload.get("message") if isinstance(payload, dict) else None
    if http_status == 401:
        error_class = "AUTHENTICATION"
    elif http_status == 403 and ("x-ratelimit-remaining: 0" in headers.lower() or
                                 "retry-after:" in headers.lower() or
                                 isinstance(message, str) and "rate limit" in message.lower()):
        error_class = "RATE_LIMITED"
    elif http_status == 403:
        error_class = "PERMISSION"
    elif http_status == 404:
        error_class = "NOT_FOUND"
    elif http_status == 429:
        error_class = "RATE_LIMITED"
    elif http_status is not None and http_status >= 500:
        error_class = "GITHUB_SERVER_ERROR"
    elif http_status is not None:
        error_class = "GITHUB_API_ERROR"
    else:
        error_class = "NETWORK_OR_CLI_ERROR"
        # stderr is not copied; only allowlisted classes are retained.
        hint = (stderr or "").lower()
        if any(term in hint for term in ("timed out", "timeout", "could not resolve",
                                         "connection refused", "connection reset",
                                         "temporary failure in name resolution")):
            error_class = "NETWORK"
        elif "http 401" in hint or "auth" in hint or "not logged" in hint:
            error_class = "AUTHENTICATION"
            message = "GitHub CLI authentication failed."
        elif "http 403" in hint or "forbidden" in hint or "resource not accessible" in hint:
            error_class = "PERMISSION"
        elif "http 404" in hint or "not found" in hint:
            error_class = "NOT_FOUND"
    return {"returncode": returncode, "http_status": http_status, "payload": None,
            "endpoint": endpoint, "error_class": error_class,
            "error_message": _safe_message(message)}


def build_snapshot(
    repository: str,
    branch: str,
    read_api: Callable[[str], Any],
    *,
    captured_at: str | None = None,
) -> dict[str, Any]:
    """Read both GitHub surfaces and retain UNKNOWN when either is incomplete."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must be an owner/name slug")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", branch):
        raise ValueError("branch must be a simple branch name")
    branch_path = quote(branch, safe="/")

    sources: dict[str, dict[str, Any]] = {}
    payloads: dict[str, Any] = {}
    endpoints = {
        "branch": f"repos/{repository}/branches/{branch_path}",
        "effective_rules": f"repos/{repository}/rules/branches/{branch_path}",
        "rulesets": f"repos/{repository}/rulesets?includes_parents=true&per_page=100",
        "branch_protection": f"repos/{repository}/branches/{branch_path}/protection",
    }
    for name, endpoint in endpoints.items():
        observed = read_api(endpoint)
        if isinstance(observed, dict) and "payload" in observed:
            status = observed.get("returncode", 1)
            http_status = observed.get("http_status")
            payload = observed.get("payload")
            error_class = observed.get("error_class")
            error_message = observed.get("error_message")
        else:
            # Backward-compatible fixture/consumer contract: (exit code, JSON body).
            status, output = observed
            http_status = None
            error_class = None if status == 0 else "NETWORK_OR_CLI_ERROR"
            error_message = None
            try:
                payload = json.loads(output) if status == 0 else None
            except (json.JSONDecodeError, TypeError):
                payload = None
        if name == "rulesets" and isinstance(payload, list) and all(isinstance(page, list) for page in payload):
            payload = [ruleset for page in payload for ruleset in page]
        expected_list = name in {"rulesets", "effective_rules"}
        valid_payload = isinstance(payload, list) if expected_list else isinstance(payload, dict)
        readable = status == 0 and valid_payload and (http_status in (None, 200))
        source_status = "READABLE" if readable else "UNKNOWN"
        if name == "branch_protection" and http_status == 404:
            # A 404 means no classic protection only after confirming the branch exists.
            source_status = "NOT_CONFIGURED"
        sources[name] = {"status": source_status, "endpoint": endpoint,
                         "exit_code": status if status else 0, "http_status": http_status,
                         "error_class": error_class, "error_message": error_message}
        if readable:
            payloads[name] = payload

    branch_exists = isinstance(payloads.get("branch"), dict)
    if not branch_exists:
        for name in ("branch_protection", "effective_rules"):
            source = sources[name]
            if source.get("http_status") == 404:
                source["status"] = "UNKNOWN"
                source["error_class"] = "BRANCH_OR_RESOURCE_NOT_FOUND"
    rulesets = payloads.get("rulesets")
    protection = payloads.get("branch_protection")
    effective_rules = payloads.get("effective_rules")
    complete = branch_exists and isinstance(effective_rules, list)
    classic_protection_configured = isinstance(protection, dict) and bool(protection)
    active_policy = bool(effective_rules) or classic_protection_configured
    bypass_actor_map = {
        json.dumps(actor, sort_keys=True, ensure_ascii=False): actor
        for ruleset in (rulesets or []) if isinstance(ruleset, dict)
        for actor in (ruleset.get("bypass_actors") or []) if isinstance(actor, dict)
    }
    normalized_protection = dict(protection or {})
    if protection:
        normalized_protection["required_checks"] = _required_checks(protection)
    snapshot = {
        "version": 1,
        "repository": repository,
        "branch": branch,
        "captured_at": captured_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_status": "COMPLETE" if complete else "UNKNOWN",
        "sources": sources,
        "branch_protection": normalized_protection,
        "rulesets": rulesets or [],
        "effective_rules": effective_rules or [],
        "branch_exists": branch_exists,
        "classic_protection_configured": classic_protection_configured,
        "protection_state": ("PROTECTED" if active_policy else "UNPROTECTED") if complete else "UNKNOWN",
        "evidence_level": "EFFECTIVE_RULES_CONFIRMED" if complete else "INCOMPLETE",
        "bypass_actors": [bypass_actor_map[key] for key in sorted(bypass_actor_map)],
        "source_complete": complete,
        "activation_authorized": False,
        "api_write_performed": False,
    }
    digest_content = {key: value for key, value in snapshot.items() if key != "captured_at"}
    snapshot["snapshot_digest"] = canonical_digest(digest_content)
    return snapshot


def query_github_api(root: Path, endpoint: str) -> dict[str, Any]:
    """Observe one GitHub API endpoint and paginate ruleset lists without retaining headers."""
    result = subprocess.run(["gh", "api", "--include", endpoint], cwd=root,
                            capture_output=True, text=True, timeout=20, check=False)
    observed = parse_gh_response(endpoint, result.returncode, result.stdout, result.stderr)
    if "/rulesets?" not in endpoint or not isinstance(observed.get("payload"), list):
        return observed
    rows = list(observed["payload"])
    page = 1
    while len(rows) == page * 100:
        page += 1
        paged_endpoint = endpoint + f"&page={page}"
        page_result = subprocess.run(["gh", "api", "--include", paged_endpoint], cwd=root,
                                     capture_output=True, text=True, timeout=20, check=False)
        page_observed = parse_gh_response(paged_endpoint, page_result.returncode,
                                          page_result.stdout, page_result.stderr)
        if page_observed.get("returncode") != 0 or not isinstance(page_observed.get("payload"), list):
            observed.update(payload=None, returncode=page_observed.get("returncode", 1),
                            http_status=page_observed.get("http_status"),
                            error_class=page_observed.get("error_class"),
                            error_message=page_observed.get("error_message"))
            return observed
        rows.extend(page_observed["payload"])
        if len(page_observed["payload"]) < 100:
            break
    observed["payload"] = rows
    return observed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", help="GitHub owner/name; inferred from origin when omitted")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--output", type=Path, help="Write the snapshot JSON to this path")
    args = parser.parse_args()
    repository = args.repository
    if not repository:
        remote = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT, capture_output=True, text=True, check=False)
        repository = repository_slug(remote.stdout) if remote.returncode == 0 else None
    if not repository:
        parser.error("cannot infer GitHub owner/name; pass --repository")

    def read_api(endpoint: str) -> dict[str, Any]:
        return query_github_api(ROOT, endpoint)

    snapshot = build_snapshot(repository, args.branch, read_api)
    rendered = json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if snapshot["source_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
