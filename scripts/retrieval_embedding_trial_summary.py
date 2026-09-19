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


def next_action(status: str, mode: str) -> str:
    if status == "TRIAL_PENDING":
        if mode == "remote":
            return ("Remote provider was explicitly selected but the repository Actions secret OPENAI_API_KEY is unavailable. "
                    "Configure the secret and re-run retrieval-semantic-trial, or select the default local provider instead.")
        return "Treat unexpected local pending state as blocked and inspect the Trial report before re-running."
    if status == "TRIAL_BLOCKED":
        if mode == "local":
            return ("Inspect the pinned local model dependency/download/runtime evidence and keep the candidate on HOLD. "
                    "No OpenAI API key is required for the default local Trial.")
        return ("Inspect remote provider/network/configuration failure evidence and keep the candidate on HOLD. "
                "Re-run only after the blocking condition is corrected.")
    if status == "FAIL":
        return ("Keep embedding retrieval disabled. Record the negative evidence as HOLD; "
                "do not tune thresholds merely to obtain PASS.")
    if status == "PASS":
        return ("Evidence is eligible for Human review only. A separate Human Adoption Decision is required "
                "before any embedding lane or production source transfer can be enabled.")
    return "Treat the result as blocked until a recognized Trial status is produced."


def _bool_text(value: Any, *, missing: str = "unknown") -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return missing


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

    mode = str(provider.get("mode") or "unknown")
    model_revision = str(provider.get("model_revision") or "")
    lines = [
        "# Retrieval Embedding Trial",
        "",
        f"- **Trial status:** `{status}`",
        f"- **Recommendation:** `{recommendation}`",
        f"- **Provider mode:** `{mode}`",
        f"- **Provider:** `{str(provider.get('id') or 'unknown')}`",
        f"- **Execution location:** `{str(provider.get('execution_location') or 'unknown')}`",
        f"- **Model:** `{str(provider.get('model') or 'unknown')}`",
    ]
    if model_revision:
        lines.append(f"- **Model revision:** `{model_revision}`")
    lines.extend([
        f"- **Credential required:** `{_bool_text(provider.get('credential_required'))}`",
        f"- **Credential available:** `{_bool_text(provider.get('credential_available'), missing='not-required')}`",
        f"- **Source scope:** `{str(privacy.get('source_scope') or 'unknown')}`",
        f"- **Repository source transfer:** `{_bool_text(privacy.get('repository_source_transfer'))}`",
        f"- **Inference source transfer:** `{_bool_text(provider.get('inference_source_transfer'))}`",
    ])
    if provider.get("model_download_network") is not None:
        lines.append(f"- **Model download network:** `{_bool_text(provider.get('model_download_network'))}`")
    if summary.get("embedding_batches_completed") is not None:
        lines.append(f"- **Embedding batches completed:** `{summary.get('embedding_batches_completed')}`")
    if summary.get("provider_total_tokens") is not None:
        lines.append(f"- **Provider tokens:** `{summary.get('provider_total_tokens')}`")
    if summary.get("provider_input_characters") is not None:
        lines.append(f"- **Provider input characters:** `{summary.get('provider_input_characters')}`")
    reason = str(summary.get("reason") or "")
    if reason:
        lines.extend(["", "## Evidence", "", reason])
    lines.extend([
        "", "## Next action", "", next_action(status, mode),
        "", "## Authority boundary", "",
        f"- Default enablement: `{str(authority.get('default_enablement', False)).lower()}`",
        f"- Provider auto-enablement: `{str(authority.get('provider_auto_enablement', False)).lower()}`",
        f"- Production source transfer: `{str(authority.get('production_source_transfer', False)).lower()}`",
        f"- Adoption without Human decision: `{str(authority.get('adoption_without_human_decision', False)).lower()}`",
        "- Human Adoption Decision required before provider/default enablement: `true`",
        "",
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
