"""Pure compilation and evidence ranking for creative prompt inputs."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from creative_errors import Blocked

ASSET_PRESETS_PATH = Path(__file__).resolve().parents[1] / "templates/creative/CREATIVE_ASSET_PRESETS.yaml"


def load_asset_preset(preset_id: Any) -> dict[str, Any] | None:
    if preset_id is None:
        return None
    if not isinstance(preset_id, str) or preset_id not in {"character", "background", "texture", "ui_ornament"}:
        raise Blocked("creative_asset_preset_invalid", "asset_preset must be one of the four registered preset IDs.",
                      phase="creative.bundle_validation")
    try:
        raw = ASSET_PRESETS_PATH.read_bytes()
        if len(raw) > 16 * 1024:
            raise ValueError("preset registry exceeds its limit")
        registry = yaml.safe_load(raw.decode("utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError, ValueError) as exc:
        raise Blocked("creative_asset_preset_unavailable", "The shared creative preset registry could not be verified.",
                      phase="creative.prompt_compilation") from exc
    presets = registry.get("presets") if isinstance(registry, dict) and registry.get("version") == 1 else None
    preset = presets.get(preset_id) if isinstance(presets, dict) else None
    if (not isinstance(preset, dict) or not isinstance(preset.get("label"), str)
            or not isinstance(preset.get("include"), list) or not isinstance(preset.get("avoid"), list)
            or any(not isinstance(item, str) or not item.strip() for item in [*preset["include"], *preset["avoid"]])):
        raise Blocked("creative_asset_preset_invalid", "The selected preset entry is malformed.",
                      phase="creative.prompt_compilation")
    return {"id": preset_id, **preset, "registry_sha256": hashlib.sha256(raw).hexdigest()}


def _profile_lines(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _profile_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def compile_creative_prompt(bundle: dict[str, Any], profiles: dict[str, dict[str, Any]]) -> str:
    """Compile approved Profile facts into a bounded, reproducible provider prompt."""
    sections: list[str] = []
    def add(label: str, values: Any) -> None:
        lines = _profile_lines(values)
        if lines:
            sections.append(f"{label}: " + "; ".join(lines))

    add("Requested image brief", bundle.get("prompt"))
    preset = load_asset_preset(bundle.get("asset_preset"))
    if preset:
        add("Creative asset preset", preset["label"])
        add("Preset guidance", preset["include"])
        add("Preset exclusions", preset["avoid"])
    character = _profile_mapping(profiles.get("character"))
    acceptance = _profile_mapping(character.get("acceptance_criteria"))
    add("Character identity", character.get("summary"))
    add("Identity features to preserve", character.get("identity_features"))
    add("Critical features", acceptance.get("critical_features"))
    add("Required character details", character.get("must_preserve"))
    variations = _profile_mapping(character.get("allowed_variations"))
    for key, label in (("expressions", "Allowed expressions"), ("poses", "Allowed poses"), ("outfit_variants", "Allowed outfit variations")):
        add(label, variations.get(key))
    add("Forbidden feature placements", acceptance.get("forbidden_misplacements"))
    style = _profile_mapping(profiles.get("style"))
    add("Art direction", style.get("intent"))
    rendering = _profile_mapping(style.get("rendering"))
    for key, label in (("medium", "Medium"), ("linework", "Linework"), ("shading", "Shading"), ("finish", "Finish")):
        add(label, rendering.get(key))
    composition = _profile_mapping(style.get("composition"))
    for key, label in (("framing", "Framing"), ("background", "Background")):
        add(label, composition.get(key))
    prompt_constraints = _profile_mapping(style.get("prompt_constraints"))
    add("Style constraints", prompt_constraints.get("must_include"))
    add("Avoid", [*(_profile_lines(character.get("must_avoid"))),
                   *(_profile_lines(style.get("must_avoid"))),
                   *(_profile_lines(prompt_constraints.get("must_avoid")))])
    collection = _profile_mapping(profiles.get("collection"))
    add("Shared collection direction", collection.get("visual_direction"))
    style_lock = _profile_mapping(collection.get("style_lock"))
    add("Shared style lock", style_lock.get("must_match"))
    add("Shared palette", style_lock.get("palette"))
    add("Collection exclusions", style_lock.get("must_avoid"))
    prompt = "\n".join(sections)
    if not prompt or len(prompt) > 12000:
        raise Blocked("compiled_prompt_invalid", "Compiled creative prompt is empty or exceeds its 12000 character limit.")
    return prompt


def model_recommendation(bundle: dict[str, Any], profiles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Rank only explicitly inventoried local candidates with reviewed evidence."""
    profile = profiles.get("model_capabilities")
    if profile is None:
        return {"status": "UNAVAILABLE", "reason_code": "model_capability_profile_not_configured", "models": []}
    models = profile.get("models")
    if not isinstance(models, list) or len(models) > 100:
        return {"status": "UNAVAILABLE", "reason_code": "model_capability_profile_invalid", "models": []}
    style = _profile_mapping(profiles.get("style"))
    rendering = _profile_mapping(style.get("rendering"))
    intent_terms = " ".join([str(style.get("intent", "")), str(rendering.get("medium", "")),
                              str(rendering.get("shading", ""))]).casefold()
    scored: list[tuple[int, float, dict[str, Any]]] = []
    for item in models:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not isinstance(item.get("capabilities"), list):
            continue
        capabilities = [term for term in item["capabilities"] if isinstance(term, str) and term.strip()]
        operations = item.get("operations")
        if not isinstance(operations, list) or bundle.get("operation") not in operations:
            continue
        overlap = [term for term in capabilities if term.casefold() in intent_terms]
        review = _profile_mapping(item.get("quality_review"))
        availability = item.get("availability") == "VERIFIED_LOCAL"
        licensed = item.get("license_status") == "VERIFIED"
        reviewed = review.get("status") == "HUMAN_REVIEWED" and isinstance(review.get("evidence"), str) and bool(review["evidence"].strip())
        scores = [review.get("style_score"), review.get("character_consistency_score")]
        numeric_scores = [score for score in scores if isinstance(score, int) and not isinstance(score, bool)]
        scores_valid = len(numeric_scores) == 2 and all(1 <= score <= 5 for score in numeric_scores)
        verified = availability and licensed and reviewed and scores_valid
        quality_score = sum(numeric_scores) / len(numeric_scores) if verified else 0.0
        scored.append((len(overlap), quality_score, {"id": item["id"][:128], "status": "EVIDENCE_BACKED" if verified else "INSUFFICIENT_EVIDENCE",
                                      "matching_capabilities": overlap[:12], "quality_evidence": "HUMAN_REVIEWED" if verified else "UNVERIFIED",
                                      "human_quality_score": quality_score if verified else None,
                                      "selection_reason": "Ranked by declared style match and human-reviewed quality evidence; no model is selected automatically."}))
    scored.sort(key=lambda candidate: (-candidate[0], -candidate[1], candidate[2]["id"].casefold()))
    ranked = [row for _, _, row in scored[:3]]
    backed = any(row["status"] == "EVIDENCE_BACKED" for row in ranked)
    return {"status": "RECOMMENDATIONS_AVAILABLE" if backed else "NO_VERIFIED_RECOMMENDATION",
            "reason_code": "local_evidence_ranked" if backed else "quality_or_local_evidence_missing",
            "selected_model_changed": False, "models": ranked}
