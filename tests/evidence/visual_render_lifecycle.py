#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.browser_runtime import (
    discover_browser,
    playwright_launch_kwargs,
    probe_browser,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def browser_precondition() -> bool:
    selection = discover_browser()
    probe = probe_browser(selection.get("path"), provider=str(selection["provider"]))
    if probe["status"] != "READY":
        print(f"ENVIRONMENT_BLOCKED: {json.dumps(probe, ensure_ascii=False)}")
        return False
    return True


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def git(project: Path, *args: str) -> str:
    result = run(["git", *args], cwd=project)
    require(result.returncode == 0, result.stderr or result.stdout)
    return result.stdout.strip()


HTML = """<!doctype html>
<html>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<link rel='stylesheet' href='components.css'>
<title>{title}</title>
</head>
<body>
<header><nav>
  <a class='nav-item selected' data-kind='nav'>Overview</a>
  <a class='nav-item legacy' data-kind='nav'>Activity</a>
  <a class='nav-item' data-kind='nav'>Settings</a>
</nav></header>
<main>
  <h1>{title}</h1>
  <section class='card'>
    <div class='row'>
      <button class='button' data-kind='button'>Save</button>
      <button class='button legacy' data-kind='button'>Publish</button>
      <span class='tag' data-kind='tag'>Stable</span>
      <span class='tag legacy' data-kind='tag'>Needs review</span>
    </div>
    <label>Name <input class='input' data-kind='input' value='{title}'></label>
    <label>Owner <input class='input legacy' data-kind='input' value='AIPS'></label>
  </section>
</main>
</body>
</html>
"""

BEFORE_CSS = """
:root { --surface:#fff; --ink:#172033; --line:#d7dce5; --accent:#3659e3; --radius:8px; }
* { box-sizing:border-box; }
body { margin:0; font-family:Arial,sans-serif; color:var(--ink); background:#f5f7fb; }
header { background:var(--surface); border-bottom:1px solid var(--line); }
nav { display:flex; gap:8px; padding:0 24px; align-items:center; }
.nav-item { display:flex; align-items:center; min-height:40px; padding:0 12px; border-bottom:0 solid var(--accent); }
.nav-item.selected { border-bottom-width:3px; }
.nav-item.legacy { min-height:46px; padding-left:18px; }
main { max-width:900px; margin:32px auto; padding:0 24px; }
.card { background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:24px; }
.row { display:flex; flex-wrap:wrap; align-items:center; gap:12px; margin-bottom:20px; }
.button { min-height:40px; padding:0 16px; border:1px solid var(--line); border-radius:var(--radius); background:#fff; }
.button:hover { border-width:3px; }
.button.legacy { min-height:48px; padding:0 22px; border-radius:14px; }
.tag { display:inline-flex; align-items:center; min-height:28px; padding:0 10px; border:1px solid var(--line); border-radius:999px; }
.tag.legacy { min-height:36px; padding:0 14px; }
label { display:block; margin-top:12px; }
.input { display:block; width:100%; height:40px; margin-top:6px; padding:0 12px; border:1px solid var(--line); border-radius:var(--radius); }
.input:focus { border-width:3px; outline:none; }
.input.legacy { height:48px; border-radius:14px; }
"""

