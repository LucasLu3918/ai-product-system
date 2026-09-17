#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version as package_version
import json
from pathlib import Path
import sys
from typing import Any

import yaml
from playwright.sync_api import sync_playwright


def fail(message: str) -> None:
    raise RuntimeError(message)


def resolve_target(project: Path, target: dict[str, Any]) -> str:
    if target.get("url"):
        return str(target["url"])
    if target.get("path"):
        path = Path(str(target["path"]))
        if not path.is_absolute():
            path = project / path
        if not path.is_file():
            fail(f"target path does not exist: {path}")
        suffix = str(target.get("query") or "")
        return f"{path.resolve().as_uri()}{suffix}"
    fail("target requires url or path")


def apply_interaction(page, interaction: object) -> None:
    if not interaction:
        return
    if not isinstance(interaction, dict):
        fail("interaction must be an object")
    action = interaction.get("type")
    selector = interaction.get("selector")
    if action in {"hover", "focus", "click"} and not selector:
        fail(f"interaction {action} requires selector")
    if action == "hover":
        page.locator(selector).hover()
    elif action == "focus":
        page.locator(selector).focus()
    elif action == "click":
        page.locator(selector).click()
    elif action in {None, "none"}:
        return
    else:
        fail(f"unsupported interaction type: {action}")


def inspect_styles(page, specs: object) -> list[dict[str, Any]]:
    if not specs:
        return []
    if not isinstance(specs, list):
        fail("inspect must be a list")
    results: list[dict[str, Any]] = []
    for spec in specs:
        if not isinstance(spec, dict):
            fail("inspect entry must be an object")
        selector = spec.get("selector")
        properties = spec.get("properties") or []
        if not selector or not isinstance(properties, list):
            fail("inspect entry requires selector and properties list")
        values = page.locator(selector).evaluate(
            """(el, props) => {
                const style = getComputedStyle(el);
                const out = {};
                for (const prop of props) out[prop] = style.getPropertyValue(prop);
                const rect = el.getBoundingClientRect();
                out.__rect = {x: rect.x, y: rect.y, width: rect.width, height: rect.height};
                return out;
            }""",
            properties,
        )
        results.append({
            "name": spec.get("name") or selector,
            "selector": selector,
            "values": values,
        })
    return results


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture(plan_path: Path, project: Path, output_path: Path) -> dict[str, Any]:
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}
    if plan.get("version") != 1:
        fail("capture plan version must be 1")

    provider = plan.get("provider") or {}
    if not isinstance(provider, dict):
        fail("provider must be an object")
    channel = str(provider.get("browser_channel") or "chrome")
    headless = bool(provider.get("headless", True))
    source_revision = str(provider.get("source_revision") or "unknown")

    target_entries = plan.get("targets") or []
    if not isinstance(target_entries, list):
        fail("targets must be a list")
    targets: dict[str, dict[str, Any]] = {}
    for target in target_entries:
        if not isinstance(target, dict) or not target.get("id"):
            fail("each target requires an id")
        targets[str(target["id"])] = target

    capture_entries = plan.get("captures") or []
    if not isinstance(capture_entries, list) or not capture_entries:
        fail("captures must be a non-empty list")

    results: list[dict[str, Any]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=channel, headless=headless)
        try:
            browser_version = browser.version
            for entry in capture_entries:
                if not isinstance(entry, dict):
                    fail("capture entry must be an object")
                capture_id = str(entry.get("id") or "")
                target_id = str(entry.get("target") or "")
                if not capture_id or target_id not in targets:
                    fail(f"capture requires id and known target: {capture_id or '<missing>'}")

                viewport = entry.get("viewport") or {}
                width = viewport.get("width")
                height = viewport.get("height")
                if not isinstance(width, int) or width <= 0 or not isinstance(height, int) or height <= 0:
                    fail(f"capture {capture_id} requires positive viewport width/height")

                artifact = Path(str(entry.get("artifact") or ""))
                if not artifact.is_absolute():
                    artifact = project / artifact
                artifact.parent.mkdir(parents=True, exist_ok=True)

                context = browser.new_context(viewport={"width": width, "height": height})
                page = context.new_page()
                try:
                    url = resolve_target(project, targets[target_id])
                    page.goto(url, wait_until=str(targets[target_id].get("wait_until") or "load"))
                    apply_interaction(page, entry.get("interaction"))
                    page.screenshot(path=str(artifact), full_page=bool(entry.get("full_page", True)))
                    metrics = inspect_styles(page, entry.get("inspect"))
                finally:
                    context.close()

                results.append({
                    "id": capture_id,
                    "kind": "screenshot",
                    "phase": entry.get("phase"),
                    "target": targets[target_id].get("label") or target_id,
                    "state": entry.get("state") or "default",
                    "viewport": {
                        "label": viewport.get("label"),
                        "width": width,
                        "height": height,
                    },
                    "artifact": str(artifact.relative_to(project)) if artifact.is_relative_to(project) else str(artifact),
                    "artifact_sha256": sha256(artifact),
                    "artifact_bytes": artifact.stat().st_size,
                    "provenance": {
                        "provider": "playwright-chrome",
                        "provider_version": package_version("playwright"),
                        "browser_channel": channel,
                        "browser_version": browser_version,
                        "source_revision": source_revision,
                        "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    },
                    "metrics": metrics,
                })
        finally:
            browser.close()

    result = {
        "version": 1,
        "provider": "playwright-chrome",
        "captures": results,
        "visual_quality_inferred": False,
        "note": "Capture provider records rendered artifacts and observable browser metrics only; Visual Quality Review remains a separate decision.",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture provider-neutral rendered visual evidence with Playwright using an installed Chrome channel.")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args()

    try:
        result = capture(args.plan.resolve(), args.project.resolve(), args.output.resolve())
    except Exception as exc:
        if args.format == "json":
            print(json.dumps({"valid": False, "error": str(exc)}, indent=2))
        else:
            print(f"VISUAL CAPTURE FAILED: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps({"valid": True, **result}, indent=2))
    else:
        print(f"VISUAL CAPTURE PASSED captures={len(result['captures'])}")
        print(result["note"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
