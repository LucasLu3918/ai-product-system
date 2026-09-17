#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "scripts" / "visual_capture.py"
REVIEW = ROOT / "scripts" / "visual_consistency_review.py"
EVIDENCE = ROOT / "scripts" / "visual_evidence.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    require(data[:8] == b"\x89PNG\r\n\x1a\n", f"not a real PNG: {path}")
    require(data[12:16] == b"IHDR", f"PNG missing IHDR: {path}")
    return struct.unpack(">II", data[16:24])


def fixture_html(*, fixed: bool) -> str:
    extra = "" if fixed else "#save { height: 44px; } .nav-item.active { padding-top: 11px; padding-bottom: 7px; }"
    return f"""<!doctype html>
<html><head><meta charset='utf-8'><style>
:root {{ --control-h: 40px; --radius: 8px; }}
* {{ box-sizing: border-box; }}
body {{ font: 16px system-ui; margin: 24px; }}
.toolbar {{ display:flex; gap:12px; align-items:center; flex-wrap:wrap; }}
.control, .nav-item {{ height:var(--control-h); padding:8px 14px; border:1px solid #777; border-radius:var(--radius); line-height:22px; background:white; }}
.tag[aria-selected='true'] {{ border-width:2px; padding:7px 13px; }}
.control:hover {{ border-width:2px; padding:7px 13px; }}
.control:focus {{ outline:2px solid currentColor; outline-offset:2px; }}
{extra}
</style></head><body>
<nav class='toolbar'><a class='nav-item active' id='nav'>Home</a><a class='nav-item'>Settings</a></nav>
<div class='toolbar' style='margin-top:24px'>
<button class='control' id='save'>Save</button>
<button class='control tag' id='tag' aria-selected='false' onclick="this.setAttribute('aria-selected', this.getAttribute('aria-selected')==='true'?'false':'true')">Tag</button>
<input class='control' id='name' value='Example'>
</div>
</body></html>"""


def metric(capture: dict, name: str) -> dict:
    for item in capture.get("metrics") or []:
        if item.get("name") == name:
            return item.get("values") or {}
    raise AssertionError(f"missing metric {name} in {capture.get('id')}")


