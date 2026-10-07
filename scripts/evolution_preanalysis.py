"""Deterministic, provider-neutral Evolution local pre-analysis."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

import yaml
from evolution_radar import validate_evidence

PREANALYSIS_START = "<!-- AIPS_EVOLUTION_PREANALYSIS_START -->"
PREANALYSIS_END = "<!-- AIPS_EVOLUTION_PREANALYSIS_END -->"

def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def evidence_digest(evidence: dict[str, Any]) -> str:
    return canonical_digest(evidence)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")



def _normalized_rule_text(value: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value).lower()))


def _title_tokens(title: str, stopwords: set[str]) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", title.lower()) if token and token not in stopwords}


def validate_local_preanalysis_config(analyzer_config: dict[str, Any], capability_map: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    local = analyzer_config.get("local_preanalysis") or {}
    if local.get("version") != 1:
        errors.append("local_preanalysis.version must be 1")
    if local.get("enabled") is not True:
        errors.append("local_preanalysis.enabled must be true")
    if local.get("mode") != "deterministic_title_metadata_only":
        errors.append("local_preanalysis.mode must remain deterministic_title_metadata_only")
    if local.get("credential_required") is not False:
        errors.append("local preanalysis must not require a credential")
    if local.get("external_network_required") is not False:
        errors.append("local preanalysis must not require external network")
    if local.get("preserve_semantic_state") != "ANALYSIS_PENDING":
        errors.append("local preanalysis must preserve ANALYSIS_PENDING semantic state")

    near = local.get("near_duplicate") or {}
    threshold = near.get("jaccard_threshold")
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or not 0 < float(threshold) <= 1:
        errors.append("near_duplicate.jaccard_threshold must be in (0, 1]")
    minimum_shared = near.get("minimum_shared_terms")
    if not isinstance(minimum_shared, int) or isinstance(minimum_shared, bool) or minimum_shared < 1:
        errors.append("near_duplicate.minimum_shared_terms must be >= 1")

    priority = local.get("review_priority") or {}
    high = priority.get("high_min_score")
    medium = priority.get("medium_min_score")
    if not isinstance(high, int) or isinstance(high, bool) or not isinstance(medium, int) or isinstance(medium, bool):
        errors.append("review priority thresholds must be integers")
    elif high <= medium or medium < 1:
        errors.append("review priority thresholds must satisfy high > medium >= 1")
    for key in ("recurrence_bonus_max", "capability_bonus_max", "evidence_bonus_max"):
        value = priority.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"review_priority.{key} must be a non-negative integer")

    budget = local.get("selection_budget") or {}
    shortlist_max = budget.get("shortlist_max")
    semantic_max = budget.get("semantic_analysis_max")
    actionable_max = budget.get("actionable_recommendations_max")
    for key, value in (
        ("shortlist_max", shortlist_max),
        ("semantic_analysis_max", semantic_max),
        ("actionable_recommendations_max", actionable_max),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value < 1 or value > 50:
            errors.append(f"selection_budget.{key} must be an integer from 1 to 50")
    if all(isinstance(v, int) and not isinstance(v, bool) for v in (shortlist_max, semantic_max, actionable_max)):
        if semantic_max > shortlist_max:
            errors.append("selection_budget.semantic_analysis_max must be <= shortlist_max")
        if actionable_max > semantic_max:
            errors.append("selection_budget.actionable_recommendations_max must be <= semantic_analysis_max")

    stopwords = local.get("stopwords")
    if not isinstance(stopwords, list) or not all(isinstance(x, str) and x.strip() for x in stopwords):
        errors.append("local_preanalysis.stopwords must be a string list")

    if capability_map.get("version") != 1 or not isinstance(capability_map.get("capabilities"), list):
        errors.append("capability map must be version 1 with a capabilities list")
        capability_ids: set[str] = set()
    else:
        capability_ids = {
            str(item.get("id"))
            for item in capability_map.get("capabilities") or []
            if isinstance(item, dict) and item.get("id")
        }

    categories = local.get("categories")
    if not isinstance(categories, list) or not categories:
        errors.append("local_preanalysis.categories must be non-empty")
        return errors

    seen: set[str] = set()
    for category in categories:
        if not isinstance(category, dict):
            errors.append("each local preanalysis category must be a mapping")
            continue
        category_id = str(category.get("id") or "").strip()
        if not category_id or category_id in seen:
            errors.append("local preanalysis category ids must be unique and non-empty")
        seen.add(category_id)
        weight = category.get("weight")
        if not isinstance(weight, int) or isinstance(weight, bool) or not 1 <= weight <= 10:
            errors.append(f"{category_id or '<unknown>'}: weight must be an integer from 1 to 10")
        terms = category.get("terms")
        if not isinstance(terms, list) or not terms or not all(isinstance(x, str) and _normalized_rule_text(x) for x in terms):
            errors.append(f"{category_id or '<unknown>'}: terms must be non-empty strings")
        refs = category.get("capability_ids")
        if not isinstance(refs, list) or not refs or not all(isinstance(x, str) and x.strip() for x in refs):
            errors.append(f"{category_id or '<unknown>'}: capability_ids must be non-empty strings")
        else:
            missing = sorted(set(refs) - capability_ids)
            if missing:
                errors.append(f"{category_id or '<unknown>'}: unknown capability ids: {', '.join(missing)}")
    return errors

def _near_duplicate_membership(signals: list[dict[str, Any]], local: dict[str, Any]) -> dict[str, tuple[str | None, int]]:
    near = local.get("near_duplicate") or {}
    if near.get("enabled") is not True or len(signals) < 2:
        return {str(s["fingerprint"]): (None, 1) for s in signals}
    stopwords = {str(x).lower() for x in local.get("stopwords") or []}
    token_sets = [_title_tokens(str(signal.get("title") or ""), stopwords) for signal in signals]
    parent = list(range(len(signals)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        lroot, rroot = find(left), find(right)
        if lroot != rroot:
            parent[max(lroot, rroot)] = min(lroot, rroot)

    threshold = float(near["jaccard_threshold"])
    minimum_shared = int(near["minimum_shared_terms"])
    for left in range(len(signals)):
        for right in range(left + 1, len(signals)):
            shared = token_sets[left] & token_sets[right]
            union_set = token_sets[left] | token_sets[right]
            if len(shared) >= minimum_shared and union_set and len(shared) / len(union_set) >= threshold:
                union(left, right)

    groups: dict[int, list[int]] = {}
    for index in range(len(signals)):
        groups.setdefault(find(index), []).append(index)

    membership: dict[str, tuple[str | None, int]] = {}
    for indexes in groups.values():
        fingerprints = sorted(str(signals[index]["fingerprint"]) for index in indexes)
        group_id = None if len(indexes) == 1 else "near-" + canonical_digest(fingerprints).split(":", 1)[1][:16]
        for index in indexes:
            membership[str(signals[index]["fingerprint"])] = (group_id, len(indexes))
    return membership


def _build_review_queue(annotations: list[dict[str, Any]], local: dict[str, Any]) -> dict[str, Any]:
    budget = local["selection_budget"]
    ranked = sorted(
        annotations,
        key=lambda item: (-int(item.get("review_score") or 0), str(item.get("signal_fingerprint") or "")),
    )
    shortlist = ranked[: int(budget["shortlist_max"])]
    semantic: list[str] = []
    seen_groups: set[str] = set()
    for item in shortlist:
        group = item.get("near_duplicate_group")
        if group and str(group) in seen_groups:
            continue
        if group:
            seen_groups.add(str(group))
        semantic.append(str(item["signal_fingerprint"]))
        if len(semantic) >= int(budget["semantic_analysis_max"]):
            break
    return {
        "shortlist_limit": int(budget["shortlist_max"]),
        "semantic_analysis_limit": int(budget["semantic_analysis_max"]),
        "actionable_recommendations_limit": int(budget["actionable_recommendations_max"]),
        "shortlist_signal_fingerprints": [str(item["signal_fingerprint"]) for item in shortlist],
        "semantic_signal_fingerprints": semantic,
    }


def _review_exclusion_reasons(
    annotations: list[dict[str, Any]], local: dict[str, Any], queue: dict[str, Any]
) -> dict[str, list[str]]:
    """Attribute only deterministic shortlist and semantic-queue exclusions."""
    shortlist = set(queue["shortlist_signal_fingerprints"])
    semantic = set(queue["semantic_signal_fingerprints"])
    semantic_limit = int(queue["semantic_analysis_limit"])
    reasons: dict[str, list[str]] = {}
    for item in annotations:
        fingerprint = str(item["signal_fingerprint"])
        codes: list[str] = []
        if not item.get("category_ids"):
            codes.append("NO_CATEGORY_MATCH")
        if item.get("review_priority") == "LOW":
            codes.append("LOW_PRIORITY")
        if fingerprint not in shortlist:
            codes.append("SHORTLIST_CAP")
        elif fingerprint not in semantic:
            if item.get("near_duplicate_group") and any(
                other.get("near_duplicate_group") == item.get("near_duplicate_group")
                and str(other.get("signal_fingerprint")) in semantic
                for other in annotations
            ):
                codes.append("DUPLICATE_SUPPRESSED")
            elif len(semantic) >= semantic_limit:
                codes.append("SEMANTIC_CAP")
        reasons[fingerprint] = codes
    return reasons


def build_local_preanalysis(
    evidence: dict[str, Any],
    analyzer_config: dict[str, Any],
    capability_map: dict[str, Any],
) -> dict[str, Any]:
    evidence_errors = validate_evidence(evidence)
    if evidence_errors:
        raise ValueError("invalid evidence: " + "; ".join(evidence_errors))
    config_errors = validate_local_preanalysis_config(analyzer_config, capability_map)
    if config_errors:
        raise ValueError("invalid local preanalysis config: " + "; ".join(config_errors))

    local = analyzer_config["local_preanalysis"]
    signals = copy.deepcopy(evidence.get("signals") or [])
    membership = _near_duplicate_membership(signals, local)
    priority = local["review_priority"]
    annotations: list[dict[str, Any]] = []
    category_counts: dict[str, int] = {str(item["id"]): 0 for item in local["categories"]}
    priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for signal in signals:
        normalized_title = " " + _normalized_rule_text(signal.get("title") or "") + " "
        matched_categories: list[str] = []
        matched_terms: set[str] = set()
        matched_capabilities: set[str] = set()
        category_score = 0
        for category in local["categories"]:
            category_terms = []
            for raw_term in category["terms"]:
                term = _normalized_rule_text(raw_term)
                if term and f" {term} " in normalized_title:
                    category_terms.append(term)
            if not category_terms:
                continue
            category_id = str(category["id"])
            matched_categories.append(category_id)
            matched_terms.update(category_terms)
            matched_capabilities.update(str(x) for x in category["capability_ids"])
            category_score += int(category["weight"])
            category_counts[category_id] += 1

        recurrence_count = int(signal.get("recurrence_count") or 1)
        recurrence_bonus = min(max(recurrence_count - 1, 0), int(priority["recurrence_bonus_max"]))
        capability_bonus = min(len(matched_capabilities), int(priority["capability_bonus_max"]))
        evidence_level = int(signal.get("evidence_level") or 0)
        evidence_bonus = min(evidence_level, int(priority["evidence_bonus_max"]))
        score = category_score + recurrence_bonus + capability_bonus + evidence_bonus
        if score >= int(priority["high_min_score"]):
            review_priority = "HIGH"
        elif score >= int(priority["medium_min_score"]):
            review_priority = "MEDIUM"
        else:
            review_priority = "LOW"
        priority_counts[review_priority] += 1

        fingerprint = str(signal["fingerprint"])
        group_id, group_count = membership[fingerprint]
        annotations.append({
            "signal_fingerprint": fingerprint,
            "title": str(signal.get("title") or ""),
            "source_id": str(signal.get("source_id") or ""),
            "source_roles": list(signal.get("source_roles") or ([signal.get("source_role")] if signal.get("source_role") else ["legacy"])),
            "verification_status": str(signal.get("verification_status") or "LEGACY_UNVERIFIED"),
            "evidence_level": int(signal.get("evidence_level") or 0),
            "evidence_strength": str(signal.get("evidence_strength") or "DISCOVERY"),
            "primary_source_count": int(signal.get("primary_source_count") or 0),
            "community_source_count": int(signal.get("community_source_count") or 0),
            "recurrence_count": recurrence_count,
            "category_ids": sorted(matched_categories),
            "matched_terms": sorted(matched_terms),
            "capability_ids": sorted(matched_capabilities),
            "review_score": score,
            "review_priority": review_priority,
            "near_duplicate_group": group_id,
            "near_duplicate_count": group_count,
        })

    review_queue = _build_review_queue(annotations, local)
    exclusion_reasons = _review_exclusion_reasons(annotations, local, review_queue)
    reason_counts: dict[str, int] = {}
    for annotation in annotations:
        codes = exclusion_reasons[str(annotation["signal_fingerprint"])]
        annotation["exclusion_reasons"] = codes
        annotation["selection_status"] = "EXCLUDED" if codes else "SELECTED"
        for code in codes:
            reason_counts[code] = reason_counts.get(code, 0) + 1
    near_groups = len({item["near_duplicate_group"] for item in annotations if item["near_duplicate_group"] is not None})
    return {
        "version": 1,
        "mode": "DETERMINISTIC_PREANALYSIS",
        "baseline": {
            "repository_revision": (evidence.get("run") or {}).get("repository_revision"),
            "evidence_digest": evidence_digest(evidence),
            "config_digest": canonical_digest(local),
            "capability_map_digest": canonical_digest(capability_map),
        },
        "execution": {
            "input_scope": "title_and_evidence_metadata_only",
            "credential_required": False,
            "external_network_required": False,
            "semantic_suitability_inferred": False,
            "recommendation_state_mutated": False,
            "preserved_semantic_state": "ANALYSIS_PENDING",
        },
        "summary": {
            "signal_count": len(annotations),
            "priority_counts": priority_counts,
            "category_counts": category_counts,
            "near_duplicate_groups": near_groups,
            "shortlist_count": len(review_queue["shortlist_signal_fingerprints"]),
            "semantic_candidate_count": len(review_queue["semantic_signal_fingerprints"]),
            "actionable_recommendations_limit": review_queue["actionable_recommendations_limit"],
            "exclusion_reason_counts": dict(sorted(reason_counts.items())),
        },
        "review_queue": review_queue,
        "signals": annotations,
        "authority": {
            "advisory_only": True,
            "human_decision_granted": False,
            "code_change_authorized": False,
            "branch_or_pr_authorized": False,
            "merge_authorized": False,
            "release_authorized": False,
            "publication_authorized": False,
        },
    }

def validate_local_preanalysis(
    evidence: dict[str, Any],
    analyzer_config: dict[str, Any],
    capability_map: dict[str, Any],
    preanalysis: dict[str, Any],
) -> list[str]:
    errors = validate_evidence(evidence)
    errors.extend(validate_local_preanalysis_config(analyzer_config, capability_map))
    local = analyzer_config.get("local_preanalysis") or {}
    if preanalysis.get("version") != 1 or preanalysis.get("mode") != "DETERMINISTIC_PREANALYSIS":
        errors.append("preanalysis must be version 1 DETERMINISTIC_PREANALYSIS")

    baseline = preanalysis.get("baseline") or {}
    expected_baseline = {
        "repository_revision": (evidence.get("run") or {}).get("repository_revision"),
        "evidence_digest": evidence_digest(evidence),
        "config_digest": canonical_digest(local),
        "capability_map_digest": canonical_digest(capability_map),
    }
    for key, value in expected_baseline.items():
        if baseline.get(key) != value:
            errors.append(f"preanalysis baseline.{key} mismatch")

    execution = preanalysis.get("execution") or {}
    expected_execution = {
        "input_scope": "title_and_evidence_metadata_only",
        "credential_required": False,
        "external_network_required": False,
        "semantic_suitability_inferred": False,
        "recommendation_state_mutated": False,
        "preserved_semantic_state": "ANALYSIS_PENDING",
    }
    for key, value in expected_execution.items():
        if execution.get(key) != value:
            errors.append(f"preanalysis execution.{key} must be {value!r}")

    evidence_ids = [str(item.get("fingerprint")) for item in evidence.get("signals") or []]
    evidence_by_id = {
        str(item.get("fingerprint")): item
        for item in evidence.get("signals") or []
        if isinstance(item, dict)
    }
    annotations = preanalysis.get("signals")
    if not isinstance(annotations, list):
        errors.append("preanalysis signals must be a list")
        annotations = []
    annotation_ids = [str(item.get("signal_fingerprint")) for item in annotations if isinstance(item, dict)]
    if annotation_ids != evidence_ids:
        errors.append("preanalysis must preserve exact evidence signal order and identity")
    if len(annotation_ids) != len(set(annotation_ids)):
        errors.append("preanalysis must not duplicate signal annotations")

    configured_categories = {str(item.get("id")) for item in local.get("categories") or [] if isinstance(item, dict)}
    capability_ids = {str(item.get("id")) for item in capability_map.get("capabilities") or [] if isinstance(item, dict)}
    computed_priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    computed_category_counts = {key: 0 for key in configured_categories}
    near_groups: set[str] = set()

    for item in annotations:
        if not isinstance(item, dict):
            errors.append("preanalysis signal annotation must be a mapping")
            continue
        if any(key in item for key in ("state", "decision", "recommendation")):
            errors.append("preanalysis annotation must not contain semantic decision fields")
        review_priority = item.get("review_priority")
        if review_priority not in computed_priority_counts:
            errors.append("preanalysis review_priority must be HIGH/MEDIUM/LOW")
        else:
            computed_priority_counts[review_priority] += 1
        score = item.get("review_score")
        if not isinstance(score, int) or isinstance(score, bool) or score < 0:
            errors.append("preanalysis review_score must be a non-negative integer")
        categories = item.get("category_ids")
        if not isinstance(categories, list) or not set(categories).issubset(configured_categories):
            errors.append("preanalysis category_ids must be declared local categories")
        else:
            for category_id in categories:
                computed_category_counts[str(category_id)] += 1
        refs = item.get("capability_ids")
        if not isinstance(refs, list) or not set(refs).issubset(capability_ids):
            errors.append("preanalysis capability_ids must exist in the Capability Map")
        terms = item.get("matched_terms")
        if not isinstance(terms, list) or not all(isinstance(x, str) for x in terms):
            errors.append("preanalysis matched_terms must be a string list")
        roles = item.get("source_roles")
        if not isinstance(roles, list) or not roles:
            errors.append("preanalysis source_roles must be a non-empty list")
        bound_signal = evidence_by_id.get(str(item.get("signal_fingerprint"))) or {}
        for key, default in (
            ("evidence_level", 0),
            ("evidence_strength", "DISCOVERY"),
            ("primary_source_count", 0),
            ("community_source_count", 0),
        ):
            if item.get(key) != bound_signal.get(key, default):
                errors.append(f"preanalysis {key} must match deterministic evidence metadata")
        group = item.get("near_duplicate_group")
        count = item.get("near_duplicate_count")
        if group is not None:
            if not isinstance(group, str) or not group.startswith("near-"):
                errors.append("preanalysis near_duplicate_group must be a deterministic near-* id")
            else:
                near_groups.add(group)
            if not isinstance(count, int) or count < 2:
                errors.append("near-duplicate group members must report count >= 2")
        elif count != 1:
            errors.append("non-grouped signal must report near_duplicate_count=1")

    expected_queue = _build_review_queue(annotations, local) if annotations else {
        "shortlist_limit": int((local.get("selection_budget") or {}).get("shortlist_max") or 0),
        "semantic_analysis_limit": int((local.get("selection_budget") or {}).get("semantic_analysis_max") or 0),
        "actionable_recommendations_limit": int((local.get("selection_budget") or {}).get("actionable_recommendations_max") or 0),
        "shortlist_signal_fingerprints": [],
        "semantic_signal_fingerprints": [],
    }
    if preanalysis.get("review_queue") != expected_queue:
        errors.append("preanalysis review_queue must match deterministic ranked selection")

    expected_reasons = _review_exclusion_reasons(annotations, local, expected_queue) if annotations else {}
    expected_reason_counts: dict[str, int] = {}
    for item in annotations:
        if not isinstance(item, dict):
            continue
        fingerprint = str(item.get("signal_fingerprint"))
        codes = expected_reasons.get(fingerprint, [])
        if item.get("exclusion_reasons") != codes:
            errors.append("preanalysis exclusion_reasons must match deterministic review selection")
        expected_status = "EXCLUDED" if codes else "SELECTED"
        if item.get("selection_status") != expected_status:
            errors.append("preanalysis selection_status must match deterministic review selection")
        for code in codes:
            expected_reason_counts[code] = expected_reason_counts.get(code, 0) + 1

    summary = preanalysis.get("summary") or {}
    if summary.get("signal_count") != len(annotations):
        errors.append("preanalysis summary signal_count mismatch")
    if summary.get("priority_counts") != computed_priority_counts:
        errors.append("preanalysis summary priority_counts mismatch")
    if summary.get("category_counts") != computed_category_counts:
        errors.append("preanalysis summary category_counts mismatch")
    if summary.get("near_duplicate_groups") != len(near_groups):
        errors.append("preanalysis summary near_duplicate_groups mismatch")
    if summary.get("shortlist_count") != len(expected_queue["shortlist_signal_fingerprints"]):
        errors.append("preanalysis summary shortlist_count mismatch")
    if summary.get("semantic_candidate_count") != len(expected_queue["semantic_signal_fingerprints"]):
        errors.append("preanalysis summary semantic_candidate_count mismatch")
    if summary.get("actionable_recommendations_limit") != expected_queue["actionable_recommendations_limit"]:
        errors.append("preanalysis summary actionable_recommendations_limit mismatch")
    if summary.get("exclusion_reason_counts") != dict(sorted(expected_reason_counts.items())):
        errors.append("preanalysis summary exclusion_reason_counts mismatch")

    authority = preanalysis.get("authority") or {}
    if authority.get("advisory_only") is not True:
        errors.append("preanalysis authority.advisory_only must be true")
    for key in ("human_decision_granted", "code_change_authorized", "branch_or_pr_authorized", "merge_authorized", "release_authorized", "publication_authorized"):
        if authority.get(key) is not False:
            errors.append(f"preanalysis authority.{key} must be false")
    return errors

def preanalysis_markdown(preanalysis: dict[str, Any]) -> str:
    summary = preanalysis.get("summary") or {}
    counts = summary.get("priority_counts") or {}
    queue = preanalysis.get("review_queue") or {}
    by_id = {
        str(item.get("signal_fingerprint")): item
        for item in preanalysis.get("signals") or []
        if isinstance(item, dict)
    }
    shortlist = [
        by_id[fp] for fp in queue.get("shortlist_signal_fingerprints") or [] if fp in by_id
    ]
    lines = [
        "## Evolution Radar — Deterministic Local Pre-analysis",
        "",
        "Credential-free first-pass triage only. Review priority is not a suitability/adoption recommendation.",
        "",
        f"- HIGH review priority: {counts.get('HIGH', 0)}",
        f"- MEDIUM review priority: {counts.get('MEDIUM', 0)}",
        f"- LOW review priority: {counts.get('LOW', 0)}",
        f"- Near-duplicate title groups: {summary.get('near_duplicate_groups', 0)}",
        f"- Shortlist: {summary.get('shortlist_count', 0)} / {queue.get('shortlist_limit', 0)}",
        f"- Semantic candidates: {summary.get('semantic_candidate_count', 0)} / {queue.get('semantic_analysis_limit', 0)}",
        f"- Actionable semantic recommendation budget: {queue.get('actionable_recommendations_limit', 0)}",
        "- Exclusion reasons: " + (
            ", ".join(f"{code}={count}" for code, count in (summary.get("exclusion_reason_counts") or {}).items())
            or "none"
        ),
        "- Semantic recommendation state remains: ANALYSIS_PENDING until validated semantic output is applied.",
        "",
        "Top review queue:",
    ]
    semantic_ids = set(queue.get("semantic_signal_fingerprints") or [])
    for item in shortlist:
        categories = ", ".join(item.get("category_ids") or []) or "unclassified"
        capabilities = ", ".join(item.get("capability_ids") or []) or "none"
        semantic_marker = "semantic" if item.get("signal_fingerprint") in semantic_ids else "review-only"
        lines.append(
            f"- **{item.get('review_priority')} / {item.get('review_score')} / {semantic_marker}** — "
            f"{item.get('title')} · categories: {categories} · capability hints: {capabilities} "
            f"· verification: {item.get('verification_status')} "
            f"· evidence: L{item.get('evidence_level', 0)}/{item.get('evidence_strength', 'DISCOVERY')}"
        )
    lines += [
        "",
        PREANALYSIS_START,
        "~~~yaml",
        yaml.safe_dump(preanalysis, sort_keys=False, allow_unicode=True).rstrip(),
        "~~~",
        PREANALYSIS_END,
        "",
    ]
    return "\n".join(lines)

def extract_preanalysis(text: str) -> dict[str, Any] | None:
    if PREANALYSIS_START not in text or PREANALYSIS_END not in text:
        return None
    payload = text.split(PREANALYSIS_START, 1)[1].split(PREANALYSIS_END, 1)[0].strip()
    if payload.startswith("~~~yaml"):
        payload = payload[len("~~~yaml"):].strip()
    if payload.endswith("~~~"):
        payload = payload[:-3].strip()
    try:
        value = yaml.safe_load(payload) or {}
    except yaml.YAMLError:
        return None
    return value if isinstance(value, dict) else None
