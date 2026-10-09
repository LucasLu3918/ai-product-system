"""Deterministic evidence for creative prompts, model advice, and local visual review."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import creative_execution as creative


def main() -> int:
    character = {
        "version": 1, "id": "mira", "name": "Mira", "summary": "A copper-haired explorer.",
        "identity_features": ["copper bob", "green eyes"], "must_preserve": ["crescent pin"],
        "acceptance_criteria": {"critical_features": ["scar above left eyebrow"], "forbidden_misplacements": ["scar on cheek"]},
        "allowed_variations": {"expressions": ["joyful"], "poses": ["three-quarter"], "outfit_variants": []},
        "must_avoid": ["photorealistic skin"],
    }
    style = {
        "version": 1, "id": "cel-anime", "intent": "Japanese fantasy anime illustration",
        "rendering": {"medium": "anime illustration", "linework": "fine expressive linework", "shading": "soft cel shading", "finish": "polished concept art"},
        "composition": {"framing": "full body", "background": "lantern-lit shrine"},
        "prompt_constraints": {"must_include": ["clear 2D anime proportions"], "must_avoid": ["photographic skin"]},
        "must_avoid": [],
    }
    collection = {"version": 1, "collection_id": "harry-hermione", "visual_direction": "Shared Japanese fantasy illustration",
                 "style_lock": {"id": "shared-cel", "must_match": ["consistent cel shading"], "must_avoid": ["photorealism"], "palette": ["indigo", "warm gold"]}}
    bundle = {"prompt": "A full-body spellcaster under cherry blossoms", "operation": "generate"}
    compiled = creative.compile_creative_prompt(bundle, {"character": character, "style": style, "collection": collection})
    for token in (bundle["prompt"], "green eyes", "scar above left eyebrow", "scar on cheek", "three-quarter", "soft cel shading", "consistent cel shading", "warm gold", "photographic skin"):
        assert token in compiled, token

    model_profile = {"version": 1, "models": [
        {"id": "verified-anime", "operations": ["generate"], "capabilities": ["anime illustration", "cel shading"],
         "availability": "VERIFIED_LOCAL", "license_status": "VERIFIED",
         "quality_review": {"status": "HUMAN_REVIEWED", "style_score": 5, "character_consistency_score": 4, "evidence": "local comparison sha256:abc"}},
        {"id": "unverified", "operations": ["generate"], "capabilities": ["anime illustration"],
         "availability": "UNVERIFIED", "license_status": "UNVERIFIED"},
    ]}
    advice = creative.model_recommendation(bundle, {"style": style, "model_capabilities": model_profile})
    assert advice["status"] == "RECOMMENDATIONS_AVAILABLE" and advice["selected_model_changed"] is False
    assert advice["models"][0]["id"] == "verified-anime" and advice["models"][0]["status"] == "EVIDENCE_BACKED"
    assert all(item["status"] == "INSUFFICIENT_EVIDENCE" for item in advice["models"] if item["id"] == "unverified")
    assert creative.model_recommendation(bundle, {"style": style})["reason_code"] == "model_capability_profile_not_configured"

    with tempfile.TemporaryDirectory(prefix="aips-creative-quality-") as temporary:
        project = Path(temporary)
        output = project / "output"
        output.mkdir()
        image = output / "image.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\nfixture image bytes")
        profile_rows = []
        for filename, data in (("CHARACTER_PROFILE.yaml", character), ("STYLE_PROFILE.yaml", style),
                               ("CREATIVE_COLLECTION_PROFILE.yaml", collection)):
            path = project / filename
            import yaml
            path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            profile_rows.append({"path": filename, "sha256": creative.digest(path)})
        manifest_path = output / "creative-execution-manifest.json"
        manifest = {"version": 1, "status": "COMPLETE", "output_scope": "output",
                    "output": {"path": "output/image.png", "sha256": creative.digest(image)},
                    "profiles": profile_rows,
                    "review": {"status": "PENDING"},
                    "acceptance": {"visual_quality": "PENDING", "user_acceptance": "NOT_RECORDED"}}
        original = json.dumps(manifest, sort_keys=True).encode()
        manifest_path.write_bytes(original)
        calls = []
        observations = [{"check": "identity", "assessment": "POSSIBLE_ISSUE", "evidence": "Scar placement is uncertain.", "suggestion": "Human should inspect the forehead."}]
        def fake_local_request(url, *, data=None, headers=None, timeout=2.0, max_bytes=creative.MAX_IMAGE_BYTES):
            calls.append((url, data, headers, timeout, max_bytes))
            if url == creative.DEFAULT_OLLAMA_BASE_URL + "/api/tags":
                return json.dumps({"models": [{"name": "vision-local"}]}).encode()
            assert url == creative.DEFAULT_OLLAMA_BASE_URL + "/api/chat"
            request = json.loads(data)
            assert request["model"] == "vision-local" and request["stream"] is False
            assert len(request["messages"][0]["images"]) == 1
            assert "You do not decide PASS/FAIL" in request["messages"][0]["content"]
            return json.dumps({"message": {"content": json.dumps({"observations": observations})}}).encode()
        creative.local_request = fake_local_request
        first = creative.review_assist(project, "output/creative-execution-manifest.json", "vision-local")
        second = creative.review_assist(project, "output/creative-execution-manifest.json", "vision-local")
        assert first["status"] == "ADVISORY_REVIEW" and second["report"].endswith("creative-visual-review-v2.json")
        assert first["external_image_egress"] is False and first["human_review_required"] is True
        assert manifest_path.read_bytes() == original
        report = json.loads((project / first["report"]).read_text())
        assert report["authority"] == "NONE" and report["user_acceptance"] == "NOT_RECORDED"
        assert report["observations"] == observations and "images" not in report and "image_bytes" not in report
        assert [call[0] for call in calls] == [creative.DEFAULT_OLLAMA_BASE_URL + "/api/tags", creative.DEFAULT_OLLAMA_BASE_URL + "/api/chat"] * 2
        calls.clear()
        try:
            creative.review_assist(project, "output/creative-execution-manifest.json", "not-installed")
        except creative.Blocked as exc:
            assert exc.reason_code == "visual_review_model_not_installed"
        else:
            raise AssertionError("review assist accepted a model absent from the local inventory")
        assert len(calls) == 1, "A missing local model must not receive an inference request or download"
        image.write_bytes(b"tampered")
        try:
            creative.review_assist(project, "output/creative-execution-manifest.json", "vision-local")
        except creative.Blocked as exc:
            assert exc.reason_code == "manifest_hash_mismatch"
        else:
            raise AssertionError("tampered image passed provenance validation")
    print("Creative quality lifecycle PASS: profile compilation, evidence-ranked advice, local-only advisory review, create-only reports, and provenance integrity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
