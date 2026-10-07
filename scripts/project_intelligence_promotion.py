"""Pure promotion eligibility and target policy for Project Intelligence."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def promotion_candidate(store: Path, intel: dict[str, Any], topic_name: str) -> tuple[dict[str, Any], Path]:
    topic = (intel.get("topics") or {}).get(topic_name)
    if not isinstance(topic, dict):
        raise RuntimeError(f"Unknown Project Intelligence topic: {topic_name}")  # noqa: TRY004 - preserve facade error contract
    path_value = topic.get("path")
    if not path_value:
        raise RuntimeError(f"Project Intelligence topic has no derived content path: {topic_name}")
    derived_path = store / str(path_value)
    if not derived_path.is_file():
        raise RuntimeError(f"Project Intelligence topic content is missing: {path_value}")
    promotion = topic.get("promotion") or {}
    confirmations = [str(value) for value in (promotion.get("confirmations") or []) if str(value).strip()]
    confirmations = list(dict.fromkeys(confirmations))
    eligible = (
        len(confirmations) >= 2
        and topic.get("type") in {"FACT", "INTERPRETATION", "OBSERVED_CONVENTION"}
        and bool(topic.get("evidence"))
    )
    return {
        "topic": topic_name,
        "status": "RECOMMENDED" if eligible else "NOT_READY",
        "approval_required": True,
        "mutation_performed": False,
        "confirmations": confirmations,
        "confirmation_count": len(confirmations),
        "reason": "repeated_confirmed_derived_invariant" if eligible else "insufficient_confirmation_or_evidence",
        "allowed_targets": ["AGENTS.md", "AGENTS.override.md", "docs/<official-project-rule>.md"],
    }, derived_path


def promotion_target(root: Path, target: str, source_names: set[str], doc_ext: set[str]) -> Path:
    raw = Path(target)
    if raw.is_absolute():
        raise RuntimeError("Promotion target must be project-relative")
    resolved = (root / raw).resolve()
    try:
        relative = resolved.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise RuntimeError("Promotion target escapes project root") from exc
    allowed = raw.name in source_names or (relative.startswith("docs/") and raw.suffix.lower() in doc_ext)
    if not allowed:
        raise RuntimeError("Promotion target must be AGENTS*/runtime instruction source or an official docs/* document")
    return resolved