def main() -> int:
    require(CAPTURE.exists(), "visual capture helper missing")
    require(REVIEW.exists(), "visual consistency review helper missing")
    require(EVIDENCE.exists(), "visual evidence helper missing")

    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "project"
        project.mkdir()
        before_html = project / "before.html"
        after_html = project / "after.html"
        before_html.write_text(fixture_html(fixed=False), encoding="utf-8")
        after_html.write_text(fixture_html(fixed=True), encoding="utf-8")

        inspect = [
            {"name": "save", "selector": "#save", "properties": ["height", "padding-top", "padding-bottom", "border-top-width"]},
            {"name": "tag", "selector": "#tag", "properties": ["height", "padding-top", "padding-bottom", "border-top-width"]},
            {"name": "name", "selector": "#name", "properties": ["height", "padding-top", "padding-bottom", "border-top-width"]},
            {"name": "nav", "selector": "#nav", "properties": ["height", "padding-top", "padding-bottom"]},
        ]

        def cap(cid: str, target: str, phase: str, state: str, label: str, width: int, height: int, *, interaction=None):
            value = {
                "id": cid,
                "target": target,
                "phase": phase,
                "state": state,
                "viewport": {"label": label, "width": width, "height": height},
                "artifact": f"evidence/{cid}.png",
                "full_page": False,
                "inspect": inspect,
            }
            if interaction:
                value["interaction"] = interaction
            return value

        plan = {
            "version": 1,
            "provider": {"browser_channel": "chrome", "headless": True, "source_revision": "fixture-shared-component-change"},
            "targets": [
                {"id": "before", "label": "/fixture-before", "path": "before.html"},
                {"id": "after", "label": "/fixture-after", "path": "after.html"},
            ],
            "captures": [
                cap("before-desktop-default", "before", "before", "default", "desktop", 1280, 720),
                cap("before-desktop-hover", "before", "before", "hover", "desktop", 1280, 720, interaction={"type": "hover", "selector": "#save"}),
                cap("before-mobile-default", "before", "before", "default", "mobile", 390, 844),
                cap("after-desktop-default", "after", "after", "default", "desktop", 1280, 720),
                cap("after-desktop-hover", "after", "after", "hover", "desktop", 1280, 720, interaction={"type": "hover", "selector": "#save"}),
                cap("after-desktop-focus", "after", "after", "focus", "desktop", 1280, 720, interaction={"type": "focus", "selector": "#name"}),
                cap("after-desktop-selected", "after", "after", "selected", "desktop", 1280, 720, interaction={"type": "click", "selector": "#tag"}),
                cap("after-mobile-default", "after", "after", "default", "mobile", 390, 844),
            ],
        }
        plan_path = project / "CAPTURE_PLAN.yaml"
        result_path = project / "CAPTURE_RESULT.yaml"
        plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")

        captured = run([sys.executable, str(CAPTURE), str(plan_path), "--project", str(project), "--output", str(result_path), "--format", "json"])
        require(captured.returncode == 0, f"real Chrome capture failed: {captured.stdout} {captured.stderr}")
        capture_result = yaml.safe_load(result_path.read_text(encoding="utf-8")) or {}
        captures = capture_result.get("captures") or []
        require(len(captures) == 8, "expected eight real rendered captures")
        require(capture_result.get("visual_quality_inferred") is False, "capture must not infer visual quality")

        by_id = {item["id"]: item for item in captures}
        for item in captures:
            artifact = project / item["artifact"]
            width, height = png_size(artifact)
            require(width == item["viewport"]["width"], f"viewport width mismatch for {item['id']}")
            require(height == item["viewport"]["height"], f"viewport height mismatch for {item['id']}")
            require(item.get("artifact_bytes", 0) > 1000, f"capture artifact too small for {item['id']}")
            require(len(item.get("artifact_sha256") or "") == 64, f"capture hash missing for {item['id']}")
            provenance = item.get("provenance") or {}
            require(provenance.get("provider") == "playwright-chrome", "provider provenance mismatch")
            require(bool(provenance.get("browser_version")), "browser version provenance missing")

        require(metric(by_id["before-desktop-default"], "save")["__rect"]["height"] == 44, "fixture must expose the original shared-control outlier")
        for cid in ("after-desktop-default", "after-desktop-hover"):
            require(metric(by_id[cid], "save")["__rect"]["height"] == 40, f"shared button geometry must be stable after fix: {cid}")
        require(metric(by_id["after-desktop-focus"], "name")["__rect"]["height"] == 40, "focused input must retain shared geometry")
        require(metric(by_id["after-desktop-selected"], "tag")["__rect"]["height"] == 40, "selected tag must retain shared geometry")
        require(metric(by_id["after-desktop-default"], "nav")["__rect"]["height"] == 40, "navigation must use shared geometry after fix")

        before = [c for c in captures if c.get("phase") == "before"]
        after = [c for c in captures if c.get("phase") == "after"]
        audit = {
            "version": 1,
            "mode": "V2",
            "status": "in_progress",
            "target": {"routes": ["/fixture-before", "/fixture-after"], "components": ["Button", "Tag", "Navigation", "Input"]},
            "baseline_source": "fixture shared controls",
            "component_inventory": [
                {"component": "Button", "source": "fixture shared CSS"},
                {"component": "Tag", "source": "fixture shared CSS"},
                {"component": "Navigation", "source": "fixture shared CSS"},
                {"component": "Input", "source": "fixture shared CSS"},
            ],
            "findings": [{
                "id": "VIS-RENDER-001",
                "component": "Button",
                "route": "/fixture-before",
                "symptom": "shared button height outlier is visible in rendered/computed evidence",
                "classification": "outlier",
                "valid_variant": False,
                "approved_exception": False,
                "root_cause": {"source": "before.html", "style": "#save height override", "token": "--control-h", "mechanism": "local override bypasses shared token"},
                "fix": "remove local height override and use shared control token",
                "status": "fixed",
            }],
            "verification": {
                "required_viewports": ["desktop", "mobile"],
                "required_states": ["default", "hover", "focus", "selected"],
                "before": before,
                "after": after,
            },
            "review": {
                "decision": "PENDING",
                "quality_assessed_by": "visual_review",
                "checks": [{"area": "rendered evidence available", "result": "pending_visual_judgment", "evidence": [c["artifact"] for c in after]}],
                "notes": ["Real browser evidence exists; a separate reviewer must decide the objective consistency contract."],
            },
            "profile_updated": False,
            "remaining_material_findings": [],
        }
        audit_path = project / "VISUAL_AUDIT.yaml"
        audit_path.write_text(yaml.safe_dump(audit, sort_keys=False), encoding="utf-8")
        evidence = run([sys.executable, str(EVIDENCE), str(audit_path), "--project", str(project), "--format", "json"])
        require(evidence.returncode == 0, f"real rendered evidence envelope should validate while review is pending: {evidence.stdout} {evidence.stderr}")
        evidence_data = json.loads(evidence.stdout)
        require(evidence_data.get("visual_quality_inferred") is False, "evidence validator must not infer quality")

        audit["status"] = "pass"
        audit_path.write_text(yaml.safe_dump(audit, sort_keys=False), encoding="utf-8")
        false_pass = run([sys.executable, str(EVIDENCE), str(audit_path), "--project", str(project), "--format", "json"])
        require(false_pass.returncode != 0, "real screenshots without an independent passing visual review must not PASS")
        false_pass_data = json.loads(false_pass.stdout)
        require(any("Visual Quality Review" in error for error in false_pass_data.get("errors", [])), "false PASS must fail at visual-review gate")

        review_plan = {
            "version": 1,
            "checks": [
                {
                    "id": "captures-cover-responsive-and-states",
                    "type": "capture_present",
                    "captures": ["before-desktop-default", "before-mobile-default", "after-desktop-default", "after-desktop-hover", "after-desktop-focus", "after-desktop-selected", "after-mobile-default"],
                    "area": "rendered evidence coverage",
                },
                {
                    "id": "before-outlier-is-observable",
                    "type": "metric_not_equal",
                    "left": {"capture": "before-desktop-default", "metric": "save", "path": "__rect.height"},
                    "right": {"capture": "before-desktop-default", "metric": "name", "path": "__rect.height"},
                    "area": "before finding reproduction",
                },
                {
                    "id": "button-matches-shared-control-baseline",
                    "type": "metric_equal",
                    "left": {"capture": "after-desktop-default", "metric": "save", "path": "__rect.height"},
                    "right": {"capture": "after-desktop-default", "metric": "name", "path": "__rect.height"},
                    "area": "shared component geometry",
                },
                {
                    "id": "navigation-matches-shared-control-baseline",
                    "type": "metric_equal",
                    "left": {"capture": "after-desktop-default", "metric": "nav", "path": "__rect.height"},
                    "right": {"capture": "after-desktop-default", "metric": "name", "path": "__rect.height"},
                    "area": "navigation geometry",
                },
                {
                    "id": "hover-state-geometry-stable",
                    "type": "metric_equal",
                    "left": {"capture": "after-desktop-default", "metric": "save", "path": "__rect.height"},
                    "right": {"capture": "after-desktop-hover", "metric": "save", "path": "__rect.height"},
                    "area": "hover state stability",
                },
                {
                    "id": "focus-state-geometry-stable",
                    "type": "metric_equal",
                    "left": {"capture": "after-desktop-default", "metric": "name", "path": "__rect.height"},
                    "right": {"capture": "after-desktop-focus", "metric": "name", "path": "__rect.height"},
                    "area": "focus state stability",
                },
                {
                    "id": "selected-state-geometry-stable",
                    "type": "metric_equal",
                    "left": {"capture": "after-desktop-default", "metric": "tag", "path": "__rect.height"},
                    "right": {"capture": "after-desktop-selected", "metric": "tag", "path": "__rect.height"},
                    "area": "selected state stability",
                },
                {
                    "id": "mobile-shared-control-geometry",
                    "type": "metric_equal",
                    "left": {"capture": "after-mobile-default", "metric": "save", "path": "__rect.height"},
                    "right": {"capture": "after-mobile-default", "metric": "name", "path": "__rect.height"},
                    "area": "responsive consistency",
                },
            ],
        }
        review_plan_path = project / "VISUAL_REVIEW_PLAN.yaml"
        review_result_path = project / "VISUAL_REVIEW_RESULT.yaml"
        review_plan_path.write_text(yaml.safe_dump(review_plan, sort_keys=False), encoding="utf-8")
        reviewed = run([sys.executable, str(REVIEW), str(result_path), str(review_plan_path), "--output", str(review_result_path), "--format", "json"])
        require(reviewed.returncode == 0, f"independent objective consistency review failed: {reviewed.stdout} {reviewed.stderr}")
        review_result = yaml.safe_load(review_result_path.read_text(encoding="utf-8")) or {}
        require(review_result.get("decision") == "PASS", "objective rendered consistency review must PASS")
        require(review_result.get("general_visual_quality_inferred") is False, "bounded consistency reviewer must not claim general aesthetic judgment")

        audit["review"] = {
            "decision": review_result["decision"],
            "quality_assessed_by": review_result["quality_assessed_by"],
            "checks": review_result["checks"],
            "notes": [review_result["note"]],
        }
        audit["status"] = "pass"
        audit_path.write_text(yaml.safe_dump(audit, sort_keys=False), encoding="utf-8")
        final_evidence = run([sys.executable, str(EVIDENCE), str(audit_path), "--project", str(project), "--format", "json"])
        require(final_evidence.returncode == 0, f"reviewed rendered evidence must PASS: {final_evidence.stdout} {final_evidence.stderr}")
        final_data = json.loads(final_evidence.stdout)
        require(final_data.get("evidence_integrity") == "PASS", "final evidence integrity must PASS")
        require(final_data.get("visual_quality_inferred") is False, "evidence validator remains separate from the reviewer")

    print("REAL VISUAL RENDER / CAPTURE / CONSISTENCY REVIEW LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
