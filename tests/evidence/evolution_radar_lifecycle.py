#!/usr/bin/env python3
from __future__ import annotations

import copy
from pathlib import Path
import socket
import sys
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import evolution_analysis as analysis  # noqa: E402
import evolution_radar as radar  # noqa: E402
import evolution_radar_rollup as rollup  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_value_error(fn, message: str) -> None:
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(message)


def main() -> int:
    config = yaml.safe_load((ROOT / "config/evolution-sources.yaml").read_text(encoding="utf-8")) or {}
    require(not radar.validate_config(config), "real Evolution Radar source config must validate")
    enabled_sources = [s for s in config["sources"] if s.get("enabled", True)]
    community_sources = [s for s in enabled_sources if s.get("role") == "community"]
    require(len(enabled_sources) >= 10, "technology intelligence must retain community plus primary-source diversity")
    require(len(community_sources) >= 6, "at least six configured community sources required")
    require(config["policy"]["minimum_community_sources_when_available"] == 5, "five successful communities are the healthy weekly floor")
    require(config["policy"]["target_community_sources"] == 6, "six community sources are the configured resilience target")
    require(config["policy"]["max_items_per_source"] == 8, "per-source candidate bound must remain eight")
    require(config["policy"]["max_raw_signals"] == 50, "weekly global raw-signal cap must remain fifty")
    require(config["policy"]["public_only"] is True, "Evolution Radar sources must remain public-only")
    require(config["policy"]["credentials_in_repository"] is False, "source credentials must remain outside repository")
    require(config["policy"]["max_response_bytes"] == 2097152, "response byte cap must remain explicit")
    require(config["policy"]["max_redirects"] == 3, "redirect cap must remain explicit")

    for blocked_url in (
        "http://example.com/feed",
        "https://user:secret@example.com/feed",
        "https://localhost/feed",
        "https://127.0.0.1/feed",
        "https://10.0.0.1/feed",
        "https://172.16.0.1/feed",
        "https://192.168.1.1/feed",
        "https://169.254.169.254/latest/meta-data/",
        "https://[::1]/feed",
        "https://[fe80::1]/feed",
    ):
        expect_value_error(
            lambda url=blocked_url: radar.validate_public_url_syntax(url),
            f"non-public or credential-bearing URL must fail: {blocked_url}",
        )

    original_getaddrinfo = radar.socket.getaddrinfo

    def fake_getaddrinfo(host, port, type=0, proto=0):
        mapping = {
            "public.example": ["93.184.216.34"],
            "private.example": ["10.0.0.9"],
            "mixed.example": ["93.184.216.34", "192.168.1.8"],
        }
        if host == "missing.example":
            raise socket.gaierror("not found")
        addresses = mapping.get(host)
        if addresses is None:
            raise socket.gaierror("unexpected host")
        rows = []
        for address in addresses:
            family = socket.AF_INET6 if ":" in address else socket.AF_INET
            sockaddr = (address, port, 0, 0) if family == socket.AF_INET6 else (address, port)
            rows.append((family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr))
        return rows

    original_request_once = radar._request_once
    radar.socket.getaddrinfo = fake_getaddrinfo
    try:
        _, resolved = radar.resolve_public_destination("https://public.example/feed")
        require(resolved == ["93.184.216.34"], "public DNS resolution must return the pinned public address")
        expect_value_error(
            lambda: radar.resolve_public_destination("https://private.example/feed"),
            "hostname resolving only to private IP must fail closed",
        )
        expect_value_error(
            lambda: radar.resolve_public_destination("https://mixed.example/feed"),
            "hostname resolving to any private IP must fail closed",
        )
        expect_value_error(
            lambda: radar.resolve_public_destination("https://missing.example/feed"),
            "DNS resolution failure must fail closed",
        )

        def redirect_private(parsed, addresses, *, timeout, max_response_bytes):
            require(addresses == ["93.184.216.34"], "HTTP request must use the previously validated public address")
            return 302, {"location": "https://private.example/internal"}, b""

        radar._request_once = redirect_private
        expect_value_error(
            lambda: radar.fetch_bytes(
                "https://public.example/start",
                1.0,
                max_response_bytes=1024,
                max_redirects=3,
            ),
            "public-to-private redirect must fail before a second request",
        )

        def redirect_http(parsed, addresses, *, timeout, max_response_bytes):
            return 302, {"location": "http://public.example/plain"}, b""

        radar._request_once = redirect_http
        expect_value_error(
            lambda: radar.fetch_bytes(
                "https://public.example/start",
                1.0,
                max_response_bytes=1024,
                max_redirects=3,
            ),
            "HTTPS downgrade redirect must fail",
        )

        def redirect_loop(parsed, addresses, *, timeout, max_response_bytes):
            return 302, {"location": "/start"}, b""

        radar._request_once = redirect_loop
        expect_value_error(
            lambda: radar.fetch_bytes(
                "https://public.example/start",
                1.0,
                max_response_bytes=1024,
                max_redirects=3,
            ),
            "redirect loop must fail",
        )

        def redirect_chain(parsed, addresses, *, timeout, max_response_bytes):
            if parsed.path == "/one":
                return 302, {"location": "/two"}, b""
            if parsed.path == "/two":
                return 302, {"location": "/three"}, b""
            return 200, {}, b"ok"

        radar._request_once = redirect_chain
        expect_value_error(
            lambda: radar.fetch_bytes(
                "https://public.example/one",
                1.0,
                max_response_bytes=1024,
                max_redirects=1,
            ),
            "redirect chain beyond configured limit must fail",
        )
    finally:
        radar.socket.getaddrinfo = original_getaddrinfo
        radar._request_once = original_request_once

    class FakeResponse:
        def __init__(self, payload: bytes, declared: str | None = None):
            self.payload = payload
            self.declared = declared

        def getheader(self, name):
            if name == "Content-Length":
                return self.declared
            return None

        def read(self, size):
            return self.payload[:size]

    expect_value_error(
        lambda: radar._bounded_read(FakeResponse(b"x", declared="2049"), 2048),
        "declared oversized response must fail before unbounded read",
    )
    expect_value_error(
        lambda: radar._bounded_read(FakeResponse(b"x" * 2049), 2048),
        "streamed oversized response must fail after bounded max+1 read",
    )
    require(radar._bounded_read(FakeResponse(b"ok", declared="2"), 2048) == b"ok", "bounded response must succeed")

    original_collect = radar.collect_source

    def fake_collect(source, max_items, timeout, *, max_response_bytes, max_redirects):
        require(max_items == 8, "collector must pass the configured bounded item count")
        require(timeout > 0, "collector must use a finite positive timeout")
        require(max_response_bytes == 2097152, "collector must enforce configured response cap")
        require(max_redirects == 3, "collector must enforce configured redirect cap")
        source_id = source["id"]
        if source_id in {config["sources"][0]["id"], config["sources"][1]["id"]}:
            return [{
                "fingerprint": radar.signal_fingerprint("Shared signal", "https://example.test/shared?utm_source=x"),
                "title": "Shared signal",
                "canonical_url": "https://example.test/shared",
                "source_id": source_id,
                "source_role": source["role"],
                "published_at": "2026-09-01",
            }]
        return [{
            "fingerprint": radar.signal_fingerprint(f"Signal {source_id}", f"https://example.test/{source_id}"),
            "title": f"Signal {source_id}",
            "canonical_url": f"https://example.test/{source_id}",
            "source_id": source_id,
            "source_role": source["role"],
            "published_at": "2026-09-02",
        }]

    radar.collect_source = fake_collect
    try:
        weekly = radar.build_evidence(config, mode="weekly", timeout=1.0)
    finally:
        radar.collect_source = original_collect

    require(not radar.validate_evidence(weekly), "weekly evidence must validate")
    require(weekly["summary"]["signal_count"] == 10, "one bounded item from each configured source expected")
    require(weekly["summary"]["deduplicated_count"] == 9, "cross-source duplicate must collapse")
    require(weekly["summary"]["global_signal_limit"] == 50, "weekly evidence must record the global signal budget")
    require(weekly["summary"]["global_signal_limit_applied"] is False, "small fixture must not claim global truncation")
    require(weekly["sources"]["community_coverage"]["status"] == "HEALTHY", "six successful community fixtures must satisfy coverage")
    require(weekly["sources"]["community_coverage"]["successful"] == 6, "all six community fixtures must be counted")
    shared = next(s for s in weekly["signals"] if s["title"] == "Shared signal")
    require(shared["recurrence_count"] == 2, "duplicate recurrence must be recorded")
    require(shared["source_roles"] == ["community"], "community duplicate provenance must be retained")
    require(shared["verification_status"] == "DISCOVERY_ONLY", "community-only signal must remain discovery evidence")
    require(all(r["state"] == "ANALYSIS_PENDING" for r in weekly["recommendations"]), "no analyzer must not infer suitability")
    require(weekly["summary"]["actionable_count"] == 0, "no analyzer must not fabricate actionable recommendations")
    require(weekly["summary"]["zero_recommendations_valid"] is True, "zero recommendations must remain valid")

    synthetic = []
    for source in enabled_sources:
        for index in range(8):
            synthetic.append({
                "fingerprint": f"{source['id']}-{index}",
                "title": f"{source['id']} {index}",
                "canonical_url": f"https://example.test/{source['id']}/{index}",
                "source_id": source["id"],
                "source_role": source["role"],
                "published_at": None,
            })
    bounded = radar.bound_signals_by_source(synthetic, [s["id"] for s in enabled_sources], 50)
    require(len(bounded) == 50, "global research budget must cap raw signals at fifty")
    per_source = {source["id"]: 0 for source in enabled_sources}
    for item in bounded:
        per_source[item["source_id"]] += 1
    require(set(per_source.values()) == {5}, "round-robin global cap must preserve source diversity")

    corroborated = radar.deduplicate([
        {
            "fingerprint": "sha256:corroborated",
            "title": "Corroborated signal",
            "canonical_url": "https://example.test/corroborated",
            "source_id": "community-a",
            "source_role": "community",
            "published_at": None,
        },
        {
            "fingerprint": "sha256:corroborated",
            "title": "Corroborated signal",
            "canonical_url": "https://example.test/corroborated",
            "source_id": "primary-a",
            "source_role": "primary",
            "published_at": None,
        },
    ])[0]
    require(corroborated["verification_status"] == "PRIMARY_CORROBORATED", "cross-role recurrence must record primary corroboration")
    require(weekly["authority"] == {
        "code_change_authorized": False,
        "branch_or_pr_authorized": False,
        "merge_authorized": False,
        "release_authorized": False,
        "human_decision_required": True,
    }, "research authority boundary must be fail-closed")

    body1 = rollup.issue_markdown(weekly)
    require(rollup.EVIDENCE_START in body1 and rollup.EVIDENCE_END in body1, "Issue must carry machine-readable evidence markers")
    parsed = rollup.extract_evidence(body1)
    require(parsed is not None and not radar.validate_evidence(parsed), "Issue evidence must round-trip")

    weekly2 = copy.deepcopy(weekly)
    weekly2["run"]["generated_at"] = "2026-09-08T01:00:00Z"
    body2 = rollup.issue_markdown(weekly2)
    old_weekly = copy.deepcopy(weekly)
    old_weekly["run"]["generated_at"] = "2026-08-25T01:00:00Z"
    old_body = rollup.issue_markdown(old_weekly)
    issues = [
        {"title": "Evolution Radar [weekly] 2026-09-01", "created_at": "2026-09-01T01:05:00Z", "body": body1},
        {"title": "Evolution Radar [weekly] 2026-09-08", "created_at": "2026-09-08T01:05:00Z", "body": body2},
        {"title": "Evolution Radar [weekly] 2026-08-25", "created_at": "2026-08-25T01:05:00Z", "body": old_body},
        {"title": "Unrelated issue", "created_at": "2026-09-09T01:05:00Z", "body": body1},
        {"title": "Evolution Radar [weekly] malformed", "created_at": "2026-09-15T01:05:00Z", "body": "no evidence"},
    ]
    require(rollup.flatten_issue_pages(issues) == issues, "single-page issue arrays must remain supported")
    paged = rollup.flatten_issue_pages([issues[:2], issues[2:]])
    require(paged == issues, "paginated gh api --slurp pages must flatten without losing evidence")
    try:
        rollup.flatten_issue_pages([[issues[0]], ["invalid"]])
    except ValueError:
        pass
    else:
        raise AssertionError("invalid paginated issue payload must fail closed")

    monthly = rollup.monthly_rollup(paged, config, period="2026-09")
    require(monthly["run"]["period"] == "2026-09", "monthly evidence must record the reviewed calendar period")
    require(monthly["run"]["weekly_evidence_count"] == 2, "monthly rollup must consume only weekly evidence from the requested calendar period")
    require(monthly["summary"]["signal_count"] == 18, "out-of-period weekly evidence must be excluded")
    require(monthly["summary"]["deduplicated_count"] == 9, "monthly rollup must deduplicate recurring signals")
    require(all(s["recurrence_count"] >= 2 for s in monthly["signals"]), "monthly rollup must accumulate recurrence")
    require(all(r["state"] == "ANALYSIS_PENDING" for r in monthly["recommendations"]), "monthly rollup must preserve analyzer truthfulness")
    require(not radar.validate_evidence(monthly), "monthly evidence must validate")

    try:
        rollup.monthly_rollup(issues, config, period="2026/09")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid monthly period format must fail closed")


    monthly_july = copy.deepcopy(monthly)
    monthly_july["run"]["period"] = "2026-07"
    monthly_august = copy.deepcopy(monthly)
    monthly_august["run"]["period"] = "2026-08"
    monthly_september = copy.deepcopy(monthly)
    monthly_september["run"]["period"] = "2026-09"
    monthly_april = copy.deepcopy(monthly)
    monthly_april["run"]["period"] = "2026-04"
    quarterly_issues = [
        {"title": "Evolution Radar [monthly] 2026-08-01", "created_at": "2026-08-01T01:35:00Z", "body": rollup.issue_markdown(monthly_july)},
        {"title": "Evolution Radar [monthly] 2026-09-01", "created_at": "2026-09-01T01:35:00Z", "body": rollup.issue_markdown(monthly_august)},
        {"title": "Evolution Radar [monthly] 2026-10-01", "created_at": "2026-10-01T01:35:00Z", "body": rollup.issue_markdown(monthly_september)},
        {"title": "Evolution Radar [monthly] 2026-05-01", "created_at": "2026-05-01T01:35:00Z", "body": rollup.issue_markdown(monthly_april)},
        {"title": "Evolution Radar [monthly] malformed", "created_at": "2026-09-15T01:35:00Z", "body": "no evidence"},
    ]
    quarterly = rollup.quarterly_rollup(quarterly_issues, config, period="2026-Q3")
    require(quarterly["run"]["period"] == "2026-Q3", "quarterly evidence must record the reviewed quarter")
    require(quarterly["run"]["months_reviewed"] == ["2026-07", "2026-08", "2026-09"], "quarterly review must bind the exact calendar months")
    require(quarterly["run"]["monthly_evidence_count"] == 3, "quarterly rollup must consume only monthly evidence from the requested quarter")
    require(quarterly["summary"]["deduplicated_count"] == monthly["summary"]["deduplicated_count"], "quarterly rollup must deterministically deduplicate recurring signals")
    require(all(s["recurrence_count"] >= 6 for s in quarterly["signals"]), "quarterly rollup must accumulate recurrence across monthly evidence")
    require(all(r["state"] == "ANALYSIS_PENDING" for r in quarterly["recommendations"]), "quarterly rollup must not promote monthly semantic states")
    require(quarterly["summary"]["actionable_count"] == 0, "quarterly deterministic review must not manufacture actionable recommendations")
    require(not radar.validate_evidence(quarterly), "quarterly evidence must validate")
    quarterly_body = rollup.issue_markdown(quarterly)
    require("Review quarter: 2026-Q3" in quarterly_body, "quarterly Human review issue must expose the bound quarter")
    require("Monthly evidence bundles reviewed: 3" in quarterly_body, "quarterly Human review issue must expose evidence count")

    try:
        rollup.quarterly_rollup(quarterly_issues, config, period="2026-Q5")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid quarterly period format must fail closed")

    bad_config = copy.deepcopy(config)
    bad_config["sources"] = bad_config["sources"][:4]
    require(radar.validate_config(bad_config), "fewer than five configured sources must fail")

    bad_community_target = copy.deepcopy(config)
    bad_community_target["sources"][0]["role"] = "primary"
    require(radar.validate_config(bad_community_target), "fewer than six configured community sources must fail")

    bad_raw_budget = copy.deepcopy(config)
    bad_raw_budget["policy"]["max_raw_signals"] = 4
    require(radar.validate_config(bad_raw_budget), "global raw budget below per-source bound must fail")

    bad_public_policy = copy.deepcopy(config)
    bad_public_policy["policy"]["public_only"] = False
    require(radar.validate_config(bad_public_policy), "public_only=false must fail config validation")

    bad_credentials_policy = copy.deepcopy(config)
    bad_credentials_policy["policy"]["credentials_in_repository"] = True
    require(radar.validate_config(bad_credentials_policy), "credentials_in_repository=true must fail config validation")

    bad_private_source = copy.deepcopy(config)
    bad_private_source["sources"][0]["url"] = "https://127.0.0.1/feed"
    require(radar.validate_config(bad_private_source), "private literal source must fail config validation")

    bad_authority = copy.deepcopy(weekly)
    bad_authority["authority"]["branch_or_pr_authorized"] = True
    require(radar.validate_evidence(bad_authority), "research must fail if it claims implementation publication authority")

    bad_adopt = copy.deepcopy(weekly)
    bad_adopt["recommendations"][0]["state"] = "ADOPT"
    require(radar.validate_evidence(bad_adopt), "unavailable analyzer must not emit ADOPT")

    bad_duplicate = copy.deepcopy(weekly)
    bad_duplicate["signals"].append(copy.deepcopy(bad_duplicate["signals"][0]))
    require(radar.validate_evidence(bad_duplicate), "duplicate fingerprints must fail evidence validation")

    analyzer_config = yaml.safe_load((ROOT / "config/evolution-analyzer.yaml").read_text(encoding="utf-8")) or {}
    require((analyzer_config.get("selection") or {}).get("fallback") == "handoff", "semantic analyzer fallback must be provider-neutral handoff")
    require((analyzer_config.get("adapter") or {}).get("optional") is True, "OpenAI adapter must be optional")
    require((analyzer_config.get("handoff") or {}).get("credential_required") is False, "handoff must not require model API credentials")
    local_config = analyzer_config.get("local_preanalysis") or {}
    require(local_config.get("credential_required") is False, "local preanalysis must require no credential")
    require(local_config.get("external_network_required") is False, "local preanalysis must require no extra network")
    require(local_config.get("preserve_semantic_state") == "ANALYSIS_PENDING", "local preanalysis must preserve semantic pending state")
    budget = local_config.get("selection_budget") or {}
    require(budget.get("shortlist_max") == 12, "Human shortlist budget must remain twelve")
    require(budget.get("semantic_analysis_max") == 10, "semantic analysis budget must remain ten")
    require(budget.get("actionable_recommendations_max") == 5, "actionable recommendation budget must remain five")

    capability_map = yaml.safe_load((ROOT / "references/evolution/CAPABILITY_MAP.yaml").read_text(encoding="utf-8")) or {}
    triage_evidence = copy.deepcopy(weekly)
    triage_titles = [
        "Agent authorization anomaly detection for runtime tools",
        "Agent authorization anomaly detection runtime tools",
        "Retrieval context embedding reliability evaluation",
        "Marketing conference posters and event planning",
    ] + [
        f"General community discussion {index}"
        for index in range(max(0, len(triage_evidence["signals"]) - 4))
    ]
    for signal, title in zip(triage_evidence["signals"], triage_titles, strict=True):
        signal["title"] = title
    triage = analysis.build_local_preanalysis(triage_evidence, analyzer_config, capability_map)
    require(
        not analysis.validate_local_preanalysis(triage_evidence, analyzer_config, capability_map, triage),
        "deterministic local preanalysis must validate",
    )
    require(
        triage == analysis.build_local_preanalysis(triage_evidence, analyzer_config, capability_map),
        "identical local-preanalysis inputs must produce identical output",
    )
    require(triage["execution"]["semantic_suitability_inferred"] is False, "local preanalysis must not infer suitability")
    require(triage["execution"]["recommendation_state_mutated"] is False, "local preanalysis must not mutate semantic state")
    require(triage["execution"]["credential_required"] is False, "local preanalysis must remain credential-free")
    require(triage["execution"]["external_network_required"] is False, "local preanalysis must not require extra network")
    require(triage["summary"]["near_duplicate_groups"] == 1, "two near-identical agent titles must form one deterministic cluster")
    require(triage["summary"]["priority_counts"]["HIGH"] >= 2, "high-signal engineering titles should reach HIGH Human review priority")
    require(triage["summary"]["priority_counts"]["LOW"] >= 1, "unmatched titles should remain LOW Human review priority")
    require(
        all(item["state"] == "ANALYSIS_PENDING" for item in triage_evidence["recommendations"]),
        "local preanalysis must leave semantic recommendations ANALYSIS_PENDING",
    )
    require(
        all("state" not in item and "decision" not in item and "recommendation" not in item for item in triage["signals"]),
        "local preanalysis annotations must not contain semantic decision fields",
    )
    queue = triage["review_queue"]
    require(len(queue["shortlist_signal_fingerprints"]) <= 12, "deterministic shortlist must be bounded")
    require(len(queue["semantic_signal_fingerprints"]) <= 10, "semantic candidate queue must be bounded")
    require(queue["actionable_recommendations_limit"] == 5, "deep/actionable recommendation budget must be five")

    package = analysis.build_analysis_package(triage_evidence, capability_map, triage)
    require(package["scope"]["selected_signal_count"] == len(queue["semantic_signal_fingerprints"]), "semantic package must use deterministic queue")
    require(package["scope"]["selected_signal_count"] <= 10, "semantic package must not exceed ten candidates")
    require(package["scope"]["max_actionable_recommendations"] == 5, "semantic package must carry actionable budget")
    package_ids = package["scope"]["selected_signal_fingerprints"]
    provider_result = {"recommendations": [
        {
            "signal_fingerprint": fp,
            "state": "HOLD",
            "aips_current_state": "Evidence is available for review.",
            "gap": "",
            "benefit": "Bounded review avoids unnecessary adoption.",
            "cost_complexity": "Low.",
            "reliability_security": "No authority change.",
            "maturity": "unknown",
            "confidence": 0.5,
            "uncertainty": "Primary verification may still be required.",
            "example": "Keep as research evidence.",
            "reuse_extension_path": [],
            "evidence_refs": ["https://example.test/evidence"],
            "architecture_diagram_review_if_adopted": False,
        }
        for fp in package_ids
    ]}
    scoped_analysis = analysis.finalize_provider_result(
        triage_evidence,
        provider_result,
        provider="test-provider",
        model="test-model",
        analyzed_at="2026-09-20T00:00:00Z",
        package=package,
    )
    scoped_evidence = analysis.apply_analysis(triage_evidence, scoped_analysis)
    require(scoped_evidence["summary"]["semantic_analyzed_count"] == len(package_ids), "partial semantic coverage count must be explicit")
    require(scoped_evidence["summary"]["semantic_pending_count"] == len(triage_evidence["signals"]) - len(package_ids), "unselected signals must remain pending")
    require(scoped_evidence["run"]["analyzer"]["coverage"] in {"FULL", "PARTIAL"}, "semantic coverage must be explicit")

    community_fp = next(
        signal["fingerprint"]
        for signal in triage_evidence["signals"]
        if "community" in (signal.get("source_roles") or [])
        and "primary" not in (signal.get("source_roles") or [])
        and signal["fingerprint"] in package_ids
    )
    unsafe_adopt = copy.deepcopy(provider_result)
    for recommendation in unsafe_adopt["recommendations"]:
        if recommendation["signal_fingerprint"] == community_fp:
            recommendation["state"] = "ADOPT"
            recommendation["gap"] = "Would otherwise be adopted without primary corroboration."
    expect_value_error(
        lambda: analysis.finalize_provider_result(
            triage_evidence,
            unsafe_adopt,
            provider="test-provider",
            model="test-model",
            analyzed_at="2026-09-20T00:00:00Z",
            package=package,
        ),
        "community-only discovery evidence must not directly produce ADOPT",
    )
    preanalysis_markdown = analysis.preanalysis_markdown(triage)
    extracted_preanalysis = analysis.extract_preanalysis(preanalysis_markdown)
    require(extracted_preanalysis == triage, "preanalysis markdown must round-trip exact deterministic evidence")

    tampered = copy.deepcopy(triage)
    tampered["execution"]["semantic_suitability_inferred"] = True
    require(
        analysis.validate_local_preanalysis(triage_evidence, analyzer_config, capability_map, tampered),
        "semantic-suitability claim must fail local-preanalysis validation",
    )
    credentialized = copy.deepcopy(analyzer_config)
    credentialized["local_preanalysis"]["credential_required"] = True
    require(
        analysis.validate_local_preanalysis_config(credentialized, capability_map),
        "local preanalysis must reject credential-required configuration",
    )

    workflow = (ROOT / ".github/workflows/evolution-radar.yml").read_text(encoding="utf-8")
    for required in (
        'cron: "0 1 * * 1"',
        'cron: "30 1 1 * *"',
        "contents: read",
        "issues: write",
        "gh issue create",
        "monthly-rollup",
        "--period",
        "gh api --paginate --slurp",
        "semantic_provider:",
        "Build deterministic local pre-analysis",
        "evolution_analysis.py preanalyze",
        "preanalysis-validate",
        "evolution-local-preanalysis.md",
        "--preanalysis evolution-local-preanalysis.md",
        "--preanalysis evolution-local-preanalysis.yaml",
        "--package evolution-analysis-package.yaml",
        "Build provider-neutral semantic handoff",
        "--handoff evolution-analysis-handoff.md",
        'selected="handoff"',
    ):
        require(required in workflow, f"workflow missing contract: {required}")
    for forbidden in ("contents: write", "pull-requests: write", "git push", "gh pr create", "gh pr merge", "releases: write"):
        require(forbidden not in workflow, f"workflow must not gain implementation authority: {forbidden}")

    with tempfile.TemporaryDirectory() as tmp:
        evidence = Path(tmp) / "evidence.yaml"
        issue_body = Path(tmp) / "issue.md"
        evidence.write_text(yaml.safe_dump(weekly, sort_keys=False), encoding="utf-8")
        require(not radar.validate_evidence(yaml.safe_load(evidence.read_text(encoding="utf-8"))), "serialized evidence must validate")
        handoff = "## Evolution Radar — Provider-Neutral Semantic Analysis Handoff\n\n- Analysis package digest: `sha256:test`"
        issue_body.write_text(rollup.issue_markdown(weekly, handoff, preanalysis_markdown), encoding="utf-8")
        require(issue_body.stat().st_size > 0, "Human review artifact must be non-empty")
        issue_text = issue_body.read_text(encoding="utf-8")
        require("Deterministic Local Pre-analysis" in issue_text, "Issue must carry credential-free local preanalysis")
        require("Provider-Neutral Semantic Analysis Handoff" in issue_text, "Issue must carry provider-neutral analysis handoff")

    print("EVOLUTION RADAR LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
