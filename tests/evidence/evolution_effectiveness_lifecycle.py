#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import evolution_effectiveness as effectiveness


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def block(start: str, end: str, doc: dict) -> str:
    return "\n".join([start, "~~~yaml", yaml.safe_dump(doc, sort_keys=False).rstrip(), "~~~", end])


def evidence(revision: str, day: str, signals: list[dict], *, raw_count: int, failures: list | None = None) -> dict:
    return {
        "version": 1,
        "run": {
            "mode": "weekly",
            "generated_at": f"2026-09-{day}T01:00:00Z",
            "repository_revision": revision,
            "analyzer": {"status": "available", "provider": "fixture", "model": "fixture"},
        },
        "sources": {
            "configured": ["source-a", "source-b"],
            "attempted": ["source-a", "source-b"],
            "failures": failures or [],
        },
        "signals": signals,
        "recommendations": [
            {
                "signal_fingerprint": item["fingerprint"],
                "state": "ANALYSIS_PENDING",
            }
            for item in signals
        ],
        "summary": {
            "signal_count": raw_count,
            "deduplicated_count": len(signals),
            "recommendation_count": len(signals),
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


def signal(fp_char: str, source_id: str, role: str) -> dict:
    return {
        "fingerprint": "sha256:" + fp_char * 64,
        "title": f"Signal {fp_char}",
        "canonical_url": f"https://example.test/{fp_char}",
        "source_id": source_id,
        "source_role": role,
        "source_ids": [source_id],
        "source_roles": [role],
        "source_provenance": [{"source_id": source_id, "role": role}],
        "verification_status": "PRIMARY_SOURCE" if role == "primary" else "DISCOVERY_ONLY",
        "evidence_level": 2 if role == "primary" else 0,
        "evidence_strength": "MEDIUM" if role == "primary" else "DISCOVERY",
        "primary_source_count": 1 if role == "primary" else 0,
        "community_source_count": 1 if role == "community" else 0,
        "published_at": None,
        "retrieved_at": f"2026-09-01T00:00:00Z",
        "summary": "",
        "recurrence_count": 1,
        "duplicate_of": None,
    }


def preanalysis(signals: list[dict], shortlist: list[str], semantic: list[str]) -> dict:
    return {
        "version": 1,
        "mode": "DETERMINISTIC_PREANALYSIS",
        "baseline": {},
        "execution": {
            "semantic_suitability_inferred": False,
            "recommendation_state_mutated": False,
        },
        "summary": {
            "signal_count": len(signals),
            "shortlist_count": len(shortlist),
            "semantic_candidate_count": len(semantic),
        },
        "review_queue": {
            "shortlist_signal_fingerprints": shortlist,
            "semantic_signal_fingerprints": semantic,
        },
        "signals": [],
        "authority": {"advisory_only": True},
    }


def analysis(states: dict[str, str]) -> dict:
    return {
        "version": 1,
        "recommendations": [
            {"signal_fingerprint": fp, "state": state}
            for fp, state in states.items()
        ],
    }


def main() -> int:
    revision = "a" * 40
    fp1 = "sha256:" + "1" * 64
    fp2 = "sha256:" + "2" * 64
    fp3 = "sha256:" + "3" * 64
    fp4 = "sha256:" + "4" * 64

    e1 = evidence(revision, "05", [signal("1", "source-a", "primary"), signal("2", "source-b", "community")], raw_count=3)
    p1 = preanalysis(e1["signals"], [fp1], [fp1])
    a1 = analysis({fp1: "TRIAL", fp2: "HOLD"})

    decision_trial = {
        "version": 1,
        "decision": {"decision": "TRIAL", "signal_fingerprint": fp1},
        "decision_fingerprint": "sha256:" + "d" * 64,
    }
    handoff = {
        "version": 1,
        "state": "TRIAL_HANDOFF_READY",
        "handoff_fingerprint": "sha256:" + "h" * 64,
        "trial": {"signal_fingerprint": fp1},
    }
    trial_pass = {
        "version": 1,
        "trial": {"signal_fingerprint": fp1},
        "result": {"status": "PASS"},
        "trial_fingerprint": "sha256:" + "t" * 64,
    }
    decision_adopt = {
        "version": 1,
        "decision": {"decision": "ADOPT", "signal_fingerprint": fp1},
        "decision_fingerprint": "sha256:" + "e" * 64,
    }
    adoption = {
        "version": 1,
        "adoption": {"signal_fingerprint": fp1},
        "adoption_fingerprint": "sha256:" + "a" * 64,
    }

    issue1 = {
        "number": 10,
        "title": "Evolution Radar [weekly] 2026-09-05",
        "createdAt": "2026-09-05T01:10:00Z",
        "body": "\n\n".join([
            block(effectiveness.EVIDENCE_START, effectiveness.EVIDENCE_END, e1),
            block(effectiveness.PREANALYSIS_START, effectiveness.PREANALYSIS_END, p1),
            block(effectiveness.ANALYSIS_START, effectiveness.ANALYSIS_END, a1),
        ]),
        "comments": [
            {"body": block(effectiveness.DECISION_START, effectiveness.DECISION_END, decision_trial)},
            {"body": block(effectiveness.TRIAL_HANDOFF_START, effectiveness.TRIAL_HANDOFF_END, handoff)},
            {"body": block(effectiveness.TRIAL_START, effectiveness.TRIAL_END, trial_pass)},
            {"body": block(effectiveness.DECISION_START, effectiveness.DECISION_END, decision_adopt)},
            {"body": block(effectiveness.ADOPTION_START, effectiveness.ADOPTION_END, adoption)},
        ],
    }

    e2 = evidence(
        revision,
        "12",
        [signal("3", "source-a", "primary"), signal("4", "source-b", "community")],
        raw_count=2,
        failures=[{"source_id": "source-b", "error": "fixture failure"}],
    )
    p2 = preanalysis(e2["signals"], [fp3], [fp3])
    a2 = analysis({fp3: "ASSESS", fp4: "HOLD"})
    issue2 = {
        "number": 11,
        "title": "Evolution Radar [weekly] 2026-09-12",
        "createdAt": "2026-09-12T01:10:00Z",
        "body": "\n\n".join([
            block(effectiveness.EVIDENCE_START, effectiveness.EVIDENCE_END, e2),
            block(effectiveness.PREANALYSIS_START, effectiveness.PREANALYSIS_END, p2),
            block(effectiveness.ANALYSIS_START, effectiveness.ANALYSIS_END, a2),
        ]),
        "comments": [],
    }

    config = yaml.safe_load((ROOT / "config/evolution-effectiveness.yaml").read_text(encoding="utf-8")) or {}
    config = copy.deepcopy(config)
    config["review_flags"]["minimum_source_signals"] = 2

    report = effectiveness.build_report(
        [issue1, issue2],
        config,
        period="2026-09",
        repository_revision=revision,
        generated_at="2026-10-02T02:15:00Z",
    )
    require(not effectiveness.validate_report(report, config), "valid effectiveness report must validate")
    require(report["baseline"]["cohort_issue_count"] == 2, "cohort must include two weekly issues")
    require(report["summary"]["raw_signal_count"] == 5, "raw signal observations must aggregate")
    require(report["summary"]["unique_signal_count"] == 4, "unique weekly observations must aggregate")
    require(report["summary"]["duplicate_count"] == 1, "duplicate count must be raw minus unique")
    require(report["summary"]["shortlist_count"] == 2, "shortlist count must aggregate")
    require(report["summary"]["semantic_signal_count"] == 2, "semantic selection count must aggregate")
    require(report["summary"]["actionable_recommendation_count"] == 2, "TRIAL + ASSESS must be actionable")
    require(report["summary"]["human_decision_counts"]["TRIAL"] == 1, "TRIAL Human Decision must be counted")
    require(report["summary"]["human_decision_counts"]["ADOPT"] == 1, "ADOPT Human Decision must be counted")
    require(report["summary"]["trial_handoff_ready_count"] == 1, "provider-neutral handoff must be counted")
    require(report["summary"]["trial_status_counts"]["PASS"] == 1, "PASS Trial must be counted")
    require(report["summary"]["adoption_count"] == 1, "adoption binding must be counted")

    rows = {row["source_id"]: row for row in report["sources"]}
    require(rows["source-a"]["collected_signal_count"] == 2, "source-a collected signals mismatch")
    require(rows["source-a"]["shortlist_signal_count"] == 2, "source-a shortlist yield mismatch")
    require(rows["source-a"]["semantic_signal_count"] == 2, "source-a semantic yield mismatch")
    require(rows["source-a"]["actionable_recommendation_count"] == 2, "source-a actionable yield mismatch")
    require(rows["source-a"]["trial_decision_count"] == 1, "source-a Trial conversion mismatch")
    require(rows["source-a"]["trial_pass_count"] == 1, "source-a PASS conversion mismatch")
    require(rows["source-a"]["adoption_count"] == 1, "source-a adoption conversion mismatch")
    require("REVIEW_LOW_SHORTLIST_YIELD" in rows["source-b"]["review_flags"], "low-yield source must be review-flagged")
    require("REVIEW_HIGH_FAILURE_RATE" in rows["source-b"]["review_flags"], "unreliable source must be review-flagged")

    tampered = copy.deepcopy(report)
    tampered["authority"]["automatic_source_weight_changes"] = True
    require(effectiveness.validate_report(tampered, config), "automatic source tuning must fail validation")

    tampered = copy.deepcopy(report)
    tampered["effectiveness_fingerprint"] = "sha256:" + "0" * 64
    require(effectiveness.validate_report(tampered, config), "fingerprint tampering must fail validation")

    rendered = effectiveness.markdown(report)
    require(effectiveness.EFFECTIVENESS_START in rendered, "Markdown must embed durable effectiveness evidence")
    require("does not automatically reweight" in rendered, "Markdown must preserve Human source-policy authority")
    print("Evolution effectiveness lifecycle OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
