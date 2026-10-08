#!/usr/bin/env python3
"""Exercise local character-art provenance and deterministic sheet composition."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import character_artifacts as artwork
import creative_evidence


def png_chunk(name: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + name
        + payload
        + struct.pack(">I", zlib.crc32(name + payload) & 0xFFFFFFFF)
    )


def tiny_png() -> bytes:
    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
        + png_chunk(b"IEND", b"")
    )


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def expect_issue(result: dict, code: str) -> None:
    assert any(item["code"] == code for item in result["issues"]), (
        code,
        result["issues"],
    )


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="aips-character-art-") as temporary:
        project = Path(temporary)
        (project / "assets").mkdir()
        (project / "output").mkdir()
        reference = project / "assets/reference.svg"
        reference.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="100"><circle cx="40" cy="40" r="20"/></svg>',
            encoding="utf-8",
        )
        full = project / "output/full.svg"
        full.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="160"><rect width="100" height="160" fill="#eee"/></svg>',
            encoding="utf-8",
        )
        expression = project / "output/joy.png"
        expression.write_bytes(tiny_png())
        profile = {
            "version": 1,
            "id": "mira",
            "name": "Mira",
            "summary": "A copper-haired explorer.",
            "identity_features": ["copper bob", "green eyes"],
            "must_preserve": ["crescent pin"],
            "allowed_variations": {
                "expressions": ["joyful"],
                "poses": ["front"],
                "outfit_variants": [],
            },
            "must_avoid": [],
            "palette": {"primary": [], "secondary": [], "accent": []},
            "references": [
                {
                    "path": "assets/reference.svg",
                    "sha256": sha(reference),
                    "role": "identity-reference",
                }
            ],
            "privacy": {
                "raw_prompt_persistence": "forbidden",
                "external_upload": "forbidden_by_default",
            },
        }
        style = {
            "version": 1,
            "id": "soft-cel",
            "name": "Soft cel",
            "intent": "Warm, expressive concept art.",
            "rendering": {"medium": "illustration"},
            "composition": {
                "text_policy": "typeset labels after image generation; never ask the image model to render text"
            },
            "reference_policy": {"extract_traits_only": True, "literal_copy": False},
            "must_avoid": [],
        }
        write_yaml(project / "CHARACTER_PROFILE.yaml", profile)
        write_yaml(project / "STYLE_PROFILE.yaml", style)
        manifest = {
            "version": 1,
            "status": "DRAFT",
            "character_profile": "CHARACTER_PROFILE.yaml",
            "style_profile": "STYLE_PROFILE.yaml",
            "execution": {
                "provider_id": "comfy_mcp_local",
                "model_id": "fixture-model@rev1",
                "runtime": {"name": "ComfyUI", "version": "fixture"},
                "model_license": {
                    "name": "Fixture License",
                    "spdx": None,
                    "source_url": "https://example.org/license",
                },
                "prompt_fingerprint": None,
                "external_egress": False,
                "performance": {
                    "measured": False,
                    "device": None,
                    "elapsed_ms": None,
                    "peak_memory_bytes": None,
                },
            },
            "assets": [
                {
                    "id": "full",
                    "role": "full_body",
                    "label": "全身立繪",
                    "path": "output/full.svg",
                    "format": "svg",
                    "width": 100,
                    "height": 160,
                    "sha256": sha(full),
                    "source_assets": [
                        {"path": "assets/reference.svg", "sha256": sha(reference)}
                    ],
                },
                {
                    "id": "joy",
                    "role": "expression",
                    "label": "喜悅表情",
                    "path": "output/joy.png",
                    "format": "png",
                    "width": 1,
                    "height": 1,
                    "sha256": sha(expression),
                    "source_assets": [
                        {"path": "assets/reference.svg", "sha256": sha(reference)}
                    ],
                },
            ],
            "sheet": {"title": "Mira 角色設定", "output": "output/sheet.svg"},
            "review": {
                "decision": "PENDING",
                "assessed_by": "visual-quality-review",
                "notes": [],
            },
        }

        checked = artwork.validate_manifest(manifest, project)
        assert checked["valid"], checked["issues"]
        assert artwork.inspect_asset(expression)["format"] == "png"
        first = artwork.compose_sheet(manifest, project)
        first_bytes = (project / first["output"]).read_bytes()
        assert "喜悅表情" in first_bytes.decode("utf-8")
        assert "image/png;base64," in first_bytes.decode("utf-8")
        manifest["sheet"]["output"] = "output/sheet-copy.svg"
        second = artwork.compose_sheet(manifest, project)
        assert first["sha256"] == second["sha256"]
        assert first_bytes == (project / second["output"]).read_bytes()
        try:
            artwork.compose_sheet(manifest, project)
        except artwork.ArtifactError as exc:
            assert exc.code == "MANIFEST_INVALID"
            assert any(
                item["code"] == "OUTPUT_EXISTS"
                for item in artwork.validate_manifest(manifest, project)["issues"]
            )
            assert (project / second["output"]).read_bytes() == first_bytes
        else:
            raise AssertionError("existing outputs must never be overwritten")

        bad = dict(manifest)
        bad["execution"] = {**manifest["execution"], "provider_id": "cloud_api"}
        expect_issue(artwork.validate_manifest(bad, project), "PROVIDER_NOT_LOCAL")
        bad = dict(manifest)
        bad["execution"] = {**manifest["execution"], "external_egress": True}
        expect_issue(artwork.validate_manifest(bad, project), "EXTERNAL_EGRESS")
        bad = dict(manifest)
        bad["execution"] = {
            **manifest["execution"],
            "model_license": {"name": "unknown", "source_url": "https://example.org"},
        }
        expect_issue(artwork.validate_manifest(bad, project), "MODEL_LICENSE_UNKNOWN")
        bad = dict(manifest)
        bad["assets"] = [{**manifest["assets"][0], "sha256": "sha256:" + "0" * 64}]
        expect_issue(
            artwork.validate_manifest(bad, project), "ARTWORK_METADATA_MISMATCH"
        )
        bad = dict(manifest)
        bad["assets"] = [{**manifest["assets"][0], "path": "../escape.svg"}]
        expect_issue(artwork.validate_manifest(bad, project), "PATH_OUTSIDE_PROJECT")
        bad_svg = project / "output/bad.svg"
        bad_svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><script>alert(1)</script></svg>',
            encoding="utf-8",
        )
        try:
            artwork.inspect_asset(bad_svg)
        except artwork.ArtifactError as exc:
            assert exc.code == "SVG_ACTIVE_CONTENT"
        else:
            raise AssertionError("active SVG content must be rejected")
        broken_png = project / "output/broken.png"
        broken_png.write_bytes(tiny_png()[:-5] + b"xxxxx")
        try:
            artwork.inspect_asset(broken_png)
        except artwork.ArtifactError:
            pass
        else:
            raise AssertionError("invalid PNG chunk checksums must be rejected")
        invalid_zlib = project / "output/invalid-zlib.png"
        invalid_zlib.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + png_chunk(b"IDAT", b"not-zlib")
            + png_chunk(b"IEND", b"")
        )
        try:
            artwork.inspect_asset(invalid_zlib)
        except artwork.ArtifactError as exc:
            assert exc.code == "PNG_IMAGE_DATA_INVALID"
        else:
            raise AssertionError("invalid PNG zlib streams must be rejected")
        bad_style = project / "output/bad-style.svg"
        bad_style.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><style>@import url(https://example.org/a.css);</style></svg>',
            encoding="utf-8",
        )
        try:
            artwork.inspect_asset(bad_style)
        except artwork.ArtifactError as exc:
            assert exc.code == "SVG_EXTERNAL_REFERENCE"
        else:
            raise AssertionError("external SVG style imports must be rejected")

        evidence_manifest = project / "evidence/ARTWORK.yaml"
        evidence_manifest.parent.mkdir()
        evidence_manifest.write_text("version: 1\n", encoding="utf-8")
        minimal_evidence = {
            "character_artwork": {
                "manifest": "evidence/ARTWORK.yaml",
                "sha256": sha(evidence_manifest),
            }
        }
        linked = creative_evidence.validate(minimal_evidence, project)
        assert not any(
            "character_artwork" in message for message in linked["errors"]
        ), linked["errors"]
        minimal_evidence["character_artwork"]["sha256"] = "sha256:" + "0" * 64
        mismatch = creative_evidence.validate(minimal_evidence, project)
        assert any("digest does not match" in message for message in mismatch["errors"])
        minimal_evidence["character_artwork"] = {
            "manifest": "../ARTWORK.yaml",
            "sha256": sha(evidence_manifest),
        }
        escaped = creative_evidence.validate(minimal_evidence, project)
        assert any(
            "character_artwork.manifest is invalid" in message
            for message in escaped["errors"]
        )
        minimal_evidence["character_artwork"] = {
            "manifest": "evidence\\..\\ARTWORK.yaml",
            "sha256": sha(evidence_manifest),
        }
        windows_path = creative_evidence.validate(minimal_evidence, project)
        assert any(
            "character_artwork.manifest is invalid" in message
            for message in windows_path["errors"]
        )

        manifest["sheet"]["output"] = "output/cli.svg"
        manifest_path = project / "manifest.yaml"
        write_yaml(manifest_path, manifest)
        cli = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/character_artifacts.py"),
                "validate",
                "manifest.yaml",
                "--project",
                str(project),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert cli.returncode == 0, cli.stdout + cli.stderr
        assert json.loads(cli.stdout)["status"] == "PASS"
    print("Character artwork lifecycle: PASS")


if __name__ == "__main__":
    run()
