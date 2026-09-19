#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


KNOWN_STATUSES = {"PASS", "FAIL", "TRIAL_PENDING", "TRIAL_BLOCKED"}


def load_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"trial": {"status": "TRIAL_BLOCKED", "recommendation": "HOLD"}, "summary": {"reason": "Trial report was not produced"}}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"trial": {"status": "TRIAL_BLOCKED", "recommendation": "HOLD"}, "summary": {"reason": f"Trial report JSON is invalid: {exc.msg}"}}
    if isinstance(doc, dict):
        return doc
    return {"trial": {"status": "TRIAL_BLOCKED", "recommendation": "HOLD"}, "summary": {"reason": "Trial report root must be an object"}}


def next_action(status: str) -> str:
    if status == "TRIAL_PENDING":
        return ("Configure the GitHub Actions repository secret OPENAI_API_KEY, then re-run the retrieval-semantic-trial workflow. "
                "Do not treat workflow SUCCESS as quality PASS until the Trial status changes.")
    if status == "TRIAL_BLOCKED":
        return ("Inspect provider/network/configuration failure evidence and keep the candidate on HOLD. "
                "Re-run only after the blocking condition is corrected.")
    if status == "FAIL":
        return ("Keep remote embedding retrieval disabled. Record the negative evidence as HOLD; "
                "do not tune thresholds merely to obtain PASS.")
    if status == "PASS":
        return ("Evidence is eligible for Human review only. A separate Human Adoption Decision is required "
                "before any embedding lane or production source transfer can be enabled.")
    return "Treat the result as blocked until a recognized Trial status is produced."


def render_markdown(doc: dict[str, Any]) -> str:
    trial = doc.get("trial") or {}
    provider = doc.get("provider") or {}
    privacy = doc.get("privacy") or {}
    summary = doc.get("summary") or {}
    authority = doc.get("authority") or {}

    status = str(trial.get("status") or "TRIAL_BLOCKED")
    recommendation = str(trial.get("recommendation") or "HOLD")
    if status not in KNOWN_STATUSES:
        status = "TRIAL_BLOCKED"
        recommendation = "HOLD"

    provider_id = str(provider.get("id") or "unknown")
    model = str(provider.get("model") or "unknown")
    credential_available = provider.get("credential_available")
    credential_text = "true" if credential_available is True else "false" if credential_available is False else "unknown"
    source_scope = str(privacy.get("source_scope") or "unknown")
    repository_source_transfer = privacy.get("repository_source_transfer")
    transfer_text = "true" if repository_source_transfer is True else "false" if repository_source_transfer is False else "unknown"
    reason = str(summary.get("reason") or "")
    requests = summary.get("requests_completed")
    provider_tokens = summary.get("provider_total_tokens")

    lines = [
        "# Retrieval Embedding Trial",
        "",
        f"- **Trial status:** `{status}`",
        f"- **Recommendation:** `{recommendation}`",
        f"- **Provider:** `{provider_id}`",
        f"- **Model:** `{model}`",
        f"- **Credential available:** `{credential_text}`",
        f"- **Source scope:** `{source_scope}`",
        f"- **Repository source transfer:** `{transfer_text}`",
    ]
    if requests is not None:
        lines.append(f"- **Requests completed:** `{requests}`")
    if provider_tokens is not None:
        lines.append(f"- **Provider tokens:** `{provider_tokens}`")
    if reason:
        lines.extend(["", "## Evidence", "", reason])
    lines.extend(["", "## Next action", "", next_action(status), "", "## Authority boundary", "",
        f"- Default enablement: `{str(authority.get('default_enablement', False)).lower()}`",
        f"- Provider auto-enablement: `{str(authority.get('provider_auto_enablement', False)).lower()}`",
        f"- Production source transfer: `{str(authority.get('production_source_transfer', False)).lower()}`",
        f"- Adoption without Human decision: `{str(authority.get('adoption_without_human_decision', False)).lower()}`",
        "- Human Adoption Decision required before provider/default enablement: `true`",
        ""
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a safe Human-readable summary for Retrieval Embedding Trial evidence.")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    doc = load_report(args.report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(doc), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