AFTER_CSS = """
:root { --surface:#fff; --ink:#172033; --line:#d7dce5; --accent:#3659e3; --radius:8px; --control-height:40px; --tag-height:28px; }
* { box-sizing:border-box; }
body { margin:0; font-family:Arial,sans-serif; color:var(--ink); background:#f5f7fb; }
header { background:var(--surface); border-bottom:1px solid var(--line); }
nav { display:flex; gap:8px; padding:0 24px; align-items:center; }
.nav-item { display:flex; align-items:center; height:var(--control-height); padding:0 12px; border-bottom:3px solid transparent; }
.nav-item.selected { border-bottom-color:var(--accent); }
.nav-item.legacy { height:var(--control-height); padding:0 12px; }
main { max-width:900px; margin:32px auto; padding:0 24px; }
.card { background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:24px; }
.row { display:flex; flex-wrap:wrap; align-items:center; gap:12px; margin-bottom:20px; }
.button { height:var(--control-height); padding:0 16px; border:1px solid var(--line); outline:2px solid transparent; outline-offset:1px; border-radius:var(--radius); background:#fff; }
.button:hover { border-color:var(--accent); }
.button:focus-visible { outline-color:var(--accent); }
.button.legacy { height:var(--control-height); padding:0 16px; border-radius:var(--radius); }
.tag { display:inline-flex; align-items:center; height:var(--tag-height); padding:0 10px; border:1px solid var(--line); border-radius:999px; }
.tag.legacy { height:var(--tag-height); padding:0 10px; }
label { display:block; margin-top:12px; }
.input { display:block; width:100%; height:var(--control-height); margin-top:6px; padding:0 12px; border:1px solid var(--line); outline:2px solid transparent; outline-offset:1px; border-radius:var(--radius); }
.input:focus { border-color:var(--accent); outline-color:var(--accent); }
.input.legacy { height:var(--control-height); border-radius:var(--radius); }
@media (max-width:600px) { nav { padding:0 12px; overflow-x:auto; } main { margin:20px auto; padding:0 12px; } .card { padding:16px; } }
"""


def family_metrics(page) -> dict[str, list[dict[str, float]]]:
    return page.evaluate("""() => {
      const out = {};
      for (const kind of ['button','tag','nav','input']) {
        out[kind] = [...document.querySelectorAll(`[data-kind="${kind}"]`)].map(el => {
          const r = el.getBoundingClientRect();
          const s = getComputedStyle(el);
          return {width:r.width,height:r.height,paddingLeft:parseFloat(s.paddingLeft),paddingRight:parseFloat(s.paddingRight),radius:parseFloat(s.borderTopLeftRadius)};
        });
      }
      return out;
    }""")


def spread(values: list[float]) -> float:
    return max(values) - min(values) if values else 0.0


def screenshot(page, path: Path) -> None:
    page.screenshot(path=str(path), full_page=True)
    require(path.exists() and path.stat().st_size > 500, f"screenshot missing/empty: {path}")


