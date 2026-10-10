#!/usr/bin/env python3
"""Validate and compose provenance-bound character artwork using local files only."""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import character_asset_validation as _character_asset_validation
import yaml

ArtifactError = _character_asset_validation.ArtifactError
FORBIDDEN_SVG_ELEMENTS = _character_asset_validation.FORBIDDEN_SVG_ELEMENTS
MAX_IMAGE_BYTES = _character_asset_validation.MAX_IMAGE_BYTES
MAX_IMAGE_DIMENSION = _character_asset_validation.MAX_IMAGE_DIMENSION
MAX_IMAGE_PIXELS = _character_asset_validation.MAX_IMAGE_PIXELS
SVG_NS = _character_asset_validation.SVG_NS
_dimensions = _character_asset_validation._dimensions
_error = _character_asset_validation._error
_png_dimensions = _character_asset_validation._png_dimensions
_project_path = _character_asset_validation._project_path
_svg_dimension = _character_asset_validation._svg_dimension
_validate_data_uri = _character_asset_validation._validate_data_uri
_validate_svg_bytes = _character_asset_validation._validate_svg_bytes
inspect_asset = _character_asset_validation.inspect_asset
sha256_file = _character_asset_validation.sha256_file

# Keep the legacy facade bound to the same implementation objects.

ALLOWED_PROVIDERS = {"comfy_mcp_local", "mflux_local"}
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}$")






















def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        _error("YAML_INVALID", f"Could not read a valid UTF-8 YAML document: {exc}")
    if not isinstance(value, dict):
        _error("YAML_ROOT_INVALID", "YAML root must be a mapping.")
    return value


def _valid_id(value: object) -> bool:
    return isinstance(value, str) and bool(ID_PATTERN.fullmatch(value))


