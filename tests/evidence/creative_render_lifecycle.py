#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import yaml
from playwright.sync_api import sync_playwright


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_helper(path: Path):
    spec = importlib.util.spec_from_file_location("creative_evidence", path)
    require(spec is not None and spec.loader is not None, "Unable to load creative_evidence.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def browser_binary() -> str:
    candidates = [
        os.environ.get("CHROME_BIN"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    for value in candidates:
        if value and Path(value).is_file():
            return str(value)
    raise AssertionError("No system Chrome/Chromium binary available for creative render evidence")


def box_inside(inner: dict, outer: dict, tolerance: float = 1.0) -> bool:
    return (
        inner["x"] >= outer["x"] - tolerance
        and inner["y"] >= outer["y"] - tolerance
        and inner["x"] + inner["width"] <= outer["x"] + outer["width"] + tolerance
        and inner["y"] + inner["height"] <= outer["y"] + outer["height"] + tolerance
    )


def render_capture(page, html: str, screenshot: Path, width: int, height: int) -> dict:
    page.set_viewport_size({"width": width, "height": height})
    page.set_content(html, wait_until="load")
    page.locator("[data-user-asset='logo']").wait_for(state="visible")
    page.locator("[data-user-asset='product']").wait_for(state="visible")

    safe = page.locator("[data-safe-area]").bounding_box()
    headline = page.locator("h1").bounding_box()
    cta = page.locator("[data-cta]").bounding_box()
    logo = page.locator("[data-user-asset='logo']").bounding_box()
    product = page.locator("[data-user-asset='product']").bounding_box()
    require(all(item is not None for item in (safe, headline, cta, logo, product)), "required banner geometry missing")
    require(box_inside(headline, safe), "headline escaped the banner safe area")
    require(box_inside(cta, safe), "CTA escaped the banner safe area")
    require(box_inside(logo, safe), "logo escaped the banner safe area")
    require(box_inside(product, safe), "product escaped the banner safe area")

    overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    require(overflow is False, "banner has horizontal overflow")

    asset_state = page.evaluate(
        """() => Array.from(document.querySelectorAll('[data-user-asset]')).map(el => ({
            type: el.dataset.userAsset,
            src: el.getAttribute('src'),
            sourcePath: el.dataset.sourcePath,
            naturalWidth: el.naturalWidth,
            naturalHeight: el.naturalHeight,
            objectFit: getComputedStyle(el).objectFit,
            visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
        }))"""
    )
    by_type = {item["type"]: item for item in asset_state}
    require(by_type["logo"]["sourcePath"] == "assets/logo.svg", f"logo source path changed: {by_type['logo']}")
    require(by_type["product"]["sourcePath"] == "assets/product.svg", f"product source path changed: {by_type['product']}")
    require(by_type["logo"]["src"].startswith("data:image/svg+xml;base64,"), "logo must render exact user-owned bytes")
    require(by_type["product"]["src"].startswith("data:image/svg+xml;base64,"), "product must render exact user-owned bytes")
    for asset_type in ("logo", "product"):
        require(by_type[asset_type]["naturalWidth"] > 0, f"{asset_type} did not load")
        require(by_type[asset_type]["naturalHeight"] > 0, f"{asset_type} did not load")
        require(by_type[asset_type]["visible"] is True, f"{asset_type} is not visible")
        require(by_type[asset_type]["objectFit"] == "contain", f"{asset_type} crop/presentation is not preserved")

    screenshot.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(screenshot), full_page=True)
    require(screenshot.is_file() and screenshot.stat().st_size > 0, "screenshot was not created")
    return {"safe": safe, "headline": headline, "cta": cta, "assets": asset_state}


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    helper_path = root / "scripts" / "creative_evidence.py"
    agent_eval = root / "scripts" / "agent_eval.py"
    creative_protocol = root / "orchestration" / "CREATIVE_DIRECTION.md"
    template = root / "templates" / "creative" / "CREATIVE_EVIDENCE.yaml"
    requirements = [
        helper_path,
        agent_eval,
        creative_protocol,
        template,
        root / "templates" / "creative" / "CREATIVE_BRIEF.md",
        root / "templates" / "creative" / "REFERENCE_BOARD.md",
        root / "templates" / "creative" / "CREATIVE_DIRECTION.yaml",
        root / "templates" / "creative" / "VISUAL_REVIEW.md",
        root / "skills" / "design" / "creative-calibration" / "SKILL.md",
        root / "skills" / "design" / "creative-reference-research" / "SKILL.md",
        root / "skills" / "design" / "visual-quality-review" / "SKILL.md",
        root / "tests" / "agent_eval" / "cases" / "021-vague-visual-request.yaml",
        root / "tests" / "agent_eval" / "results" / "021-vague-visual-request.yaml",
        root / "tests" / "agent_eval" / "cases" / "022-user-assets-banner.yaml",
        root / "tests" / "agent_eval" / "results" / "022-user-assets-banner.yaml",
    ]
    for path in requirements:
        require(path.is_file(), f"required creative evidence artifact missing: {path.relative_to(root)}")

    protocol = creative_protocol.read_text(encoding="utf-8")
    require("2–3 Differentiated Directions" in protocol, "creative protocol must retain differentiated direction calibration")
    require("user-owned assets and references" in protocol, "creative protocol must prioritize user-owned inputs")
    helper = load_helper(helper_path)

    for scenario in ("021-vague-visual-request", "022-user-assets-banner"):
        scored = subprocess.run(
            [
                sys.executable,
                str(agent_eval),
                "score",
                "--case",
                str(root / "tests" / "agent_eval" / "cases" / f"{scenario}.yaml"),
                "--result",
                str(root / "tests" / "agent_eval" / "results" / f"{scenario}.yaml"),
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        require(scored.returncode == 0, f"Agent Eval failed for {scenario}: {scored.stdout} {scored.stderr}")
        scored_doc = json.loads(scored.stdout)
        require(scored_doc["status"] == "PASS", f"Agent Eval did not PASS for {scenario}: {scored_doc}")

    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "creative-project"
        assets_dir = project / "assets"
        evidence_dir = project / "evidence"
        assets_dir.mkdir(parents=True)
        evidence_dir.mkdir(parents=True)

        logo = assets_dir / "logo.svg"
        product = assets_dir / "product.svg"
        logo.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="72" viewBox="0 0 240 72">'
            '<rect width="240" height="72" rx="12" fill="#161616"/>'
            '<text x="120" y="45" text-anchor="middle" font-family="Arial" font-size="28" fill="#f7f0e7">ATELIER</text>'
            "</svg>", encoding="utf-8")
        product.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="520" viewBox="0 0 480 520">'
            '<rect width="480" height="520" rx="40" fill="#eee5da"/>'
            '<rect x="135" y="65" width="210" height="390" rx="46" fill="#1f1f1f"/>'
            '<circle cx="240" cy="190" r="62" fill="#c9ad83"/>'
            '<text x="240" y="360" text-anchor="middle" font-family="Arial" font-size="26" fill="#f7f0e7">SERUM</text>'
            "</svg>", encoding="utf-8")
        before_hashes = {"logo": sha256_file(logo), "product": sha256_file(product)}

        creative_brief = project / "CREATIVE_BRIEF.md"
        creative_brief.write_text(
            "# Creative Brief\n\n## Artifact\nWebsite hero banner; desktop and mobile.\n\n"
            "## User-provided Assets\n- REQUIRED: assets/logo.svg — preserve exact user-owned logo.\n"
            "- REQUIRED: assets/product.svg — preserve exact product artwork.\n\n"
            "## Desired Feel\nPremium, minimal, fashionable.\n\n"
            "## Success Criteria\nDirection approved before implementation; preserve assets; readable headline/CTA; safe responsive crop.\n",
            encoding="utf-8")

        reference_board = project / "REFERENCE_BOARD.md"
        reference_board.write_text(
            "# Reference Board\n\n## User-provided References\n"
            "| Reference | What the user likes | What not to copy | Aspect |\n|---|---|---|---|\n"
            "| Ref A | split editorial composition | exact arrangement/content | layout |\n"
            "| Ref B | warm neutral palette | exact colors/artwork | color |\n"
            "| Ref C | fashion serif contrast | exact type treatment | typography |\n\n"
            "## Runtime Research\nCurrent premium editorial references were used for trait calibration only; third-party assets are not stored.\n\n"
            "## Candidate Directions\n### Direction A — Quiet Luxury Split\nWarm neutral, split layout, restrained serif/sans pairing.\n"
            "### Direction B — Monochrome Editorial\nHigh-contrast monochrome, oversized editorial type, asymmetric whitespace.\n"
            "### Direction C — Fashion Grid\nStructured modular grid, compact sans typography, product-forward imagery.\n\n"
            "## Selected Direction\nA layout + B typography restraint.\n",
            encoding="utf-8")

        creative_direction = project / "CREATIVE_DIRECTION.yaml"
        creative_direction.write_text(yaml.safe_dump({
            "version": 1,
            "status": "approved",
            "artifact_type": "website_banner",
            "brand_profile": "approved-brand-profile",
            "style_mix": ["direction-a:layout", "direction-b:typography"],
            "reference_mapping": {"layout": "Ref A", "color": "Ref B", "typography": "Ref C", "imagery": "user-owned product asset", "motion": None},
            "traits": {"must_have": ["preserve logo", "preserve product", "generous whitespace", "clear CTA"], "must_avoid": ["literal reference copy", "cropped logo", "busy decorative effects"]},
            "axes": {"premium": 0.9, "minimal": 0.85, "playful": 0.15, "warm": 0.65, "technical": 0.1, "editorial": 0.8},
            "assets": {"required": ["assets/logo.svg", "assets/product.svg"], "optional": []},
            "notes": ["Approved before broad implementation after calibration of likes/dislikes and aspect mixing."],
        }, sort_keys=False), encoding="utf-8")

        visual_review = project / "VISUAL_REVIEW.md"
        visual_review.write_text(
            "# Visual Review\n\nDecision: PASS\nArtifact: banner.html\nCreative Direction: CREATIVE_DIRECTION.yaml\nBrand Profile: approved-brand-profile\n\n"
            "## Findings\n| Area | Result | Evidence | Recommendation |\n|---|---|---|---|\n"
            "| Composition | PASS | desktop/mobile renders | none |\n"
            "| Headline / CTA readability | PASS | visible inside safe area | none |\n"
            "| Safe area | PASS | measured geometry | none |\n"
            "| Crop | PASS | required assets use contain | none |\n"
            "| Brand consistency | PASS | approved direction + exact assets | none |\n\n## Decision\nPASS\n",
            encoding="utf-8")

        logo_data = "data:image/svg+xml;base64," + base64.b64encode(logo.read_bytes()).decode("ascii")
        product_data = "data:image/svg+xml;base64," + base64.b64encode(product.read_bytes()).decode("ascii")
        banner = project / "banner.html"
        banner_html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box}} html,body{{margin:0;min-width:0;background:#efe8df;color:#181716;font-family:Arial,sans-serif}}
.hero{{min-height:100vh;display:flex;align-items:stretch;overflow:hidden}}
.safe{{width:100%;max-width:1440px;margin:auto;padding:48px 64px;display:grid;grid-template-columns:minmax(0,1fr) minmax(280px,.72fr);gap:48px;align-items:center}}
.copy{{min-width:0}}.logo{{width:180px;height:54px;object-fit:contain;display:block;margin-bottom:54px}}
.eyebrow{{letter-spacing:.18em;text-transform:uppercase;font-size:13px;margin:0 0 16px}}
h1{{font-family:Georgia,serif;font-weight:500;font-size:clamp(44px,6vw,86px);line-height:.96;max-width:760px;margin:0 0 28px}}
p{{max-width:560px;font-size:18px;line-height:1.5;margin:0 0 30px}}
.cta{{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:0 24px;border:1px solid #181716;color:#181716;text-decoration:none;font-weight:700}}
.visual{{min-width:0;display:flex;justify-content:center}}.product{{display:block;width:min(100%,430px);height:min(62vh,520px);object-fit:contain}}
@media(max-width:700px){{.safe{{padding:28px 24px 36px;grid-template-columns:1fr;gap:24px}}.logo{{width:145px;height:44px;margin-bottom:30px}}h1{{font-size:48px}}.visual{{order:-1}}.product{{height:260px;width:100%}}p{{font-size:16px}}}}
</style></head><body><section class="hero"><div class="safe" data-safe-area><div class="copy">
<img class="logo" data-user-asset="logo" data-source-path="assets/logo.svg" src="{logo_data}" alt="Atelier logo">
<p class="eyebrow">Daily ritual / refined</p><h1>Quiet confidence, made visible.</h1>
<p>A focused serum presented with restrained editorial rhythm and the original product artwork.</p>
<a class="cta" data-cta href="#shop">Discover the ritual</a></div><div class="visual">
<img class="product" data-user-asset="product" data-source-path="assets/product.svg" src="{product_data}" alt="Serum product">
</div></div></section></body></html>'''
        banner.write_text(banner_html, encoding="utf-8")

        desktop_shot = evidence_dir / "banner-desktop.png"
        mobile_shot = evidence_dir / "banner-mobile.png"
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=browser_binary(), headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            page = browser.new_page()
            desktop_state = render_capture(page, banner_html, desktop_shot, 1440, 640)
            mobile_state = render_capture(page, banner_html, mobile_shot, 390, 640)
            browser.close()

        for state in (desktop_state, mobile_state):
            by_type = {item["type"]: item for item in state["assets"]}
            for asset_type, source_path in (("logo", logo), ("product", product)):
                encoded = by_type[asset_type]["src"].split(",", 1)[1]
                require(base64.b64decode(encoded) == source_path.read_bytes(), f"{asset_type} rendered bytes differ from user-owned source")

        after_hashes = {"logo": sha256_file(logo), "product": sha256_file(product)}
        require(before_hashes == after_hashes, "user-owned source assets changed during banner lifecycle")

        candidates = [
            {"id": "A", "fingerprint": "split-warm-serif"},
            {"id": "B", "fingerprint": "asymmetric-monochrome-editorial"},
            {"id": "C", "fingerprint": "modular-fashion-grid"},
        ]
        common = {
            "version": 1,
            "status": "PASS",
            "intake": {"approved_brand_visual_system_loaded": True, "user_assets_loaded": True},
            "references": {"analyzed_by_aspect": True, "literal_copy": False, "aspects": ["layout", "color", "typography", "imagery"]},
            "direction": {"candidates": candidates, "selected": "A"},
            "calibration": {"likes": ["Direction A layout", "Direction B typography restraint"], "dislikes": ["busy ornament", "literal reference copying"], "aspect_mix": ["A:layout", "B:typography"]},
            "approval": {"status": "approved", "before_broad_implementation": True},
            "artifacts": {"creative_brief": creative_brief.name, "reference_board": reference_board.name, "creative_direction": creative_direction.name, "visual_review": visual_review.name},
            "assets": [
                {"type": "logo", "path": "assets/logo.svg", "required": True, "sha256_before": before_hashes["logo"], "sha256_after": after_hashes["logo"], "used_in_render": True, "visible": True, "crop_reviewed": True},
                {"type": "product", "path": "assets/product.svg", "required": True, "sha256_before": before_hashes["product"], "sha256_after": after_hashes["product"], "used_in_render": True, "visible": True, "crop_reviewed": True},
            ],
            "renders": {
                "captures": [
                    {"viewport": {"label": "desktop", "width": 1440, "height": 640}, "artifact": "evidence/banner-desktop.png"},
                    {"viewport": {"label": "mobile", "width": 390, "height": 640}, "artifact": "evidence/banner-mobile.png"},
                ],
                "checks": {"required_assets_visible": True, "safe_area_respected": True, "headline_cta_visible": True, "crop_reviewed": True, "no_horizontal_overflow": True},
            },
            "review": {"decision": "PASS", "quality_assessed_by": "visual_review", "checks": ["composition", "headline_cta_readability", "safe_area", "crop", "brand_consistency"]},
        }

        vague = yaml.safe_load(yaml.safe_dump(common))
        vague["mode"] = "vague_visual_request"
        vague["references"]["current_research_used_when_unclear"] = True
        vague_path = evidence_dir / "CREATIVE_EVIDENCE_021.yaml"
        vague_path.write_text(yaml.safe_dump(vague, sort_keys=False), encoding="utf-8")

        banner_evidence = yaml.safe_load(yaml.safe_dump(common))
        banner_evidence["mode"] = "user_asset_banner"
        banner_evidence["references"]["current_research_used_when_unclear"] = False
        banner_path = evidence_dir / "CREATIVE_EVIDENCE_022.yaml"
        banner_path.write_text(yaml.safe_dump(banner_evidence, sort_keys=False), encoding="utf-8")

        for evidence_path, document in ((vague_path, vague), (banner_path, banner_evidence)):
            checked = helper.validate(document, project)
            require(checked["valid"] is True, json.dumps(checked, indent=2))
            require(checked["visual_quality_inferred"] is False, "evidence validator must not infer visual taste")
            cli = subprocess.run([sys.executable, str(helper_path), str(evidence_path), "--project", str(project), "--format", "json"], capture_output=True, text=True, timeout=10)
            require(cli.returncode == 0, cli.stdout + cli.stderr)

        no_lock = yaml.safe_load(yaml.safe_dump(vague))
        no_lock["approval"]["before_broad_implementation"] = False
        require(helper.validate(no_lock, project)["valid"] is False, "vague request without direction lock must fail closed")

        literal_copy = yaml.safe_load(yaml.safe_dump(banner_evidence))
        literal_copy["references"]["literal_copy"] = True
        require(helper.validate(literal_copy, project)["valid"] is False, "literal reference copying must fail closed")

        replaced_asset = yaml.safe_load(yaml.safe_dump(banner_evidence))
        replaced_asset["assets"][0]["sha256_after"] = "sha256:" + ("0" * 64)
        require(helper.validate(replaced_asset, project)["valid"] is False, "changed required user-owned asset must fail closed")

        skipped_review = yaml.safe_load(yaml.safe_dump(banner_evidence))
        skipped_review["review"]["decision"] = "REQUEST CHANGES"
        require(helper.validate(skipped_review, project)["valid"] is False, "PASS cannot survive a non-passing Visual Quality Review")

    print("CREATIVE RENDER LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