def capture_record(cid: str, phase: str, target: str, state: str, label: str, size: tuple[int, int], artifact: Path, project: Path, revision: str, provider: str) -> dict:
    return {
        "id": cid,
        "phase": phase,
        "kind": "screenshot",
        "target": target,
        "state": state,
        "viewport": {"label": label, "width": size[0], "height": size[1]},
        "artifact": str(artifact.relative_to(project)),
        "input_assets": ["components.css"],
        "provenance": {
            "provider": provider,
            "source_revision": revision,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def rendered_markup(title: str, css: str) -> str:
    return HTML.format(title=title).replace("<link rel='stylesheet' href='components.css'>", f"<style>{css}</style>")


def main() -> int:
    if not browser_precondition():
        return 2
    root = Path(__file__).resolve().parents[2]
    helper = root / "scripts" / "visual_evidence.py"
    require(helper.exists(), f"visual evidence helper missing: {helper}")

    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "visual-product"
        evidence = project / "evidence"
        docs = project / "docs" / "design"
        evidence.mkdir(parents=True)
        docs.mkdir(parents=True)
        (project / "dashboard.html").write_text(HTML.format(title="Dashboard"), encoding="utf-8")
        (project / "settings.html").write_text(HTML.format(title="Settings"), encoding="utf-8")
        (project / "components.css").write_text(BEFORE_CSS, encoding="utf-8")
        profile = {
            "version": 1,
            "status": "APPROVED",
            "direction": {"archetype": "quiet-premium", "status": "approved", "confidence": "high"},
            "representative_routes": ["dashboard.html", "settings.html"],
            "golden_components": {"controls": {"source": "components.css", "reason": "shared component stylesheet"}},
            "state_rules": {"geometry_must_remain_stable": True},
            "exceptions": [],
        }
        (docs / "PROJECT_VISUAL_PROFILE.yaml").write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")

        git(project, "init", "-q")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Visual Evidence")
        git(project, "add", ".")
        git(project, "commit", "-qm", "fixture before visual repair")
        before_sha = git(project, "rev-parse", "HEAD")

        loaded_profile = yaml.safe_load((docs / "PROJECT_VISUAL_PROFILE.yaml").read_text(encoding="utf-8"))
        require(loaded_profile.get("status") == "APPROVED", "visual baseline must be loaded before repair")
        require(len(loaded_profile.get("representative_routes") or []) == 2, "V2 must use representative routes")

        captures_before: list[dict] = []
        captures_after: list[dict] = []
        with sync_playwright() as p:
            launch_kwargs, provider = playwright_launch_kwargs(p)
            launch_kwargs["args"] = ["--no-sandbox", "--disable-dev-shm-usage"]
            browser = p.chromium.launch(**launch_kwargs)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.set_content(rendered_markup("Dashboard", BEFORE_CSS))
            before_metrics = family_metrics(page)
            for kind in ("button", "tag", "nav", "input"):
                require(spread([m["height"] for m in before_metrics[kind]]) >= 6, f"fixture must expose {kind} height outlier")
            before_path = evidence / "dashboard-before-desktop.png"
            screenshot(page, before_path)
            captures_before.append(capture_record("before-dashboard-desktop", "before", "dashboard.html", "default", "desktop", (1280, 800), before_path, project, before_sha, provider))

            (project / "components.css").write_text(AFTER_CSS, encoding="utf-8")
            git(project, "add", "components.css")
            git(project, "commit", "-qm", "normalize shared visual component geometry")
            after_sha = git(project, "rev-parse", "HEAD")

            for route in ("dashboard.html", "settings.html"):
                page.set_viewport_size({"width": 1280, "height": 800})
                page.set_content(rendered_markup(Path(route).stem.title(), AFTER_CSS))
                metrics = family_metrics(page)
                for kind in ("button", "tag", "nav", "input"):
                    delta = spread([m["height"] for m in metrics[kind]])
                    require(delta <= 1, f"{route}: {kind} geometry remains inconsistent: {delta}")
                overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
                require(overflow <= 1, f"{route}: desktop horizontal overflow")
                artifact = evidence / f"{Path(route).stem}-after-desktop.png"
                screenshot(page, artifact)
                captures_after.append(capture_record(f"after-{Path(route).stem}-desktop", "after", route, "default", "desktop", (1280, 800), artifact, project, after_sha, provider))

            page.set_content(rendered_markup("Dashboard", AFTER_CSS))
            page.set_viewport_size({"width": 390, "height": 844})
            overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
            require(overflow <= 1, "dashboard: mobile horizontal overflow")
            mobile_path = evidence / "dashboard-after-mobile.png"
            screenshot(page, mobile_path)
            captures_after.append(capture_record("after-dashboard-mobile", "after", "dashboard.html", "default", "mobile", (390, 844), mobile_path, project, after_sha, provider))

            page.set_viewport_size({"width": 1280, "height": 800})
            page.set_content(rendered_markup("Dashboard", AFTER_CSS))
            button = page.locator("button.button").first
            default_box = button.bounding_box()
            button.hover()
            hover_box = button.bounding_box()
            require(default_box and hover_box and abs(default_box["height"] - hover_box["height"]) <= 0.5 and abs(default_box["width"] - hover_box["width"]) <= 0.5, "hover must not shift button geometry")
            hover_path = evidence / "dashboard-after-hover.png"
            screenshot(page, hover_path)
            captures_after.append(capture_record("after-dashboard-hover", "after", "dashboard.html", "hover", "desktop", (1280, 800), hover_path, project, after_sha, provider))

            inp = page.locator("input.input").first
            input_default = inp.bounding_box()
            inp.focus()
            input_focus = inp.bounding_box()
            require(input_default and input_focus and abs(input_default["height"] - input_focus["height"]) <= 0.5 and abs(input_default["width"] - input_focus["width"]) <= 0.5, "focus must not shift input geometry")
            focus_path = evidence / "dashboard-after-focus.png"
            screenshot(page, focus_path)
            captures_after.append(capture_record("after-dashboard-focus", "after", "dashboard.html", "focus", "desktop", (1280, 800), focus_path, project, after_sha, provider))

            selected = page.locator(".nav-item.selected")
            selected_box = selected.bounding_box()
            page.evaluate("document.querySelector('.nav-item.selected').classList.remove('selected'); document.querySelectorAll('.nav-item')[1].classList.add('selected')")
            selected_after = page.locator(".nav-item.selected").bounding_box()
            require(selected_box and selected_after and abs(selected_box["height"] - selected_after["height"]) <= 0.5, "selected state must preserve nav height")
            selected_path = evidence / "dashboard-after-selected.png"
            screenshot(page, selected_path)
            captures_after.append(capture_record("after-dashboard-selected", "after", "dashboard.html", "selected", "desktop", (1280, 800), selected_path, project, after_sha, provider))
            browser.close()

        review_checks = [
            "approved Project Visual Profile loaded before repair",
            "representative dashboard/settings routes rendered",
            "Button/Tag/Nav/Input inventory measured from rendered DOM",
            "before evidence contains material repeated-component outliers",
            "shared components.css root cause repaired instead of page-specific nudges",
            "after component-family geometry is consistent on both representative routes",
            "desktop and mobile have no horizontal overflow",
            "hover/focus/selected preserve control geometry",
            "rendered before/after screenshots exist and are non-empty",
        ]
        audit = {
            "version": 1,
            "mode": "V2",
            "status": "pass",
            "target": {"routes": ["dashboard.html", "settings.html"], "components": ["Button", "Tag", "Nav", "Input"]},
            "baseline_source": "docs/design/PROJECT_VISUAL_PROFILE.yaml",
            "component_inventory": [
                {"component": "Button", "source": "components.css"},
                {"component": "Tag", "source": "components.css"},
                {"component": "Nav", "source": "components.css"},
                {"component": "Input", "source": "components.css"},
            ],
            "findings": [{
                "id": "VIS-039-055-001",
                "component": "shared controls",
                "route": "dashboard.html + settings.html",
                "symptom": "legacy Button/Tag/Nav/Input variants use inconsistent geometry and state borders shift layout",
                "classification": "outlier",
                "valid_variant": False,
                "approved_exception": False,
                "root_cause": {"source": "components.css", "style": "legacy modifiers and state border widths", "token": "--control-height / --tag-height", "mechanism": "shared component geometry overrides"},
                "fix": "normalize shared component geometry and reserve state outline/border space",
                "status": "fixed",
            }],
            "review": {
                "decision": "PASS",
                "quality_assessed_by": "visual_review",
                "checks": review_checks,
                "notes": "Independent fixture review is limited to objective visual-consistency, responsive and state-geometry criteria; it does not claim generic aesthetic scoring.",
            },
            "verification": {
                "before": captures_before,
                "after": captures_after,
                "required_viewports": ["desktop", "mobile"],
                "required_states": ["default", "hover", "focus", "selected"],
                "desktop": "pass",
                "tablet": "not_applicable",
                "mobile": "pass",
                "states": {"default": "pass", "hover": "pass", "focus": "pass", "active": "not_applicable", "selected": "pass", "disabled": "not_applicable"},
            },
            "profile_updated": False,
            "remaining_material_findings": [],
        }
        audit_path = project / "VISUAL_AUDIT.yaml"
        audit_path.write_text(yaml.safe_dump(audit, sort_keys=False), encoding="utf-8")
        validated = run([sys.executable, str(helper), str(audit_path), "--project", str(project), "--format", "json"])
        require(validated.returncode == 0, f"visual evidence validation failed: {validated.stdout} {validated.stderr}")
        result = json.loads(validated.stdout)
        require(result.get("evidence_integrity") == "PASS", "rendered evidence integrity must PASS")
        require(result.get("visual_quality_inferred") is False, "integrity helper must not infer visual quality")

    print("VISUAL RENDER LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