def validate_character_profile(
    doc: dict[str, Any], project: Path
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if doc.get("version") != 1:
        issues.append(
            {
                "code": "PROFILE_VERSION",
                "message": "Character profile version must be 1.",
            }
        )
    for key in ("id", "name", "summary"):
        value = doc.get(key)
        if (
            not isinstance(value, str)
            or not value.strip()
            or (key == "id" and not _valid_id(value))
        ):
            issues.append(
                {
                    "code": "PROFILE_FIELD",
                    "message": f"Character profile field {key} is required.",
                }
            )
    for key in ("identity_features", "must_preserve"):
        values = doc.get(key)
        if not isinstance(values, list) or (key == "identity_features" and not values):
            issues.append(
                {
                    "code": "PROFILE_IDENTITY",
                    "message": f"{key} must be a list; identity_features cannot be empty.",
                }
            )
    for section in ("allowed_variations", "palette", "privacy"):
        if not isinstance(doc.get(section), dict):
            issues.append(
                {
                    "code": "PROFILE_SECTION",
                    "message": f"Character profile {section} must be a mapping.",
                }
            )
    acceptance = doc.get("acceptance_criteria")
    if acceptance is not None:
        if not isinstance(acceptance, dict):
            issues.append({"code": "PROFILE_ACCEPTANCE", "message": "acceptance_criteria must be a mapping."})
        else:
            for key in ("critical_features", "forbidden_misplacements"):
                values = acceptance.get(key, [])
                if (not isinstance(values, list) or len(values) > 24
                        or any(not isinstance(item, str) or not item.strip() or len(item) > 160 for item in values)):
                    issues.append({"code": "PROFILE_ACCEPTANCE", "message": f"acceptance_criteria.{key} must contain at most 24 bounded strings."})
    if (doc.get("privacy") or {}).get("raw_prompt_persistence") != "forbidden":
        issues.append(
            {
                "code": "PROMPT_PERSISTENCE",
                "message": "Character profile must forbid raw prompt persistence.",
            }
        )
    if (doc.get("privacy") or {}).get("external_upload") not in {
        "forbidden_by_default",
        "forbidden",
    }:
        issues.append(
            {
                "code": "EXTERNAL_EGRESS_POLICY",
                "message": "Character profile must forbid external upload by default.",
            }
        )
    references = doc.get("references")
    if not isinstance(references, list) or not references:
        issues.append(
            {
                "code": "REFERENCE_REQUIRED",
                "message": "At least one identity reference is required.",
            }
        )
    else:
        seen: set[str] = set()
        for index, reference in enumerate(references):
            if not isinstance(reference, dict):
                issues.append(
                    {
                        "code": "REFERENCE_INVALID",
                        "message": f"references[{index}] must be a mapping.",
                    }
                )
                continue
            raw_path = reference.get("path")
            try:
                path = _project_path(project, raw_path)
                actual = inspect_asset(path)
                if reference.get("sha256") != actual["sha256"]:
                    issues.append(
                        {
                            "code": "REFERENCE_HASH_MISMATCH",
                            "message": f"Reference digest mismatch: {raw_path}",
                        }
                    )
                if raw_path in seen:
                    issues.append(
                        {
                            "code": "REFERENCE_DUPLICATE",
                            "message": f"Duplicate reference: {raw_path}",
                        }
                    )
                seen.add(str(raw_path))
            except (ArtifactError, OSError) as exc:
                issues.append(
                    {
                        "code": getattr(exc, "code", "REFERENCE_INVALID"),
                        "message": f"Reference {raw_path}: {exc}",
                    }
                )
            if (
                not isinstance(reference.get("role"), str)
                or not reference["role"].strip()
            ):
                issues.append(
                    {
                        "code": "REFERENCE_ROLE",
                        "message": f"references[{index}].role is required.",
                    }
                )
    return issues


def validate_style_profile(doc: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if doc.get("version") != 1 or not _valid_id(doc.get("id")):
        issues.append(
            {
                "code": "STYLE_ID",
                "message": "Style profile requires version 1 and a stable id.",
            }
        )
    for key in ("name", "intent"):
        if not isinstance(doc.get(key), str) or not doc[key].strip():
            issues.append(
                {
                    "code": "STYLE_FIELD",
                    "message": f"Style profile field {key} is required.",
                }
            )
    for section in ("rendering", "composition", "reference_policy"):
        if not isinstance(doc.get(section), dict):
            issues.append(
                {
                    "code": "STYLE_SECTION",
                    "message": f"Style profile {section} must be a mapping.",
                }
            )
    if (doc.get("reference_policy") or {}).get("literal_copy") is not False:
        issues.append(
            {
                "code": "REFERENCE_COPY_POLICY",
                "message": "Style profile must prohibit literal reference copying.",
            }
        )
    if (
        (doc.get("composition") or {}).get("text_policy")
        != "typeset labels after image generation; never ask the image model to render text"
    ):
        issues.append(
            {
                "code": "TEXT_COMPOSITION_POLICY",
                "message": "Style profile must typeset text after image generation.",
            }
        )
    constraints = doc.get("prompt_constraints")
    if constraints is not None:
        if not isinstance(constraints, dict):
            issues.append({"code": "STYLE_CONSTRAINTS", "message": "prompt_constraints must be a mapping."})
        else:
            for key in ("must_include", "must_avoid"):
                values = constraints.get(key, [])
                if (not isinstance(values, list) or len(values) > 24
                        or any(not isinstance(item, str) or not item.strip() or len(item) > 160 for item in values)):
                    issues.append({"code": "STYLE_CONSTRAINTS", "message": f"prompt_constraints.{key} must contain at most 24 bounded strings."})
    lock_id = doc.get("style_lock_id")
    if lock_id is not None and not _valid_id(lock_id):
        issues.append({"code": "STYLE_LOCK_ID", "message": "style_lock_id must be null or a stable lowercase id."})
    return issues


def validate_collection_profile(doc: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if doc.get("version") != 1 or not _valid_id(doc.get("collection_id")):
        issues.append({"code": "COLLECTION_ID", "message": "Collection profile requires version 1 and a stable collection_id."})
    if not isinstance(doc.get("visual_direction"), str) or not doc["visual_direction"].strip():
        issues.append({"code": "COLLECTION_DIRECTION", "message": "Collection visual_direction is required."})
    characters = doc.get("characters")
    if not isinstance(characters, list) or not 1 <= len(characters) <= 24:
        issues.append({"code": "COLLECTION_CHARACTERS", "message": "Collection must list between 1 and 24 characters."})
    else:
        identifiers: set[str] = set()
        for index, item in enumerate(characters):
            if not isinstance(item, dict) or not _valid_id(item.get("id")) or not isinstance(item.get("name"), str) or not item["name"].strip() or not isinstance(item.get("bundle"), str) or not item["bundle"].strip():
                issues.append({"code": "COLLECTION_CHARACTER", "message": f"characters[{index}] requires id, name, and bundle."})
                continue
            if item["id"] in identifiers:
                issues.append({"code": "COLLECTION_DUPLICATE", "message": f"Duplicate collection character id: {item['id']}."})
            identifiers.add(item["id"])
    lock = doc.get("style_lock", {"id": None, "must_match": [], "must_avoid": [], "palette": []})
    if not isinstance(lock, dict):
        issues.append({"code": "COLLECTION_STYLE_LOCK", "message": "style_lock must be a mapping."})
    else:
        if lock.get("id") is not None and not _valid_id(lock.get("id")):
            issues.append({"code": "COLLECTION_STYLE_LOCK", "message": "style_lock.id must be null or a stable lowercase id."})
        for key in ("must_match", "must_avoid", "palette"):
            values = lock.get(key, [])
            if not isinstance(values, list) or len(values) > 24 or any(not isinstance(value, str) or not value.strip() or len(value) > 160 for value in values):
                issues.append({"code": "COLLECTION_STYLE_LOCK", "message": f"style_lock.{key} must contain at most 24 bounded strings."})
    return issues


def validate_manifest(doc: dict[str, Any], project: Path) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if doc.get("version") != 1:
        issues.append(
            {
                "code": "MANIFEST_VERSION",
                "message": "Artwork manifest version must be 1.",
            }
        )
    if doc.get("status") not in {"DRAFT", "COMPLETE", "REJECTED"}:
        issues.append(
            {
                "code": "MANIFEST_STATUS",
                "message": "Manifest status must be DRAFT, COMPLETE, or REJECTED.",
            }
        )

    try:
        character_path = _project_path(project, doc.get("character_profile"))
        character = _read_yaml(character_path)
        issues.extend(validate_character_profile(character, project))
    except (ArtifactError, OSError) as exc:
        issues.append(
            {
                "code": getattr(exc, "code", "CHARACTER_PROFILE_INVALID"),
                "message": f"Character profile: {exc}",
            }
        )
        character = {}
    try:
        style_path = _project_path(project, doc.get("style_profile"))
        style = _read_yaml(style_path)
        issues.extend(validate_style_profile(style))
    except (ArtifactError, OSError) as exc:
        issues.append(
            {
                "code": getattr(exc, "code", "STYLE_PROFILE_INVALID"),
                "message": f"Style profile: {exc}",
            }
        )
        style = {}
    collection_reference = doc.get("collection_profile")
    if collection_reference is not None:
        try:
            collection = _read_yaml(_project_path(project, collection_reference))
            issues.extend(validate_collection_profile(collection))
            lock_id = (collection.get("style_lock") or {}).get("id")
            if lock_id and style.get("style_lock_id") != lock_id:
                issues.append({"code": "COLLECTION_STYLE_LOCK_MISMATCH", "message": "Character Style Profile must use the collection's shared style_lock_id."})
        except (ArtifactError, OSError) as exc:
            issues.append({"code": getattr(exc, "code", "COLLECTION_PROFILE_INVALID"), "message": f"Collection profile: {exc}"})

    execution = doc.get("execution")
    if not isinstance(execution, dict):
        issues.append(
            {
                "code": "EXECUTION_REQUIRED",
                "message": "Manifest execution provenance is required.",
            }
        )
        execution = {}
    if execution.get("provider_id") not in ALLOWED_PROVIDERS:
        issues.append(
            {
                "code": "PROVIDER_NOT_LOCAL",
                "message": "Only comfy_mcp_local and mflux_local providers are allowed.",
            }
        )
    if execution.get("external_egress") is not False:
        issues.append(
            {
                "code": "EXTERNAL_EGRESS",
                "message": "Approved workflow requires external_egress: false.",
            }
        )
    if (
        not isinstance(execution.get("model_id"), str)
        or not execution["model_id"].strip()
    ):
        issues.append(
            {
                "code": "MODEL_ID_REQUIRED",
                "message": "Record the exact model identifier and revision.",
            }
        )
    runtime = execution.get("runtime")
    if (
        not isinstance(runtime, dict)
        or not isinstance(runtime.get("name"), str)
        or not runtime["name"].strip()
    ):
        issues.append(
            {
                "code": "RUNTIME_REQUIRED",
                "message": "Record the local image runtime name.",
            }
        )
    elif not isinstance(runtime.get("version"), str) or not runtime["version"].strip():
        issues.append(
            {
                "code": "RUNTIME_VERSION_REQUIRED",
                "message": "Record the exact local image runtime version.",
            }
        )
    license_info = execution.get("model_license")
    if (
        not isinstance(license_info, dict)
        or not isinstance(license_info.get("name"), str)
        or not license_info["name"].strip()
    ):
        issues.append(
            {
                "code": "MODEL_LICENSE_REQUIRED",
                "message": "Record the model license name; unknown licenses cannot pass.",
            }
        )
    elif license_info["name"].strip().lower() in {"unknown", "n/a", "none", "tbd"}:
        issues.append(
            {
                "code": "MODEL_LICENSE_UNKNOWN",
                "message": "Model license must be verified before treating the manifest as complete.",
            }
        )
    license_url = (
        license_info.get("source_url") if isinstance(license_info, dict) else None
    )
    parsed_license_url = urlsplit(license_url) if isinstance(license_url, str) else None
    if (
        not parsed_license_url
        or parsed_license_url.scheme != "https"
        or not parsed_license_url.hostname
        or parsed_license_url.username
        or parsed_license_url.password
    ):
        issues.append(
            {
                "code": "LICENSE_SOURCE_REQUIRED",
                "message": "Record an HTTPS model-license source URL.",
            }
        )
    fingerprint = execution.get("prompt_fingerprint")
    if fingerprint is not None and not SHA256_PATTERN.fullmatch(str(fingerprint)):
        issues.append(
            {
                "code": "PROMPT_FINGERPRINT_INVALID",
                "message": "Prompt fingerprint must be a SHA-256 digest, never raw prompt text.",
            }
        )
    performance = execution.get("performance")
    if performance is not None:
        if not isinstance(performance, dict) or not isinstance(
            performance.get("measured"), bool
        ):
            issues.append(
                {
                    "code": "PERFORMANCE_INVALID",
                    "message": "Performance evidence requires an explicit measured boolean.",
                }
            )
        elif performance["measured"]:
            if (
                not isinstance(performance.get("device"), str)
                or not performance["device"].strip()
            ):
                issues.append(
                    {
                        "code": "PERFORMANCE_DEVICE_REQUIRED",
                        "message": "Measured performance requires a device identifier.",
                    }
                )
            if (
                not isinstance(performance.get("elapsed_ms"), int)
                or performance["elapsed_ms"] <= 0
            ):
                issues.append(
                    {
                        "code": "PERFORMANCE_VALUE_INVALID",
                        "message": "Measured elapsed_ms must be a positive integer.",
                    }
                )
            for key in ("peak_memory_bytes",):
                value = performance.get(key)
                if value is not None and (not isinstance(value, int) or value < 0):
                    issues.append(
                        {
                            "code": "PERFORMANCE_VALUE_INVALID",
                            "message": f"Measured {key} must be a non-negative integer.",
                        }
                    )

    references = {
        item.get("path"): item.get("sha256")
        for item in character.get("references", [])
        if isinstance(item, dict)
    }
    assets = doc.get("assets")
    if not isinstance(assets, list) or not assets:
        issues.append(
            {
                "code": "ARTWORKS_REQUIRED",
                "message": "At least one character artwork asset is required.",
            }
        )
        assets = []
    seen_ids: set[str] = set()
    asset_records: list[dict[str, Any]] = []
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            issues.append(
                {
                    "code": "ARTWORK_INVALID",
                    "message": f"assets[{index}] must be a mapping.",
                }
            )
            continue
        asset_id = asset.get("id")
        if not _valid_id(asset_id) or asset_id in seen_ids:
            issues.append(
                {
                    "code": "ARTWORK_ID_INVALID",
                    "message": f"assets[{index}] id must be unique and stable.",
                }
            )
        seen_ids.add(str(asset_id))
        if not isinstance(asset.get("role"), str) or not asset["role"].strip():
            issues.append(
                {
                    "code": "ARTWORK_ROLE_REQUIRED",
                    "message": f"assets[{index}].role is required.",
                }
            )
        if not isinstance(asset.get("label"), str) or not asset["label"].strip():
            issues.append(
                {
                    "code": "ARTWORK_LABEL_REQUIRED",
                    "message": f"assets[{index}].label is required.",
                }
            )
        sources = asset.get("source_assets")
        if not isinstance(sources, list) or not sources:
            issues.append(
                {
                    "code": "ARTWORK_LINEAGE_REQUIRED",
                    "message": f"assets[{index}] must identify its source reference assets.",
                }
            )
        else:
            for source in sources:
                if not isinstance(source, dict) or references.get(
                    source.get("path")
                ) != source.get("sha256"):
                    issues.append(
                        {
                            "code": "ARTWORK_LINEAGE_MISMATCH",
                            "message": f"assets[{index}] source must match a hashed character reference.",
                        }
                    )
        try:
            path = _project_path(project, asset.get("path"))
            metadata = inspect_asset(path)
            for key in ("format", "width", "height", "sha256"):
                expected = metadata.get(key)
                if key in asset and asset.get(key) != expected:
                    issues.append(
                        {
                            "code": "ARTWORK_METADATA_MISMATCH",
                            "message": f"assets[{index}].{key} does not match the file.",
                        }
                    )
                elif key == "sha256" and asset.get(key) != expected:
                    issues.append(
                        {
                            "code": "ARTWORK_HASH_MISMATCH",
                            "message": f"assets[{index}] digest does not match the file.",
                        }
                    )
            asset_records.append({**asset, **metadata, "resolved_path": path})
        except (ArtifactError, OSError) as exc:
            issues.append(
                {
                    "code": getattr(exc, "code", "ARTWORK_INVALID"),
                    "message": f"assets[{index}]: {exc}",
                }
            )

    sheet = doc.get("sheet")
    if (
        not isinstance(sheet, dict)
        or not isinstance(sheet.get("title"), str)
        or not sheet["title"].strip()
    ):
        issues.append(
            {
                "code": "SHEET_TITLE_REQUIRED",
                "message": "A character-sheet title is required.",
            }
        )
    else:
        try:
            output = _project_path(project, sheet.get("output"), must_exist=False)
            if output.suffix.lower() != ".svg":
                issues.append(
                    {
                        "code": "SHEET_FORMAT_UNSUPPORTED",
                        "message": "Character sheets are composed as SVG.",
                    }
                )
            if output.exists():
                issues.append(
                    {
                        "code": "OUTPUT_EXISTS",
                        "message": "Character-sheet output already exists; source and prior outputs are never overwritten.",
                    }
                )
            source_paths = {
                str(record.get("resolved_path")) for record in asset_records
            }
            if str(output) in source_paths:
                issues.append(
                    {
                        "code": "OUTPUT_OVERWRITES_SOURCE",
                        "message": "Sheet output cannot overwrite an input asset.",
                    }
                )
        except (ArtifactError, OSError) as exc:
            issues.append(
                {
                    "code": getattr(exc, "code", "SHEET_OUTPUT_INVALID"),
                    "message": f"Sheet output: {exc}",
                }
            )

    if doc.get("status") == "COMPLETE":
        review = doc.get("review")
        if (
            not isinstance(review, dict)
            or review.get("decision") not in {"PASS", "PASS WITH COMMENTS"}
            or review.get("assessed_by") != "visual-quality-review"
        ):
            issues.append(
                {
                    "code": "VISUAL_REVIEW_REQUIRED",
                    "message": "COMPLETE requires a separate passing Visual Quality Review.",
                }
            )

    return {
        "valid": not issues,
        "status": str(doc.get("status", "")),
        "issues": issues,
        "assets": asset_records,
    }


def _append_text(
    parent: ET.Element,
    x: int,
    y: int,
    value: str,
    *,
    size: int = 28,
    weight: str = "400",
    color: str = "#27231f",
) -> None:
    element = ET.SubElement(
        parent,
        f"{{{SVG_NS}}}text",
        {
            "x": str(x),
            "y": str(y),
            "font-size": str(size),
            "font-weight": weight,
            "fill": color,
        },
    )
    element.text = value


def compose_sheet(
    manifest: dict[str, Any], project: Path, output_value: str | None = None
) -> dict[str, Any]:
    validated = validate_manifest(manifest, project)
    if not validated["valid"]:
        _error(
            "MANIFEST_INVALID", "Artwork manifest is invalid; see validation issues."
        )
    asset_records = validated["assets"]
    main_index = next(
        (i for i, item in enumerate(asset_records) if item.get("role") == "full_body"),
        0,
    )
    main_asset = asset_records[main_index]
    side_assets = [
        item for index, item in enumerate(asset_records) if index != main_index
    ]
    sheet = manifest["sheet"]
    output = _project_path(
        project, output_value or sheet.get("output"), must_exist=False
    )
    if output.suffix.lower() != ".svg":
        _error("SHEET_FORMAT_UNSUPPORTED", "Sheet output must use the .svg extension.")
    if output.exists():
        _error(
            "OUTPUT_EXISTS",
            "Character-sheet output already exists; it will not be overwritten.",
        )
    if output in {item["resolved_path"] for item in asset_records}:
        _error(
            "OUTPUT_OVERWRITES_SOURCE", "Sheet output cannot overwrite an input asset."
        )

    rows = max(1, math.ceil(len(side_assets) / 2))
    width = 1800
    height = max(1400, 360 + rows * 420)
    if height > 10_000:
        _error(
            "SHEET_TOO_LARGE",
            "Too many side assets for one sheet; compose smaller groups.",
        )
    root = ET.Element(
        f"{{{SVG_NS}}}svg",
        {
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
            "role": "img",
            "aria-labelledby": "sheet-title sheet-description",
        },
    )
    title = ET.SubElement(root, f"{{{SVG_NS}}}title", {"id": "sheet-title"})
    title.text = str(sheet["title"])
    description = ET.SubElement(root, f"{{{SVG_NS}}}desc", {"id": "sheet-description"})
    description.text = f"{main_asset['label']} plus {len(side_assets)} related character artwork assets."
    ET.SubElement(
        root,
        f"{{{SVG_NS}}}rect",
        {"width": str(width), "height": str(height), "fill": "#f6f0e5"},
    )
    _append_text(root, 70, 92, str(sheet["title"]), size=42, weight="700")
    _append_text(
        root,
        72,
        135,
        "角色身份與風格參考；文字標籤由版面工具排版",
        size=22,
        color="#6c6258",
    )
    ET.SubElement(
        root,
        f"{{{SVG_NS}}}rect",
        {
            "x": "60",
            "y": "175",
            "width": "980",
            "height": str(height - 230),
            "rx": "18",
            "fill": "#fffdf8",
            "stroke": "#d9cfbf",
            "stroke-width": "2",
        },
    )

    def place(
        item: dict[str, Any],
        x: int,
        y: int,
        box_width: int,
        box_height: int,
        label: str,
    ) -> None:
        ET.SubElement(
            root,
            f"{{{SVG_NS}}}rect",
            {
                "x": str(x),
                "y": str(y),
                "width": str(box_width),
                "height": str(box_height),
                "rx": "12",
                "fill": "#fffdf8",
                "stroke": "#d9cfbf",
                "stroke-width": "2",
            },
        )
        image = ET.SubElement(
            root,
            f"{{{SVG_NS}}}image",
            {
                "x": str(x + 16),
                "y": str(y + 16),
                "width": str(box_width - 32),
                "height": str(box_height - 72),
                "preserveAspectRatio": "xMidYMid meet",
                "role": "img",
                "aria-label": label,
            },
        )
        media_type = "image/svg+xml" if item["format"] == "svg" else "image/png"
        image.set(
            "href",
            f"data:{media_type};base64,"
            + base64.b64encode(item["resolved_path"].read_bytes()).decode("ascii"),
        )
        _append_text(root, x + 20, y + box_height - 22, label, size=22, weight="600")

    place(main_asset, 85, 200, 930, height - 280, str(main_asset["label"]))
    for index, item in enumerate(side_assets):
        col = index % 2
        row = index // 2
        place(item, 1090 + col * 335, 205 + row * 420, 310, 390, str(item["label"]))

    payload = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    _validate_svg_bytes(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".character-sheet-", suffix=".svg", dir=output.parent, delete=False
        ) as stream:
            temp_path = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temp_path, output)
        except FileExistsError:
            _error(
                "OUTPUT_EXISTS",
                "Character-sheet output appeared during composition; it was not overwritten.",
            )
        return {
            "status": "PASS",
            "output": output.relative_to(project.resolve()).as_posix(),
            "sha256": sha256_file(output),
            "bytes": output.stat().st_size,
            "asset_count": len(asset_records),
            "visual_quality_inferred": False,
        }
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _result(
    status: str, *, code: str | None = None, message: str | None = None, **values: Any
) -> dict[str, Any]:
    result: dict[str, Any] = {"status": status, **values}
    if code:
        result["code"] = code
    if message:
        result["message"] = message
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate local character-art assets or compose a deterministic SVG character sheet."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser(
        "validate", help="Validate an artwork manifest and its referenced assets."
    )
    validate_parser.add_argument("manifest", type=Path)
    validate_parser.add_argument("--project", type=Path, default=Path.cwd())
    compose_parser = subparsers.add_parser(
        "compose",
        help="Compose a new SVG character sheet without overwriting source files.",
    )
    compose_parser.add_argument("manifest", type=Path)
    compose_parser.add_argument("--project", type=Path, default=Path.cwd())
    compose_parser.add_argument("--output")
    args = parser.parse_args()
    project = args.project.resolve()
    manifest_path = (
        args.manifest if args.manifest.is_absolute() else project / args.manifest
    )
    try:
        manifest = _read_yaml(manifest_path)
        if args.command == "validate":
            result = validate_manifest(manifest, project)
            result = _result(
                "PASS" if result["valid"] else "FAIL",
                manifest_status=result["status"],
                issues=result["issues"],
                asset_count=len(result["assets"]),
                visual_quality_inferred=False,
            )
        else:
            result = compose_sheet(manifest, project, args.output)
    except (ArtifactError, OSError) as exc:
        result = _result(
            "FAIL",
            code=getattr(exc, "code", "IO_ERROR"),
            message=str(exc),
            visual_quality_inferred=False,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
