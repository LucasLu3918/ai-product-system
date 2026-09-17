#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

import yaml
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
VISUAL_EVIDENCE = ROOT / "scripts" / "visual_evidence.py"

BEFORE_CSS = r"""
:root {
  --control-height: 40px;
  --tag-height: 28px;
  --radius: 8px;
  --space: 8px;
  --ink: #1d2939;
  --muted: #667085;
  --line: #d0d5dd;
  --accent: #2563eb;
  --surface: #ffffff;
  --soft: #f2f4f7;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: Arial, sans-serif; color: var(--ink); background: #f8fafc; }
.shell { max-width: 960px; margin: 0 auto; padding: 24px; }
.nav { display: flex; gap: 8px; border-bottom: 1px solid var(--line); margin-bottom: 24px; overflow-x: auto; }
.nav-item { height: 40px; display: inline-flex; align-items: center; padding: 0 12px; border: 0; border-bottom: 2px solid transparent; background: transparent; color: var(--muted); font: inherit; }
.nav-item[aria-current="page"] { height: 44px; padding: 2px 12px 0; border-bottom-width: 4px; border-bottom-color: var(--accent); color: var(--ink); }
.card { background: var(--surface); border: 1px solid #e4e7ec; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
.row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
.button { height: var(--control-height); display: inline-flex; align-items: center; justify-content: center; padding: 0 16px; border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface); color: var(--ink); font-size: 14px; line-height: 20px; }
.button--primary { height: 44px; padding: 0 20px; background: var(--accent); border-color: var(--accent); color: white; }
.button--primary:hover { background: #1d4ed8; }
.button--primary:focus { outline: 3px solid #bfdbfe; outline-offset: 2px; }
.tag { height: var(--tag-height); display: inline-flex; align-items: center; padding: 0 10px; border: 1px solid var(--line); border-radius: 999px; background: var(--soft); color: var(--ink); font-size: 13px; line-height: 18px; }
.tag--featured { height: 32px; padding: 0 13px; background: #eff6ff; border-color: #bfdbfe; color: #1d4ed8; }
.tag--compact { height: 24px; padding: 0 8px; font-size: 12px; line-height: 16px; }
.tag[aria-pressed="true"] { background: #dbeafe; border-color: var(--accent); }
.input { height: var(--control-height); padding: 0 12px; border: 1px solid var(--line); border-radius: var(--radius); background: white; color: var(--ink); font-size: 14px; line-height: 20px; }
.input--search { height: 44px; padding: 0 16px; }
@media (max-width: 520px) {
  .shell { padding: 14px; }
  .card { padding: 16px; }
}
""".strip() + "\n"

FIXED_CSS = r"""
:root {
  --control-height: 40px;
  --tag-height: 28px;
  --radius: 8px;
  --space: 8px;
  --ink: #1d2939;
  --muted: #667085;
  --line: #d0d5dd;
  --accent: #2563eb;
  --surface: #ffffff;
  --soft: #f2f4f7;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: Arial, sans-serif; color: var(--ink); background: #f8fafc; }
.shell { max-width: 960px; margin: 0 auto; padding: 24px; }
.nav { display: flex; gap: 8px; border-bottom: 1px solid var(--line); margin-bottom: 24px; overflow-x: auto; }
.nav-item { height: 40px; display: inline-flex; align-items: center; padding: 0 12px; border: 0; border-bottom: 2px solid transparent; background: transparent; color: var(--muted); font: inherit; }
.nav-item[aria-current="page"] { height: 40px; padding: 0 12px; border-bottom-width: 2px; border-bottom-color: var(--accent); color: var(--ink); }
.card { background: var(--surface); border: 1px solid #e4e7ec; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
.row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
.button { height: var(--control-height); display: inline-flex; align-items: center; justify-content: center; padding: 0 16px; border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface); color: var(--ink); font-size: 14px; line-height: 20px; }
.button--primary { height: var(--control-height); padding: 0 16px; background: var(--accent); border-color: var(--accent); color: white; }
.button--primary:hover { background: #1d4ed8; }
.button--primary:focus { outline: 3px solid #bfdbfe; outline-offset: 2px; }
.tag { height: var(--tag-height); display: inline-flex; align-items: center; padding: 0 10px; border: 1px solid var(--line); border-radius: 999px; background: var(--soft); color: var(--ink); font-size: 13px; line-height: 18px; }
.tag--featured { height: var(--tag-height); padding: 0 10px; background: #eff6ff; border-color: #bfdbfe; color: #1d4ed8; }
.tag--compact { height: 24px; padding: 0 8px; font-size: 12px; line-height: 16px; }
.tag[aria-pressed="true"] { background: #dbeafe; border-color: var(--accent); }
.input { height: var(--control-height); padding: 0 12px; border: 1px solid var(--line); border-radius: var(--radius); background: white; color: var(--ink); font-size: 14px; line-height: 20px; }
.input--search { height: var(--control-height); padding: 0 12px; }
@media (max-width: 520px) {
  .shell { padding: 14px; }
  .card { padding: 16px; }
}
""".strip() + "\n"

HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="../styles/shared.css">
</head>
<body>
  <main class="shell">
    <nav class="nav" aria-label="Primary">
      <button class="nav-item" data-component="Nav" data-variant="default" data-golden="true" data-source="src/styles/shared.css">Home</button>
      <button class="nav-item" data-component="Nav" data-variant="current" data-source="src/styles/shared.css" aria-current="page">{title}</button>
    </nav>
    <section class="card">
      <h1>{title}</h1>
      <p>Representative route for executable visual consistency evidence.</p>
      <div class="row">
        <button class="button" data-component="Button" data-variant="default" data-golden="true" data-source="src/styles/shared.css">Cancel</button>
        <button id="primary" class="button button--primary" data-component="Button" data-variant="primary" data-source="src/styles/shared.css">Save</button>
      </div>
    </section>
    <section class="card">
      <div class="row">
        <button class="tag" data-component="Tag" data-variant="default" data-golden="true" data-source="src/styles/shared.css" aria-pressed="false">Default</button>
        <button id="featured" class="tag tag--featured" data-component="Tag" data-variant="featured" data-source="src/styles/shared.css" aria-pressed="false">Featured</button>
        <button class="tag tag--compact" data-component="Tag" data-variant="compact" data-valid-variant="true" data-source="src/styles/shared.css" aria-pressed="false">Compact</button>
      </div>
    </section>
    <section class="card">
      <div class="row">
        <input class="input" data-component="Input" data-variant="default" data-golden="true" data-source="src/styles/shared.css" value="Baseline">
        <input class="input input--search" data-component="Input" data-variant="search" data-source="src/styles/shared.css" value="Search">
      </div>
    </section>
  </main>
  <script>
    document.querySelectorAll('.tag').forEach((el) => el.addEventListener('click', () => {
      el.setAttribute('aria-pressed', el.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
    }));
  </script>
</body>
</html>
"""

PROFILE = {
    "version": 1,
    "status": "APPROVED",
    "direction": {"archetype": "quiet-product", "status": "approved", "confidence": "high"},
    "representative_routes": ["/dashboard", "/settings"],
    "golden_components": {
        "Button": {"source": "src/styles/shared.css"},
        "Tag": {"source": "src/styles/shared.css"},
        "Nav": {"source": "src/styles/shared.css"},
        "Input": {"source": "src/styles/shared.css"},
    },
    "exceptions": [
        {"id": "tag-compact", "component": "Tag", "variant": "compact", "reason": "Documented dense metadata variant"}
    ],
    "state_rules": {"geometry_must_remain_stable": True, "rules": []},
    "watch": {"paths": ["src/styles/**", "pages/**"], "signals": ["shared_component_change"]},
}

GEOMETRY_KEYS = ("height", "paddingLeft", "paddingRight", "borderRadius", "fontSize", "lineHeight")
STYLE_KEYS = ("backgroundColor", "color", "fontFamily", "fontWeight")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_revision(project: Path) -> str:
    digest = hashlib.sha256()
    for rel in ("src/styles/shared.css", "pages/dashboard.html", "pages/settings.html", "docs/design/PROJECT_VISUAL_PROFILE.yaml"):
        digest.update(rel.encode())
        digest.update((project / rel).read_bytes())
    return digest.hexdigest()


def write_fixture(project: Path) -> None:
    (project / "src/styles").mkdir(parents=True)
    (project / "pages").mkdir(parents=True)
    (project / "docs/design").mkdir(parents=True)
    (project / "evidence").mkdir(parents=True)
    (project / "src/styles/shared.css").write_text(BEFORE_CSS, encoding="utf-8")
    (project / "pages/dashboard.html").write_text(HTML.format(title="Dashboard"), encoding="utf-8")
    (project / "pages/settings.html").write_text(HTML.format(title="Settings"), encoding="utf-8")
    (project / "docs/design/PROJECT_VISUAL_PROFILE.yaml").write_text(yaml.safe_dump(PROFILE, sort_keys=False), encoding="utf-8")


def metrics(page, route: str) -> list[dict[str, Any]]:
    rows = page.locator("[data-component]").evaluate_all(
        """(els, route) => els.map((el, index) => {
          const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
          return {
            route, index,
            component: el.dataset.component,
            variant: el.dataset.variant || 'default',
            golden: el.dataset.golden === 'true',
            valid_variant: el.dataset.validVariant === 'true',
            source: el.dataset.source || null,
            height: Math.round(r.height * 100) / 100,
            width: Math.round(r.width * 100) / 100,
            paddingLeft: cs.paddingLeft, paddingRight: cs.paddingRight,
            borderRadius: cs.borderRadius, fontSize: cs.fontSize, lineHeight: cs.lineHeight,
            backgroundColor: cs.backgroundColor, color: cs.color,
            fontFamily: cs.fontFamily, fontWeight: cs.fontWeight
          };
        })""",
        route,
    )
    return rows


def discover_routes(project: Path) -> list[str]:
    profile = yaml.safe_load((project / "docs/design/PROJECT_VISUAL_PROFILE.yaml").read_text(encoding="utf-8")) or {}
    require(profile.get("status") == "APPROVED", "fixture must load approved visual profile")
    routes = profile.get("representative_routes") or []
    require(routes == ["/dashboard", "/settings"], "V2 must reuse representative route knowledge")
    return routes


def page_for_route(project: Path, route: str) -> Path:
    return project / "pages" / f"{route.strip('/')}.html"


def collect_inventory(browser, project: Path, routes: list[str], viewport: dict[str, int]) -> list[dict[str, Any]]:
    page = browser.new_page(viewport=viewport)
    collected: list[dict[str, Any]] = []
    try:
        for route in routes:
            page.goto(page_for_route(project, route).resolve().as_uri())
            collected.extend(metrics(page, route))
    finally:
        page.close()
    return collected


def baseline_by_component(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    baseline: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("golden") and row["component"] not in baseline:
            baseline[row["component"]] = row
    return baseline


def geometry_signature(row: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(row.get(key) for key in GEOMETRY_KEYS)


def style_signature(row: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(row.get(key) for key in STYLE_KEYS)


def outliers(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baseline = baseline_by_component(rows)
    found: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if row.get("golden") or row.get("valid_variant"):
            continue
        base = baseline.get(row["component"])
        if base and geometry_signature(row) != geometry_signature(base):
            found.setdefault((row["component"], row["variant"]), row)
    return list(found.values())


def capture(page, project: Path, *, phase: str, route: str, viewport_label: str, viewport: dict[str, int], state: str, selector: str | None = None) -> dict[str, Any]:
    page.set_viewport_size(viewport)
    page.goto(page_for_route(project, route).resolve().as_uri())
    if state == "hover":
        require(selector is not None, "hover capture requires selector")
        page.locator(selector).hover()
    elif state == "focus":
        require(selector is not None, "focus capture requires selector")
        page.locator(selector).focus()
    elif state == "selected":
        require(selector is not None, "selected capture requires selector")
        page.locator(selector).click()
        require(page.locator(selector).get_attribute("aria-pressed") == "true", "selected interaction must change rendered state")
    target = route.strip("/")
    artifact = project / "evidence" / f"{phase}-{target}-{viewport_label}-{state}.png"
    page.screenshot(path=str(artifact), full_page=True)
    require(artifact.is_file() and artifact.stat().st_size > 1000, "real browser screenshot must be non-empty")
    return {
        "id": artifact.stem,
        "kind": "screenshot",
        "target": route,
        "state": state,
        "artifact": str(artifact.relative_to(project)),
        "viewport": {"label": viewport_label, **viewport},
        "provenance": {
            "provider": f"playwright-{importlib.metadata.version('playwright')}:chrome-{page.context.browser.version}",
            "source_revision": source_revision(project),
            "captured_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def box(page, selector: str) -> tuple[float, float]:
    value = page.locator(selector).bounding_box()
    require(value is not None, f"missing geometry for {selector}")
    return round(value["width"], 2), round(value["height"], 2)


def verify_state_geometry(page, project: Path) -> None:
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(page_for_route(project, "/dashboard").resolve().as_uri())
    base_button = box(page, "#primary")
    page.locator("#primary").hover()
    require(box(page, "#primary") == base_button, "hover must not shift button geometry")
    page.locator("#primary").focus()
    require(box(page, "#primary") == base_button, "focus must not shift button geometry")
    base_tag = box(page, "#featured")
    page.locator("#featured").click()
    require(box(page, "#featured") == base_tag, "selected must not shift tag geometry")


def verify_responsive(page, project: Path, routes: list[str]) -> None:
    for viewport in ({"width": 1280, "height": 800}, {"width": 390, "height": 844}):
        page.set_viewport_size(viewport)
        for route in routes:
            page.goto(page_for_route(project, route).resolve().as_uri())
            no_overflow = page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            require(bool(no_overflow), f"responsive overflow detected: {route} {viewport['width']}")


def main() -> int:
    artifact_dir = Path(os.environ["AIPS_VISUAL_ARTIFACT_DIR"]).resolve() if os.environ.get("AIPS_VISUAL_ARTIFACT_DIR") else None
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "visual-product"
        write_fixture(project)
        routes = discover_routes(project)
        page_hashes = {route: sha256(page_for_route(project, route)) for route in routes}
        profile_hash = sha256(project / "docs/design/PROJECT_VISUAL_PROFILE.yaml")

        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True, args=["--disable-dev-shm-usage"])
            try:
                desktop = {"width": 1280, "height": 800}
                mobile = {"width": 390, "height": 844}
                before_inventory = collect_inventory(browser, project, routes, desktop)
                before_outliers = outliers(before_inventory)
                require({row["component"] for row in before_outliers} == {"Button", "Tag", "Nav", "Input"}, "fixture must expose Button/Tag/Nav/Input outliers")
                require(any(row["component"] == "Tag" and row["variant"] == "compact" and row["valid_variant"] for row in before_inventory), "documented compact Tag variant must be classified before normalization")

                page = browser.new_page(viewport=desktop)
                before_captures = [
                    capture(page, project, phase="before", route="/dashboard", viewport_label="desktop", viewport=desktop, state="default"),
                    capture(page, project, phase="before", route="/settings", viewport_label="mobile", viewport=mobile, state="default"),
                ]
                page.close()
                before_default_hash = sha256(project / before_captures[0]["artifact"])

                (project / "src/styles/shared.css").write_text(FIXED_CSS, encoding="utf-8")
                require(all(sha256(page_for_route(project, route)) == page_hashes[route] for route in routes), "shared fix must not mutate route-local HTML")
                require(sha256(project / "docs/design/PROJECT_VISUAL_PROFILE.yaml") == profile_hash, "shared fix must preserve approved visual profile")

                after_inventory = collect_inventory(browser, project, routes, desktop)
                after_outliers = outliers(after_inventory)
                require(not after_outliers, f"shared fix must remove unexplained material outliers: {after_outliers}")

                before_styles = {(r["component"], r["variant"]): style_signature(r) for r in before_inventory}
                after_styles = {(r["component"], r["variant"]): style_signature(r) for r in after_inventory}
                require(before_styles == after_styles, "Preserve Before Redesign: semantic color/type treatment must remain unchanged")

                page = browser.new_page(viewport=desktop)
                verify_state_geometry(page, project)
                verify_responsive(page, project, routes)
                after_captures = [
                    capture(page, project, phase="after", route="/dashboard", viewport_label="desktop", viewport=desktop, state="default"),
                    capture(page, project, phase="after", route="/settings", viewport_label="mobile", viewport=mobile, state="default"),
                    capture(page, project, phase="after", route="/dashboard", viewport_label="desktop", viewport=desktop, state="hover", selector="#primary"),
                    capture(page, project, phase="after", route="/dashboard", viewport_label="desktop", viewport=desktop, state="focus", selector="#primary"),
                    capture(page, project, phase="after", route="/dashboard", viewport_label="desktop", viewport=desktop, state="selected", selector="#featured"),
                ]
                page.close()

                require(sha256(project / after_captures[0]["artifact"]) != before_default_hash, "before/after rendered evidence must reflect the shared geometry repair")
                state_hashes = {c["state"]: sha256(project / c["artifact"]) for c in after_captures if c["target"] == "/dashboard" and c["viewport"]["label"] == "desktop"}
                require(state_hashes["hover"] != state_hashes["default"], "hover screenshot must reflect a real interaction state")
                require(state_hashes["focus"] != state_hashes["default"], "focus screenshot must reflect a real interaction state")
                require(state_hashes["selected"] != state_hashes["default"], "selected screenshot must reflect a real interaction state")
            finally:
                browser.close()

        findings = []
        for idx, row in enumerate(before_outliers, start=1):
            findings.append({
                "id": f"VIS-{idx:03d}",
                "component": row["component"],
                "route": row["route"],
                "symptom": f"{row['component']} variant {row['variant']} diverges from golden geometry",
                "classification": "outlier",
                "valid_variant": False,
                "approved_exception": False,
                "root_cause": {"source": "src/styles/shared.css", "mechanism": f"shared {row['component']} variant geometry"},
                "fix": "normalize shared variant geometry while preserving semantic style",
                "status": "fixed",
            })

        audit = {
            "version": 1,
            "mode": "V2",
            "status": "pass",
            "target": {"routes": routes, "components": ["Button", "Tag", "Nav", "Input"]},
            "baseline_source": "docs/design/PROJECT_VISUAL_PROFILE.yaml",
            "component_inventory": ["Button", "Tag", "Nav", "Input"],
            "findings": findings,
            "verification": {
                "before": before_captures,
                "after": after_captures,
                "required_viewports": ["desktop", "mobile"],
                "required_states": ["default", "hover", "focus", "selected"],
                "desktop": "pass",
                "tablet": "not_applicable",
                "mobile": "pass",
                "states": {"default": "pass", "hover": "pass", "focus": "pass", "selected": "pass"},
            },
            "review": {
                "decision": "PASS",
                "quality_assessed_by": "visual_review",
                "checks": [
                    {"check": "representative_routes_rendered", "result": "pass", "evidence": routes},
                    {"check": "component_outliers_resolved", "result": "pass", "evidence": ["Button", "Tag", "Nav", "Input"]},
                    {"check": "responsive_no_overflow", "result": "pass", "evidence": ["desktop", "mobile"]},
                    {"check": "interaction_state_geometry_stable", "result": "pass", "evidence": ["hover", "focus", "selected"]},
                    {"check": "preserve_before_redesign", "result": "pass", "evidence": "semantic color/type signatures unchanged"},
                ],
            },
            "profile_updated": False,
            "remaining_material_findings": [],
        }
        audit_path = project / "VISUAL_AUDIT.yaml"
        audit_path.write_text(yaml.safe_dump(audit, sort_keys=False), encoding="utf-8")
        (project / "evidence/component-inventory-before.json").write_text(json.dumps(before_inventory, indent=2), encoding="utf-8")
        (project / "evidence/component-inventory-after.json").write_text(json.dumps(after_inventory, indent=2), encoding="utf-8")

        checked = subprocess.run(
            [sys.executable, str(VISUAL_EVIDENCE), str(audit_path), "--project", str(project), "--format", "json"],
            capture_output=True,
            text=True,
        )
        require(checked.returncode == 0, f"visual evidence integrity failed: {checked.stdout} {checked.stderr}")
        evidence_result = json.loads(checked.stdout)
        require(evidence_result.get("visual_quality_inferred") is False, "deterministic evidence validator must not infer visual quality")

        summary = {
            "status": "PASS",
            "provider": "playwright-system-chrome",
            "routes": routes,
            "components": ["Button", "Tag", "Nav", "Input"],
            "before_outliers": len(before_outliers),
            "after_outliers": len(after_outliers),
            "viewports": ["desktop", "mobile"],
            "states": ["default", "hover", "focus", "selected"],
            "scenario_contracts": ["039", "055"],
            "visual_evidence_integrity": evidence_result.get("evidence_integrity"),
        }
        (project / "evidence/summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        (project / "evidence/VISUAL_AUDIT.yaml").write_text(audit_path.read_text(encoding="utf-8"), encoding="utf-8")

        if artifact_dir:
            if artifact_dir.exists():
                shutil.rmtree(artifact_dir)
            shutil.copytree(project / "evidence", artifact_dir)

        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
